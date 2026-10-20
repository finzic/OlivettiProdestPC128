#!/usr/bin/env python3
"""MCP server: lets a coding assistant run Thomson BASIC / 6809 code on a PC128 (MAME).

    pip install mcp        # works with mcp 1.x and 2.x
    python3 mcp_server.py        # stdio transport
"""
try:                                    # mcp >= 2
    from mcp.server.mcpserver import Image, MCPServer as FastMCP
except ImportError:                     # mcp 1.x
    from mcp.server.fastmcp import FastMCP, Image

import sys
import threading
from pathlib import Path

from pc128 import ROOT, format_report, run_job

sys.path.insert(0, str(ROOT / "tools" / "debugger"))

mcp = FastMCP("pc128")


def _result(report: dict):
    content = [format_report(report)]
    shot = report.get("screenshot")
    if shot:
        content.append(Image(path=shot))
    return content


@mcp.tool()
def run_basic(code: str, dump: list[str] | None = None, done_addr: str | None = None,
              run_frames: int | None = None) -> list:
    """Run PC128 BASIC 128 source (menu_key in config.json) on an emulated Olivetti Prodest PC128 (MO6).

    The program is typed into a freshly booted machine (NEW, your lines, RUN).
    Use numbered lines. Text is uppercased outside string literals.
    Results come back as CPU registers, memory dumps and a screenshot of the screen.

    Tips: POKE results into RAM and read them with `dump`; end the program with
    POKE &H9F01,1 and pass done_addr="9F01" to stop early instead of waiting run_frames.

    Args:
        code: BASIC source, one numbered line per row.
        dump: memory ranges to read back, "HEXADDR:LENGTH", e.g. ["9F00:16"]. In $6000-$9FFF
            BASIC 128 banks apply: add "@n" for BANK n (default 6, the power-on bank) or "@cpu".
        done_addr: hex address; the program writes a non-zero byte there when finished ("@n" allowed).
        run_frames: max frames (50 per emulated second) to run after RUN. Default from config.
    """
    return _result(run_job("basic", code, dump, run_frames, None, done_addr))


@mcp.tool()
def run_asm(code: str, dump: list[str] | None = None, done_addr: str | None = None,
            run_frames: int | None = None) -> list:
    """Assemble 6809 source with lwasm and run it on an emulated PC128 (MO6).

    Use ORG for the load address (user RAM is roughly $2000-$9FFF; $9000 is a safe choice)
    and `END label` to set the entry point. The code is injected into RAM after the machine
    has booted, then the CPU PC is set to the entry point, so BASIC is not involved.
    Finish with `BRA *` and/or store a non-zero byte at done_addr.

    Args:
        code: lwasm-syntax 6809 assembly.
        dump: memory ranges to read back, "HEXADDR:LENGTH", e.g. ["9F00:16"].
        done_addr: hex address; the program stores a non-zero byte there when finished.
        run_frames: max frames (50 per emulated second) to run. Default from config.
    """
    return _result(run_job("asm", code, dump, run_frames, None, done_addr))


@mcp.tool()
def run_c(code: str, dump: list[str] | None = None, done_addr: str | None = None,
          run_frames: int | None = None) -> list:
    """Compile C with CMOC + the Olivetti library (pc128-c/, #include <olivetti.h>) and run it on a PC128.

    The program is linked at $6000 (limit $9F00), loaded into BASIC BANK 6 and started with EXEC;
    returning from main() goes back to the BASIC prompt. The library wraps the ROM monitor
    (ol_putc, ol_puts, ol_locate, ol_plot, ol_line, ol_getc, ol_beep, ...) and the extramonitor
    (xm_begin, xm_box, xm_ellipse, xm_from_int, xm_op, xm_to_str, ...); printf works too.
    Finish with ol_done() (writes 1 to $9F01) and pass done_addr="9F01"; store results with
    ol_debug_byte/ol_debug_word(i, v) ($9F10+i) and read them with dump ["9F10:16"].

    Args:
        code: C source with main(). Extra asm/C files are not available here (use the CLI).
        dump: memory ranges to read back, "HEXADDR:LENGTH" (BANK 6 by default, "@n" for another bank).
        done_addr: hex address the program writes a non-zero byte to when finished.
        run_frames: max frames (50 per emulated second) to run. Default from config.
    """
    return _result(run_job("c", code, dump, run_frames, None, done_addr))


# ------------------------------------------------------------------ debugger --
# One persistent MAME debug session (tools/debugger) shared by the debug_* tools.
_dbg = None
_dbg_log = []
_dbg_lock = threading.Lock()


def _dbg_session():
    if _dbg is None or _dbg.state == "exited":
        raise RuntimeError("no debug session: call debug_start first")
    return _dbg


def _dbg_text(text, s=None):
    out = []
    if _dbg_log:
        out.append("\n".join(_dbg_log))
        _dbg_log.clear()
    if text:
        out.append(text)
    if s is not None:
        out.append(s.status_line())
    return "\n".join(out)


@mcp.tool()
def debug_start(code: str | None = None, kind: str = "asm", program: str | None = None,
                stop_on_entry: bool = True, breakpoints: list[str] | None = None,
                window: bool = False, boot: bool = True, floppy: str | None = None,
                floppy2: str | None = None, floppy_controller: str | None = None,
                cassette: str | None = None, cartridge: str | None = None) -> str:
    """Start an interactive debug session on an emulated PC128 (MAME, 6809) and keep it alive.

    Replaces any previous session. The machine boots into BASIC 128, then the program (if any)
    is loaded: assembly is assembled with lwasm, stored in RAM ($6000-$9FFF goes to BANK 6) and
    started with EXEC; BASIC is typed in and RUN. With stop_on_entry the session stops at the
    entry point / first BASIC line. Continue with debug_command.

    Args:
        code: program source (lwasm 6809 assembly, C with <olivetti.h> when kind="c",
            or numbered BASIC lines when kind="basic").
        kind: "asm", "c" or "basic" (only used with `code`). C programs support source breakpoints
            ("prog.c:12") and source stepping (debug_command "sn" / "si").
        program: path of a .asm / .c / .bas file instead of `code`.
        stop_on_entry: stop at the entry point / first BASIC line.
        breakpoints: set before the program starts, in debug_command syntax for `bp`, e.g.
            ["PUTC", "9010", "mon0:F6D9 if a==0x41", "line 40"] ("line N" = BASIC line).
        window: show the MAME window (default headless).
        boot: go through the boot menu into BASIC 128 first.
        floppy: .fd image for drive 0, e.g. "media/KEYJOY.FD" (programs can then LOADM/LOAD from it).
        floppy2: .fd image for the second drive (cd90_351 only).
        floppy_controller: "cd90_351" (3.5", 80 tracks, default) or "cd90_640" (5.25", 40 tracks).
        cassette: cassette image.  cartridge: cartridge image (the boot menu is skipped).
        Unset media fall back to config.json, like run_basic / run_asm.
    """
    global _dbg
    from commands import Session
    with _dbg_lock:
        if _dbg is not None:
            try:
                _dbg.close()
            except Exception:
                pass
            _dbg = None
        _dbg_log.clear()
        if code is not None:
            tmp = ROOT / "build" / "dbg-mcp"
            tmp.mkdir(parents=True, exist_ok=True)
            ext = {"basic": "bas", "bas": "bas", "c": "c"}.get(kind.lower(), "asm")
            program = str(tmp / ("prog." + ext))
            Path(program).write_text(code if code.endswith("\n") else code + "\n")
        s = Session()
        s._quiet = True
        media = {"floppy": floppy, "floppy2": floppy2, "controller": floppy_controller,
                 "cassette": cassette, "cartridge": cartridge}
        s.start(media=media, window=window, boot=boot, log=_dbg_log.append)
        _dbg = s
        if program and not program.lower().endswith((".bas", ".txt")):
            s.assemble_program(program)
        for spec in breakpoints or []:
            spec = spec.strip()
            _dbg_log.append(s.execute(("bl " + spec[5:]) if spec.lower().startswith("line ") else "bp " + spec))
        if program:
            s.load_program(program, stop_on_entry=stop_on_entry, log=_dbg_log.append,
                           assembled=s.program if not program.lower().endswith((".bas", ".txt")) else None)
            if stop_on_entry or breakpoints:
                s.wait_stopped(60 if program.lower().endswith((".bas", ".txt")) else 20)
        elif stop_on_entry:
            s.pause()
        return _dbg_text("debug session ready", s)


@mcp.tool()
def debug_command(command: str, wait_seconds: float = 10.0) -> list:
    """Run a debugger command in the session started by debug_start; returns its text output.

    Main commands (`help` lists all):
      r [REG=val]          registers + CC flags + location (ROM page / symbol)   banks   where   line   bt
      m ADDR[@view] [LEN]  hex dump       d [ADDR] [N]  disassemble (with symbols)
      a ADDR asm | asm     assemble live into RAM, e.g. "a 9F00 LDA #$41 | SWI PUTC | RTS"
      hex ADDR 12 34 ..    store bytes    str ADDR "TEXT\n\0"   fill ADDR LEN BYTE
      bp ADDR|SYM [if COND]   bl LINE [if COND] (BASIC line)   bc N|all   bd/be N   wp ADDR [LEN] [r|w|rw]
      bp FILE:LINE (C/asm source line, e.g. prog.c:12)
      g [ADDR]  s [N]  n (step over)  out  until ADDR  nl (next BASIC line)  stop  wait [SECS]
      sn / si  step over / into one C or asm source line     src [N]  source around PC
      sym REGEX   type TEXT   key TEXT   status   snap   reset   mame RAWCMD
    Addresses: hex (9F00, $9F00), symbols (PUTC), expressions (X+2), . = PC, page-qualified (mon0:F6D9).
    Views in $6000-$9FFF: @1..@6 BASIC BANK n, @p0..@p7 RAM page, @cpu. Conditions use MAME syntax
    (hex by default, e.g. "a==41 && x>9000").

    After execution commands (g, s, n, out, until, nl) the tool waits up to wait_seconds for the
    machine to stop and reports where it is. `snap` also returns the screenshot image.
    """
    with _dbg_lock:
        s = _dbg_session()
        out = s.execute(command)
        verb = command.strip().split(" ", 1)[0].lower()
        runs = verb in ("g", "c", "go", "s", "step", "n", "over", "out", "finish", "until", "nl", "nextline", "sn", "si")
        if runs:
            if wait_seconds > 0:
                s.wait_stopped(wait_seconds)
            out = None                    # the fresh status below supersedes the command's own report
        content = [_dbg_text(out, s if runs else None)]
        if verb == "snap" and out and out.endswith(".png"):
            content.append(Image(path=out))
        return content


@mcp.tool()
def debug_stop() -> str:
    """End the debug session started by debug_start (closes MAME)."""
    global _dbg
    with _dbg_lock:
        if _dbg is None:
            return "no debug session"
        _dbg.close()
        _dbg = None
        return "debug session closed"


if __name__ == "__main__":
    mcp.run()
