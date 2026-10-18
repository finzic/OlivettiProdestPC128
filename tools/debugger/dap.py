#!/usr/bin/env python3
"""Debug Adapter Protocol server for the PC128 (stdio). Started by the VS Code extension
tools/vscode-pc128-debug, debug type "pc128".

launch.json attributes:
    program        .asm (assembled with lwasm, loaded, EXEC'd) or .bas (typed, RUN); optional
    stopOnEntry    stop at the program entry / first BASIC line (default false)
    noExec         load the program without running it
    headless       no MAME window (default false)
    symbols        extra symbol files (.sym, lwasm --symbol-dump, .json)
    boot           go through the boot menu first (default true)
  media, the same choices as a normal run (unset = config.json):
    media          "floppy351" | "floppy" | "cassette" | "cartridge" | "none", with image / image2
                   (the run-mame.sh / VS Code task choice)
    floppy, floppy2, floppyController ("cd90_351" | "cd90_640"), cassette, cartridge
    mameArgs       extra MAME arguments
"""
import base64
import json
import os
import sys
import threading
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from commands import Session, SETLINE, DIRECT_MODE, CC_FLAGS, bank_sort_key  # noqa: E402
from client import DebugError  # noqa: E402
import symbols as symlib  # noqa: E402
import pc128  # noqa: E402

THREAD_ID = 1
REG_ORDER = ("PC", "A", "B", "D", "X", "Y", "U", "S", "DP", "CC")
SCOPE_REGS, SCOPE_FLAGS, SCOPE_BANKS, SCOPE_LOC, SCOPE_BASIC, SCOPE_STACK = 1, 2, 3, 4, 5, 6
STOP_REASON = {"breakpoint": "breakpoint", "basic-line": "breakpoint", "watchpoint": "data breakpoint",
               "step": "step", "over": "step", "out": "step", "nextline": "step", "until": "step",
               "pause": "pause", "entry": "entry"}


def launch_media(a):
    """launch.json attributes -> media dict for Session.start (empty strings = not set)."""
    media = pc128.media_from_kind(a["media"], a.get("image", ""), a.get("image2", "")) if a.get("media") else {}
    for key, attr in (("floppy", "floppy"), ("floppy2", "floppy2"), ("controller", "floppyController"),
                      ("cassette", "cassette"), ("cartridge", "cartridge")):
        if a.get(attr):
            media[key] = a[attr]
    return media


class Adapter:
    def __init__(self, rfile, wfile):
        self.rfile, self.wfile = rfile, wfile
        self.seq = 1
        self.wlock = threading.Lock()
        self.s = None
        self.args = {}
        self.client_caps = {}
        self.source_bps = {}        # file -> [mame index]
        self.fn_bps, self.insn_bps, self.data_bps = [], [], []
        self.ready = threading.Event()
        self.configured = threading.Event()
        self.terminated = False
        self.stepping_basic = False

    # ------------------------------------------------------------ wire --
    def send(self, msg):
        msg["seq"] = self.seq
        self.seq += 1
        body = json.dumps(msg).encode()
        with self.wlock:
            self.wfile.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
            self.wfile.flush()

    def respond(self, req, body=None, success=True, message=None):
        r = {"type": "response", "request_seq": req["seq"], "command": req["command"], "success": success}
        if body is not None:
            r["body"] = body
        if message:
            r["message"] = message
        self.send(r)

    def event(self, name, body=None):
        e = {"type": "event", "event": name}
        if body is not None:
            e["body"] = body
        self.send(e)

    def log(self, text, category="console"):
        self.event("output", {"category": category, "output": text if text.endswith("\n") else text + "\n"})

    def read_message(self):
        length = None
        while True:
            line = self.rfile.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            k, _, v = line.decode().partition(":")
            if k.lower() == "content-length":
                length = int(v)
        return json.loads(self.rfile.read(length)) if length else None

    def run(self):
        while not self.terminated:
            msg = self.read_message()
            if msg is None:
                break
            if msg.get("type") != "request":
                continue
            handler = getattr(self, "req_" + msg["command"], None)
            if handler is None:
                self.respond(msg, success=False, message="unsupported request " + msg["command"])
                continue
            try:
                handler(msg, msg.get("arguments") or {})
            except DebugError as e:
                self.respond(msg, success=False, message=str(e))
            except Exception as e:
                self.log(traceback.format_exc(), "stderr")
                self.respond(msg, success=False, message="%s: %s" % (type(e).__name__, e))
        self.shutdown()

    def background(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    # ---------------------------------------------------------- session --
    def on_session_event(self, name, data):
        if name == "stopped":
            reason = STOP_REASON.get(data.get("kind"), "pause")
            body = {"reason": reason, "threadId": THREAD_ID, "allThreadsStopped": True}
            if data.get("description"):
                body["description"] = data["description"]
                body["text"] = data["description"]
            if data.get("bp"):
                body["hitBreakpointIds"] = data["bp"]
            self.event("stopped", body)
        elif name == "running":
            self.event("continued", {"threadId": THREAD_ID, "allThreadsContinued": True})
        elif name == "exited":
            if not self.terminated:
                self.event("exited", {"exitCode": 0})
                self.event("terminated")
                self.terminated = True
        elif name == "output":
            self.log(data.get("text", ""))

    def shutdown(self):
        if self.s:
            try:
                self.s.close()
            except Exception:
                pass

    # -------------------------------------------------------- lifecycle --
    def req_initialize(self, req, a):
        self.client_caps = a
        self.respond(req, {
            "supportsConfigurationDoneRequest": True,
            "supportsFunctionBreakpoints": True,
            "supportsConditionalBreakpoints": True,
            "supportsEvaluateForHovers": True,
            "supportsSetVariable": True,
            "supportsReadMemoryRequest": True,
            "supportsWriteMemoryRequest": True,
            "supportsDisassembleRequest": True,
            "supportsSteppingGranularity": True,
            "supportsInstructionBreakpoints": True,
            "supportsDataBreakpoints": True,
            "supportsTerminateRequest": True,
            "supportsValueFormattingOptions": False,
            "supportsCompletionsRequest": False,
        })

    def req_launch(self, req, a):
        self.args = a
        try:
            self.s = Session(extra_symbols=a.get("symbols") or [])
        except Exception as e:
            self.respond(req, success=False, message=str(e))
            return
        self.s.listeners.append(self.on_session_event)
        prog = a.get("program")
        if prog and Path(prog).suffix.lower() not in (".bas", ".txt"):
            try:
                self.s.assemble_program(prog)       # source map before breakpoints arrive
            except Exception as e:
                self.respond(req, success=False, message="assembly failed:\n%s" % e)
                return
        elif prog:
            self.s.basic_file = str(Path(prog).resolve())
            self.s.basic_lines = self.s.parse_basic_source(Path(prog).read_text(errors="replace"))

        try:
            media = launch_media(a)
            pc128.mame_media_args(self.s.cfg, media)            # report bad paths before booting
        except ValueError as e:
            self.respond(req, success=False, message=str(e))
            return

        def boot():
            try:
                self.s.start(media=media, window=not a.get("headless", False), boot=a.get("boot", True),
                             log=self.log, extra_args=a.get("mameArgs") or [])
            except Exception as e:
                self.respond(req, success=False, message=str(e))
                self.event("terminated")
                return
            self.log("MAME ready (debug port %s). Type 'help' in the debug console for commands." % self.s.client.port)
            self.respond(req)
            self.event("initialized")
            if not self.configured.wait(60):
                self.log("no configurationDone from the client; continuing")
            self.start_program()
        self.background(boot)

    def start_program(self):
        a = self.args
        prog = a.get("program")
        try:
            if prog:
                self.s.load_program(prog, exec_program=not a.get("noExec", False),
                                    stop_on_entry=a.get("stopOnEntry", False), log=self.log,
                                    assembled=self.s.program if not prog.lower().endswith((".bas", ".txt")) else None)
            elif a.get("stopOnEntry"):
                self.s.pause(wait=False)
        except Exception as e:
            self.log("program load failed: %s" % e, "stderr")

    def req_configurationDone(self, req, a):
        self.respond(req)
        self.configured.set()

    def req_disconnect(self, req, a):
        self.terminated = True
        self.respond(req)
        self.shutdown()

    def req_terminate(self, req, a):
        self.respond(req)
        self.shutdown()

    # ------------------------------------------------------ breakpoints --
    def _verified(self, bp, line=None, source=None, message=None):
        out = {"id": bp.index, "verified": True}
        if line:
            out["line"] = line
        if source:
            out["source"] = source
        if message:
            out["message"] = message
        return out

    def req_setBreakpoints(self, req, a):
        src = a.get("source", {})
        path = src.get("path")
        key = str(Path(path).resolve()) if path else src.get("name", "?")
        for idx in self.source_bps.pop(key, []):
            self.s.clear_breakpoint(idx)
        out, ids = [], []
        is_basic = key.lower().endswith((".bas", ".txt"))
        for b in a.get("breakpoints", []):
            line, cond = b["line"], b.get("condition")
            try:
                if is_basic:
                    text = Path(key).read_text(errors="replace").replace("\r\n", "\n").split("\n")
                    import re
                    num = None
                    for i in range(line - 1, len(text)):
                        m = re.match(r"^\s*(\d+)", text[i])
                        if m:
                            num, line = int(m.group(1)), i + 1
                            break
                    if num is None:
                        out.append({"verified": False, "line": b["line"], "message": "no BASIC line here"})
                        continue
                    bp = self.s.set_basic_breakpoint(num, cond)
                else:
                    hit = self.s.source_line_to_addr(key, line)
                    if hit is None:
                        out.append({"verified": False, "line": line,
                                    "message": "no code for this line in the launched program"})
                        continue
                    addr, line = hit
                    bp = self.s.set_breakpoint(addr, None, cond, source=(key, line))
                ids.append(bp.index)
                out.append(self._verified(bp, line, src))
            except DebugError as e:
                out.append({"verified": False, "line": line, "message": str(e)})
        self.source_bps[key] = ids
        self.respond(req, {"breakpoints": out})

    def _replace(self, old, specs, make):
        for idx in old:
            self.s.clear_breakpoint(idx)
        old.clear()
        out = []
        for spec in specs:
            try:
                bp = make(spec)
                old.append(bp.index)
                out.append(self._verified(bp, message=bp.describe(self.s)))
            except DebugError as e:
                out.append({"verified": False, "message": str(e)})
        return out

    def req_setFunctionBreakpoints(self, req, a):
        def make(spec):
            name = spec["name"].strip()
            if name.lower().startswith("line "):
                return self.s.set_basic_breakpoint(int(name[5:]), spec.get("condition"))
            addr, _, space = self.s.parse_addr(name, allow_view=False)
            return self.s.set_breakpoint(addr, space, spec.get("condition"))
        self.respond(req, {"breakpoints": self._replace(self.fn_bps, a.get("breakpoints", []), make)})

    def req_setInstructionBreakpoints(self, req, a):
        def make(spec):
            addr = (int(spec["instructionReference"], 0) + spec.get("offset", 0)) & 0xFFFF
            return self.s.set_breakpoint(addr, None, spec.get("condition"))
        self.respond(req, {"breakpoints": self._replace(self.insn_bps, a.get("breakpoints", []), make)})

    def req_dataBreakpointInfo(self, req, a):
        name = a.get("name", "")
        ref = a.get("variablesReference")
        try:
            if ref == SCOPE_REGS and name in ("X", "Y", "U", "S"):
                addr = self.s.regs()[name]
                length = 1
            else:
                spec, _, ln = name.partition(":")
                addr, _, _ = self.s.parse_addr(spec, allow_view=False)
                length = int(ln) if ln else 1
        except Exception:
            self.respond(req, {"dataId": None, "description": "not an address: %s" % name})
            return
        self.respond(req, {"dataId": "%04X:%d" % (addr, length), "description": "$%04X (%d byte%s)" % (
            addr, length, "s" if length > 1 else ""), "accessTypes": ["read", "write", "readWrite"], "canPersist": True})

    def req_setDataBreakpoints(self, req, a):
        for idx in self.data_bps:
            self.s.clear_watchpoint(idx)
        self.data_bps = []
        out = []
        for b in a.get("breakpoints", []):
            addr, _, ln = b["dataId"].partition(":")
            kind = {"read": "r", "write": "w", "readWrite": "rw"}.get(b.get("accessType", "write"), "w")
            try:
                idx = self.s.set_watchpoint(int(addr, 16), int(ln or 1), kind, b.get("condition"))
                self.data_bps.append(idx)
                out.append({"id": 1000 + idx, "verified": True})
            except DebugError as e:
                out.append({"verified": False, "message": str(e)})
        self.respond(req, {"breakpoints": out})

    # -------------------------------------------------------- execution --
    def req_threads(self, req, a):
        self.respond(req, {"threads": [{"id": THREAD_ID, "name": "6809"}]})

    def req_continue(self, req, a):
        self.s.go()
        self.respond(req, {"allThreadsContinued": True})

    def req_pause(self, req, a):
        self.respond(req)
        self.s.pause(wait=False)

    def _in_basic_context(self):
        return bool(self.s.basic_file) and self.s.last_stop.get("kind") in ("basic-line", "nextline", "entry") \
            and self.s.last_stop.get("pc") == SETLINE

    def req_next(self, req, a):
        self.respond(req)
        if a.get("granularity") != "instruction" and self._in_basic_context():
            self.s.next_basic_line(wait=False)
        else:
            self.s.step_over(wait=False)

    def req_stepIn(self, req, a):
        self.respond(req)
        if a.get("granularity") != "instruction" and self._in_basic_context():
            self.s.next_basic_line(wait=False)
        else:
            self.s.step(1, wait=False)

    def req_stepOut(self, req, a):
        self.respond(req)
        self.s.step_out(wait=False)

    # ------------------------------------------------------------ state --
    def _source(self, path):
        return {"name": Path(path).name, "path": path}

    def _program_source(self, addr, loc):
        """Source line of the loaded program at addr, if the program's bytes are what is mapped there."""
        if loc.kind in ("rom", "ext"):
            return None
        if loc.kind == "page" and loc.space != "p%d" % (int(self.s.cfg["default_bank"]) + 1):
            return None
        return self.s.addr_to_source(addr)

    def req_stackTrace(self, req, a):
        s = self.s
        frames = []
        banks = s.banks()
        for i, addr in enumerate(s.backtrace()):
            loc = s.locator.locate(addr, banks)
            sym = symlib.fmt_symbol(s.symbols.lookup(loc))
            name = sym or "$%04X" % addr
            if loc.kind == "rom":
                name += "  [%s]" % loc.space
            elif loc.kind == "page":
                name += "  [%s]" % loc.space
            f = {"id": i + 1, "name": name, "line": 0, "column": 0,
                 "instructionPointerReference": "0x%04X" % addr}
            src = self._program_source(addr, loc)
            if src:
                f["source"] = self._source(src[0])
                f["line"] = src[1]
                f["column"] = 1
            elif loc.kind in ("rom", "ext"):
                f["presentationHint"] = "subtle" if i else "normal"
            frames.append(f)
        if s.basic_file:
            try:
                r = s.regs()
                cur = r["U"] if r["PC"] == SETLINE and s._space_at(SETLINE) == "b128.1" else s.basic_line_value()
            except DebugError:
                cur = DIRECT_MODE
            if cur != DIRECT_MODE and cur in s.basic_lines:
                frames.append({"id": 900, "name": "BASIC line %d" % cur, "line": s.basic_lines[cur], "column": 1,
                               "source": self._source(s.basic_file)})
                if self._in_basic_context():
                    frames.insert(0, frames.pop())
        self.respond(req, {"stackFrames": frames, "totalFrames": len(frames)})

    def req_scopes(self, req, a):
        scopes = [{"name": "Registers", "variablesReference": SCOPE_REGS, "expensive": False},
                  {"name": "Location / ROM", "variablesReference": SCOPE_LOC, "expensive": False},
                  {"name": "Banking", "variablesReference": SCOPE_BANKS, "expensive": False},
                  {"name": "Stack", "variablesReference": SCOPE_STACK, "expensive": False},
                  {"name": "BASIC", "variablesReference": SCOPE_BASIC, "expensive": False}]
        self.respond(req, {"scopes": scopes})

    def _var(self, name, value, ref=0, mem=None, kind=None):
        v = {"name": name, "value": value, "variablesReference": ref}
        if mem is not None:
            v["memoryReference"] = "0x%04X" % mem
        if kind:
            v["presentationHint"] = {"kind": kind}
        return v

    def req_variables(self, req, a):
        s = self.s
        ref = a["variablesReference"]
        out = []
        if ref == SCOPE_REGS:
            r = s.regs()
            for name in REG_ORDER:
                width = 4 if name in ("PC", "D", "X", "Y", "U", "S") else 2
                val = "$%0*X" % (width, r[name])
                if width == 4:
                    sym = symlib.fmt_symbol(s.symbols.lookup(s.locate(r[name]), 0x100))
                    if sym:
                        val += "  <%s>" % sym
                    out.append(self._var(name, val, mem=r[name]))
                elif name == "CC":
                    flags = "".join(f if r["CC"] & (0x80 >> i) else "." for i, f in enumerate(CC_FLAGS))
                    out.append(self._var(name, "%s  %s" % (val, flags), SCOPE_FLAGS))
                else:
                    out.append(self._var(name, "%s  (%d)" % (val, r[name])))
        elif ref == SCOPE_FLAGS:
            cc = s.regs()["CC"]
            names = {"E": "entire state", "F": "FIRQ mask", "H": "half carry", "I": "IRQ mask",
                     "N": "negative", "Z": "zero", "V": "overflow", "C": "carry"}
            for i, f in enumerate(CC_FLAGS):
                out.append(self._var("%s (%s)" % (f, names[f]), "1" if cc & (0x80 >> i) else "0"))
        elif ref == SCOPE_LOC:
            r = s.regs()
            loc, sym = s.where(r["PC"])
            out.append(self._var("PC", "$%04X" % r["PC"], mem=r["PC"]))
            out.append(self._var("mapped", loc.describe()))
            out.append(self._var("symbol", sym or "-"))
            if loc.rom_offset is not None:
                out.append(self._var("rom offset", "$%04X in pc128.rom (%s)" % (loc.rom_offset, loc.space)))
            src = self._program_source(r["PC"], loc)
            if src:
                out.append(self._var("source", "%s:%d" % (Path(src[0]).name, src[1])))
        elif ref == SCOPE_BANKS:
            b = s.banks()
            for start, end in ((0x0000, 0x1FFF), (0x2000, 0x5FFF), (0x6000, 0x7FFF), (0x8000, 0x9FFF),
                               (0xA000, 0xA7BF), (0xA7C0, 0xA7FF), (0xB000, 0xBFFF), (0xC000, 0xEFFF), (0xF000, 0xFFFF)):
                out.append(self._var("$%04X-$%04X" % (start, end), s.locator.locate(start, b).describe(), mem=start))
            for k, v in sorted(b.items(), key=bank_sort_key):
                out.append(self._var(k, str(v)))
        elif ref == SCOPE_STACK:
            r = s.regs()
            data = s.read(r["S"], 32)
            for i in range(0, 32, 2):
                if data[i] is None or data[i + 1] is None:
                    continue
                w = (data[i] << 8) | data[i + 1]
                sym = symlib.fmt_symbol(s.symbols.lookup(s.locate(w), 0x100))
                out.append(self._var("S+%d ($%04X)" % (i, (r["S"] + i) & 0xFFFF),
                                     "$%04X%s" % (w, "  <%s>" % sym if sym else ""), mem=w))
        elif ref == SCOPE_BASIC:
            v = s.basic_line_value()
            out.append(self._var("current line ($2131)", "direct mode" if v == DIRECT_MODE else str(v)))
            r = s.regs()
            if r["PC"] == SETLINE and s._space_at(SETLINE) == "b128.1":
                out.append(self._var("line about to run", str(r["U"])))
            tp = s.client.read_bytes(0x21C7, 2)
            out.append(self._var("text pointer ($21C7)", "$%04X" % ((tp[0] << 8) | tp[1]), mem=(tp[0] << 8) | tp[1]))
        self.respond(req, {"variables": out})

    def req_setVariable(self, req, a):
        s = self.s
        ref, name, value = a["variablesReference"], a["name"], a["value"].strip()
        if ref == SCOPE_REGS and name in REG_ORDER:
            s.require_stopped()
            v = s.eval_expr(value.split()[0])
            s.client.set_reg(name, v)
            self.respond(req, {"value": "$%04X" % v if name in ("PC", "D", "X", "Y", "U", "S") else "$%02X" % v})
        elif ref == SCOPE_FLAGS:
            bit = 0x80 >> CC_FLAGS.index(name[0])
            cc = s.regs()["CC"]
            cc = (cc | bit) if value not in ("0", "false") else (cc & ~bit)
            s.client.set_reg("CC", cc & 0xFF)
            self.respond(req, {"value": "1" if cc & bit else "0"})
        else:
            raise DebugError("read-only")
        self._invalidate()

    def _invalidate(self):
        if self.client_caps.get("supportsInvalidatedEvent"):
            self.event("invalidated", {"areas": ["variables"], "threadId": THREAD_ID})

    # ----------------------------------------------------------- memory --
    def req_readMemory(self, req, a):
        addr = (int(a["memoryReference"], 0) + a.get("offset", 0))
        count = a.get("count", 0)
        if addr < 0 or addr > 0xFFFF:
            self.respond(req, {"address": "0x%X" % max(addr, 0), "unreadableBytes": count})
            return
        n = min(count, 0x10000 - addr)
        data = self.s.read(addr, n)
        raw = bytes(0 if b is None else b for b in data)
        self.respond(req, {"address": "0x%04X" % addr, "data": base64.b64encode(raw).decode(),
                           "unreadableBytes": count - n})

    def req_writeMemory(self, req, a):
        addr = (int(a["memoryReference"], 0) + a.get("offset", 0)) & 0xFFFF
        data = base64.b64decode(a["data"])
        self.s.write(addr, data)
        self.respond(req, {"offset": 0, "bytesWritten": len(data)})
        self.event("memory", {"memoryReference": a["memoryReference"], "offset": a.get("offset", 0), "count": len(data)})
        self._invalidate()

    def req_disassemble(self, req, a):
        s = self.s
        base = (int(a["memoryReference"], 0) + a.get("offset", 0)) & 0xFFFF
        ioff = a.get("instructionOffset", 0)
        count = a["instructionCount"]
        before = []
        if ioff < 0:
            before = self._disasm_back(base, -ioff)
        insns = list(before)
        addr = base
        if ioff > 0:
            skip = s.disasm(base, ioff)
            addr = (skip[-1].addr + skip[-1].length) & 0xFFFF
        while len(insns) < count:
            chunk = s.disasm(addr, min(count - len(insns), 64))
            insns += chunk
            addr = (chunk[-1].addr + chunk[-1].length) & 0xFFFF
        banks = s.banks()
        out = []
        for ins in insns[:count]:
            loc = s.locator.locate(ins.addr, banks)
            label = s.symbols.exact(loc)
            text = ins.text
            if ins.comment:
                text += "    ; " + ins.comment
            elif ins.target is not None:
                tsym = symlib.fmt_symbol(s.symbols.lookup(s.locator.locate(ins.target, banks), 0x40))
                if tsym:
                    text += "    ; " + tsym
            d = {"address": "0x%04X" % ins.addr, "instructionBytes": ins.raw.hex(" ").upper(), "instruction": text}
            if label:
                d["symbol"] = label.name
            src = self._program_source(ins.addr, loc)
            if src:
                d["location"] = self._source(src[0])
                d["line"] = src[1]
            if "invalid" in ins.flags:
                d["presentationHint"] = "invalid"
            out.append(d)
        self.respond(req, {"instructions": out})

    def _disasm_back(self, addr, n, depth=0):
        """n instructions ending right before addr. 6809 code is variable length, so prefer known
        instruction starts (program source map), then the longest lookback that lands exactly on addr
        (decoding from further back self-synchronises more reliably)."""
        lo = max(0, addr - n * 5 - 8)
        known = sorted(x for x in self.s.addr_to_src if lo <= x < addr)
        starts = known[:1] + list(range(lo, addr - n + 1))
        for start in starts:
            seq, a = [], start
            for i in self.s.disasm(start, addr - start):
                if a >= addr:
                    break
                seq.append(i)
                a = i.addr + i.length
            if a == addr and len(seq) >= n:
                return seq[-n:]
            if a == addr and start in known and seq and depth < 4:
                return (self._disasm_back(start, n - len(seq), depth + 1) + seq)[-n:]
        return self.s.disasm(max(0, addr - n), n)

    # --------------------------------------------------------- evaluate --
    def req_evaluate(self, req, a):
        s = self.s
        expr = a.get("expression", "").strip()
        ctx = a.get("context", "repl")
        if ctx == "repl":
            if expr.startswith(">"):
                expr = expr[1:]
            try:
                out = s.execute(expr)
            except DebugError as e:
                if "unknown command" not in str(e):
                    raise
                out = self._eval_value(expr)
            self.respond(req, {"result": out, "variablesReference": 0})
            if s.is_stopped:
                self._invalidate()
            return
        self.respond(req, {"result": self._eval_value(expr), "variablesReference": 0})

    def _eval_value(self, expr):
        s = self.s
        up = expr.upper()
        if up in REG_ORDER:
            v = s.regs()[up]
            return "$%04X" % v if up in ("PC", "D", "X", "Y", "U", "S") else "$%02X (%d)" % (v, v)
        spec, _, ln = expr.partition(":")
        addr, view, space = s.parse_addr(spec)
        n = int(ln) if ln.isdigit() else 8
        data = s.read(addr, n, view)
        hx = " ".join("??" if b is None else "%02X" % b for b in data)
        sym = s.symbol_at(addr, space)
        return "$%04X%s: %s" % (addr, " <%s>" % sym if sym else "", hx)


def main():
    if sys.platform == "win32":
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    ad = Adapter(sys.stdin.buffer, sys.stdout.buffer)
    sys.stdout = sys.stderr       # stray prints must not corrupt the protocol stream
    ad.run()


if __name__ == "__main__":
    main()
