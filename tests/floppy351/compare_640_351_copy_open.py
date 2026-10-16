from ft import *
exec(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"copy_verify_writeprot.py")).read().split("f01 = ")[0])
f01 = open("/tmp/f01.bin","rb").read()
def mk(img, tr):
    subprocess.run(["python3", FD, "new", img, "--tracks", str(tr), "--name", "T"], check=True, capture_output=True)
ERR='\n900 POKE &H5002,ERR\n910 POKE &H5003,ERL AND 255\n920 POKE &H5001,1'
for ctl, tr in (("cd90_640", 40), ("cd90_351", 80)):
    img = "/tmp/t10_%s.fd" % ctl; mk(img, tr)
    kw = dict(floppy_controller=ctl, timeout_s=900, **({} if ctl=="cd90_351" else {"menu_frames": 300}))
    # COPY with file on the disk (small file so 640 fits)
    open("/tmp/small.bin","wb").write(bytes([0,0,16,0x60,0])+bytes(range(16))+bytes([0xFF,0,0,0x60,0]))
    subprocess.run(["python3", FD, "put", img, "/tmp/small.bin", "--as", "S.BIN", "--type", "2", "--tracks", str(tr), "--side", "0"], check=True, capture_output=True)
    r = go('5 CLEAR 1000\n10 ON ERROR GOTO 900\n30 COPY "S.BIN" TO "T.BIN"\n40 POKE &H5001,1\n50 END'+ERR, img, ["5000:4@cpu"], **kw)
    m = mem(r,"5000"); P(ctl, "COPY: err=%d erl=%d" % (m[2], m[3]), "(255=none)")
    r = go('5 CLEAR 1000\n10 ON ERROR GOTO 900\n20 OPEN "O",#1,"SEQ.DAT"\n30 PRINT #1,"HELLO"\n40 CLOSE #1\n50 POKE &H5001,1\n60 END'+ERR, img, ["5000:4@cpu"], **kw)
    m = mem(r,"5000"); P(ctl, "OPEN O/PRINT#/CLOSE: err=%d erl=%d" % (m[2], m[3]), "(255=none)")
    ls = subprocess.run(["python3", FD, "ls", img, "--tracks", str(tr), "--side", "0"], capture_output=True, text=True).stdout
    P(ctl, "dir now:", " | ".join(l.strip() for l in ls.strip().splitlines()))
