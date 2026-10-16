from ft import *
import os, stat
def fresh(path, name="T"):
    subprocess.run(["python3", FD, "new", path, "--tracks", "80", "--name", name], check=True, capture_output=True)
def put(img, f, as_):
    subprocess.run(["python3", FD, "put", img, f, "--as", as_, "--type", "2", "--tracks", "80", "--side", "0"], check=True, capture_output=True)
def getf(img, name):
    p = subprocess.run(["python3", FD, "get", img, name, "/tmp/_g.bin", "--tracks", "80", "--side", "0"], capture_output=True)
    return open("/tmp/_g.bin","rb").read() if p.returncode == 0 else None
def stats():
    L=log(); return "writes %d reads %d timeouts %d crcerr %d" % (L.count("write_sector end"),L.count("read_sector end"),L.count("sector search timeout"),L.count("crcer"))
f01 = open("/tmp/f01.bin","rb").read()

# C: COPY + VERIFY ON
C="/tmp/t9c.fd"; fresh(C); put(C, "/tmp/f01.bin", "F01.BIN")
r = go('5 CLEAR 1000\n10 ON ERROR GOTO 900\n20 VERIFY ON\n30 COPY "F01.BIN" TO "CPY.BIN"\n40 POKE &H5001,1\n50 END\n900 POKE &H5002,ERR\n910 POKE &H5003,ERL AND 255\n920 POKE &H5001,1', C, ["5000:4@cpu"], timeout_s=900)
m = mem(r,"5000"); g = getf(C,"CPY.BIN")
P("C COPY+VERIFY ON: status=%s err=%d erl=%d (255=none) | CPY.BIN == F01.BIN: %s | %s" % (r.get("status"), m[2], m[3], g == f01, stats()))

# D: write protect (image file read-only)
D="/tmp/t9d.fd"; fresh(D); put(D, "/tmp/f01.bin", "F01.BIN"); before=open(D,"rb").read(); os.chmod(D, 0o444)
r = go('5 CLEAR 1000\n10 ON ERROR GOTO 900\n20 DSKO$ 0,79,5,STRING$(128,65)\n30 POKE &H5001,1\n40 END\n900 POKE &H5002,ERR\n910 POKE &H5003,ERL AND 255\n920 POKE &H5001,1', D, ["5000:4@cpu"], timeout_s=900)
m = mem(r,"5000"); P("D write-protected DSKO$: status=%s err=%d erl=%d | image unchanged: %s | %s" % (r.get("status"), m[2], m[3], open(D,"rb").read()==before, stats()))
r = go('5 CLEAR 1000\n10 ON ERROR GOTO 900\n20 LOADM "F01.BIN"\n30 POKE &H5010,PEEK(&H6000)\n40 POKE &H5001,1\n50 END\n900 POKE &H5002,ERR\n920 POKE &H5001,1', D, ["5000:3@cpu","5010:1@cpu"], timeout_s=900)
m = mem(r,"5000"); n = mem(r,"5010"); P("D read from write-protected disk: status=%s err=%d marker=%d (want 1)" % (r.get("status"), m[2], n[0]))
os.chmod(D, 0o644)
