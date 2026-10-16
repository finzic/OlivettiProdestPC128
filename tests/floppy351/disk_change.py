from ft import *
exec(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"copy_verify_writeprot.py")).read().split("f01 = ")[0])
def mkfile(path, marker):
    open(path,"wb").write(bytes([0,0,16,0x60,0, marker])+bytes(15)+bytes([0xFF,0,0,0x60,0]))
A, B = "/tmp/t13a.fd", "/tmp/t13b.fd"
for img, nm, fn, mk in ((A,"DISKA","FA.BIN",0xA1),(B,"DISKB","FB.BIN",0xB2)):
    subprocess.run(["python3", FD, "new", img, "--tracks", "80", "--name", nm], check=True, capture_output=True)
    mkfile("/tmp/_m.bin", mk)
    subprocess.run(["python3", FD, "put", img, "/tmp/_m.bin", "--as", fn, "--type", "2", "--tracks", "80", "--side", "0"], check=True, capture_output=True)
prog='''5 CLEAR 1000
6 POKE &H5005,0
10 ON ERROR GOTO 900
20 LOADM "FA.BIN"
30 POKE &H5010,PEEK(&H6000)
40 POKE &H5005,90
50 FOR I=1 TO 400:NEXT
60 LOADM "FB.BIN"
70 POKE &H5011,PEEK(&H6000)
80 POKE &H5001,1
90 END
900 POKE &H5002,ERR
910 POKE &H5003,ERL AND 255
920 POKE &H5001,1'''
r = go(prog, A, ["5000:4@cpu","5010:2@cpu"], poke_swap={"addr":0x5005,"image":B}, timeout_s=900)
m = mem(r,"5000"); n = mem(r,"5010")
P("disk change A->B: status=%s err=%d erl=%d | marker from A=%02X (want A1) | marker from B after swap=%02X (want B2)" % (r.get("status"), m[2], m[3], n[0], n[1]))
P([l for l in open(str(ROOT / "build/result.txt")) if "poke_swap" in l])
P(stats())
