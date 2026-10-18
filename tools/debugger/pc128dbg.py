#!/usr/bin/env python3
"""pc128dbg - interactive PC128 debugger (MAME + tools/debugger).

    python3 tools/debugger/pc128dbg.py                    boot to BASIC 128, then prompt
    python3 tools/debugger/pc128dbg.py prog.asm --stop    assemble, load, EXEC, stop at entry
    python3 tools/debugger/pc128dbg.py prog.bas           type the program and RUN it
    python3 tools/debugger/pc128dbg.py -x "bp PUTC" -x g  run commands before the prompt
    python3 tools/debugger/pc128dbg.py prog.bas --media floppy351 media/KEYJOY.FD   with a disk (also --floppy, --cassette, --cart ...)

Type 'help' at the prompt for the command list. Ctrl-C stops the machine; 'quit' exits.
"""
import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from commands import Session  # noqa: E402
import pc128  # noqa: E402  (on sys.path via commands)
from client import DebugError  # noqa: E402

try:
    import readline  # noqa: F401  (history and line editing)
except ImportError:
    pass


def main():
    ap = argparse.ArgumentParser(description="PC128 debugger (MAME)")
    ap.add_argument("program", nargs="?", help=".asm (assembled with lwasm, loaded, EXECed) or .bas (typed + RUN)")
    ap.add_argument("--stop", action="store_true", help="stop at the program entry / first BASIC line")
    ap.add_argument("--noexec", action="store_true", help="load the program but do not run it")
    ap.add_argument("--headless", action="store_true", help="no MAME window")
    ap.add_argument("--noboot", action="store_true", help="do not go through the boot menu")
    m = ap.add_argument_group("media (same choices as a normal run; defaults from config.json)")
    m.add_argument("--media", nargs="+", metavar=("KIND", "IMAGE"),
                   help="run-mame.sh style: floppy351 IMAGE [IMAGE2] | floppy IMAGE | cassette IMAGE | cartridge IMAGE | none")
    m.add_argument("--floppy", "--fd", help=".fd image for drive 0")
    m.add_argument("--floppy2", "--fd2", help=".fd image for the second drive (cd90_351 only)")
    m.add_argument("--controller", choices=pc128.FLOPPY_CONTROLLERS, help="floppy controller")
    m.add_argument("--cassette", help="cassette image")
    m.add_argument("--cart", help="cartridge image")
    m.add_argument("--mame-arg", action="append", default=[], help="extra MAME argument (repeatable)")
    ap.add_argument("--sym", action="append", default=[], help="extra symbol file (.sym, lwasm --symbol-dump, .json)")
    ap.add_argument("-x", "--exec", action="append", default=[], help="command to run before the prompt")
    ap.add_argument("--batch", action="store_true", help="exit after the -x commands")
    args = ap.parse_args()

    try:
        media = pc128.media_from_kind(*args.media[:3]) if args.media else {}
    except (ValueError, TypeError) as e:
        ap.error("--media: %s" % e)
    for key, val in (("floppy", args.floppy), ("floppy2", args.floppy2), ("controller", args.controller),
                     ("cassette", args.cassette), ("cartridge", args.cart)):
        if val:
            media[key] = val

    s = Session(extra_symbols=args.sym)

    def on_event(name, data):
        if name == "stopped" and not s._quiet:
            print("\n" + s.status_line() + "\npc128> ", end="", flush=True)
        elif name == "exited":
            print("\nMAME exited", flush=True)

    s._quiet = True
    s.listeners.append(on_event)
    try:
        s.start(media=media, window=not args.headless, boot=not args.noboot, program=args.program,
                stop_on_entry=args.stop, exec_program=not args.noexec, extra_args=args.mame_arg)
        if args.stop:
            s.wait_stopped(60)
            print(s.status_line())
    except (DebugError, ValueError) as e:
        print("error:", e)
        s.close()
        return 1

    def run(line):
        if line.strip().lower() in ("q", "quit", "exit"):
            return False
        try:
            out = s.execute(line)
            if out:
                print(out)
        except DebugError as e:
            print("error:", e)
        except Exception as e:   # keep the REPL alive
            print("error: %s: %s" % (type(e).__name__, e))
        return True

    for cmd in args.exec:
        print("pc128> " + cmd)
        if not run(cmd):
            break
    if args.batch:
        s.close()
        return 0
    s._quiet = False
    while s.state != "exited":
        try:
            line = input("pc128> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            if s.state == "run":
                run("stop")
            continue
        s._quiet = True
        try:
            if not run(line):
                break
        finally:
            s._quiet = False
    s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
