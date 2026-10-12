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
    missing = [str(path.relative_to(ROOT)) for path in (pc128_path, cd90_path) if not path.is_file()]
    if missing:
        print("Missing source ROM file(s): " + ", ".join(missing), file=sys.stderr)
        print("Place pc128.rom and cd90-640.rom in src-rom/.", file=sys.stderr)
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

    shutil.copyfile(cd90_path, ROM_DIR / "cd90-640.rom")
    print("Copied src-rom/cd90-640.rom to roms/cd90-640.rom")
    shutil.copyfile(cd90_path, pro128_dir / "cd90-640.rom")  # MAME looks for the extension ROM here
    print("Copied src-rom/cd90-640.rom to roms/pro128/cd90-640.rom")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())