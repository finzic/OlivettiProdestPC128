#!/usr/bin/env python3
"""Investigate PC128 BASIC 128 internals with MAME's scripted debugger (no debugger window).

Boots BASIC 128 (boot menu key "1"), optionally types a program, then runs one recipe:

  vectors                         dump the RAM vector rows ($2180-$22FF, $2770-$2830) as RTS/JMP/JSR
  dasm ADDR LEN [--rombank 0|1]   disassemble live memory (ROM bank 0=basico-2, 1=basico-3)
  peek ADDR LEN                   hex dump of live memory
  trace [--bp ADDR ...]           trace the CPU while the typed program RUNs; summarise RAM code
                                  executed and ROM routines called; log registers at breakpoints
  run                             RUN the typed program, then screenshot (and --peek)

  common options: --prog FILE.bas | --line "10 FOO 5" (repeatable; "@WAIT n" pauses n frames), --frames N, --fd DISK.fd,
                  --load FILE.bin (DECB, written to RAM before typing; EXECed if --exec),
                  --peek ADDR:LEN (hex, read after the run)

Results go to investigate/out/. Reads mame/rompath/machine from ../../config.json.
"""
import argparse
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CONFIG = HERE.parents[1] / "config.json"
# MAME input field names (thomson.cpp, pro128 keyboard)
KEY_NAMES = {"UP": "\u2191", "DOWN": "\u2193", "LEFT": "\u2190", "RIGHT": "\u2192", "SPACE": "Space"}

LUA = r"""
local m = manager.machine
local dbg = m.debugger
local mem = m.devices[":maincpu"].spaces["program"]
local P = PARAMS
local f, i, t0, exitat, loaded, gap, held = 0, 1, nil, nil, false, 0, false

local function out(name) return P.out .. "/" .. name end

local function with_rombank(fn)
  if not P.rombank then return fn() end
  local lo, hi = m.memory.banks[P.rom_banks[1]], m.memory.banks[P.rom_banks[2]]
  local a, b = lo.entry, hi.entry
  lo.entry, hi.entry = 6 + P.rombank, 6 + P.rombank
  local ok, err = pcall(fn)
  lo.entry, hi.entry = a, b
  if not ok then error(err) end
end

local function do_static()
  if P.recipe == "dasm" then
    with_rombank(function()
      dbg:command(string.format("dasm %s,%x,%x", out("dasm.asm"), P.addr, P.len))
    end)
  elseif P.recipe == "peek" then
    local fh = io.open(out("peek.txt"), "w")
    for a = P.addr, P.addr + P.len - 1, 16 do
      local row = {}
      for k = a, math.min(a + 15, P.addr + P.len - 1) do row[#row + 1] = string.format("%02X", mem:read_u8(k)) end
      fh:write(string.format("%04X: %s\n", a, table.concat(row, " ")))
    end
    fh:close()
  elseif P.recipe == "vectors" then
    local fh = io.open(out("vectors.txt"), "w")
    for _, r in ipairs(P.ranges) do
      for a = r[1], r[2] do
        local op = mem:read_u8(a)
        local w = mem:read_u8(a + 1) * 256 + mem:read_u8(a + 2)
        if op == 0x39 then fh:write(string.format("%04X: RTS\n", a))
        elseif op == 0x7E then fh:write(string.format("%04X: JMP $%04X\n", a, w))
        elseif op == 0xBD then fh:write(string.format("%04X: JSR $%04X\n", a, w)) end
      end
    end
    fh:close()
  end
end

SUB = emu.add_machine_frame_notifier(function()
  f = f + 1
  if exitat then
    if f >= exitat then m:exit() end
    return
  end
  if f == P.boot_frames then m.natkeyboard:post(P.menu_key) end
  if f < P.boot_frames + P.menu_frames then return end
  if not loaded then
    loaded = true
    for _, seg in ipairs(P.segments) do
      for k = 1, #seg.hex, 2 do mem:write_u8(seg.addr + (k - 1) // 2, tonumber(seg.hex:sub(k, k + 1), 16)) end
    end
  end
  if not t0 then
    if m.natkeyboard.is_posting then gap = P.line_gap; return end
    if gap > 0 then gap = gap - 1; return end
    if P.lines[i] then
      local w = P.lines[i]:match("^@WAIT%s+(%d+)$")
      if w then gap = tonumber(w) else m.natkeyboard:post(P.lines[i] .. "\r") end
      i = i + 1
      return
    end
  end
  if not t0 then
    t0 = f
    if P.recipe == "trace" or P.recipe == "run" then
      for _, a in ipairs(P.bps) do
        dbg:command(string.format(
          "bpset %x,1,{logerror \"BP %04X A=%%02X B=%%02X X=%%04X Y=%%04X U=%%04X S=%%04X DP=%%02X CC=%%02X ret=%%04X\\n\",a,b,x,y,u,s,dp,cc,w@s; g}", a, a))
      end
      if P.recipe == "trace" then dbg:command(string.format("trace %s,maincpu,noloop", out("trace.log"))) end
      m.natkeyboard:post("RUN\r")
    else
      do_static()
      exitat = f + 2
    end
    return
  end
  if not held and f >= t0 + P.hold_after and #P.hold > 0 then
    held = true
    for _, port in pairs(m.ioport.ports) do
      for name, field in pairs(port.fields) do
        for _, want in ipairs(P.hold) do
          if name == want then field:set_value(1) end
        end
      end
    end
  end
  if f >= t0 + P.frames then
    if P.recipe == "trace" then dbg:command("trace off,maincpu") end
    if P.peek then
      P.recipe, P.addr, P.len = "peek", P.peek[1], P.peek[2]
      do_static()
    end
    m.video:snapshot()
    exitat = f + 3
  end
end)
"""


def load_basic(args):
    lines = []
    if args.prog:
        lines += [l.rstrip() for l in Path(args.prog).read_text().splitlines() if l.strip()]
    lines += args.line or []
    return lines


def summarize_trace(path, ram=(0x2000, 0x9FFF)):
    ram_pcs, calls = Counter(), Counter()
    rx = re.compile(r"^([0-9A-F]{4}): (\S+)\s*(.*)$")
    for line in path.open(errors="replace"):
        m = rx.match(line.strip())
        if not m:
            continue
        pc = int(m.group(1), 16)
        if ram[0] <= pc <= ram[1]:
            ram_pcs[pc] += 1
        if m.group(2) in ("JSR", "JMP", "LBSR", "BSR") and m.group(3).startswith("$"):
            calls[m.group(3)] += 1
    lines = ["RAM code executed (address: count) - candidate hooks/vectors:"]
    lines += ["  %04X: %d" % (a, n) for a, n in sorted(ram_pcs.items())]
    lines += ["", "Most frequent JSR/JMP/BSR targets:"]
    lines += ["  %s: %d" % kv for kv in calls.most_common(40)]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("recipe", choices=["vectors", "dasm", "peek", "trace", "run"])
    ap.add_argument("addr", nargs="?", help="hex address (dasm/peek)")
    ap.add_argument("len", nargs="?", help="hex length (dasm/peek)")
    ap.add_argument("--rombank", type=int, choices=[0, 1])
    ap.add_argument("--prog")
    ap.add_argument("--line", action="append")
    ap.add_argument("--bp", action="append", default=[], help="hex breakpoint address (trace)")
    ap.add_argument("--frames", type=int, default=60, help="frames to trace after RUN")
    ap.add_argument("--fd", help=".fd floppy image (needs the controller ROM, see config floppy_controller)")
    ap.add_argument("--load", help="DECB .bin to write into RAM after boot")
    ap.add_argument("--exec", action="store_true", help="EXEC the --load entry point before the program")
    ap.add_argument("--peek", help="ADDR:LEN (hex) to dump after run/trace")
    ap.add_argument("--hold", action="append", default=[],
                    help="key held down from --hold-after frames after RUN: UP DOWN LEFT RIGHT SPACE or a MAME key name")
    ap.add_argument("--hold-after", type=int, default=10)
    a = ap.parse_args()

    cfg = json.loads(CONFIG.read_text())
    if cfg.get("rompath"):
        rompath = Path(os.path.expandvars(os.path.expanduser(cfg["rompath"])))
        if not rompath.is_absolute():
            rompath = CONFIG.parent / rompath
        cfg["rompath"] = str(rompath)
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*"):
        old.unlink()
    if a.recipe in ("dasm", "peek") and not (a.addr and a.len):
        sys.exit("dasm/peek need ADDR and LEN (hex)")

    segments, entry = [], None
    if a.load:
        sys.path.insert(0, str(HERE.parents[1]))
        from pc128 import parse_decb
        segs, entry = parse_decb(Path(a.load).read_bytes())
        segments = [{"addr": ad, "hex": d.hex()} for ad, d in segs]
    lines = load_basic(a)
    if a.exec and entry is not None:
        lines = ["EXEC &H%04X" % entry] + lines
    peek = [int(x, 16) for x in a.peek.split(":")] if a.peek else None

    params = {
        "recipe": a.recipe,
        "out": str(OUT),
        "boot_frames": int(cfg.get("boot_frames", 250)),
        "menu_key": "1",
        "menu_frames": int(cfg.get("menu_frames", 150)),
        "lines": lines,
        "line_gap": 25,
        "segments": segments,
        "peek": peek,
        "hold": [KEY_NAMES.get(k.upper(), k) for k in a.hold],
        "hold_after": a.hold_after,
        "frames": a.frames,
        "bps": [int(x, 16) for x in a.bp],
        "addr": int(a.addr, 16) if a.addr else 0,
        "len": int(a.len, 16) if a.len else 0,
        "rombank": a.rombank,
        "rom_banks": cfg.get("rom_banks", [":bank10", ":bank11"]),
        "ranges": [[0x2180, 0x22FF], [0x2770, 0x2830]],
    }
    lua = OUT / "job.lua"
    lua.write_text("PARAMS = " + to_lua(params) + "\n" + LUA)

    cmd = [cfg["mame"], cfg["machine"], "-debug", "-debugger", "none", "-log",
           "-sound", "none", "-nothrottle", "-skip_gameinfo", "-window",
           "-snapshot_directory", str(OUT), "-snapname", "screen",
           "-autoboot_script", str(lua), "-seconds_to_run", "900"]
    if cfg.get("rompath"):
        cmd += ["-rompath", cfg["rompath"]]
    if a.fd:
        cmd += ["-extension", cfg.get("floppy_controller", "cd90_640"), "-flop1", str(Path(a.fd).resolve())]
    p = subprocess.run(cmd, cwd=OUT, capture_output=True, text=True, timeout=1200)
    if p.returncode not in (0,):
        print((p.stdout + p.stderr)[-1500:])

    if a.recipe in ("trace", "run"):
        trace = OUT / "trace.log"
        if trace.exists():
            summary = summarize_trace(trace)
            (OUT / "trace_summary.txt").write_text(summary + "\n")
            print(summary[:3000])
        log = OUT / "error.log"
        if log.exists():
            bps = [l for l in log.read_text(errors="replace").splitlines() if l.startswith("BP ")]
            (OUT / "breakpoints.txt").write_text("\n".join(bps) + "\n")
            print("\n".join(bps[:40]))
        pk = OUT / "peek.txt"
        if pk.exists():
            print(pk.read_text())
    else:
        name = {"dasm": "dasm.asm", "peek": "peek.txt", "vectors": "vectors.txt"}[a.recipe]
        f = OUT / name
        print(f.read_text() if f.exists() else "no output (see MAME messages above)")
    print("\nfiles in", OUT.relative_to(HERE.parents[1]))


def to_lua(o):
    if o is None:
        return "nil"
    if isinstance(o, bool):
        return "true" if o else "false"
    if isinstance(o, int):
        return str(o)
    if isinstance(o, str):
        return '"' + o.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(o, list):
        return "{" + ",".join(to_lua(x) for x in o) + "}"
    return "{" + ",".join("[%s]=%s" % (to_lua(k), to_lua(v)) for k, v in o.items()) + "}"


if __name__ == "__main__":
    main()
