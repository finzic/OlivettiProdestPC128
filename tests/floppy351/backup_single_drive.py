from ft import *
SRC="/tmp/t7src.fd"; DST="/tmp/t7dst.fd"
shutil.copy("/tmp/pc128-full.fd", SRC)
subprocess.run(["python3", FD, "new", DST, "--tracks", "80", "--name", "BLANK"], check=True)
prog='5 CLEAR 1000\n6 ON ERROR GOTO 900\n10 BACKUP 0 TO 0\n20 POKE &H5001,1\n30 END\n900 POKE &H5002,ERR\n910 POKE &H5001,1'
rk={"pc_lo":0xF000,"pc_hi":0xF7FF,"idle_frames":120,"key":"\r","images":[DST,SRC]}
r=go(prog, SRC, ["5000:4@cpu"], frames=150000, timeout_s=3000, run_keys=rk)
P(r.get("status"), r.get("frames"), r.get("error"))
open("/tmp/t7.res","w").write(open(str(ROOT / "build/result.txt")).read())
a=open(SRC,"rb").read(); b=open(DST,"rb").read()
d=[i for i in range(len(a)) if a[i]!=b[i]]
P("src==dst:", not d, len(d), "diff bytes", "first track", d[0]//4096 if d else None)
L=log(); P("reads",L.count("read_sector end"),"writes",L.count("write_sector end"),"timeouts",L.count("sector search timeout"),"crcerr",L.count("crcer"))
