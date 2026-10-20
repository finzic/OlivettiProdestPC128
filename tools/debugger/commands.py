"""Debug session + command language shared by the terminal REPL, the VS Code adapter and MCP.

`Session` wraps a DebugClient with symbols, ROM correlation, bank-qualified breakpoints,
step-over that understands PC128 `SWI <service>`, BASIC line breakpoints and live assembly.
`Session.execute(line)` runs one text command and returns its output (see HELP).
"""
from __future__ import annotations

import queue
import re
import shlex
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import pc128  # noqa: E402
import asm as asmlib  # noqa: E402
import symbols as symlib  # noqa: E402
from client import DebugClient, DebugError, view_to_banks, REGS  # noqa: E402
from m6809 import disassemble, swi_service_name  # noqa: E402

CURLIN = 0x2131          # BASIC 128: current line number (word)
SETLINE = 0xD01E         # b128.1: STU <$31, U = number of the line about to run
DIRECT_MODE = 0xFFFF
CC_FLAGS = "EFHINZVC"
ROM_SPACES = set(symlib.ROM_PAGES) | set(symlib.EXT_ROMS) | {"ext"}

HELP = """\
Addresses: hex (9000, $9000, &H9000, 0x9000), #decimal, symbols (PUTC, KW_PRINT+3), registers
(PC, X, Y, U, S; . = PC) and sums (X+10). Add @view to read/write another bank: @1..@6 BASIC BANK n,
@p0..@p7 RAM page, @mon0/@mon1, @b128.0/@b128.1, @b1.0/@b1.1, @cram0..7, @cpu (default).
Put a page prefix on a breakpoint to make it bank-qualified: bp mon0:F6D9, bp b128.1:D04B.

 State      r | regs [REG=VAL ...]       registers (set with r X=9000 CC=50)
            banks                         MAME bank entries + what is mapped where
            where [ADDR]                  location, ROM page and nearest symbol
            line                          current BASIC line number
            bt                            heuristic call stack (return addresses on S)
 Memory     m | dump ADDR[@view] [LEN]    hex dump (default 64 bytes)
            d | dis [ADDR[@view]] [N]     disassemble (default PC, 12 instructions)
 Patch      a | asm ADDR[@view] CODE      assemble and store: a 9000 LDA #1 | SWI PUTC | RTS
            hex ADDR[@view] BYTES         store bytes: hex 9000 86 41 3F 02 39
            str ADDR[@view] "TEXT"        store a string (\\n = $0D, \\0 = NUL)
            fill ADDR[@view] LEN BYTE     fill memory
 Breaks     bp [ADDR [if COND]]           set / list breakpoints (COND: MAME expression)
            bp FILE:LINE [if COND]        break at a C/asm source line (bp main.c:12)
            bl LINE [if COND]             break when BASIC line LINE starts
            bc N|all  be N  bd N          clear / enable / disable breakpoints
            wp ADDR [LEN] [r|w|rw] [if C] watchpoint;  wc N|all
 Run        g | c | go [ADDR]             continue (from ADDR)
            s | step [N]                  step into
            n | over                      step over JSR/BSR/LBSR/SWI svc
            out | finish                  run until return
            until ADDR                    run to ADDR (temporary breakpoint)
            nl | nextline                 run to the next BASIC line
            sn | si                       source step over / into (C or asm program line)
            src | list [N]                program source around PC (N lines of context)
            stop | pause                  break into the debugger
            wait [SECONDS]                wait until the machine stops (scripts)
 Symbols    sym [REGEX]                   search symbols;  sym load FILE
 Machine    type TEXT  key TEXT  snap  reset [hard]  throttle on|off
            load FILE.asm|FILE.c|FILE.bas [noexec]  build+load+EXEC / type+RUN a program
            mame COMMAND                  raw MAME debugger command
"""


@dataclass
class Breakpoint:
    index: int
    addr: int
    space: str | None = None       # bank qualifier (symbol space) or None
    condition: str | None = None
    basic_line: int | None = None
    enabled: bool = True
    source: tuple | None = None    # (file, line) for source breakpoints

    def describe(self, session):
        if self.basic_line is not None:
            s = "BASIC line %d" % self.basic_line
        else:
            s = ("%s:" % self.space if self.space else "") + "%04X" % self.addr
            name = session.symbol_at(self.addr, self.space)
            if name:
                s += " <%s>" % name
        if self.condition and self.basic_line is None:
            s += " if " + self.condition
        if self.source:
            s += "  (%s:%d)" % (Path(self.source[0]).name, self.source[1])
        return "#%d %s%s" % (self.index, s, "" if self.enabled else " [disabled]")


def bank_sort_key(kv):
    """bank1..bank11 numerically, then device banks such as extension:cd90_351:rom_bank."""
    name = kv[0]
    return (0, int(name[4:]), "") if name.startswith("bank") and name[4:].isdigit() else (1, 0, name)


class Session:
    def __init__(self, cfg_overrides=None, extra_symbols=()):
        self.cfg = pc128.load_config(cfg_overrides)
        self.symbols, self.roms_dir, self.rom = symlib.build_default(self.cfg, extra_symbols)
        self.locator = symlib.Locator()
        self.client = None
        self.bps = {}                 # MAME index -> Breakpoint
        self.wps = {}
        self.listeners = []           # callback(event, data)
        self.program = None           # AsmResult of the loaded program
        self.addr_to_src = {}
        self.src_to_addr = {}
        self.basic_file = None        # .bas source being run, and BASIC line -> file line
        self.basic_lines = {}
        self._q = queue.Queue()
        self._stopped = threading.Event()
        self._action = None           # what the next stop means: step/over/out/until/pause/entry
        self._temp_space = None
        self._temps = []              # temporary breakpoints to re-arm after a filtered stop
        self._banks_cache = None
        self._ext_checked = False
        self.last_stop = {}
        self.state = "none"
        self._quiet = False
        self.media_args = []
        self._silent = False          # internal pause/resume: don't report to front ends
        self._worker = threading.Thread(target=self._event_loop, daemon=True)
        self._worker.start()

    # ------------------------------------------------------------ launch --
    def start(self, media=None, window=True, boot=True, program=None, stop_on_entry=False,
              exec_program=True, log=print, extra_args=()):
        """Launch MAME, boot to BASIC and optionally load a .asm / .bas program.
        media: {"floppy", "floppy2", "controller", "cassette", "cartridge"} (see pc128.mame_media_args)."""
        self.media_args = pc128.mame_media_args(self.cfg, media)     # validates before MAME starts
        self.client = DebugClient()
        self.client.listeners.append(lambda name, data: self._q.put((name, data)))
        log("starting MAME%s ..." % ("" if not self.media_args else " with " + " ".join(
            a if not a.startswith("/") else Path(a).name for a in self.media_args)))
        self.client.launch(media=media, window=window, extra_args=extra_args)
        self.state = "run"
        if boot:
            self.boot(log, menu="-cart" not in self.media_args)
        if program:
            self.load_program(program, exec_program=exec_program, stop_on_entry=stop_on_entry, log=log)
        elif stop_on_entry:
            self.pause()
        return self

    def boot(self, log=print, menu=True):
        c = self.client
        key = str(self.cfg["menu_key"])
        c.throttle(False)
        c.wait_frames(int(self.cfg["boot_frames"]), timeout=120)
        if not menu:             # a cartridge takes over at power-on: don't type into it
            log("cartridge inserted: skipping the boot menu")
            c.wait_frames(int(self.cfg["menu_frames"]), timeout=120)
            c.throttle(True)
            self._check_ext()
            return
        log("booting (menu key %r) ..." % key)
        retried = False
        for _ in range(6):
            c.key(key)
            c.wait_frames(100, timeout=60)
            # BASIC 128 maps its ROM pages (bank entries 6/7) at $B000-$EFFF; the menu uses entry 5
            if key != "1" or c.banks().get("bank10") in (6, 7):
                break
            log("menu key not taken yet, retrying ...")
            retried = True
        c.wait_frames(int(self.cfg["menu_frames"]), timeout=120)
        if retried:     # a late duplicate menu key may sit on the BASIC input line: flush it
            c.type_text("\n", timeout=30)
        c.throttle(True)
        self._check_ext()

    def load_program(self, path, exec_program=True, stop_on_entry=False, log=print, assembled=None):
        path = Path(path)
        if path.suffix.lower() in (".bas", ".txt"):
            text = path.read_text(errors="replace")
            self.basic_file = str(path.resolve())
            self.basic_lines = self.parse_basic_source(text)
            lines = pc128.prepare_basic(text)
            if not exec_program:
                lines = lines[:-1]
            if stop_on_entry:
                self.set_basic_breakpoint(self._first_basic_line(lines), temporary=True)
            log("typing %d BASIC lines ..." % (len(lines) - 1))
            self._ensure_running()
            self.client.throttle(False)
            self.type_text("\n".join(lines) + "\n", timeout=300)
            self.client.throttle(True)
            return None
        res = assembled or self.assemble_program(path)
        was_stopped = self.is_stopped
        if not was_stopped:
            self._silent = True
            self.pause()
        try:
            for addr, data in res.segments:
                self.write_program(addr, data)
        except Exception:
            self._silent = False
            raise
        log("loaded %s: %d bytes in %d segment(s), entry %s" % (
            path.name, res.size, len(res.segments), "$%04X" % res.entry if res.entry is not None else "none"))
        if res.entry is None or not exec_program:
            if not was_stopped:
                self.go()
            self._silent = False
            return res
        if stop_on_entry:
            self._set_temp(res.entry)
            self._action = "entry"
        self.go()
        self._silent = False
        self.type_text("EXEC &H%04X\n" % res.entry, timeout=30)
        return res

    def type_text(self, text, timeout=120):
        """Type on the emulated keyboard; returns when typing is done or the machine stops."""
        self._ensure_running()
        self.client.type_text(text, line_gap=int(self.cfg["line_gap_frames"]), wait=False)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.client._typed.wait(0.1) or self.is_stopped:
                return True
        return False

    def assemble_program(self, path):
        """Assemble without loading: symbols + source map become available for breakpoints."""
        res = asmlib.assemble_file(path, self.cfg)
        self.program = res
        self.addr_to_src = {}
        self.src_to_addr = {}
        for ln in res.lines:
            if not ln.data:
                continue
            self.addr_to_src.setdefault(ln.addr, (ln.file, ln.line))
            self.src_to_addr.setdefault((ln.file, ln.line), ln.addr)
        for name, addr in res.symbols.items():
            self.symbols.add("any", addr, name, "program")
        return res

    def source_line_to_addr(self, file, line):
        """(address, actual line) for the first code line at or after `line` in `file`, or None."""
        file = str(Path(file).resolve())
        lines = sorted(l for (f, l) in self.src_to_addr if f == file and l >= line)
        if not lines:
            return None
        return self.src_to_addr[(file, lines[0])], lines[0]

    def addr_to_source(self, addr):
        return self.addr_to_src.get(addr)

    @staticmethod
    def parse_basic_source(text):
        """BASIC line number -> 1-based line in the source file."""
        out = {}
        for i, raw in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
            m = re.match(r"^\s*(\d+)", raw)
            if m:
                out.setdefault(int(m.group(1)), i)
        return out

    @staticmethod
    def _first_basic_line(lines):
        nums = [int(m.group(1)) for l in lines if (m := re.match(r"^\s*(\d+)", l))]
        return min(nums) if nums else 0

    def close(self):
        if self.client:
            self.client.close()
        self.state = "exited"

    # ------------------------------------------------------------ events --
    def _event_loop(self):
        while True:
            name, data = self._q.get()
            try:
                if name == "stopped":
                    self._banks_cache = None
                    info = self._classify_stop(int(data.get("pc", "0"), 16), data.get("reason", ""))
                    if info is None:          # breakpoint in the wrong bank: keep running
                        for a, cond in self._temps:     # the server drops temporary bps on every stop
                            self.client.bp_set(a, condition=cond, temp=True)
                        self.client.go()
                        continue
                    self.state = "stop"
                    self._temps = []
                    self.last_stop = info
                    silent = self._silent     # read before waking the waiter, which may clear it
                    self._stopped.set()
                    if not silent:
                        self._emit("stopped", info)
                elif name == "running":
                    self.state = "run"
                    self._stopped.clear()
                    if not self._silent:
                        self._emit("running", {})
                elif name == "exited":
                    self.state = "exited"
                    self._stopped.set()
                    self._emit("exited", {})
                else:
                    self._emit(name, data)
            except Exception as e:   # never let the event thread die
                self._emit("output", {"text": "event error: %s\n" % e})

    def _emit(self, name, data):
        for cb in list(self.listeners):
            try:
                cb(name, data)
            except Exception:
                pass

    def _classify_stop(self, pc, reason):
        action, self._action = self._action, None
        info = {"pc": pc, "reason": reason, "kind": action or "pause", "bp": [], "description": reason}
        m = re.search(r"Stopped at breakpoint (\d+)", reason)
        if m:
            idx = int(m.group(1))
            hits = []
            if idx in self.bps:       # MAME reports the breakpoint whose condition fired
                u = None
                for bp in self.bps.values():
                    if bp.addr != pc or not bp.enabled:
                        continue
                    if bp.basic_line is not None:
                        u = self.regs()["U"] if u is None else u
                        if u != bp.basic_line:
                            continue
                    hits.append(bp)
            if hits:
                ok = [bp for bp in hits if not bp.space or self._space_at(pc) == bp.space]
                if not ok:
                    self._action = action
                    return None
                info["kind"] = "breakpoint"
                info["bp"] = [bp.index for bp in ok]
                if any(bp.basic_line is not None for bp in ok):
                    info["kind"] = "basic-line"
                    info["description"] = "BASIC line %d" % self.basic_line_value(stopped_u=True)
            elif idx not in self.bps:
                space, self._temp_space = self._temp_space, None
                if space and self._space_at(pc) != space:
                    self._temp_space, self._action = space, action
                    return None
                info["kind"] = action if action in ("over", "out", "until", "entry", "nextline") else "breakpoint"
                info["description"] = ""
        elif "watchpoint" in reason.lower():
            info["kind"] = "watchpoint"
        elif action is None:
            info["kind"] = "pause"
        elif action in ("step", "out"):
            info["description"] = ""
        if info["kind"] in ("nextline", "entry") and self._space_at(pc) == "b128.1" and pc == SETLINE:
            info["description"] = "BASIC line %d" % self.regs()["U"]
        if info["kind"] != "breakpoint":
            self._temp_space = None
        return info

    def _space_at(self, addr):
        return self.locator.locate(addr, self.banks()).space

    # ------------------------------------------------------------- state --
    @property
    def is_stopped(self):
        return self.state == "stop"

    def require_stopped(self):
        if not self.is_stopped:
            raise DebugError("the machine is running (use 'stop' first)")

    def wait_stopped(self, timeout=None):
        return self._stopped.wait(timeout)

    def regs(self):
        return self.client.regs()

    def banks(self):
        if self._banks_cache is None or not self.is_stopped:
            self._banks_cache = self.client.banks()
        return self._banks_cache

    def _check_ext(self):
        try:
            sample = bytes(b or 0 for b in self.client.read(0xA000, 32))
            self.locator.identify_ext(sample, self.roms_dir)
        except DebugError:
            pass

    def locate(self, addr, banks=None):
        return self.locator.locate(addr, banks or self.banks())

    def symbol_at(self, addr, space=None, max_dist=0x200):
        if space:
            loc = symlib.Location(addr, "rom" if space in ROM_SPACES else "page", space)
            if space in symlib.EXT_ROMS or space == "ext":
                loc.kind = "ext"
        else:
            loc = self.locate(addr)
        return symlib.fmt_symbol(self.symbols.lookup(loc, max_dist))

    def where(self, addr=None):
        if addr is None:
            addr = self.regs()["PC"]
        loc = self.locate(addr)
        sym = symlib.fmt_symbol(self.symbols.lookup(loc))
        return loc, sym

    def basic_line_value(self, stopped_u=False):
        if stopped_u:
            return self.regs()["U"]
        d = self.client.read_bytes(CURLIN, 2)
        return (d[0] << 8) | d[1]

    # ----------------------------------------------------------- address --
    def parse_addr(self, text, allow_view=True):
        """'9000', '$9000@3', 'mon0:F6D9', 'PUTC+2', 'X+$10' -> (addr, view, space)."""
        t = text.strip()
        view = None
        if allow_view and "@" in t:
            t, view = t.rsplit("@", 1)
            view_to_banks(view)    # validate
        space = None
        m = re.match(r"^([A-Za-z][\w.]*):(.+)$", t)
        if m and m.group(1).lower() in ROM_SPACES | {"rom"} | {"p%d" % i for i in range(8)}:
            sp = m.group(1).lower()
            val = self.eval_expr(m.group(2))
            if sp == "rom":
                sp, val = symlib.rom_page_of(val)
                if sp is None:
                    raise DebugError("ROM offset out of range: %s" % text)
            return val & 0xFFFF, view, sp
        val = self.eval_expr(t)
        sym = self.symbols.find(t)
        if sym is not None and sym.space != "any":
            space = sym.space
        return val & 0xFFFF, view, space

    def eval_expr(self, text):
        tokens = re.findall(r"[+-]|[^+\-\s]+", text.replace(" ", ""))
        if not tokens:
            raise DebugError("missing address")
        total, sign = 0, 1
        for tok in tokens:
            if tok == "+":
                sign = 1
                continue
            if tok == "-":
                sign = -1
                continue
            total += sign * self._term(tok)
            sign = 1
        return total

    def _term(self, tok):
        up = tok.upper()
        if up.startswith("$"):
            return int(tok[1:], 16)
        if up.startswith("&H"):
            return int(tok[2:], 16)
        if up.startswith("0X"):
            return int(tok[2:], 16)
        if tok.startswith("#"):
            return int(tok[1:], 10)
        sym = self.symbols.find(tok)
        if sym is not None:
            return sym.addr
        if up in ("PC", "X", "Y", "U", "S"):
            return self.regs()[up]
        if tok == ".":
            return self.regs()["PC"]
        if re.fullmatch(r"[0-9A-Fa-f]+", tok):
            return int(tok, 16)
        raise DebugError("unknown symbol or value %r" % tok)

    # --------------------------------------------------------- execution --
    def _ensure_running(self):
        if self.is_stopped:
            self.go()

    def go(self, addr=None):
        self._stopped.clear()
        self.state = "run"
        self.client.go(addr)

    def pause(self, wait=True):
        if self.is_stopped:
            return True
        self._action = "pause"
        self._stopped.clear()
        self.client.request("stop")
        return self.wait_stopped(5) if wait else True

    def step(self, count=1, wait=True):
        self.require_stopped()
        self._action = "step"
        self._stopped.clear()
        self.state = "run"
        self.client.request("step", count)
        return self.wait_stopped(10) if wait else True

    def step_over(self, wait=True):
        self.require_stopped()
        pc = self.regs()["PC"]
        ins = self.disasm_at(pc)
        if "call" not in ins.flags:
            return self.step(1, wait)
        self._action = "over"
        self._temp_space = self._space_at(pc)
        self._set_temp((pc + ins.length) & 0xFFFF)
        self.go()
        return self.wait_stopped(10) if wait else True

    def step_out(self, wait=False):
        self.require_stopped()
        self._action = "out"
        self._stopped.clear()
        self.state = "run"
        self.client.mame("out")
        return self.wait_stopped(10) if wait else True

    def program_source_at(self, addr, loc=None):
        """(file, line) of the loaded program at addr, if the program's bytes are what is mapped there."""
        if not self.addr_to_src:
            return None
        loc = loc or self.locate(addr)
        if loc.kind in ("rom", "ext"):
            return None
        if loc.kind == "page" and loc.space != "p%d" % (int(self.cfg["default_bank"]) + 1):
            return None
        return self.addr_to_source(addr)

    def step_source(self, over=True, wait=True, max_steps=20000):
        """Source-level step (C or asm program): run until the program's source line changes.

        over=True steps over calls (JSR/BSR/SWI ...); over=False enters calls whose target has
        source (C or asm in the program/library) and steps over calls into ROM.
        Intermediate stops are silent; one 'stopped' event is reported at the end.
        """
        self.require_stopped()
        start = self.program_source_at(self.regs()["PC"])
        if start is None:
            return self.step_over(wait) if over else self.step(1, wait)
        if wait:
            return self._step_source_loop(start, over, max_steps)
        threading.Thread(target=self._step_source_loop, args=(start, over, max_steps), daemon=True).start()
        return True

    def _step_source_loop(self, start, over, max_steps):
        self._silent = True
        self._emit("running", {})
        info = None
        try:
            for _ in range(max_steps):
                pc = self.regs()["PC"]
                ins = self.disasm_at(pc)
                if "call" in ins.flags:
                    ret = (pc + ins.length) & 0xFFFF
                    if over:
                        self.step_over(False)
                        self.wait_stopped()      # a call may wait for a key: 'pause' interrupts it
                    else:
                        self.step(1, True)
                        if self.last_stop.get("kind") == "step" and \
                                self.program_source_at(self.regs()["PC"]) is None:
                            self.run_until(ret, self._space_at(pc), wait=False)
                            self.wait_stopped()
                else:
                    self.step(1, True)
                if self.state == "exited":
                    return False
                if not self.is_stopped:
                    self.pause()
                kind = self.last_stop.get("kind")
                if kind in ("breakpoint", "watchpoint", "basic-line", "pause"):
                    info = dict(self.last_stop)
                    break
                cur = self.program_source_at(self.regs()["PC"])
                if cur is None or cur != start:
                    break
            else:
                self._emit("output", {"text": "step: %d instructions without leaving %s:%d\n" % (
                    max_steps, Path(start[0]).name, start[1])})
        except Exception as e:
            self._emit("output", {"text": "step error: %s\n" % e})
        finally:
            self._silent = False
        if info is None:
            info = dict(self.last_stop, kind="step", reason="step", description="", bp=[])
            src = self.program_source_at(info.get("pc", self.regs()["PC"]))
            if src:
                info["description"] = "%s:%d" % (Path(src[0]).name, src[1])
            self.last_stop = info
        if self.state != "exited":
            self._emit("stopped", info)
        return True

    def run_until(self, addr, space=None, wait=False):
        self.require_stopped()
        self._action = "until"
        self._temp_space = space
        self._set_temp(addr)
        self.go()
        return self.wait_stopped(10) if wait else True

    def next_basic_line(self, wait=False):
        self.require_stopped()
        self._action = "nextline"
        self._temp_space = "b128.1"
        self._set_temp(SETLINE)
        self.go()
        return self.wait_stopped(10) if wait else True

    # -------------------------------------------------------- breakpoints --
    def _set_temp(self, addr, condition=None):
        self.client.bp_set(addr, condition=condition, temp=True)
        self._temps.append((addr, condition))
    def set_breakpoint(self, addr, space=None, condition=None, source=None):
        idx = self.client.bp_set(addr, condition=condition)
        bp = Breakpoint(idx, addr, space, condition, source=source)
        self.bps[idx] = bp
        return bp

    def set_basic_breakpoint(self, line, condition=None, temporary=False):
        cond = "u==0x%x" % line + (" && (%s)" % condition if condition else "")
        if temporary:
            self._action = "entry"
            self._temp_space = "b128.1"
            self._set_temp(SETLINE, cond)
            return None
        idx = self.client.bp_set(SETLINE, condition=cond)
        bp = Breakpoint(idx, SETLINE, "b128.1", cond, basic_line=line)
        self.bps[idx] = bp
        return bp

    def clear_breakpoint(self, index=None):
        if index is None:
            for i in list(self.bps):
                self.client.bp_clear(i)
            self.bps.clear()
        else:
            self.client.bp_clear(index)
            self.bps.pop(index, None)

    def enable_breakpoint(self, index, on=True):
        self.client.bp_enable(index, on)
        if index in self.bps:
            self.bps[index].enabled = on

    def set_watchpoint(self, addr, length=1, kind="w", condition=None):
        idx = self.client.wp_set(addr, length, kind, condition)
        self.wps[idx] = (addr, length, kind, condition)
        return idx

    def clear_watchpoint(self, index=None):
        self.client.wp_clear(index)
        if index is None:
            self.wps.clear()
        else:
            self.wps.pop(index, None)

    # ------------------------------------------------------------ memory --
    def read(self, addr, length, view=None):
        return self.client.read(addr, length, view)

    def write(self, addr, data, view=None):
        self.client.write(addr, data, view)
        self._banks_cache = None

    def write_program(self, addr, data):
        """Store program bytes; $6000-$9FFF goes to the BASIC bank programs run in (config default_bank),
        because the interpreter maps other pages there while it works."""
        end = addr + len(data)
        cut = [addr] + [b for b in (0x6000, 0xA000) if addr < b < end] + [end]
        for a, b in zip(cut, cut[1:]):
            view = str(self.cfg.get("default_bank", 6)) if 0x6000 <= a < 0xA000 else None
            self.write(a, data[a - addr:b - addr], view)

    def disasm_at(self, addr, view=None):
        return self.disasm(addr, 1, view)[0]

    def disasm(self, addr, count, view=None):
        raw = self.read(addr, count * 5 + 5, view)
        base = addr

        def rd(a):
            i = (a - base) & 0xFFFF
            v = raw[i] if i < len(raw) else None
            return 0 if v is None else v
        out = []
        for _ in range(count):
            ins = disassemble(rd, addr)
            out.append(ins)
            addr = (addr + ins.length) & 0xFFFF
        return out

    def format_insn(self, ins, banks=None, pc=None):
        banks = banks or self.banks()
        loc = self.locator.locate(ins.addr, banks)
        label = self.symbols.exact(loc)
        comment = ins.comment
        if ins.target is not None and not ins.comment:
            tsym = symlib.fmt_symbol(self.symbols.lookup(self.locator.locate(ins.target, banks), 0x40))
            if tsym:
                comment = tsym
        hexb = " ".join("%02X" % b for b in ins.raw)
        mark = ">" if pc == ins.addr else " "
        s = "%s%04X  %-14s %-22s" % (mark, ins.addr, hexb, ins.text)
        if comment:
            s += " ; " + comment
        if label:
            s = "%s:\n%s" % (label.name, s)
        return s.rstrip()

    def assemble(self, addr, code, view=None, write=True):
        res = asmlib.assemble_snippet(code, addr, self.cfg, self.symbols)
        if write:
            for a, data in res.segments:
                self.write(a, data, view)
        return res

    def backtrace(self, depth=8, scan=48):
        """Return addresses found on the S stack whose preceding bytes are a call instruction."""
        r = self.regs()
        frames = [r["PC"]]
        stack = self.read(r["S"], scan)
        banks = self.banks()
        for i in range(len(stack) - 1):
            if stack[i] is None or stack[i + 1] is None:
                continue
            ret = (stack[i] << 8) | stack[i + 1]
            if self._is_return_address(ret):
                frames.append(ret)
                if len(frames) > depth:
                    break
        return frames

    def _is_return_address(self, ret):
        if ret < 0x2000 or 0xA7C0 <= ret < 0xB000:
            return False
        try:
            raw = self.read((ret - 4) & 0xFFFF, 4)
        except DebugError:
            return False
        if None in raw:
            return False
        b = raw
        # JSR ext (BD hh ll), JSR dir/idx (9D xx / AD pb), BSR (8D rr), LBSR (17 hh ll), SWI svc (3F nn)
        return (b[1] == 0xBD or b[1] == 0x17 or b[2] in (0x8D, 0x9D, 0x3F) or
                (b[2] == 0xAD and not (b[3] & 0x80)) or (b[1] == 0xAD and b[2] & 0x80))

    # ------------------------------------------------------------ format --
    def format_regs(self, r=None):
        r = r or self.regs()
        cc = r["CC"]
        flags = "".join(f if cc & (0x80 >> i) else "." for i, f in enumerate(CC_FLAGS))
        loc, sym = self.where(r["PC"])
        return ("PC=%04X  A=%02X B=%02X D=%04X  X=%04X Y=%04X U=%04X S=%04X  DP=%02X  CC=%02X %s\n"
                "     at %s%s" % (r["PC"], r["A"], r["B"], r["D"], r["X"], r["Y"], r["U"], r["S"], r["DP"], cc,
                                  flags, loc.describe(), "  <%s>" % sym if sym else ""))

    def format_banks(self):
        b = self.banks()
        lines = ["MAME banks: " + " ".join("%s=%d" % kv for kv in sorted(b.items(), key=bank_sort_key))]
        for start, end in ((0x0000, 0x1FFF), (0x2000, 0x5FFF), (0x6000, 0x7FFF), (0x8000, 0x9FFF),
                           (0xA000, 0xA7BF), (0xA7C0, 0xA7FF), (0xB000, 0xBFFF), (0xC000, 0xEFFF), (0xF000, 0xFFFF)):
            lines.append("  $%04X-$%04X  %s" % (start, end, self.locator.locate(start, b).describe()))
        return "\n".join(lines)

    def format_dump(self, addr, data):
        lines = []
        for off in range(0, len(data), 16):
            row = data[off:off + 16]
            hx = " ".join("??" if v is None else "%02X" % v for v in row)
            asc = "".join("." if v is None or not 32 <= v < 127 else chr(v) for v in row)
            lines.append("%04X  %-47s  %s" % ((addr + off) & 0xFFFF, hx, asc))
        return "\n".join(lines)

    def status_line(self):
        if not self.is_stopped:
            return "running"
        info = self.last_stop
        r = self.regs()
        head = "stopped (%s%s)" % (info.get("kind", "?"), ": " + info["description"] if info.get("description") else "")
        ins = self.disasm_at(r["PC"])
        out = head + "\n" + self.format_regs(r)
        src = self.program_source_at(r["PC"])
        if src:
            out += "\n     source %s:%d%s" % (Path(src[0]).name, src[1], self._source_text(*src))
        return out + "\n" + self.format_insn(ins, pc=r["PC"])

    def _source_text(self, file, line):
        try:
            text = Path(file).read_text(errors="replace").splitlines()
            return "  " + text[line - 1].strip() if 0 < line <= len(text) else ""
        except OSError:
            return ""

    def find_source_file(self, name):
        """Resolve a source name (path or bare file name) to a file known to the program's source map."""
        p = Path(name)
        if p.exists():
            return str(p.resolve())
        files = {f for f, _ in self.src_to_addr}
        for f in sorted(files):
            if Path(f).name == p.name or f.endswith("/" + name):
                return f
        return name

    # ----------------------------------------------------------- command --
    def execute(self, line):
        line = line.strip()
        if not line or line.startswith(";"):
            return ""
        cmd, _, rest = line.partition(" ")
        cmd = cmd.lower()
        rest = rest.strip()
        fn = COMMANDS.get(cmd)
        if fn is None:
            raise DebugError("unknown command %r (try 'help')" % cmd)
        return fn(self, rest) or ""


# =================================================================== commands
def _split_if(rest):
    m = re.match(r"^(.*?)\s+if\s+(.+)$", rest, re.I)
    return (m.group(1).strip(), m.group(2).strip()) if m else (rest.strip(), None)


def cmd_help(s, rest):
    return HELP


def cmd_regs(s, rest):
    s.require_stopped()
    for tok in rest.split():
        name, _, val = tok.partition("=")
        if not val:
            raise DebugError("use REG=VALUE")
        s.client.set_reg(name.upper(), s.eval_expr(val))
    return s.format_regs()


def cmd_banks(s, rest):
    s.require_stopped()
    return s.format_banks()


def cmd_where(s, rest):
    s.require_stopped()
    if rest:
        addr, _, space = s.parse_addr(rest, allow_view=False)
        if space:
            return "%s:%04X  <%s>" % (space, addr, s.symbol_at(addr, space) or "?")
    else:
        addr = None
    loc, sym = s.where(addr)
    return "%04X  %s%s" % (loc.addr, loc.describe(), "  <%s>" % sym if sym else "")


def cmd_line(s, rest):
    s.require_stopped()
    v = s.basic_line_value()
    r = s.regs()
    if r["PC"] == SETLINE and s._space_at(SETLINE) == "b128.1":
        return "BASIC line %d is about to run (previous: %s)" % (r["U"], "direct mode" if v == DIRECT_MODE else v)
    return "direct mode (no program line)" if v == DIRECT_MODE else "BASIC line %d" % v


def cmd_bt(s, rest):
    s.require_stopped()
    out = []
    banks = s.banks()
    for i, a in enumerate(s.backtrace()):
        loc = s.locator.locate(a, banks)
        sym = symlib.fmt_symbol(s.symbols.lookup(loc))
        out.append("#%d %04X  %-28s %s" % (i, a, sym, loc.describe()))
    return "\n".join(out)


def cmd_dump(s, rest):
    s.require_stopped()
    parts = rest.split()
    if not parts:
        raise DebugError("usage: m ADDR[@view] [LEN]")
    addr, view, _ = s.parse_addr(parts[0])
    n = s.eval_expr(parts[1]) if len(parts) > 1 and not parts[1].isdigit() else int(parts[1]) if len(parts) > 1 else 64
    return s.format_dump(addr, s.read(addr, n, view))


def cmd_dis(s, rest):
    s.require_stopped()
    parts = rest.split()
    pc = s.regs()["PC"]
    view = None
    addr = pc
    if parts:
        addr, view, _ = s.parse_addr(parts[0])
    n = int(parts[1]) if len(parts) > 1 else 12
    banks = s.banks() if view is None else dict(s.banks(), **_view_dict(view))
    return "\n".join(s.format_insn(i, banks, pc) for i in s.disasm(addr, n, view))


def _view_dict(view):
    spec = view_to_banks(view)
    if spec == "-":
        return {}
    return {k: int(v) for k, v in (p.split("=") for p in spec.split(","))}


def cmd_asm(s, rest):
    s.require_stopped()
    target, _, code = rest.partition(" ")
    if not code.strip():
        raise DebugError("usage: a ADDR[@view] INSTRUCTION [| INSTRUCTION ...]")
    addr, view, _ = s.parse_addr(target)
    res = s.assemble(addr, code, view)
    out = []
    for a, data in res.segments:
        out.append("stored %d byte(s) at $%04X%s: %s" % (len(data), a, "@" + view if view else "",
                                                          " ".join("%02X" % b for b in data)))
    a0, d0 = res.segments[0]
    banks = s.banks() if view is None else dict(s.banks(), **_view_dict(view))
    out += [s.format_insn(i, banks) for i in s.disasm(a0, min(32, len(d0)), view) if i.addr < a0 + len(d0)]
    return "\n".join(out)


def cmd_hex(s, rest):
    s.require_stopped()
    target, _, data = rest.partition(" ")
    addr, view, _ = s.parse_addr(target)
    b = asmlib.parse_hex_bytes(data)
    if not b:
        raise DebugError("no bytes given")
    s.write(addr, b, view)
    return "stored %d byte(s) at $%04X: %s" % (len(b), addr, b.hex(" ").upper())


def cmd_str(s, rest):
    s.require_stopped()
    target, _, text = rest.partition(" ")
    addr, view, _ = s.parse_addr(target)
    b = asmlib.parse_string(text)
    s.write(addr, b, view)
    return "stored %d byte(s) at $%04X: %s" % (len(b), addr, b.hex(" ").upper())


def cmd_fill(s, rest):
    s.require_stopped()
    parts = rest.split()
    if len(parts) != 3:
        raise DebugError("usage: fill ADDR[@view] LEN BYTE")
    addr, view, _ = s.parse_addr(parts[0])
    n = int(parts[1], 0) if parts[1].isdigit() else s.eval_expr(parts[1])
    s.write(addr, bytes([s.eval_expr(parts[2]) & 0xFF]) * n, view)
    return "filled %d byte(s) at $%04X" % (n, addr)


def cmd_bp(s, rest):
    if not rest:
        if not s.bps:
            return "no breakpoints"
        return "\n".join(bp.describe(s) for bp in sorted(s.bps.values(), key=lambda b: b.index))
    target, cond = _split_if(rest)
    m = re.fullmatch(r"(.+\.(?:c|h|asm|s|inc)):(\d+)", target, re.I)
    if m:
        hit = s.source_line_to_addr(s.find_source_file(m.group(1)), int(m.group(2)))
        if hit is None:
            raise DebugError("no code at or after %s" % target)
        bp = s.set_breakpoint(hit[0], None, cond, source=(s.find_source_file(m.group(1)), hit[1]))
        return "breakpoint " + bp.describe(s)
    addr, _, space = s.parse_addr(target, allow_view=False)
    bp = s.set_breakpoint(addr, space, cond)
    return "breakpoint " + bp.describe(s)


def cmd_bl(s, rest):
    target, cond = _split_if(rest)
    if not target.isdigit():
        raise DebugError("usage: bl LINE [if COND]")
    bp = s.set_basic_breakpoint(int(target), cond)
    return "breakpoint " + bp.describe(s)


def _index_arg(rest):
    if rest.lower() in ("", "all", "*"):
        return None
    return int(rest.lstrip("#"))


def cmd_bc(s, rest):
    s.clear_breakpoint(_index_arg(rest))
    return "cleared"


def cmd_be(s, rest):
    s.enable_breakpoint(_index_arg(rest), True)
    return "enabled"


def cmd_bd(s, rest):
    s.enable_breakpoint(_index_arg(rest), False)
    return "disabled"


def cmd_wp(s, rest):
    if not rest:
        if not s.wps:
            return "no watchpoints"
        return "\n".join("#%d %04X len %d %s%s" % (i, a, n, k, " if " + c if c else "")
                         for i, (a, n, k, c) in sorted(s.wps.items()))
    spec, cond = _split_if(rest)
    parts = spec.split()
    addr, _, _ = s.parse_addr(parts[0], allow_view=False)
    length, kind = 1, "w"
    for p in parts[1:]:
        if p.lower() in ("r", "w", "rw"):
            kind = p.lower()
        else:
            length = int(p, 0) if p.isdigit() else s.eval_expr(p)
    idx = s.set_watchpoint(addr, length, kind, cond)
    return "watchpoint #%d %04X len %d %s" % (idx, addr, length, kind)


def cmd_wc(s, rest):
    s.clear_watchpoint(_index_arg(rest))
    return "cleared"


def _after_run(s, ok):
    if not ok:
        return "running (use 'stop' to break)"
    return s.status_line()


def cmd_go(s, rest):
    if s.is_stopped and rest:
        s.go(s.parse_addr(rest, allow_view=False)[0])
    else:
        s.go()
    return "running"


def cmd_step(s, rest):
    return _after_run(s, s.step(int(rest) if rest else 1))


def cmd_over(s, rest):
    return _after_run(s, s.step_over())


def cmd_out(s, rest):
    return _after_run(s, s.step_out(wait=True))


def cmd_until(s, rest):
    addr, _, space = s.parse_addr(rest, allow_view=False)
    return _after_run(s, s.run_until(addr, space, wait=True))


def cmd_source_next(s, rest):
    return _after_run(s, s.step_source(over=True))


def cmd_source_step(s, rest):
    return _after_run(s, s.step_source(over=False))


def cmd_src(s, rest):
    s.require_stopped()
    src = s.program_source_at(s.regs()["PC"])
    if src is None:
        return "no program source at PC"
    around = int(rest) if rest.isdigit() else 3
    try:
        text = Path(src[0]).read_text(errors="replace").splitlines()
    except OSError as e:
        return "%s:%d (%s)" % (src[0], src[1], e)
    lo, hi = max(1, src[1] - around), min(len(text), src[1] + around)
    out = [str(src[0])]
    for n in range(lo, hi + 1):
        out.append("%s%5d  %s" % ("=>" if n == src[1] else "  ", n, text[n - 1]))
    return "\n".join(out)


def cmd_nextline(s, rest):
    return _after_run(s, s.next_basic_line(wait=True))


def cmd_stop(s, rest):
    s.pause()
    return s.status_line()


def cmd_wait(s, rest):
    timeout = float(rest) if rest else 30.0
    if not s.wait_stopped(timeout):
        return "still running after %gs" % timeout
    return s.status_line()


def cmd_status(s, rest):
    return s.status_line()


def cmd_sym(s, rest):
    if rest.lower().startswith("load "):
        p = rest[5:].strip()
        n = s.symbols.load_lwasm_symbols(p) if "EQU" in Path(p).read_text(errors="replace").upper() else s.symbols.load_file(p)
        return "loaded %d symbol(s)" % n
    hits = s.symbols.names_like(rest or ".")
    lines = ["%-8s %04X  %-18s %s" % (h.space, h.addr, h.name, h.comment) for h in hits[:200]]
    if len(hits) > 200:
        lines.append("... %d more" % (len(hits) - 200))
    return "\n".join(lines) or "no match"


def cmd_type(s, rest):
    s.type_text(asmlib.parse_string(rest).decode("latin-1").replace("\r", "\n"))
    return "typed" if not s.is_stopped else s.status_line()


def cmd_key(s, rest):
    s._ensure_running()
    s.client.key(asmlib.parse_string(rest).decode("latin-1"))
    return "ok"


def cmd_snap(s, rest):
    p = s.client.snapshot()
    return str(p) if p else "no snapshot (headless?)"


def cmd_reset(s, rest):
    s.client.reset(rest.strip().lower() == "hard")
    return "reset"


def cmd_throttle(s, rest):
    s.client.throttle(rest.strip().lower() not in ("off", "0", "no"))
    return "ok"


def cmd_load(s, rest):
    parts = shlex.split(rest)
    if not parts:
        raise DebugError("usage: load FILE [noexec]")
    out = []
    s.load_program(parts[0], exec_program="noexec" not in parts[1:], log=out.append)
    return "\n".join(out)


def cmd_mame(s, rest):
    return "\n".join(s.client.mame(rest))


COMMANDS = {
    "help": cmd_help, "?": cmd_help, "h": cmd_help,
    "r": cmd_regs, "regs": cmd_regs, "banks": cmd_banks, "where": cmd_where, "line": cmd_line, "bt": cmd_bt,
    "m": cmd_dump, "dump": cmd_dump, "x": cmd_dump, "d": cmd_dis, "dis": cmd_dis, "u": cmd_dis,
    "a": cmd_asm, "asm": cmd_asm, "hex": cmd_hex, "poke": cmd_hex, "str": cmd_str, "fill": cmd_fill,
    "bp": cmd_bp, "b": cmd_bp, "bl": cmd_bl, "bc": cmd_bc, "be": cmd_be, "bd": cmd_bd,
    "wp": cmd_wp, "wc": cmd_wc,
    "g": cmd_go, "c": cmd_go, "go": cmd_go, "s": cmd_step, "step": cmd_step, "n": cmd_over, "over": cmd_over,
    "out": cmd_out, "finish": cmd_out, "until": cmd_until, "nl": cmd_nextline, "nextline": cmd_nextline,
    "sn": cmd_source_next, "si": cmd_source_step, "src": cmd_src, "list": cmd_src,
    "stop": cmd_stop, "pause": cmd_stop, "status": cmd_status, "wait": cmd_wait,
    "sym": cmd_sym, "type": cmd_type, "key": cmd_key, "snap": cmd_snap, "reset": cmd_reset,
    "throttle": cmd_throttle, "load": cmd_load, "mame": cmd_mame,
}
