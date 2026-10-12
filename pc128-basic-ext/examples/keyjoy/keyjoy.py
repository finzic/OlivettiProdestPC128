#!/usr/bin/env python3
"""Build and test the KEYJOY disk using only BASIC 128 inside MAME.

  build: blank .fd -> DSKINI -> type a DATA/POKE loader, RUN it -> SAVEM "KEYJOY"
         -> type demo.bas -> SAVE "DEMO". No disk structure is written by our tools.
  test:  LOADM from that disk, hold each key combination, read USR0(0) back.

  python3 keyjoy.py build|test [keyjoy|keyjoy2]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[2] / "tools"
INVESTIGATE = HERE.parents[1] / "investigate" / "investigate.py"
DISK = HERE / "keyjoy.fd"
BIN = HERE / "keyjoy.bin"
NAME = "keyjoy"


def select(name):
    global DISK, BIN, NAME
    NAME = name
    DISK = HERE / (name + ".fd")
    BIN = HERE / (name + ".bin")


def investigate(lines, *extra):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(lines) + "\n")
    p = subprocess.run([sys.executable, str(INVESTIGATE), "run", "--fd", str(DISK), "--prog", f.name, *extra],
                       capture_output=True, text=True)
    return p.stdout + p.stderr


def build():
    subprocess.run(["make", "-C", str(HERE), BIN.name], check=True)
    with tempfile.TemporaryDirectory() as t:
        loader = Path(t) / "loader.bas"
        subprocess.run([sys.executable, str(TOOLS / "bin2bas.py"), str(BIN), str(loader),
                        "--clear", "0x9EFF", "--no-exec"], check=True)
        loader_lines = [l for l in loader.read_text().splitlines() if l.strip()]
    size = BIN.stat().st_size - 10            # DECB: 5-byte header + 5-byte trailer
    end = 0x9F00 + size - 1
    demo_name = "demo2.bas" if NAME == "keyjoy2" else "demo.bas"
    demo = [l for l in (HERE / demo_name).read_text().splitlines() if l.strip()]
    DISK.write_bytes(b"\xE5" * 163840)         # unformatted; BASIC formats it
    lines = (["DSKINI 0", "@WAIT 3000", "NEW"] + loader_lines + ["RUN", "@WAIT 600",
             'SAVEM "%s",&H9F00,&H%04X,&H9F00' % (NAME.upper(), end), "@WAIT 400", "NEW"] + demo
             + ['SAVE "%s"' % ("DEMO2" if NAME == "keyjoy2" else "DEMO"), "@WAIT 400", "NEW", "DIR", "@WAIT 100"])
    investigate(lines, "--frames", "20")
    print(subprocess.run([sys.executable, str(TOOLS / "fdtool.py"), "ls", str(DISK)],
                         capture_output=True, text=True).stdout)


CASES = [((), 0), (("UP",), 1), (("UP", "RIGHT"), 2), (("RIGHT",), 3), (("DOWN", "RIGHT"), 4),
         (("DOWN",), 5), (("DOWN", "LEFT"), 6), (("LEFT",), 7), (("UP", "LEFT"), 8),
         (("SPACE",), 128), (("UP", "SPACE"), 129), (("UP", "DOWN", "LEFT"), 0)]


def run_cases(setup, base, cases, label):
    prog = setup + ["DEFUSR0=&H%04X" % base, "10 FOR I=1 TO 600:NEXT", "20 K=USR0(0)",
            "30 POKE &H5F00,K", "31 A=PEEK(&H%04X):POKE &H5F02,A" % (base + 4),
            "32 A=PEEK(&H%04X):POKE &H5F03,A" % (base + 5), "40 POKE &H5F01,1"]
    ok = True
    for keys, want in cases:
        hold = [a for k in keys for a in ("--hold", k)]
        out = investigate(prog, *hold, "--hold-after", "40", "--frames", "300", "--peek", "5F00:4")
        got = next((l.split()[1:] for l in out.splitlines() if l.startswith("5F00:")), ["??"] * 4)
        exp = ["%02X" % want, "01", "%02X" % (want & 15), "%02X" % (1 if want & 128 else 0)]
        good = got == exp
        ok &= good
        print("%-8s %-18s expect %3d  got %s  %s" % (label, "+".join(keys) or "none", want, " ".join(got),
                                                     "OK" if good else "FAIL"))
    return ok


def test():
    # default location $9F00, then the same code loaded at $5000 (LOADM offset $5000-$9F00 = &HB100)
    ok = run_cases(["CLEAR ,&H9EFF", 'LOADM "KEYJOY"', "@WAIT 300"], 0x9F00, CASES, "$9F00")
    relocated = [CASES[0], CASES[3], CASES[6], CASES[9], CASES[10]]
    ok &= run_cases(["CLEAR ,&H4FFF", 'LOADM "KEYJOY",&HB100', "@WAIT 300"], 0x5000, relocated, "$5000")
    sys.exit(0 if ok else 1)


# (keys held, P1 dir, P1 fire, P2 dir, P2 fire, USR value); W A S D / Enter / Space as in keyjoy2.asm; A is "A `" in MAME
CASES2 = [((), 0, 0, 0, 0, 0), (("UP",), 1, 0, 0, 0, 1), (("DOWN", "LEFT"), 6, 0, 0, 0, 6),
          (("Enter",), 0, 1, 0, 0, 128), (("W",), 0, 0, 1, 0, 0), (("W", "D"), 0, 0, 2, 0, 0),
          (("D",), 0, 0, 3, 0, 0), (("S", "D"), 0, 0, 4, 0, 0), (("S",), 0, 0, 5, 0, 0),
          (("S", "A `"), 0, 0, 6, 0, 0), (("A `",), 0, 0, 7, 0, 0), (("W", "A `"), 0, 0, 8, 0, 0),
          (("Space",), 0, 0, 0, 1, 0), (("W", "A `", "S"), 0, 0, 0, 0, 0),
          (("UP", "Enter", "W", "D", "Space"), 1, 1, 2, 1, 129)]


def run_cases2(setup, base, cases, label):
    prog = setup + ["DEFUSR0=&H%04X" % base, "10 FOR I=1 TO 600:NEXT", "20 K=USR0(0)",
            "30 A=PEEK(&H%04X):POKE &H5F00,A" % (base + 4), "31 A=PEEK(&H%04X):POKE &H5F01,A" % (base + 5),
            "32 A=PEEK(&H%04X):POKE &H5F02,A" % (base + 6), "33 A=PEEK(&H%04X):POKE &H5F03,A" % (base + 7),
            "34 POKE &H5F04,K", "40 POKE &H5F05,1"]
    ok = True
    for keys, *want in cases:
        hold = [a for k in keys for a in ("--hold", k)]
        out = investigate(prog, *hold, "--hold-after", "40", "--frames", "300", "--peek", "5F00:6")
        got = next((l.split()[1:] for l in out.splitlines() if l.startswith("5F00:")), ["??"] * 6)
        exp = ["%02X" % v for v in want] + ["01"]
        good = got == exp
        ok &= good
        print("%-8s %-26s expect %s  got %s  %s" % (label, "+".join(keys) or "none", " ".join(exp[:5]),
                                                    " ".join(got[:5]), "OK" if good else "FAIL"))
    return ok


def test2():
    # default location $9F00, then the same code loaded at $5000 (LOADM offset $5000-$9F00 = &HB100)
    ok = run_cases2(["CLEAR ,&H9EFF", 'LOADM "KEYJOY2"', "@WAIT 300"], 0x9F00, CASES2, "$9F00")
    relocated = [CASES2[0], CASES2[3], CASES2[9], CASES2[-1]]
    ok &= run_cases2(["CLEAR ,&H4FFF", 'LOADM "KEYJOY2",&HB100', "@WAIT 300"], 0x5000, relocated, "$5000")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    select(sys.argv[2] if len(sys.argv) > 2 else "keyjoy")
    {"build": build, "test": test2 if NAME == "keyjoy2" else test}[sys.argv[1] if len(sys.argv) > 1 else "build"]()
