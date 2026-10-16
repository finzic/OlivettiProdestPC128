# Builds the ROM set MAME needs for the pro128 driver from the repo's src-rom/ images.
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/pc128-mame-save-load-roms") / "pro128"
OUT.mkdir(parents=True, exist_ok=True)
pc = (ROOT / "src-rom/pc128.rom").read_bytes()
(OUT / "pro128.iw01").write_bytes(pc[:0x8000])
(OUT / "basico.iw02").write_bytes(pc[0x8000:0x10000])
cd = (ROOT / "src-rom/cd90-351.rom").read_bytes()
for i in range(4):
    (OUT / ("cd-351-%d.rom" % i)).write_bytes(cd[2048 * i + 0: 2048 * i + 1984])
(OUT / "cd90-640.rom").write_bytes((ROOT / "roms/pro128/cd90-640.rom").read_bytes())
print("staged in", OUT)
