#!/usr/bin/env python3
"""Create and edit Thomson/PC128 .fd floppy images (Microsoft BASIC DOS format).

Format (Manuel technique TO8, pp.208-209), checked against disks written by BASIC 128 with
the CD 90-640 controller in MAME: 40 tracks x 16 sectors x 256 bytes per side (255 data
bytes used per sector), blocks of
8 sectors (2 per track), track 20 reserved: sector 1 disk name, sector 2 FAT (byte 0 = 0,
byte n+1 = block n: $FF free, $FE reserved/absent, 0-$BF next block, $C1-$C8 last block +
sectors used), sectors 3-16 directory (32-byte entries; $FF = end, $00 = deleted).

Image sizes: 163840 = one side; 327680 = two sides. Two-sided track order (--layout): 40-track images
are interleaved per track (what MAME 0.264 uses for the CD 90-640); 80-track images are sequential,
all of side 0 then all of side 1 (verified in DCMOTO). Use --side 1 for the second face.

Use --tracks 80 on every command for 3.5in CD 90-351 images (655360 bytes for two sides).

    fdtool.py new  DISK.fd [--name NAME] [--sides 1|2] [--tracks 40|80]
  fdtool.py put  DISK.fd FILE [--as NAME.EXT] [--type 0-3] [--ascii] [--side 0|1]
    fdtool.py pack FOLDER DISK.fd [--name NAME] [--sides 1|2] [--tracks 40|80]
    fdtool.py tokenize FILE.bas OUT.bas [--rom pc128.rom]
    fdtool.py detokenize FILE.bas OUT.bas [--rom pc128.rom]
  fdtool.py ls   DISK.fd [--side 0|1]     (default: every side of a two-sided image)
  fdtool.py get  DISK.fd NAME.EXT OUTFILE [--side 0|1]
  fdtool.py cp   SRC.fd DST.fd [--src-tracks 40|80] [--dst-tracks 40|80] [--src-side N] [--dst-side N]
                 [--dst-sides 1|2] [--src-layout L] [--dst-layout L] [--name LABEL]

--layout interleaved|sequential overrides the default two-sided track order of any command.

`put` guesses the type from the extension: .BIN -> 2 (machine code, binary),
.BAS -> 0 BASIC (numbered source becomes native tokenized BASIC B by default; use --ascii
or --basic-format ascii for BASIC A saved with SAVE ...,A), else 1 data.
else 1 data.
"""
import argparse
import re
import sys
from pathlib import Path

from basic_codec import (BasicCodecError, detokenize_file, is_native_basic,
                        load_token_table, tokenize_source, validate_source)

SECTOR, SPT = 256, 16
# BASIC 128 DOS stores 255 data bytes per sector; the 256th is $00 (verified with SAVE/SAVEM)
DATA_PER_SECTOR = 255
DIR_TRACK = 20
BLOCK_SECTORS = 8
FAT_ENTRIES = 160


class Disk:
    def __init__(self, data, side=0, tracks=40, layout=None):
        side_size = SECTOR * SPT * tracks
        if len(data) not in (side_size, 2 * side_size):
            raise SystemExit("unsupported image size %d (expected %d or %d for %d tracks)"
                             % (len(data), side_size, 2 * side_size, tracks))
        if side and len(data) == side_size:
            raise SystemExit("single-sided image has no side 1")
        self.d = bytearray(data)
        self.tracks = tracks
        self.nblocks = tracks * 2
        self.sides = len(data) // side_size
        self.side = side
        # 80-track two-sided images: side 0 then side 1 (verified in DCMOTO); 40-track: MAME 0.264 interleaves
        self.layout = layout or ("sequential" if tracks == 80 else "interleaved")

    def off(self, track, sector):
        if self.layout == "sequential":
            return ((self.side * self.tracks + track) * SPT + sector - 1) * SECTOR
        return ((track * self.sides + self.side) * SPT + sector - 1) * SECTOR

    def block_off(self, b):
        return self.off(b // 2, (b % 2) * BLOCK_SECTORS + 1)

    @classmethod
    def blank(cls, name="", sides=1, tracks=40, layout=None):
        disk = cls(bytearray(b"\xE5" * SECTOR * SPT * tracks * sides), 0, tracks, layout)
        for side in range(sides):
            disk.side = side
            disk.format_side(name)
        disk.side = 0
        return disk

    def format_side(self, name):
        o = self.off(DIR_TRACK, 1)
        # Label as written by DSKINI on a real/DCMOTO disk: name, 3 constant bytes (meaning unknown), zeros
        self.d[o:o + SECTOR] = name.upper().encode("ascii")[:8].ljust(8) + b"\x8D\x5E\x25" + b"\x00" * (SECTOR - 11)
        fat = bytearray(SECTOR)
        for b in range(FAT_ENTRIES):
            fat[b + 1] = 0xFF if b < self.nblocks and b // 2 != DIR_TRACK else 0xFE
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
        order = sorted(range(self.nblocks), key=lambda b: (abs(b // 2 - DIR_TRACK), b))
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

def ascii_basic_payload(data):
    text = data.decode("latin-1")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    numbered = []
    previous_line = -1
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r"^\s*(\d+)(?:\s|$)", line)
        if not match:
            return None
        line_number = int(match.group(1))
        if line_number <= previous_line:
            raise SystemExit("BASIC source line numbers must be strictly increasing")
        previous_line = line_number
        numbered.append(line.lstrip().rstrip())
    if not numbered:
        return None
    return b"\r\n" + b"".join(line.encode("latin-1") + b"\r\n" for line in numbered)


def prepare_file(data, ext, ftype=None, ascii_force=False, basic_format="tokenized", rom_path=None):
    if ext == "BAS":
        if ftype not in (None, 0):
            raise SystemExit(".BAS files must use DOS BASIC type 0")
        if is_native_basic(data):
            return 0, False, data
        if ascii_force:
            payload = ascii_basic_payload(data)
            if payload is None:
                raise SystemExit("--ascii requires numbered ASCII BASIC source")
            return 0, True, payload
        payload = ascii_basic_payload(data)
        if payload is None:
            raise SystemExit("unrecognized .BAS file; expected numbered ASCII source or native tokenized BASIC B")
        if basic_format == "ascii":
            return 0, True, payload
        try:
            return 0, False, tokenize_source(data, load_token_table(rom_path))
        except BasicCodecError as exc:
            raise SystemExit(str(exc))
    if ftype is None:
        ftype = {"BIN": 2, "ASM": 3}.get(ext, 1)
    return ftype, ascii_force, data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("disk"); n.add_argument("--name", default="")
    n.add_argument("--sides", type=int, choices=(1, 2), default=1)
    p = sub.add_parser("put"); p.add_argument("disk"); p.add_argument("file")
    p.add_argument("--as", dest="as_name"); p.add_argument("--type", type=int, choices=range(4))
    p.add_argument("--ascii", action="store_true")
    p.add_argument("--basic-format", choices=("tokenized", "ascii"), default="tokenized",
                    help="format for plain-text .BAS files (default: tokenized BASIC B)")
    p.add_argument("--rom", help="PC128 ROM used to tokenize BASIC source")
    pack = sub.add_parser("pack", help="create a DCMOTO-compatible disk from a folder")
    pack.add_argument("folder"); pack.add_argument("disk")
    pack.add_argument("--name", default="")
    pack.add_argument("--sides", type=int, choices=(1, 2), default=1)
    pack.add_argument("--tracks", type=int, choices=(40, 80), default=80)
    pack.add_argument("--basic-format", choices=("tokenized", "ascii"), default="tokenized",
                      help="format for plain-text .BAS files (default: tokenized BASIC B)")
    pack.add_argument("--rom", help="PC128 ROM used to tokenize BASIC source")
    enc = sub.add_parser("tokenize", help="encode numbered BASIC source as native PC128 BASIC B")
    enc.add_argument("file"); enc.add_argument("out"); enc.add_argument("--rom")
    dec = sub.add_parser("detokenize", help="decode native PC128 BASIC B to numbered source")
    dec.add_argument("file"); dec.add_argument("out"); dec.add_argument("--rom")
    l = sub.add_parser("ls"); l.add_argument("disk")
    g = sub.add_parser("get"); g.add_argument("disk"); g.add_argument("name"); g.add_argument("out")
    c = sub.add_parser("cp", help="copy all files between images, e.g. 40-track to 80-track")
    c.add_argument("src"); c.add_argument("dst")
    c.add_argument("--src-tracks", type=int, choices=(40, 80), default=40)
    c.add_argument("--dst-tracks", type=int, choices=(40, 80), default=80)
    c.add_argument("--src-side", type=int, choices=(0, 1), default=0)
    c.add_argument("--dst-side", type=int, choices=(0, 1), default=0)
    c.add_argument("--dst-sides", type=int, choices=(1, 2), default=1, help="sides when DST is created")
    c.add_argument("--src-layout", choices=("interleaved", "sequential"))
    c.add_argument("--dst-layout", choices=("interleaved", "sequential"))
    c.add_argument("--name", default="", help="label when DST is created")
    for sp in (p, g):
        sp.add_argument("--side", type=int, choices=(0, 1), default=0)
    l.add_argument("--side", type=int, choices=(0, 1), help="default: all sides")
    for sp in (n, p, l, g):
        sp.add_argument("--tracks", type=int, choices=(40, 80), default=80,
                        help="80 = 3.5in (CD 90-351, default), 40 = 5.25in (CD 90-640)")
        sp.add_argument("--layout", choices=("interleaved", "sequential"),
                        help="two-sided track order; default sequential for 80 tracks, interleaved for 40")
    a = ap.parse_args()

    if a.cmd == "tokenize":
        table = load_token_table(a.rom)
        data = tokenize_source(Path(a.file).read_bytes(), table)
        Path(a.out).write_bytes(data)
        print("tokenized", a.file, "->", a.out)
        return

    if a.cmd == "detokenize":
        table = load_token_table(a.rom)
        try:
            text = detokenize_file(Path(a.file).read_bytes(), table)
        except BasicCodecError as exc:
            raise SystemExit(str(exc))
        Path(a.out).write_text(text, encoding="latin-1", newline="")
        print("detokenized", a.file, "->", a.out)
        return

    if a.cmd == "pack":
        folder, dpath = Path(a.folder), Path(a.disk)
        if not folder.is_dir():
            raise SystemExit("not a folder: %s" % folder)
        if dpath.exists():
            raise SystemExit("refusing to overwrite existing disk: %s" % dpath)
        sources = sorted(p for p in folder.iterdir() if p.is_file() and not p.name.startswith("."))
        if not sources:
            raise SystemExit("folder contains no files: %s" % folder)
        disk = Disk.blank(a.name, a.sides, a.tracks)
        for source in sources:
            name, ext = split_name(source.name)
            data = source.read_bytes()
            try:
                ftype, ascii_flag, data = prepare_file(data, ext, basic_format=a.basic_format,
                                                       rom_path=a.rom)
            except SystemExit as exc:
                raise SystemExit("%s: %s" % (source.name, exc))
            try:
                disk.put(name, ext, data, ftype, ascii_flag)
            except SystemExit as exc:
                raise SystemExit("%s: %s" % (source.name, exc))
        dpath.parent.mkdir(parents=True, exist_ok=True)
        dpath.write_bytes(disk.d)
        print("packed %d files into %s" % (len(sources), dpath))
        for _, name, ext, ftype, flag, first, last_bytes in disk.files():
            print("  %s.%s type=%d ascii=%s bytes=%d" %
                  (name, ext, ftype, bool(flag), len(disk.read(first, last_bytes))))
        return

    if a.cmd == "cp":
        src = Disk(Path(a.src).read_bytes(), a.src_side, a.src_tracks, a.src_layout)
        dpath = Path(a.dst)
        if dpath.exists():
            dst = Disk(dpath.read_bytes(), a.dst_side, a.dst_tracks, a.dst_layout)
        else:
            dst = Disk.blank(a.name, a.dst_sides, a.dst_tracks, a.dst_layout)
            dst.side = a.dst_side
        for _, name, ext, t, flag, first, lb in list(src.files()):
            dst.put(name, ext, src.read(first, lb), t, bool(flag))
            print("copied %s.%s" % (name, ext))
        dpath.write_bytes(dst.d)
        return

    if a.cmd == "new":
        Path(a.disk).write_bytes(Disk.blank(a.name, a.sides, a.tracks, a.layout).d)
        print("created", a.disk)
        return
    disk = Disk(Path(a.disk).read_bytes(), a.side or 0, a.tracks, a.layout)
    if a.cmd == "ls":
        types = {0: "BASIC", 1: "DATA", 2: "BIN", 3: "ASM"}
        sides = range(disk.sides) if a.side is None else [a.side]
        for side in sides:
            disk.side = side
            if len(sides) > 1:
                label = disk.d[disk.off(DIR_TRACK, 1):][:8].decode("latin-1").rstrip()
                print("side %d: %s" % (side, label))
            free = len(disk.free_blocks())
            for _, name, ext, t, flag, first, lb in disk.files():
                size = len(disk.read(first, lb))
                print("%-8s.%-3s %-5s %s %6d bytes" % (name, ext, types.get(t, t), "A" if flag else "B", size))
            print("%d free blocks (%d KB)" % (free, free * 2))
    elif a.cmd == "put":
        name, ext = split_name(a.as_name or a.file)
        data = Path(a.file).read_bytes()
        ftype, ascii_flag, data = prepare_file(data, ext, a.type, a.ascii,
                                               a.basic_format, a.rom)
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
