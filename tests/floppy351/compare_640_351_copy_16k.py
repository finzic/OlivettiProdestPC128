from ft import *
exec(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"copy_verify_writeprot.py")).read().split("f01 = ")[0])
ERR='\n900 POKE &H5002,ERR\n910 POKE &H5003,ERL AND 255\n920 POKE &H5001,1'
f01 = open("/tmp/f01.bin","rb").read()
for ctl, tr in (("cd90_640", 40), ("cd90_351", 80)):
    kw = dict(floppy_controller=ctl, timeout_s=900, **({} if ctl=="cd90_351" else {"menu_frames": 300}))
    img = "/tmp/t12_%s.fd" % ctl
    subprocess.run(["python3", FD, "new", img, "--tracks", str(tr), "--name", "T"], check=True, capture_output=True)
    subprocess.run(["python3", FD, "put", img, "/tmp/f01.bin", "--as", "F01.BIN", "--type", "2", "--tracks", str(tr), "--side", "0"], check=True, capture_output=True)
    r = go('5 CLEAR 1000\n10 ON ERROR GOTO 900\n30 COPY "F01.BIN" TO "CPY.BIN"\n40 POKE &H5001,1\n50 END'+ERR, img, ["5000:4@cpu"], **kw)
    m = mem(r,"5000")
    p = subprocess.run(["python3", FD, "get", img, "CPY.BIN", "/tmp/_g.bin", "--tracks", str(tr), "--side", "0"], capture_output=True)
    g = open("/tmp/_g.bin","rb").read() if p.returncode == 0 else None
    P(ctl, "COPY 16K file: err=%d erl=%d (255=none) copy exact: %s" % (m[2], m[3], g == f01))
