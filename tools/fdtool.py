#!/usr/bin/env python3
"""Create and edit Thomson/PC128 .fd floppy images (Microsoft BASIC DOS format).

Format (Manuel technique TO8, pp.208-209), checked against disks written by BASIC 128 with
the CD 90-640 controller in MAME: 40 tracks x 16 sectors x 256 bytes per side (255 data
bytes used per sector), blocks of
8 sectors (2 per track), track 20 reserved: sector 1 disk name, sector 2 FAT (byte 0 = 0,
byte n+1 = block n: $FF free, $FE reserved/absent, 0-$BF next block, $C1-$C8 last block +
sectors used), sectors 3-16 directory (32-byte entries; $FF = end, $00 = deleted).

Image sizes: 163840 = one side; 327680 = two sides interleaved per track (MAME .fd layout
for the 40-track CD 90-640); use --side 1 for the second face (drive 1 in BASIC).

  fdtool.py new  DISK.fd [--name NAME] [--sides 1|2]
  fdtool.py put  DISK.fd FILE [--as NAME.EXT] [--type 0-3] [--ascii] [--side 0|1]
  fdtool.py ls   DISK.fd [--side 0|1]
  fdtool.py get  DISK.fd NAME.EXT OUTFILE [--side 0|1]

`put` guesses the type from the extension: .BIN -> 2 (machine code, binary),
.BAS -> 0 BASIC (sent as ASCII text with CR LF line ends, flag $FF), else 1 data.
"""
import argparse
import sys
from pathlib import Path

SECTOR, SPT, TRACKS = 256, 16, 40
# BASIC 128 DOS stores 255 data bytes per sector; the 256th is $00 (verified with SAVE/SAVEM)
DATA_PER_SECTOR = 255
DIR_TRACK = 20
BLOCK_SECTORS = 8
NBLOCKS = TRACKS * 2
SIDE_SIZE = SECTOR * SPT * TRACKS
FAT_ENTRIES = 160


class Disk:
    def __init__(self, data, side=0):
        if len(data) not in (SIDE_SIZE, 2 * SIDE_SIZE):
            raise SystemExit("unsupported image size %d (expected %d or %d)" % (len(data), SIDE_SIZE, 2 * SIDE_SIZE))
        if side and len(data) == SIDE_SIZE:
            raise SystemExit("single-sided image has no side 1")
        self.d = bytearray(data)
        self.sides = len(data) // SIDE_SIZE
        self.side = side

    def off(self, track, sector):
        return ((track * self.sides + self.side) * SPT + sector - 1) * SECTOR

    def block_off(self, b):
        return self.off(b // 2, (b % 2) * BLOCK_SECTORS + 1)

    @classmethod
    def blank(cls, name="", sides=1):
        disk = cls(bytearray(b"\xE5" * SIDE_SIZE * sides))
        for side in range(sides):
            disk.side = side
            disk.format_side(name)
        disk.side = 0
        return disk

    def format_side(self, name):
        o = self.off(DIR_TRACK, 1)
        self.d[o:o + SECTOR] = b"\xFF" * SECTOR
        self.d[o:o + 8] = name.upper().encode("ascii")[:8].ljust(8)
        fat = bytearray(SECTOR)
        for b in range(FAT_ENTRIES):
            fat[b + 1] = 0xFF if b < NBLOCKS and b // 2 != DIR_TRACK else 0xFE
        o = self.off(DIR_TRACK, 2)
        self.d[o:o + SECTOR] = fat
        for s in range(3, 17):
            o = self.off(DIR_TRACK, s)
            self.d[o:o + SECTOR] = b"\xFF" * SECTOR

    @property
    def fat(self):
        o = self.off(DIR_TRACK, 2)
        return memoryview(self.d)[o:o + SECTOR]

    def entries(self):
        for s in range(3, 17):
            base = self.off(DIR_TRACK, s)
            for k in range(SECTOR // 32):
                o = base + 32 * k
                yield o, self.d[o:o + 32]

    def files(self):
        for o, e in self.entries():
            if e[0] == 0xFF:
                return
            if e[0] == 0:
                continue
            name = e[0:8].decode("latin-1").rstrip()
            ext = e[8:11].decode("latin-1").rstrip()
            yield o, name, ext, e[11], e[12], e[13], int.from_bytes(e[14:16], "big")

    def chain(self, first):
        b, out = first, []
        while True:
            out.append(b)
            nxt = self.fat[b + 1]
            if nxt >= 0xC1:
                return out, nxt - 0xC0
            if nxt > 0xBF:
                raise SystemExit("corrupt FAT at block %d ($%02X)" % (b, nxt))
            b = nxt

    def read(self, first, last_bytes):
        blocks, last_secs = self.chain(first)
        secs = []
        for i, b in enumerate(blocks):
            n = last_secs if i == len(blocks) - 1 else BLOCK_SECTORS
            secs += [self.block_off(b) + k * SECTOR for k in range(n)]
        data = bytearray()
        for k, o in enumerate(secs):
            data += self.d[o:o + (last_bytes if k == len(secs) - 1 else DATA_PER_SECTOR)]
        return bytes(data)

    def free_blocks(self):
        # Allocate outwards from the directory track, as Thomson DOS does
        order = sorted(range(NBLOCKS), key=lambda b: (abs(b // 2 - DIR_TRACK), b))
        return [b for b in order if self.fat[b + 1] == 0xFF]

    def put(self, name, ext, data, ftype, ascii_flag):
        if any(n == name and x == ext for _, n, x, *_ in self.files()):
            raise SystemExit("%s.%s already on disk" % (name, ext))
        if not data:
            raise SystemExit("empty file")
        nsec = -(-len(data) // DATA_PER_SECTOR)
        nblk = -(-nsec // BLOCK_SECTORS)
        free = self.free_blocks()
        if len(free) < nblk:
            raise SystemExit("disk full")
        blocks = free[:nblk]
        slot = next((o for o, e in self.entries() if e[0] in (0x00, 0xFF)), None)
        if slot is None:
            raise SystemExit("directory full")
        for k in range(nsec):
            chunk = data[k * DATA_PER_SECTOR:(k + 1) * DATA_PER_SECTOR]
            o = self.block_off(blocks[k // BLOCK_SECTORS]) + (k % BLOCK_SECTORS) * SECTOR
            self.d[o:o + SECTOR] = chunk.ljust(SECTOR, b"\x00")
        for i, b in enumerate(blocks):
            last = i == nblk - 1
            self.fat[b + 1] = (0xC0 + (nsec - i * BLOCK_SECTORS)) if last else blocks[i + 1]
        last_bytes = len(data) - (nsec - 1) * DATA_PER_SECTOR
        e = bytearray(b"\x00" * 32)
        e[0:8] = name.encode("ascii").ljust(8)
        e[8:11] = ext.encode("ascii").ljust(3)
        e[11] = ftype
        e[12] = 0xFF if ascii_flag else 0x00
        e[13] = blocks[0]
        e[14:16] = last_bytes.to_bytes(2, "big")
        e[17:24] = b" " * 7
        was_end = self.d[slot] == 0xFF
        self.d[slot:slot + 32] = e
        nxt = slot + 32
        if was_end and nxt < self.off(DIR_TRACK, 16) + SECTOR:
            self.d[nxt] = 0xFF


def split_name(s):
    p = Path(s).name.upper()
    name, _, ext = p.partition(".")
    if not name or len(name) > 8 or len(ext) > 3:
        raise SystemExit("bad file name %r (8.3 max)" % s)
    return name, ext


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("disk"); n.add_argument("--name", default="")
    n.add_argument("--sides", type=int, choices=(1, 2), default=1)
    p = sub.add_parser("put"); p.add_argument("disk"); p.add_argument("file")
    p.add_argument("--as", dest="as_name"); p.add_argument("--type", type=int, choices=range(4))
    p.add_argument("--ascii", action="store_true")
    l = sub.add_parser("ls"); l.add_argument("disk")
    g = sub.add_parser("get"); g.add_argument("disk"); g.add_argument("name"); g.add_argument("out")
    for sp in (p, l, g):
        sp.add_argument("--side", type=int, choices=(0, 1), default=0)
    a = ap.parse_args()

    if a.cmd == "new":
        Path(a.disk).write_bytes(Disk.blank(a.name, a.sides).d)
        print("created", a.disk)
        return
    disk = Disk(Path(a.disk).read_bytes(), a.side)
    if a.cmd == "ls":
        types = {0: "BASIC", 1: "DATA", 2: "BIN", 3: "ASM"}
        free = len(disk.free_blocks())
        for _, name, ext, t, flag, first, lb in disk.files():
            size = len(disk.read(first, lb))
            print("%-8s.%-3s %-5s %s %6d bytes" % (name, ext, types.get(t, t), "A" if flag else "B", size))
        print("%d free blocks (%d KB)" % (free, free * 2))
    elif a.cmd == "put":
        name, ext = split_name(a.as_name or a.file)
        data = Path(a.file).read_bytes()
        ftype, ascii_flag = a.type, a.ascii
        if ftype is None:
            ftype = {"BIN": 2, "BAS": 0}.get(ext, 1)
        if ext == "BAS" and a.type is None:
            text = data.decode("ascii").replace("\r\n", "\n").split("\n")
            # BASIC 128's own SAVE "x",A starts the file with CR LF
            data = b"\r\n" + b"".join(l.encode("ascii") + b"\r\n" for l in text if l.strip())
            ascii_flag = True
        disk.put(name, ext, data, ftype, ascii_flag)
        Path(a.disk).write_bytes(disk.d)
        print("added %s.%s (%d bytes)" % (name, ext, len(data)))
    elif a.cmd == "get":
        name, ext = split_name(a.name)
        for _, n, x, t, flag, first, lb in disk.files():
            if (n, x) == (name, ext):
                Path(a.out).write_bytes(disk.read(first, lb))
                return
        sys.exit("not found: %s.%s" % (name, ext))


if __name__ == "__main__":
    main()
