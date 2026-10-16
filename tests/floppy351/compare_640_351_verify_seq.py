from ft import *
exec(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"copy_verify_writeprot.py")).read().split("f01 = ")[0])
ERR='\n900 POKE &H5002,ERR\n910 POKE &H5003,ERL AND 255\n920 POKE &H5001,1'
def mk(img, tr, name="T"):
    subprocess.run(["python3", FD, "new", img, "--tracks", str(tr), "--name", name], check=True, capture_output=True)
for ctl, tr in (("cd90_640", 40), ("cd90_351", 80)):
    kw = dict(floppy_controller=ctl, timeout_s=900, **({} if ctl=="cd90_351" else {"menu_frames": 300}))
    img = "/tmp/t11_%s.fd" % ctl; mk(img, tr)
    r = go('5 CLEAR 1000\n10 ON ERROR GOTO 900\n20 VERIFY ON\n30 POKE &H5001,1\n40 END'+ERR, img, ["5000:4@cpu"], **kw)
    m = mem(r,"5000"); P(ctl, "VERIFY ON alone: err=%d erl=%d" % (m[2], m[3]))
    open("/tmp/small.bin","wb").write(bytes([0,0,16,0x60,0])+bytes(range(16))+bytes([0xFF,0,0,0x60,0]))
    subprocess.run(["python3", FD, "put", img, "/tmp/small.bin", "--as", "S.BIN", "--type", "2", "--tracks", str(tr), "--side", "0"], check=True, capture_output=True)
    r = go('5 CLEAR 1000\n10 ON ERROR GOTO 900\n20 VERIFY ON\n30 COPY "S.BIN" TO "V.BIN"\n40 POKE &H5001,1\n50 END'+ERR, img, ["5000:4@cpu"], **kw)
    m = mem(r,"5000"); P(ctl, "VERIFY ON + COPY: err=%d erl=%d" % (m[2], m[3]), stats())
    # sequential write of 20 records, then read back and sum
    r = go('5 CLEAR 1000\n10 ON ERROR GOTO 900\n20 OPEN "O",#1,"SEQ.DAT"\n30 FOR I=1 TO 300\n40 PRINT #1,I\n50 NEXT\n60 CLOSE #1\n70 POKE &H5001,1\n80 END'+ERR, img, ["5000:4@cpu"], **kw)
    m = mem(r,"5000"); P(ctl, "write 300 records: err=%d erl=%d" % (m[2], m[3]), stats())
    r = go('5 CLEAR 1000\n10 ON ERROR GOTO 900\n20 OPEN "I",#1,"SEQ.DAT"\n30 FOR I=1 TO 100\n40 INPUT #1,A\n50 S=S+A\n60 NEXT\n70 POKE &H5010,S AND 255\n72 POKE &H5011,S\\256 AND 255\n74 POKE &H5012,I AND 255\n80 POKE &H5001,1\n90 END'+ERR, img, ["5000:4@cpu","5010:3@cpu"], **kw)
    m = mem(r,"5000"); n = mem(r,"5010"); S = sum(range(1,101))
    P(ctl, "read back first 100 of 300 records: err=%d erl=%d sum=%d (want %d)" % (m[2], m[3], n[0]+256*n[1], S & 0xFFFF))
