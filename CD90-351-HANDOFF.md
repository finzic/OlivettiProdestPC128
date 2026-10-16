# CD 90-351 Write Support Handoff

## Goal

Implement MAME write support for the Thomson CD 90-351 / THMFC1 floppy
controller, using DCMOTO and the controller ROM to reverse engineer behavior.

## Current State

- MAME source is in `~/src/mame`, separate from this workspace. The only
  modified files there are `src/devices/machine/thmfc1.cpp` and `.h`.
- The local `thomson` target builds with `cd ~/src/mame && make
  SUBTARGET=thomson -j6`.
- Sector-write mode and raw write-gate mode have been added. The MAME floppy
  write-protect status was corrected to match active-high `wpt_r()`.
- Four-index-pulse state was added to sector-header search; its effect still
  needs targeted validation.

## Verified

- `SAVE "WTEST"` ran on a temporary, valid 80-track image with the rebuilt
  `~/src/mame/thomson` and `cd90_351` extension. The image hash changed, and
  `tools/fdtool.py ls ... --tracks 80 --side 0` lists `WTEST.BAS` (43 bytes).
- The original `media/test351.fd` was not modified.
- MAME compiled after the latest controller changes; `git diff --check` and a
  direct C++20 syntax check passed.

## Still Unresolved

- `DSKINI 0` did not demonstrate a successful format. The image stayed
  unchanged, and the trace showed repeated read-sector commands/seeks but no
  `raw write start`. The routine appeared to reach its following BASIC line,
  so inspect the screen and status/error path; do not treat formatting as
  verified.
- Read-header mode (CMD0 mode 2) still calls `exit(0)`.
- Validate sector CRC, splice timing, data-ready timing, and repeat writes on
  both sides/tracks. The write path currently has inferred timing/layout.

## Reverse-Engineering Notes

- DCMOTO64 is UPX-packed and performs disk operations through host-side HLE
  traps rather than emulating THMFC1 register writes. Ghidra 12.1.4 was used
  for the unpacked executable and the actual 6809 CD 90-351 ROM.
- ROM listings are in `~/tools/re/rom351/bank0.lst` through `bank3.lst`;
  Ghidra project/scripts are in `~/tools/re`. Ghidra needs the JDK in
  `~/tools/jdk-21*` via `JAVA_HOME`.
- The CD 90-351 ROM uses CMD0 `$19` for MFM sector writes, after loading
  WCLK `$0A` and preloading WDATA `$A1`. It sends `$A1 $A1 $FB` and sector
  bytes; the controller generates the CRC. Format/FM paths use raw writes and
  send their own bytes and CRCs.
- DCMOTO's sector HLE traps observed in decompilation: `$11F2` write,
  `$11F5` read, `$11F3` initialize, `$11F4` format.

## Test Artifacts

- Successful sector-write image: `/tmp/cd90-mame-s_gr698s/sector-test.fd`
- DSKINI test image: `/tmp/cd90-mame-s_gr698s/format-test.fd`
- Temporary staged MAME ROMs and harness: `/tmp/cd90-mame-s_gr698s/`
- The staged PC128 ROM halves were sliced from `src-rom/pc128.rom`; both
  SHA-1 hashes match MAME's expected ROMs. The CD 90-351 ROMs came from this
  repository's `roms/pro128`.