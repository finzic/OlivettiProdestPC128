from ft import *
IMG="/tmp/t8.fd"
subprocess.run(["python3", FD, "new", IMG, "--tracks", "80", "--name", "T79"], check=True)
prog='''5 CLEAR 1000
10 ON ERROR GOTO 900
20 A$=STRING$(128,65)
25 B$=STRING$(128,66)
30 DSKO$ 0,79,5,A$
40 DSKO$ 0,79,16,STRING$(128,67)
50 C$=DSKI$(0,79,5)
60 POKE &H5010,ASC(C$)
62 POKE &H5011,ASC(RIGHT$(C$,1))
64 POKE &H5012,LEN(C$)
70 POKE &H5001,1
80 END
900 POKE &H5002,ERR
910 POKE &H5003,ERL AND 255
920 POKE &H5001,1'''
r=go(prog, IMG, ["5000:4@cpu","5010:4@cpu"], frames=20000, timeout_s=900)
P(r.get("status"), r.get("frames"))
m=mem(r,"5000"); n=mem(r,"5010"); P("err/erl", m[2], m[3], "(unset=junk)", "C$[0]=%d D$[0]=%d len %d %d"%tuple(n))
s5=sector(IMG,79,5); s16=sector(IMG,79,16)
P("s5 first/mid/last:", s5[0], s5[127], s5[128], s5[255], "| s16:", s16[0], s16[127], s16[128], s16[255])
P("DSKI$ read back: first=%c last=%c len=%d" % (n[0], n[1], n[2]))
L=log(); P("writes",L.count("write_sector end"),"reads",L.count("read_sector end"),"timeouts",L.count("sector search timeout"),"crcerr",L.count("crcer"))
