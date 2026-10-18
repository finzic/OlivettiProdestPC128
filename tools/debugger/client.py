"""Client for the MAME-side debug server (pc128_dbg.lua): launch MAME, talk to it, wait for stops.

Standard library only. Thread-safe request/reply; events go to a queue and optional callbacks.
"""
import os
import queue
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
LUA_SERVER = HERE / "pc128_dbg.lua"
REGS = ("PC", "S", "U", "X", "Y", "A", "B", "DP", "CC")

sys.path.insert(0, str(ROOT))
import pc128  # noqa: E402  (config loading shared with the run harness)


class DebugError(Exception):
    pass


def tohex(text):
    return text.encode("latin-1", "replace").hex().upper() if text else "-"


def fromhex(h):
    return bytes.fromhex(h).decode("latin-1") if h and h != "-" else ""


def _die_with_parent():
    """Linux: SIGKILL MAME if the debugger front end dies without closing it (no orphaned emulators)."""
    try:
        import ctypes
        ctypes.CDLL("libc.so.6", use_errno=True).prctl(1, 9)     # PR_SET_PDEATHSIG, SIGKILL
    except Exception:
        pass


_spawn_q = None


def _spawn(cmd, **kw):
    """Popen from one thread that lives as long as the process: PR_SET_PDEATHSIG fires when the
    *thread* that forked exits, and front ends launch from short-lived worker threads."""
    global _spawn_q
    if not sys.platform.startswith("linux"):
        return subprocess.Popen(cmd, **kw)
    if _spawn_q is None:
        _spawn_q = queue.Queue()

        def spawner():
            while True:
                args, kwargs, box, done = _spawn_q.get()
                try:
                    box.append(subprocess.Popen(args, preexec_fn=_die_with_parent, **kwargs))
                except Exception as e:
                    box.append(e)
                done.set()
        threading.Thread(target=spawner, daemon=True, name="mame-spawner").start()
    box, done = [], threading.Event()
    _spawn_q.put((cmd, kw, box, done))
    done.wait()
    if isinstance(box[0], Exception):
        raise box[0]
    return box[0]


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ------------------------------------------------------------------ views --
# A "view" selects what the CPU address space shows while reading/writing:
#   None / "cpu"     the current CPU mapping
#   "1".."6"         BASIC 128 BANK n = RAM page n+1 at $6000-$9FFF
#   "p0".."p7"       raw RAM page at $6000-$9FFF
#   "mon0"/"mon1"    monitor ROM page at $F000-$FFFF
#   "b128.0"/"b128.1", "b1.0"/"b1.1"   BASIC ROM pages at $B000-$EFFF
#   "cram0".."cram7" RAM page mapped at $B000-$EFFF (cartridge-space RAM)
#   "bank9=1,..."    raw MAME bank entries
def view_to_banks(view):
    if view in (None, "", "cpu", "-"):
        return "-"
    v = str(view).strip().lower()
    if "=" in v:
        return v
    if v.isdigit():
        n = int(v)
        if not 1 <= n <= 6:
            raise DebugError("BASIC 128 bank must be 1-6 (got %s)" % view)
        return "bank7=%d,bank8=%d" % (n + 1, n + 1)
    if v.startswith("p") and v[1:].isdigit():
        n = int(v[1:])
        if not 0 <= n <= 7:
            raise DebugError("RAM page must be p0-p7")
        return "bank7=%d,bank8=%d" % (n, n)
    if v in ("mon0", "mon1"):
        return "bank9=%s" % v[3]
    if v in ("b128.0", "b128.1"):
        e = 6 + int(v[-1])
        return "bank10=%d,bank11=%d" % (e, e)
    if v in ("b1.0", "b1.1"):
        e = 4 + int(v[-1])
        return "bank10=%d,bank11=%d" % (e, e)
    if v.startswith("cram") and v[4:].isdigit():
        e = 8 + int(v[4:])
        return "bank10=%d,bank11=%d" % (e, e)
    raise DebugError("unknown memory view %r (use 1-6, p0-p7, mon0/1, b128.0/1, b1.0/1, cram0-7, cpu)" % view)


def parse_kv(payload):
    out = {}
    for tok in payload.split():
        k, _, v = tok.partition("=")
        out[k] = v
    return out


class DebugClient:
    """Connection to one MAME instance running pc128_dbg.lua."""

    def __init__(self):
        self.sock = None
        self.proc = None
        self.port = None
        self.events = queue.Queue()
        self.listeners = []
        self._pending = {}
        self._lock = threading.Lock()
        self._next_id = 1
        self._reader = None
        self.state = "run"
        self.paused = False
        self.stop_reason = ""
        self.stop_pc = None
        self._stopped = threading.Event()
        self._typed = threading.Event()
        self.closed = threading.Event()
        self.mame_output = []
        self.cfg = None
        self.snapshot_dir = None

    # ------------------------------------------------------------ launch --
    def launch(self, media=None, debugger_ui="script", start="run", window=True, extra_args=(),
               cfg_overrides=None, port=None):
        """Start MAME with the debug server, with the same media options as a normal run
        (pc128.mame_media_args): media = {"floppy", "floppy2", "controller", "cassette", "cartridge"};
        unset entries fall back to config.json."""
        cfg = pc128.load_config(cfg_overrides)
        self.cfg = cfg
        self.port = port or free_port()
        build = ROOT / "build"
        self.snapshot_dir = build / "dbg-snap"
        for d in (build / "dbg-cfg", build / "nvram", self.snapshot_dir):
            d.mkdir(parents=True, exist_ok=True)
        # Same key mapping as tools/run-mame.sh (F11 = MAME menu, F12 = exit, keyboard layout);
        # copied so a debug session never rewrites the repository's settings.
        for f in (ROOT / "tools" / "mame-cfg").glob("*.cfg"):
            shutil.copyfile(f, build / "dbg-cfg" / f.name)
        cmd = [cfg["mame"], cfg["machine"], "-debug", "-debugger", debugger_ui,
               "-autoboot_script", str(LUA_SERVER), "-skip_gameinfo",
               "-cfg_directory", str(build / "dbg-cfg"), "-nvram_directory", str(build / "nvram"),
               "-snapshot_directory", str(self.snapshot_dir), "-snapname", "%i"]
        if window:
            cmd += ["-window", "-resolution", "960x720", "-nomaximize", "-ui_active", "-noconfirm_quit"]
        else:
            cmd += ["-video", "none", "-sound", "none"]
        if cfg["rompath"]:
            cmd += ["-rompath", cfg["rompath"]]
        try:
            cmd += pc128.mame_media_args(cfg, media)
        except ValueError as e:
            raise DebugError(str(e))
        cmd += list(cfg.get("extra_args", [])) + list(extra_args)
        env = dict(os.environ, PC128_DBG_PORT=str(self.port), PC128_DBG_START=start)
        try:
            self.proc = _spawn(cmd, cwd=str(ROOT), env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, errors="replace")
        except FileNotFoundError:
            raise DebugError("MAME not found (%r). Build it with tools/prepare-mame.sh." % cfg["mame"])
        threading.Thread(target=self._pump_output, daemon=True).start()
        self.connect(self.port, timeout=60)
        hello = self.request("hello")
        if "proto=2" not in hello:
            raise DebugError("unexpected debug server: " + hello)
        return hello

    def _pump_output(self):
        for line in self.proc.stdout:
            self.mame_output.append(line.rstrip())
            if len(self.mame_output) > 400:
                del self.mame_output[:100]
            if "unknown option" in line.lower() and "debugger" in line.lower():
                self.mame_output.append("hint: rebuild MAME with tools/prepare-mame.sh (needs patch 0003)")
        self.closed.set()

    def connect(self, port, timeout=30):
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            if self.proc and self.proc.poll() is not None:
                raise DebugError("MAME exited (code %s):\n%s" % (self.proc.returncode, "\n".join(self.mame_output[-25:])))
            try:
                self.sock = socket.create_connection(("127.0.0.1", port), timeout=2)
                self.sock.settimeout(None)
                break
            except OSError as e:
                last = e
                time.sleep(0.2)
        else:
            raise DebugError("cannot connect to the MAME debug server on port %s: %s" % (port, last))
        self.port = port
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        st = parse_kv(self.request("status"))
        self.state = st.get("state", "run")
        if self.state == "stop":
            self.stop_pc = int(st.get("pc", "0"), 16)
            self._stopped.set()

    def _read_loop(self):
        buf = b""
        try:
            while True:
                chunk = self.sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    self._dispatch(line.decode("latin-1").rstrip("\r"))
        except OSError:
            pass
        self.closed.set()
        with self._lock:
            for q in self._pending.values():
                q.put(("ERR", "connection closed"))
            self._pending.clear()
        self._emit("exited", {})

    def _dispatch(self, line):
        parts = line.split(" ", 2)
        if len(parts) < 2:
            return
        rid, kind = parts[0], parts[1]
        rest = parts[2] if len(parts) > 2 else ""
        if rid == "0" and kind == "EVT":
            name, _, payload = rest.partition(" ")
            data = parse_kv(payload)
            if name == "stopped":
                self.state = "stop"
                self.stop_pc = int(data.get("pc", "0"), 16)
                self.stop_reason = fromhex(data.get("reason", "-"))
                data["reason"] = self.stop_reason
                self._stopped.set()
            elif name == "running":
                self.state = "run"
                self._stopped.clear()
            elif name == "typed":
                self._typed.set()
            elif name in ("paused", "unpaused"):
                self.paused = name == "paused"
            self._emit(name, data)
            return
        with self._lock:
            q = self._pending.pop(rid, None)
        if q:
            q.put((kind, rest))

    def _emit(self, name, data):
        self.events.put((name, data))
        for cb in list(self.listeners):
            try:
                cb(name, data)
            except Exception:  # listener bugs must not kill the reader
                pass

    # ----------------------------------------------------------- request --
    def request(self, *words, timeout=20):
        if self.closed.is_set() or not self.sock:
            raise DebugError("not connected to MAME")
        q = queue.Queue()
        with self._lock:
            rid = str(self._next_id)
            self._next_id += 1
            self._pending[rid] = q
        line = " ".join([rid] + [str(w) for w in words]) + "\n"
        self.sock.sendall(line.encode("latin-1"))
        try:
            kind, rest = q.get(timeout=timeout)
        except queue.Empty:
            with self._lock:
                self._pending.pop(rid, None)
            raise DebugError("MAME did not answer %r" % words[0])
        if kind != "OK":
            raise DebugError(rest)
        return rest

    # ------------------------------------------------------------- state --
    def status(self):
        return parse_kv(self.request("status"))

    def regs(self):
        r = {k: int(v, 16) for k, v in parse_kv(self.request("regs")).items()}
        r["D"] = (r["A"] << 8) | r["B"]
        return r

    def set_reg(self, name, value):
        self.request("setreg", name.upper(), "%X" % value)

    def banks(self):
        return {k: int(v) for k, v in parse_kv(self.request("banks")).items()}

    def read(self, addr, length, view=None, force_io=False):
        """Bytes at addr..addr+length-1; unreadable I/O bytes come back as None in a list."""
        out = []
        pos = addr
        remaining = length
        while remaining > 0:
            n = min(remaining, 0x1000)
            h = self.request("mem", "%X" % pos, "%X" % n, view_to_banks(view), "force" if force_io else "-")
            for i in range(0, len(h), 2):
                t = h[i:i + 2]
                out.append(None if t == "??" else int(t, 16))
            pos = (pos + n) & 0xFFFF
            remaining -= n
        return out

    def read_bytes(self, addr, length, view=None):
        return bytes(b if b is not None else 0 for b in self.read(addr, length, view))

    def write(self, addr, data, view=None):
        data = bytes(data)
        for i in range(0, len(data), 0x800):
            self.request("write", "%X" % ((addr + i) & 0xFFFF), data[i:i + 0x800].hex().upper(), view_to_banks(view))

    # -------------------------------------------------------- breakpoints --
    def bp_set(self, addr, condition=None, action=None, temp=False):
        r = parse_kv(self.request("bpset", "%X" % addr, "t" if temp else "-", tohex(condition), tohex(action)))
        return int(r["index"])

    def bp_clear(self, index=None):
        self.request("bpclear", *([] if index is None else [index]))

    def bp_enable(self, index, enabled=True):
        self.request("bpenable", index, 1 if enabled else 0)

    def bp_list(self):
        out = []
        for tok in self.request("bplist").split():
            idx, addr, en, cond = tok.split(":")
            out.append({"index": int(idx), "address": int(addr, 16), "enabled": en == "1", "condition": fromhex(cond)})
        return out

    def wp_set(self, addr, length=1, kind="w", condition=None, action=None):
        r = parse_kv(self.request("wpset", "%X" % addr, "%X" % length, kind, tohex(condition), tohex(action)))
        return int(r["index"])

    def wp_clear(self, index=None):
        self.request("wpclear", *([] if index is None else [index]))

    def wp_list(self):
        out = []
        for tok in self.request("wplist").split():
            idx, addr, ln, kind, en, cond = tok.split(":")
            out.append({"index": int(idx), "address": int(addr, 16), "length": int(ln, 16), "type": kind,
                        "enabled": en == "1", "condition": fromhex(cond)})
        return out

    # ---------------------------------------------------------- execution --
    def stop(self, wait=True, timeout=5):
        self._stopped.clear()
        self.request("stop")
        if wait:
            return self.wait_stopped(timeout)
        return True

    def go(self, target=None):
        self._stopped.clear()
        self.state = "run"
        self.request("go", *([] if target is None else ["%X" % target]))

    def step(self, count=1, wait=True, timeout=5):
        self._stopped.clear()
        self.request("step", count)
        if wait:
            return self.wait_stopped(timeout)
        return True

    def run_to(self, addr, wait=False, timeout=None):
        """Temporary breakpoint at addr, then run."""
        self.bp_set(addr, temp=True)
        self.go()
        if wait:
            return self.wait_stopped(timeout)
        return True

    def step_out(self, wait=False, timeout=None):
        self._stopped.clear()
        self.mame("out")
        if wait:
            return self.wait_stopped(timeout)
        return True

    def wait_stopped(self, timeout=None):
        return self._stopped.wait(timeout)

    @property
    def is_stopped(self):
        return self.state == "stop"

    def mame(self, command):
        """Run a MAME debugger console command; returns its output lines."""
        out = self.request("mame", tohex(command))
        return [fromhex(h) for h in out.split("|") if h]

    # ------------------------------------------------------------ machine --
    def throttle(self, on=True):
        self.request("throttle", 1 if on else 0)

    def type_text(self, text, line_gap=6, wait=True, timeout=None):
        """Type text on the emulated keyboard; '\\n' ends a line (sent as RETURN)."""
        self._typed.clear()
        self.request("type", tohex(text.replace("\r\n", "\n").replace("\n", "\r")), line_gap)
        if wait:
            return self._typed.wait(timeout)
        return True

    def key(self, text):
        self.request("key", tohex(text))

    def wait_frames(self, n, timeout=None):
        """Wait until the emulated machine has run n more frames (machine must be running)."""
        start = int(self.status()["frame"])
        deadline = None if timeout is None else time.time() + timeout
        while int(self.status()["frame"]) < start + n:
            if deadline and time.time() > deadline:
                return False
            time.sleep(0.05)
        return True

    def snapshot(self, timeout=5):
        before = set(self.snapshot_dir.glob("*.png")) if self.snapshot_dir else set()
        self.request("snap")
        deadline = time.time() + timeout
        while time.time() < deadline:
            new = set(self.snapshot_dir.glob("*.png")) - before
            if new:
                return max(new, key=lambda p: p.stat().st_mtime)
            time.sleep(0.1)
        return None

    def reset(self, hard=False):
        self.request("reset", "hard" if hard else "soft")

    def close(self, kill=True):
        try:
            if self.sock and not self.closed.is_set():
                try:
                    self.request("quit", timeout=3)
                except DebugError:
                    pass
                self.sock.close()
        finally:
            if self.proc and kill:
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
