#!/usr/bin/env python3
"""Locate BASIC extension points in a 6809 BASIC ROM dump (PC128/MO6/TO).

Applies the search method of "L'interpreteur BASIC TO7-70/TO9" to a ROM
image instead of PEEKing on the machine:
  * keyword tables (several encodings) and their token numbers
  * every reference to a keyword table address (LDX #, data word, ...)
  * candidate dispatch tables (runs of ROM pointers)
  * JSR/JMP from ROM into RAM  -> the interpreter's RAM hooks
  * JSR <dp (direct) targets   -> CHRGET/CHRGOT-style RAM routines
  * most-called ROM routines   -> SN error, expression evaluator, ...

Usage:
  rom_scan.py --rom basic128_b0.rom@0xB000 [--rom other.rom@0xC000 ...]
              [--ram 0x2000-0x9FFF] [--dump 0xB123:64]
Each --rom is scanned as a separate bank mapped at the given address.
"""
import argparse
import re
from collections import Counter, defaultdict

KNOWN = {"END", "FOR", "NEXT", "DATA", "INPUT", "DIM", "READ", "LET", "GOTO",
         "RUN", "IF", "RESTORE", "GOSUB", "RETURN", "REM", "STOP", "PRINT",
         "SGN", "INT", "ABS", "SQR", "LOG", "EXP", "COS", "SIN", "TAN", "PEEK",
         "LEN", "STR$", "VAL", "ASC", "CHR$", "LEFT$", "RIGHT$", "MID$", "POKE"}
WORDCH = set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ$#()0123456789+-*/^<>=&'")


def parse(data, i, fmt):
    """Parse one keyword at i; return (word, next_index) or None."""
    if fmt == "hibit_last":
        j, w = i, bytearray()
        while j < len(data) and len(w) < 10:
            c = data[j]
            if c & 0x80:
                if (c & 0x7F) in WORDCH:
                    w.append(c & 0x7F)
                    return w.decode(), j + 1
                return None
            if c not in WORDCH:
                return None
            w.append(c)
            j += 1
    elif fmt == "hibit_first":
        if i >= len(data) or not data[i] & 0x80 or (data[i] & 0x7F) not in WORDCH:
            return None
        j, w = i + 1, bytearray([data[i] & 0x7F])
        while j < len(data) and data[j] in WORDCH and not data[j] & 0x80 and len(w) < 10:
            w.append(data[j])
            j += 1
        return w.decode(), j
    elif fmt == "zero_term":
        m = re.match(rb"[A-Z][A-Z$#()0-9+\-*/^<>=&']{0,9}\x00", data[i:i + 12])
        if m:
            return m.group()[:-1].decode(), i + len(m.group())
    elif fmt == "len_prefix":
        n = data[i]
        if 1 <= n <= 9 and all(c in WORDCH for c in data[i + 1:i + 1 + n]) and len(data) > i + n:
            return data[i + 1:i + 1 + n].decode(), i + 1 + n
    return None


def find_tables(data, base, min_words=8):
    tables = []
    for fmt in ("hibit_last", "hibit_first", "zero_term", "len_prefix"):
        i = 0
        while i < len(data):
            j, words = i, []
            while (r := parse(data, j, fmt)):
                words.append(r[0])
                j = r[1]
            if len(words) >= min_words and len(KNOWN & set(words)) >= 3:
                tables.append((base + i, fmt, words, base + j))
                i = j
            else:
                i += 1
    return tables


def word_refs(data, base, value):
    """Places where `value` appears big-endian, with the preceding opcode."""
    hi, lo = value >> 8, value & 0xFF
    ops = {0x8E: "LDX #", 0xCE: "LDU #", 0xCC: "LDD #", 0xBE: "LDX ext", 0xFC: "LDD ext",
           0xBD: "JSR", 0x7E: "JMP", 0xBF: "STX ext", 0xFD: "STD ext"}
    out = []
    for i in range(1, len(data) - 1):
        if data[i] == hi and data[i + 1] == lo:
            op = data[i - 1]
            if i >= 2 and data[i - 2] == 0x10 and op == 0x8E:
                kind = "LDY #"
            else:
                kind = ops.get(op, "data")
            out.append((base + i, kind))
    return out


def pointer_runs(data, base, lo, hi, min_len=16):
    runs, i = [], 0
    while i < len(data) - 1:
        j = i
        while j < len(data) - 1 and lo <= (data[j] << 8 | data[j + 1]) <= hi:
            j += 2
        n = (j - i) // 2
        if n >= min_len:
            runs.append((base + i, n))
            i = j
        else:
            i += 1
    return runs


def calls(data, base, ram_lo, ram_hi):
    ram = defaultdict(list)
    rom = Counter()
    direct = Counter()
    end = base + len(data)
    for i in range(len(data) - 3):
        op = data[i]
        if op in (0xBD, 0x7E):
            t = data[i + 1] << 8 | data[i + 2]
            if ram_lo <= t <= ram_hi:
                ram[t].append(("JSR" if op == 0xBD else "JMP", base + i))
            elif base <= t < end and op == 0xBD:
                rom[t] += 1
        elif op in (0xAD, 0x6E) and data[i + 1] == 0x9F:
            t = data[i + 2] << 8 | data[i + 3]
            if ram_lo <= t <= ram_hi:
                ram[t].append(("JSR[]" if op == 0xAD else "JMP[]", base + i))
        elif op == 0x17:  # LBSR
            off = (data[i + 1] << 8 | data[i + 2])
            off = off - 0x10000 if off & 0x8000 else off
            t = base + i + 3 + off
            if base <= t < end:
                rom[t] += 1
        elif op == 0x9D:
            direct[data[i + 1]] += 1
    return ram, rom, direct


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", action="append", required=True, help="FILE@ADDR")
    ap.add_argument("--ram", default="0x2000-0x9FFF", help="RAM range for hooks")
    ap.add_argument("--dump", action="append", default=[], help="ADDR:LEN hex dump")
    a = ap.parse_args()
    ram_lo, ram_hi = (int(x, 0) for x in a.ram.split("-"))

    for spec in a.rom:
        path, addr = spec.rsplit("@", 1)
        base = int(addr, 0)
        data = open(path, "rb").read()
        end = base + len(data) - 1
        print(f"\n######## {path}  ${base:04X}-${end:04X}")

        print("\n== Keyword tables")
        for start, fmt, words, stop in find_tables(data, base):
            print(f"\n-- ${start:04X}-${stop - 1:04X}  format={fmt}  words={len(words)}")
            for k in range(0, len(words), 8):
                print("   " + "  ".join(f"{0x80 + n:02X}:{w}" for n, w in enumerate(words[k:k + 8], k)))
            for ref, kind in word_refs(data, base, start):
                print(f"   referenced at ${ref:04X} ({kind})")

        print("\n== Pointer runs into this ROM (dispatch table candidates)")
        for start, n in pointer_runs(data, base, base, end):
            refs = ", ".join(f"${r:04X}({k})" for r, k in word_refs(data, base, start)[:6])
            print(f"   ${start:04X}: {n} entries   refs: {refs or '-'}")

        ram, rom, direct = calls(data, base, ram_lo, ram_hi)
        print(f"\n== JSR/JMP into RAM ${ram_lo:04X}-${ram_hi:04X} (hooks)")
        for t in sorted(ram):
            sites = ram[t]
            s = ", ".join(f"{k}@${p:04X}" for k, p in sites[:6])
            more = f" (+{len(sites) - 6})" if len(sites) > 6 else ""
            print(f"   ${t:04X}  x{len(sites):<3} {s}{more}")

        print("\n== Most used JSR <direct targets (CHRGET/CHRGOT candidates; add DP*256)")
        print("   " + "  ".join(f"${t:02X}:{n}" for t, n in direct.most_common(12)))

        print("\n== Most called ROM routines (SN error, evaluator, ...)")
        print("   " + "  ".join(f"${t:04X}:{n}" for t, n in rom.most_common(30)))

        for d in a.dump:
            ad, ln = (int(x, 0) for x in d.split(":"))
            if base <= ad <= end:
                print(f"\n== Dump ${ad:04X}")
                for k in range(ad, min(ad + ln, end + 1), 16):
                    chunk = data[k - base:k - base + 16]
                    print(f"   {k:04X}: " + " ".join(f"{c:02X}" for c in chunk))


if __name__ == "__main__":
    main()
