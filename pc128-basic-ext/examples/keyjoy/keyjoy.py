#!/usr/bin/env python3
"""Build and test the KEYJOY disk.

  build: assemble keyjoy.asm and keyjoy2.asm, create one reusable disk image keyjoy.fd with
         tools/fdtool.py and copy the routines (KEYJOY.BIN, KEYJOY2.BIN), the demos (DEMO.BAS,
         DEMO2.BAS) and the test programs in tests/*.bas onto it. MAME is not needed to build it.
  test:  boot MAME with that disk and RUN one of the test programs (KJTEST, KJTESTR, KJ2TEST,
         KJ2TESTR; the R ones load the routine at $5000) while holding each key combination.
         Only RUN "name" is typed; each program loads the routine and POKEs the results to $5F00.

  python3 keyjoy.py build
  python3 keyjoy.py test [keyjoy|keyjoy2]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[2] / "tools"
INVESTIGATE = HERE.parents[1] / "investigate" / "investigate.py"
DISK = HERE / "keyjoy.fd"
NAME = "keyjoy"


def select(name):
    global NAME
    NAME = name


def investigate(lines, *extra):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(lines) + "\n")
    p = subprocess.run([sys.executable, str(INVESTIGATE), "run", "--fd", str(DISK), "--prog", f.name, *extra],
                       capture_output=True, text=True)
    return p.stdout + p.stderr


def fdtool(*args):
    return subprocess.run([sys.executable, str(TOOLS / "fdtool.py"), *args], check=True,
                          capture_output=True, text=True).stdout


def build():
    subprocess.run(["make", "-C", str(HERE), "keyjoy.bin", "keyjoy2.bin"], check=True)
    DISK.unlink(missing_ok=True)
    fdtool("new", str(DISK), "--name", "KEYJOY")
    for src, name in (("keyjoy.bin", "KEYJOY.BIN"), ("keyjoy2.bin", "KEYJOY2.BIN"),
                      ("demo.bas", "DEMO.BAS"), ("demo2.bas", "DEMO2.BAS"),
                      *((str(t.relative_to(HERE)), t.stem.upper() + ".BAS")
                        for t in sorted((HERE / "tests").glob("*.bas")))):
        fdtool("put", str(DISK), str(HERE / src), "--as", name)
    print(fdtool("ls", str(DISK)))


CASES = [((), 0), (("UP",), 1), (("UP", "RIGHT"), 2), (("RIGHT",), 3), (("DOWN", "RIGHT"), 4),
         (("DOWN",), 5), (("DOWN", "LEFT"), 6), (("LEFT",), 7), (("UP", "LEFT"), 8),
         (("SPACE",), 128), (("UP", "SPACE"), 129), (("UP", "DOWN", "LEFT"), 0)]


def run_cases(program, cases, label):
    ok = True
    for keys, want in cases:
        hold = [a for k in keys for a in ("--hold", k)]
        out = investigate(['RUN "%s"' % program], *hold, "--hold-after", "40", "--frames", "500", "--peek", "5F00:4")
        got = next((l.split()[1:] for l in out.splitlines() if l.startswith("5F00:")), ["??"] * 4)
        exp = ["%02X" % want, "01", "%02X" % (want & 15), "%02X" % (1 if want & 128 else 0)]
        good = got == exp
        ok &= good
        print("%-8s %-18s expect %3d  got %s  %s" % (label, "+".join(keys) or "none", want, " ".join(got),
                                                     "OK" if good else "FAIL"))
    return ok


def test():
    # default location $9F00, then the same code loaded at $5000 (LOADM offset $5000-$9F00 = &HB100)
    ok = run_cases("KJTEST", CASES, "$9F00")
    relocated = [CASES[0], CASES[3], CASES[6], CASES[9], CASES[10]]
    ok &= run_cases("KJTESTR", relocated, "$5000")
    sys.exit(0 if ok else 1)


# (keys held, P1 dir, P1 fire, P2 dir, P2 fire, USR value); W A S D / Enter / Space as in keyjoy2.asm; A is "A `" in MAME
CASES2 = [((), 0, 0, 0, 0, 0), (("UP",), 1, 0, 0, 0, 1), (("DOWN", "LEFT"), 6, 0, 0, 0, 6),
          (("Enter",), 0, 1, 0, 0, 128), (("W",), 0, 0, 1, 0, 0), (("W", "D"), 0, 0, 2, 0, 0),
          (("D",), 0, 0, 3, 0, 0), (("S", "D"), 0, 0, 4, 0, 0), (("S",), 0, 0, 5, 0, 0),
          (("S", "A `"), 0, 0, 6, 0, 0), (("A `",), 0, 0, 7, 0, 0), (("W", "A `"), 0, 0, 8, 0, 0),
          (("Space",), 0, 0, 0, 1, 0), (("W", "A `", "S"), 0, 0, 0, 0, 0),
          (("UP", "Enter", "W", "D", "Space"), 1, 1, 2, 1, 129)]


def run_cases2(program, cases, label):
    ok = True
    for keys, *want in cases:
        hold = [a for k in keys for a in ("--hold", k)]
        out = investigate(['RUN "%s"' % program], *hold, "--hold-after", "40", "--frames", "500", "--peek", "5F00:6")
        got = next((l.split()[1:] for l in out.splitlines() if l.startswith("5F00:")), ["??"] * 6)
        exp = ["%02X" % v for v in want] + ["01"]
        good = got == exp
        ok &= good
        print("%-8s %-26s expect %s  got %s  %s" % (label, "+".join(keys) or "none", " ".join(exp[:5]),
                                                    " ".join(got[:5]), "OK" if good else "FAIL"))
    return ok


def test2():
    # default location $9F00, then the same code loaded at $5000 (LOADM offset $5000-$9F00 = &HB100)
    ok = run_cases2("KJ2TEST", CASES2, "$9F00")
    relocated = [CASES2[0], CASES2[3], CASES2[9], CASES2[-1]]
    ok &= run_cases2("KJ2TESTR", relocated, "$5000")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    select(sys.argv[2] if len(sys.argv) > 2 else "keyjoy")
    {"build": build, "test": test2 if NAME == "keyjoy2" else test}[sys.argv[1] if len(sys.argv) > 1 else "build"]()
