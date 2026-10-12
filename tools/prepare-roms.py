#!/usr/bin/env python3
"""Prepare the ignored MAME ROM directory from locally supplied DCMOTO ROMs."""
import shutil
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "src-rom"
ROM_DIR = ROOT / "roms"

SEGMENTS = (
    ("basico-0.rom", 0x0000, 12288, 0x98B10D5E),
    ("pro128-0.rom", 0x3000, 4096, 0xA8AEF291),
    ("basico-1.rom", 0x4000, 12288, 0x721D2124),
    ("pro128-1.rom", 0x7000, 4096, 0x5B3340EC),
    ("basico-2.rom", 0x8000, 16384, 0x135438AB),
    ("basico-3.rom", 0xC000, 16384, 0x2C2BEFA6),
)


def main():
    pc128_path = SOURCE_DIR / "pc128.rom"
    cd90_path = SOURCE_DIR / "cd90-640.rom"
    cd351_path = SOURCE_DIR / "cd90-351.rom"
    if not pc128_path.is_file() or not (cd351_path.is_file() or cd90_path.is_file()):
        print("Place pc128.rom and cd90-351.rom (or cd90-640.rom) in src-rom/.", file=sys.stderr)
        return 1

    image = pc128_path.read_bytes()
    if len(image) != 0x10000:
        print(f"{pc128_path.relative_to(ROOT)} must be exactly 65536 bytes; got {len(image)}.", file=sys.stderr)
        return 1

    prepared = []
    for name, offset, size, expected_crc in SEGMENTS:
        data = image[offset:offset + size]
        actual_crc = zlib.crc32(data)
        if actual_crc != expected_crc:
            print(f"Unexpected CRC32 for {name}: {actual_crc:08x} (expected {expected_crc:08x}).", file=sys.stderr)
            return 1
        prepared.append((name, data))

    pro128_dir = ROM_DIR / "pro128"
    pro128_dir.mkdir(parents=True, exist_ok=True)
    for name, data in prepared:
        (pro128_dir / name).write_bytes(data)
        print(f"Prepared roms/pro128/{name}")

    if cd351_path.is_file():
        data = cd351_path.read_bytes()
        if len(data) != 8192:
            print(f"{cd351_path.relative_to(ROOT)} must be 8192 bytes; got {len(data)}.", file=sys.stderr)
            return 1
        for i in range(4):  # 4 pages of 2 KB, MAME uses the first 1984 bytes of each
            for d in (ROM_DIR / "cd90_351", pro128_dir):
                d.mkdir(parents=True, exist_ok=True)
                (d / f"cd-351-{i}.rom").write_bytes(data[i * 2048:i * 2048 + 1984])
        print("Prepared cd-351-0..3.rom in roms/cd90_351/ and roms/pro128/")
    if cd90_path.is_file():
        shutil.copyfile(cd90_path, ROM_DIR / "cd90-640.rom")
        print("Copied src-rom/cd90-640.rom to roms/cd90-640.rom")
        shutil.copyfile(cd90_path, pro128_dir / "cd90-640.rom")  # MAME looks for the extension ROM here
        print("Copied src-rom/cd90-640.rom to roms/pro128/cd90-640.rom")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())