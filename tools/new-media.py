#!/usr/bin/env python3
"""Create a blank floppy (.fd), cassette (.wav) or cartridge (.rom) image.

Usage: new-media.py <floppy|cassette|cartridge> <path> [--name LABEL] [--sides 1|2] [--tracks 40|80]
"""
import argparse
import subprocess
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("kind", choices=("floppy", "cassette", "cartridge"))
    ap.add_argument("path")
    ap.add_argument("--name", default="")
    ap.add_argument("--sides", default="1")
    ap.add_argument("--tracks", default="40", help="floppy: 40 (CD 90-640) or 80 (CD 90-351)")
    a = ap.parse_args()

    p = Path(a.path)
    if p.exists():
        sys.exit("Refusing to overwrite existing file: %s" % p)
    p.parent.mkdir(parents=True, exist_ok=True)

    if a.kind == "floppy":
        cmd = [sys.executable, str(HERE / "fdtool.py"), "new", str(p), "--sides", a.sides, "--tracks", a.tracks]
        if a.name:
            cmd += ["--name", a.name]
        subprocess.run(cmd, check=True)
    elif a.kind == "cassette":
        # 5 minutes of silence at 44.1 kHz, 8-bit mono; MAME records over it
        with wave.open(str(p), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(1)
            w.setframerate(44100)
            w.writeframes(b"\x80" * 44100 * 300)
    else:
        p.write_bytes(b"\xff" * 0x4000)
    print("Created %s" % p)


if __name__ == "__main__":
    main()
