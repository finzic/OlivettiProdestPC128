# DSKINI an 80-track image, then SAVEM 18 files of 16128 bytes (one boot each), verify byte-exact on the host.
# Produces /tmp/pc128-full.fd, the input of the other tests.
from ft import *
import os
IMG = "/tmp/pc128-full.fd"; N = 18; SZ = 16128
pat = bytes((i*7+3) & 255 for i in range(SZ))
open("/tmp/PAT.BIN", "wb").write(bytes([0, 0x3F, 0, 0x60, 0]) + pat + bytes([0xFF, 0, 0, 0x60, 0]))
def fd(*a): return subprocess.run(["python3", FD, *a], capture_output=True, text=True).stdout
fd("new", IMG, "--sides", "1", "--tracks", "80", "--name", "JUNK")
r = go("5 ON ERROR GOTO 100\n10 DSKINI 0\n20 POKE &H5001,1\n30 END\n100 POKE &H5002,ERR\n110 POKE &H5001,1", IMG, ["5000:3@cpu"], frames=30000, timeout_s=900)
P("DSKINI:", r.get("status"), fd("ls", IMG, "--tracks", "80", "--side", "0").strip().splitlines()[-1])
fd("put", IMG, "/tmp/PAT.BIN", "--type", "2", "--tracks", "80")
for k in range(1, N+1):
    prog = ('5 ON ERROR GOTO 900\n10 LOADM "PAT"\n20 POKE &H6000,%d\n30 POKE &H9EFE,%d\n40 SAVEM "F%02d",&H6000,&H9EFF,&H6000\n'
            '50 POKE &H5001,1\n60 END\n900 POKE &H5002,ERR\n910 POKE &H5001,1') % (k, k, k)
    go(prog, IMG, ["5000:3@cpu"], frames=30000, timeout_s=900)
good = 0
for k in range(1, N+1):
    p = "/tmp/_f.bin"
    if os.path.exists(p): os.remove(p)
    subprocess.run(["python3", FD, "get", IMG, "F%02d.BIN" % k, p, "--tracks", "80", "--side", "0"], capture_output=True)
    if not os.path.exists(p): P("F%02d missing" % k); continue
    d = open(p, "rb").read(); b = bytearray(pat); b[0] = k; b[SZ-2] = k
    good += d == bytes([0, 0x3F, 0, 0x60, 0]) + bytes(b) + bytes([0xFF, 0, 0, 0x60, 0])
P("whole-disk write: %d/%d files byte-exact on host" % (good, N))
