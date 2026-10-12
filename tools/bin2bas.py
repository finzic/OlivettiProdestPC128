#!/usr/bin/env python3
"""Turn a Thomson/DECB .BIN (LOADM format) into a BASIC loader program.

The loader POKEs the code from DATA lines (with per-line checksums), like
the "creation programs" in 02-interpreteur-basic-to9, then EXECs it.

Usage: bin2bas.py basext.bin basext.bas [--clear 0x8FFF] [--start 10]
"""
import argparse


def segments(blob):
    i, segs, exec_addr = 0, [], None
    while i < len(blob):
        kind = blob[i]
        n = blob[i + 1] << 8 | blob[i + 2]
        addr = blob[i + 3] << 8 | blob[i + 4]
        if kind == 0x00:
            segs.append((addr, blob[i + 5:i + 5 + n]))
            i += 5 + n
        elif kind == 0xFF:
            exec_addr = addr
            break
        else:
            raise SystemExit(f"bad block type ${kind:02X} at offset {i}")
    return segs, exec_addr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bin")
    ap.add_argument("bas")
    ap.add_argument("--clear", default="0x8FFF")
    ap.add_argument("--start", type=int, default=10)
    ap.add_argument("--no-exec", action="store_true", help="only POKE the code (e.g. USR routines)")
    a = ap.parse_args()

    segs, exec_addr = segments(open(a.bin, "rb").read())
    ln = a.start
    out = []

    def line(text):
        nonlocal ln
        out.append(f"{ln} {text}")
        ln += 10

    line(f"CLEAR ,{int(a.clear, 0)}")
    line("READ A:IF A<0 THEN END" if a.no_exec else "READ A:IF A<0 THEN READ E:EXEC E:END")
    line("READ H$,C:S=0")
    line('FOR I=1 TO LEN(H$) STEP 2:V=VAL("&H"+MID$(H$,I,2)):POKE A,V:A=A+1:S=S+V:NEXT')
    line('IF S<>C THEN PRINT "CHECKSUM ERROR AT";A:END')
    line(f"GOTO {a.start + 10}")
    for addr, data in segs:
        # Trailing reserved space (rmb) is not emitted by the assembler.
        for k in range(0, len(data), 24):
            chunk = data[k:k + 24]
            line(f'DATA {addr + k},"{chunk.hex().upper()}",{sum(chunk)}')
    line(f"DATA -1,{exec_addr}")
    with open(a.bas, "w", newline="\r\n") as f:
        f.write("\n".join(out) + "\n")
    print(f"{a.bas}: {len(out)} lines, exec ${exec_addr:04X}")


if __name__ == "__main__":
    main()
