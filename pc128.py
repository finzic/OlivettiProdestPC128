#!/usr/bin/env python3
"""PC128 / Thomson MO6 emulator harness (scripted MAME). Standard library only.

CLI:
    python3 pc128.py basic examples/hello.bas [--dump 9F00:16] [--done-addr 9F01]
    python3 pc128.py asm   examples/hello.asm [--dump 9F00:16] [--done-addr 9F01]

Each run boots a fresh emulated machine, runs the program, and returns:
status (done/timeout), CPU registers, requested memory dumps, and a screenshot.
"""
import argparse
import json
import re
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FPS = 50  # Thomson MO6 / PC128 video frame rate
# The only supported MAME: built from source and patched by tools/prepare-mame.sh.
LOCAL_MAME = ROOT / "tools" / ".local" / "mame" / "mame_thomson" / "thomson"

DEFAULT_CONFIG = {
    "mame": "mame",            # "mame" = LOCAL_MAME (never a system MAME); or an explicit path
    "machine": "pro128",        # check: mame -listxml | grep -i -E "pc128|mo6"
    "rompath": "",             # folder with the Thomson ROM sets (MAME needs them)
    "lwasm": str(ROOT / "tools" / ".local" / "lwtools-4.24" / "lwasm" / "lwasm"),
    "boot_frames": 250,        # ~5 s of emulated time to reach the boot menu
    "menu_key": "1",           # boot menu: "1" BASIC 128, "2" BASIC 1.0
    "menu_frames": 600,        # wait after menu_key for the BASIC prompt (CD90-351 boot)
    "default_bank": 6,         # BASIC 128 bank read at $6000-$9FFF when no @n is given (power-on bank)
    "data_banks": [":bank7", ":bank8"],  # MAME banks behind $6000-$7FFF and $8000-$9FFF (pro128, MAME 0.264)
    "line_gap_frames": 6,      # pause between typed BASIC lines
    "run_frames": 300,         # ~6 s of emulated run time
    "timeout_s": 120,          # real-time limit for the whole MAME process
    "headless": False,         # True adds -video none (screenshot may not work)
    "floppy": "",              # .fd image for drive 0 (empty = no floppy controller)
    "floppy2": "",             # cd90_351 only: .fd image for the second drive (BASIC 2:/3:)
    "floppy_controller": "cd90_351",  # original 3.5" drive; cd90_640 is the optional fallback
    "extra_args": [],
}


# ------------------------------------------------------------------ helpers --
def load_config(overrides=None):
    cfg = dict(DEFAULT_CONFIG)
    path = ROOT / "config.json"
    if path.exists():
        cfg.update(json.loads(path.read_text()))
    cfg.update({k: v for k, v in (overrides or {}).items() if v is not None})
    if cfg["mame"] == "mame":
        cfg["mame"] = str(LOCAL_MAME)
    lwasm_path = Path(cfg["lwasm"])
    cfg["lwasm"] = str(lwasm_path if lwasm_path.is_absolute() else ROOT / lwasm_path)
    cfg["rompath"] = os.path.expandvars(os.path.expanduser(cfg["rompath"]))
    rompath = os.path.expandvars(os.path.expanduser(cfg["rompath"]))
    if rompath:
        rompath_path = Path(rompath)
        if not rompath_path.is_absolute():
            rompath_path = ROOT / rompath_path
        cfg["rompath"] = str(rompath_path)
    return cfg


def parse_int(value):
    """Python int, or a hex string: 0x9F00, $9F00, &H9F00 or bare 9F00 (always hex)."""
    if isinstance(value, int):
        return value
    s = str(value).strip()
    s = re.sub(r"^(0x|\$|&H)", "", s, flags=re.I)
    return int(s, 16)


def parse_dump(spec):
    """'9F00:16' or '9F00:16@3' (BASIC 128 bank 3) -> {'addr', 'len', 'bank'}. Address hex, length decimal."""
    if isinstance(spec, dict):
        return {"addr": parse_int(spec["addr"]), "len": int(spec["len"]), "bank": spec.get("bank")}
    spec, _, bank = str(spec).partition("@")
    addr, _, length = spec.partition(":")
    return {"addr": parse_int(addr), "len": int(length or 16), "bank": bank.strip() or None}


def resolve_page(addr, bank, cfg, mode):
    """RAM page (0-7) to read at addr, or None for the CPU's current view.

    BASIC 128 maps 'BANK n' (n=1..6) to page n+1 at $6000-$9FFF; '@cpu' forces the CPU view.
    """
    if not 0x6000 <= addr <= 0x9FFF or str(bank).lower() == "cpu":
        return None
    if bank is None:
        if mode != "basic" or cfg["menu_key"] != "1":
            return None
        bank = cfg["default_bank"]
    n = int(bank)
    if not 1 <= n <= 6:
        raise ValueError("BASIC 128 bank must be 1-6 (got %s)" % bank)
    return n + 1


def lua_literal(obj):
    if obj is None:
        return "nil"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, str):
        out = []
        for b in obj.encode("utf-8"):
            if 32 <= b < 127 and chr(b) not in '"\\':
                out.append(chr(b))
            else:
                out.append("\\%03d" % b)
        return '"' + "".join(out) + '"'
    if isinstance(obj, (list, tuple)):
        return "{" + ",".join(lua_literal(x) for x in obj) + "}"
    if isinstance(obj, dict):
        return "{" + ",".join("[%s]=%s" % (lua_literal(k), lua_literal(v)) for k, v in obj.items()) + "}"
    raise TypeError(type(obj))


def upcase_outside_quotes(line):
    out, in_q = [], False
    for ch in line:
        if ch == '"':
            in_q = not in_q
        out.append(ch if in_q else ch.upper())
    return "".join(out)


def prepare_basic(text, upcase=True):
    lines = ["NEW"]
    for raw in text.replace("\r\n", "\n").split("\n"):
        s = raw.rstrip().encode("ascii", "replace").decode()
        if not s.strip():
            continue
        lines.append(upcase_outside_quotes(s) if upcase else s)
    lines.append("RUN")
    return lines


def parse_decb(data):
    """Parse a DECB/CoCo-style binary (lwasm --format=decb): returns (segments, exec_addr)."""
    segs, entry, i = [], None, 0
    while i < len(data):
        t = data[i]
        if t == 0x00:
            length = (data[i + 1] << 8) | data[i + 2]
            addr = (data[i + 3] << 8) | data[i + 4]
            segs.append((addr, data[i + 5:i + 5 + length]))
            i += 5 + length
        elif t == 0xFF:
            entry = (data[i + 3] << 8) | data[i + 4]
            break
        else:
            raise ValueError("bad DECB record type 0x%02X at offset %d" % (t, i))
    if not segs:
        raise ValueError("assembler produced no code")
    if not entry:
        entry = segs[0][0]
    return segs, entry


def assemble(code, cfg):
    build = ROOT / "build"
    src, binf, lst = build / "prog.asm", build / "prog.bin", build / "prog.lst"
    src.write_text(code)
    binf.unlink(missing_ok=True)
    try:
        p = subprocess.run(
            [cfg["lwasm"], "--format=decb", "--output=%s" % binf, "--list=%s" % lst, str(src)],
            capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return {"ok": False, "error": "lwasm not found (%r). Run tools/setup-lwasm.sh first." % cfg["lwasm"]}
    if p.returncode != 0 or not binf.exists():
        return {"ok": False, "error": (p.stdout + p.stderr).strip() or "assembler failed"}
    try:
        segs, entry = parse_decb(binf.read_bytes())
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "segments": segs, "entry": entry, "listing": str(lst),
            "warnings": (p.stdout + p.stderr).strip()}


def parse_result(path):
    res = {"status": "no-result", "frames": None, "regs": {}, "mem": {}, "notes": []}
    if not path.exists():
        return res
    for line in path.read_text().splitlines():
        key, _, rest = line.partition(" ")
        if key == "status":
            res["status"] = rest
        elif key == "frames":
            res["frames"] = int(rest)
        elif key == "reg":
            name, _, val = rest.partition("=")
            res["regs"][name] = val
        elif key == "mem":
            label, hexbytes = rest.split(" ")
            res["mem"][label] = hexbytes
        elif key == "note":
            res["notes"].append(rest)
    return res


# --------------------------------------------------------------------- main --
def run_job(mode, code, dumps=None, run_frames=None, boot_frames=None,
            done_addr=None, upcase=True, cfg_overrides=None):
    """Run BASIC (mode='basic') or 6809 assembly (mode='asm'); returns a dict."""
    if mode not in ("basic", "asm"):
        raise ValueError("mode must be 'basic' or 'asm'")
    cfg = load_config(cfg_overrides)
    build, out = ROOT / "build", ROOT / "out"
    for d in (build, out, build / "cfg", build / "nvram"):
        d.mkdir(parents=True, exist_ok=True)
    for old in out.rglob("*.png"):
        old.unlink()
    result_path = build / "result.txt"
    result_path.unlink(missing_ok=True)

    run_frames = int(run_frames or cfg["run_frames"])
    boot_frames = int(boot_frames or cfg["boot_frames"])
    dump_list = []
    for spec in dumps or []:
        d = parse_dump(spec)
        page = resolve_page(d["addr"], d["bank"], cfg, mode)
        label = "%04X:%d" % (d["addr"], d["len"]) + ("@%d" % (page - 1) if page else "")
        dump_list.append({"addr": d["addr"], "len": d["len"], "page": page, "label": label})
    done = parse_dump(str(done_addr)) if done_addr not in (None, "") else None
    job = {
        "mode": mode,
        "boot_frames": boot_frames,
        "menu_key": cfg["menu_key"],
        "menu_frames": int(cfg["menu_frames"]),
        "line_gap_frames": int(cfg["line_gap_frames"]),
        "char_gap_frames": int(cfg.get("char_gap_frames", 0)),
        "run_keys": cfg.get("run_keys"),
        "poke_swap": cfg.get("poke_swap"),
        "run_frames": run_frames,
        "done_addr": done["addr"] if done else None,
        "done_page": resolve_page(done["addr"], done["bank"], cfg, mode) if done else None,
        "dumps": dump_list,
        "data_banks": list(cfg["data_banks"]),
        "result_path": str(result_path),
    }
    reply = {"ok": True, "mode": mode}

    if mode == "basic":
        job["basic_lines"] = prepare_basic(code, upcase)
        n_lines = len(job["basic_lines"])
        # typing takes boot + lines * (gap + a few frames to be typed)
        typing_frames = n_lines * (job["line_gap_frames"] + 12) + \
            (job["char_gap_frames"] + 4 if job["char_gap_frames"] else 0) * sum(len(l) + 1 for l in job["basic_lines"])
    else:
        asm = assemble(code, cfg)
        if not asm["ok"]:
            return {"ok": False, "stage": "assemble", "error": asm["error"]}
        job["segments"] = [{"addr": a, "hex": d.hex()} for a, d in asm["segments"]]
        job["entry"] = asm["entry"]
        reply.update(entry="%04X" % asm["entry"], listing=asm["listing"],
                     segments=["%04X+%d" % (a, len(d)) for a, d in asm["segments"]])
        if asm["warnings"]:
            reply["assembler_output"] = asm["warnings"]
        typing_frames = 0

    total_frames = boot_frames + int(cfg["menu_frames"]) + typing_frames + run_frames + 20
    job_lua = build / "job.lua"
    job_lua.write_text("CONFIG = %s\n%s" % (lua_literal(job), (ROOT / "harness.lua").read_text()))

    cmd = [cfg["mame"], cfg["machine"],
           "-sound", "none", "-nothrottle", "-skip_gameinfo", "-natural",
           "-snapshot_directory", str(out), "-snapname", "screen",
           "-cfg_directory", str(build / "cfg"), "-nvram_directory", str(build / "nvram"),
           "-autoboot_script", str(job_lua),
           "-seconds_to_run", str(total_frames // FPS + 10)]
    cmd += ["-video", "none"] if cfg["headless"] else ["-window", "-resolution", "960x720", "-nomaximize"]
    if cfg["rompath"]:
        cmd += ["-rompath", cfg["rompath"]]
    if cfg["floppy"]:
        cmd += ["-extension", cfg["floppy_controller"], "-flop1", str(Path(cfg["floppy"]).resolve())]
        if cfg["floppy2"] and cfg["floppy_controller"] == "cd90_351":
            cmd += ["-extension:cd90_351:thmfc1:1", "dd90_352", "-flop2", str(Path(cfg["floppy2"]).resolve())]
    cmd += list(cfg["extra_args"])

    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=int(cfg["timeout_s"]))
    except FileNotFoundError:
        return {"ok": False, "stage": "launch",
                "error": "MAME not found (%r). Build it with tools/prepare-mame.sh." % cfg["mame"]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "launch", "error": "MAME exceeded timeout_s=%s" % cfg["timeout_s"]}

    res = parse_result(result_path)
    shots = sorted(out.rglob("*.png"), key=lambda f: f.stat().st_mtime)
    reply.update(res)
    reply["screenshot"] = str(shots[-1]) if shots else None
    if res["status"] == "no-result":
        reply["ok"] = False
        reply["stage"] = "emulator"
        reply["error"] = ("MAME exited without writing results (exit code %d). Usually missing ROMs, "
                          "a wrong machine name, or a Lua error - see mame_output." % p.returncode)
        reply["mame_output"] = (p.stdout + p.stderr).strip()[-2000:]
    return reply


def format_report(r):
    if not r.get("ok"):
        return "FAILED (%s): %s\n%s" % (r.get("stage", "?"), r.get("error", ""), r.get("mame_output", ""))
    lines = ["status: %s after %s frames" % (r["status"], r["frames"])]
    if r.get("entry"):
        lines.append("entry: %s  segments: %s" % (r["entry"], ", ".join(r["segments"])))
    if r["regs"]:
        lines.append("regs: " + " ".join("%s=%s" % kv for kv in r["regs"].items()))
    for k, v in r["mem"].items():
        lines.append("mem %s: %s" % (k, " ".join(v[i:i + 2] for i in range(0, len(v), 2))))
    for n in r["notes"]:
        lines.append("note: " + n)
    lines.append("screenshot: %s" % r.get("screenshot"))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["basic", "asm"])
    ap.add_argument("file")
    ap.add_argument("--dump", action="append", default=[], help="HEXADDR:LEN, repeatable")
    ap.add_argument("--done-addr", help="hex address; program writes non-zero there to finish early")
    ap.add_argument("--run-frames", type=int)
    ap.add_argument("--boot-frames", type=int)
    ap.add_argument("--no-upcase", action="store_true", help="BASIC: do not uppercase typed text")
    ap.add_argument("--json", action="store_true", help="print raw JSON")
    ap.add_argument("--fd", help=".fd floppy image to mount in drive 0")
    a = ap.parse_args()

    code = Path(a.file).read_text()
    r = run_job(a.mode, code, a.dump, a.run_frames, a.boot_frames, a.done_addr, not a.no_upcase,
                cfg_overrides={"floppy": a.fd})
    print(json.dumps(r, indent=2) if a.json else format_report(r))
    sys.exit(0 if r.get("ok") else 1)


if __name__ == "__main__":
    main()
