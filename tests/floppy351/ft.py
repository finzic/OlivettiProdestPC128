import sys, subprocess, shutil
ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); import pc128
FD = str(ROOT / "tools/fdtool.py")
def P(*a): print(*a, flush=True)
def cfg(img, **kw):
    c = {"mame": str(pc128.LOCAL_MAME), "rompath": "/tmp/pc128-mame-save-load-roms", "floppy": img,
         "line_gap_frames": 30, "char_gap_frames": 3, "floppy_controller": "cd90_351", "menu_frames": 600,
         "headless": True, "timeout_s": 900, "extra_args": ["-log"]}
    c.update(kw); return c
def go(prog, img, dumps, frames=20000, **kw):
    r = pc128.run_job("basic", prog, dumps=dumps, run_frames=frames, done_addr="5001@cpu", cfg_overrides=cfg(img, **kw))
    return r
def mem(r, prefix):
    for k, v in (r.get("mem") or {}).items():
        if k.startswith(prefix): return bytes.fromhex(v)
def log():
    return open("/tmp/error.log", errors="replace").read()
def sector(img, t, s, side=0):
    d = open(img, "rb").read(); o = (t*16 + s-1)*256; return d[o:o+256]
