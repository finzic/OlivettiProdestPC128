#!/usr/bin/env python3
"""Build and test the KEYJOY disk using only BASIC 128 inside MAME.

  build: blank .fd -> DSKINI -> type a DATA/POKE loader, RUN it -> SAVEM "KEYJOY"
         -> type demo.bas -> SAVE "DEMO". No disk structure is written by our tools.
  test:  LOADM from that disk, hold each key combination, read USR0(0) back.

  python3 keyjoy.py build|test
"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1] / "tools"
INVESTIGATE = HERE.parents[1] / "investigate" / "investigate.py"
DISK = HERE / "keyjoy.fd"
BIN = HERE / "keyjoy.bin"


def investigate(lines, *extra):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(lines) + "\n")
    p = subprocess.run([sys.executable, str(INVESTIGATE), "run", "--fd", str(DISK), "--prog", f.name, *extra],
                       capture_output=True, text=True)
    return p.stdout + p.stderr


def build():
    subprocess.run(["make", "-C", str(HERE), "keyjoy.bin"], check=True)
    with tempfile.TemporaryDirectory() as t:
        loader = Path(t) / "loader.bas"
        subprocess.run([sys.executable, str(TOOLS / "bin2bas.py"), str(BIN), str(loader),
                        "--clear", "0x9EFF", "--no-exec"], check=True)
        loader_lines = [l for l in loader.read_text().splitlines() if l.strip()]
    size = BIN.stat().st_size - 10            # DECB: 5-byte header + 5-byte trailer
    end = 0x9F00 + size - 1
    demo = [l for l in (HERE / "demo.bas").read_text().splitlines() if l.strip()]
    DISK.write_bytes(b"\xE5" * 163840)         # unformatted; BASIC formats it
    lines = (["DSKINI 0", "@WAIT 3000", "NEW"] + loader_lines + ["RUN", "@WAIT 600",
             'SAVEM "KEYJOY",&H9F00,&H%04X,&H9F00' % end, "@WAIT 400", "NEW"] + demo
             + ['SAVE "DEMO"', "@WAIT 400", "NEW", "DIR", "@WAIT 100"])
    investigate(lines, "--frames", "20")
    print(subprocess.run([sys.executable, str(TOOLS / "fdtool.py"), "ls", str(DISK)],
                         capture_output=True, text=True).stdout)


CASES = [((), 0), (("UP",), 1), (("UP", "RIGHT"), 2), (("RIGHT",), 3), (("DOWN", "RIGHT"), 4),
         (("DOWN",), 5), (("DOWN", "LEFT"), 6), (("LEFT",), 7), (("UP", "LEFT"), 8),
         (("SPACE",), 128), (("UP", "SPACE"), 129), (("UP", "DOWN", "LEFT"), 0)]


def test():
    prog = ["CLEAR ,&H9EFF", 'LOADM "KEYJOY"', "@WAIT 300", "DEFUSR0=&H9F00",
            "10 FOR I=1 TO 600:NEXT", "20 POKE &H5F00,USR0(0):POKE &H5F01,1"]
    ok = True
    for keys, want in CASES:
        hold = [a for k in keys for a in ("--hold", k)]
        out = investigate(prog, *hold, "--hold-after", "40", "--frames", "300", "--peek", "5F00:2")
        got = next((l.split()[1:] for l in out.splitlines() if l.startswith("5F00:")), ["??", "??"])
        good = got == ["%02X" % want, "01"]
        ok &= good
        print("%-18s expect %3d  got %s  %s" % ("+".join(keys) or "none", want, " ".join(got), "OK" if good else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    {"build": build, "test": test}[sys.argv[1] if len(sys.argv) > 1 else "build"]()
