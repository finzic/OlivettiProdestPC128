import sys, subprocess, shutil
ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); import pc128
FD = str(ROOT / "tools/fdtool.py")
def fd(*a): return subprocess.run(["python3", FD, *a], capture_output=True, text=True).stdout
SRC = "/tmp/pc128-full.fd"; N = 18; SZ = 16128
pat = bytes((i*7+3) & 255 for i in range(SZ))
def expect(k):
    b = bytearray(pat); b[0] = k; b[16126] = k; return bytes(b)
def cfgfor(img):
    return {"mame": str(pc128.LOCAL_MAME), "rompath": "/tmp/pc128-mame-save-load-roms", "floppy": img, "line_gap_frames": 30,
            "floppy_controller": "cd90_351", "menu_frames": 600, "headless": True, "timeout_s": 900, "extra_args": ["-log"]}
def stats():
    log = open("/tmp/error.log", errors="replace").read()
    return (log.count("read_sector end"), log.count("write_sector end"), log.count("sector search timeout"), log.count("crcer"))
def mem(r, prefix):
    for k, v in (r.get("mem") or {}).items():
        if k.startswith(prefix): return bytes.fromhex(v)
    return None
def P(*a): print(*a, flush=True)

# D: read phase, one boot per file, five sentinel bytes read inside the machine
RD = "/tmp/pc128-full-read.fd"; shutil.copy(SRC, RD); bad = 0; tr = tt = tc = 0
for k in range(1, N+1):
    prog = ('10 LOADM "F%02d"\n20 POKE &H5200,PEEK(&H6000):X=0\n30 POKE &H5201,PEEK(&H6001):X=0\n40 POKE &H5202,PEEK(&H7F40):X=0\n'
            '50 POKE &H5203,PEEK(&H9EFE):X=0\n60 POKE &H5204,PEEK(&H9EFF):X=0\n70 POKE &H5001,1') % k
    r = pc128.run_job("basic", prog, dumps=["5200:5@cpu"], run_frames=20000, done_addr="5001@cpu", cfg_overrides=cfgfor(RD))
    rd, w, to, c = stats(); tr += rd; tt += to; tc += c
    m = mem(r, "5200"); e = expect(k); want = bytes([e[0], e[1], e[8000], e[16126], e[16127]])
    if m != want:
        bad += 1; P("  F%02d: got %s want %s" % (k, m.hex(" ") if m else None, want.hex(" ")))
P("D read phase: %d/%d files loaded and sampled correctly in-machine | sector reads=%d timeouts=%d crcerr=%d" % (N-bad, N, tr, tt, tc))

# E: KILL, reuse freed space, exact read-back
EX = "/tmp/pc128-full-kill.fd"; shutil.copy(SRC, EX)
r = pc128.run_job("basic", '10 ON ERROR GOTO 900\n20 KILL "F01.BIN"\n30 POKE &H5001,1\n40 END\n900 POKE &H5002,ERR\n910 POKE &H5001,1', dumps=["5000:3@cpu"], run_frames=20000, done_addr="5001@cpu", cfg_overrides=cfgfor(EX))
ls = fd("ls", EX, "--tracks", "80", "--side", "0"); m = mem(r, "5000")
P("E1 KILL F01: status=%s err=%s | F01 gone: %s | %s" % (r.get("status"), m[2] if m else None, "F01" not in ls, ls.strip().splitlines()[-1]))
r = pc128.run_job("basic", '10 ON ERROR GOTO 900\n20 LOADM "F10"\n30 SAVEM "RB",&H6000,&H9EFF,&H6000\n40 POKE &H5001,1\n50 END\n900 POKE &H5002,ERR\n910 POKE &H5001,1', dumps=["5000:3@cpu"], run_frames=20000, done_addr="5001@cpu", cfg_overrides=cfgfor(EX))
p = subprocess.run(["python3", FD, "get", EX, "RB.BIN", "/tmp/RB.BIN", "--tracks", "80", "--side", "0"], capture_output=True, text=True)
if p.returncode == 0:
    d = open("/tmp/RB.BIN", "rb").read()
    P("E2 saved into freed space, LOADM F10 -> SAVEM RB: body == expected F10: %s (len %d)" % (d[5:5+SZ] == expect(10), len(d)))
else:
    P("E2 RB.BIN missing; status", r.get("status"), mem(r, "5000"))

# F: SAVEM on a full disk must fail cleanly and leave existing files intact
FL = "/tmp/pc128-full-full.fd"; shutil.copy(SRC, FL)
r = pc128.run_job("basic", '10 ON ERROR GOTO 900\n20 LOADM "F05"\n30 SAVEM "TOOBIG",&H6000,&H9EFF,&H6000\n40 POKE &H5001,1\n50 END\n900 POKE &H5002,ERR\n910 POKE &H5001,1', dumps=["5000:3@cpu"], run_frames=20000, done_addr="5001@cpu", cfg_overrides=cfgfor(FL))
m = mem(r, "5000"); ls = fd("ls", FL, "--tracks", "80", "--side", "0"); intact = 0
for k in range(1, N+1):
    subprocess.run(["python3", FD, "get", FL, "F%02d.BIN" % k, "/tmp/chk.bin", "--tracks", "80", "--side", "0"], capture_output=True)
    d = open("/tmp/chk.bin", "rb").read(); intact += (d[5:5+SZ] == expect(k))
P("F disk-full SAVEM: status=%s ERR recorded=%s | TOOBIG in directory: %s | existing files still byte-exact: %d/%d" % (r.get("status"), m[2] if m else None, "TOOBIG" in ls, intact, N))
P("DONE")
