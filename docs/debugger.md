# PC128 debugger

A source-level and machine-level debugger for 6809 assembly and BASIC 128 programs on the emulated
Olivetti Prodest PC128 (Thomson MO6). It drives the workspace's patched MAME through a small Lua
server, and has three front ends sharing one command language:

| Front end | Start it with |
|---|---|
| VS Code (debug type `pc128`) | `F5` on a `.asm` / `.bas` file, or a configuration in `.vscode/launch.json` |
| Terminal REPL | `python3 tools/debugger/pc128dbg.py [program] [--stop] [--media floppy351 DISK.FD]` or task `PC128: debugger REPL (current file)` |
| Coding assistant (MCP) | tools `debug_start`, `debug_command`, `debug_stop` |

## Requirements

- The patched MAME from `./tools/prepare-mame.sh`. Patch `mame-patch/0003-script-debugger-module.patch`
  adds the `-debugger script` module (MAME's debugger runs, driven only by Lua) and `membank`
  `read_u8`/`write_u8` Lua bindings (writes into a specific RAM page). If your build predates the patch,
  run `./tools/prepare-mame.sh` again.
- The ROMs in `roms/` (`tools/prepare-roms.py`), and lwasm (`tools/check-environment.sh` builds it).
- The VS Code front end: install the extension once with the task
  `PC128: build + install debugger extension` (or `python3 tools/vscode-pc128-debug/build.py --install`),
  then run `Developer: Reload Window`.

## Terminal REPL

```
python3 tools/debugger/pc128dbg.py [program] [options]
```

| Option | Meaning |
|---|---|
| `program` | `.asm` (assembled with lwasm, loaded into BANK 6, `EXEC`ed) or `.bas` (typed, then `RUN`) |
| `--stop` | stop at the program entry / first BASIC line |
| `--noexec` | load the program but do not run it |
| `--headless` | no MAME window |
| `--noboot` | do not go through the boot menu |
| `--sym FILE` | extra symbol file (`.sym`, lwasm `--symbol-dump`, `.json`) |
| `-x CMD` | run a command before the prompt (repeatable) |
| `--batch` | exit after the `-x` commands (scripts, CI) |
| media options | see [Media](#media-floppy-cassette-cartridge) |

At the prompt, `Ctrl-C` stops the running machine and `quit` (or `q`, `exit`) leaves; MAME closes
with the REPL. Example script:

```
python3 tools/debugger/pc128dbg.py prog.bas --headless --media floppy351 DISK.FD --batch \
    -x "bl 80" -x "wait 60" -x "m 9F00@6 16"
```

`wait SECS` waits only for a stop (breakpoint, watchpoint, step). Keep it short in scripts if the
program may never stop, and follow it with `stop` to inspect anyway.

## Coding assistant (MCP)

- `debug_start(code?, kind="asm"|"basic", program?, stop_on_entry=True, breakpoints?, window=False,
  boot=True, floppy?, floppy2?, floppy_controller?, cassette?, cartridge?)` boots one machine, loads
  the program and stops at entry. Example breakpoints: `["PUTC", "9010 if a==41", "line 40"]`.
- `debug_command(command, wait_seconds=10)` runs any command below and waits up to `wait_seconds`
  for run commands to stop.
- `debug_stop()` closes MAME.

Only one session exists at a time; `debug_start` replaces it.

## Media (floppy, cassette, cartridge)

The debugger mounts the same media as a normal run (`tools/run-mame.sh`, the task
`PC128: start MAME session`, `pc128.py`), so programs can `LOADM`, `LOAD`, `SAVE` and use `DIR`.
Anything not given falls back to `config.json` (`floppy`, `floppy2`, `floppy_controller`, `cassette`,
`cartridge`). Images are used in place and BASIC can write to them, so debug on a copy if the disk
matters.

| Media | REPL | VS Code `launch.json` | MCP `debug_start` |
|---|---|---|---|
| choice like run-mame.sh | `--media floppy351 A.FD [B.FD]`, `--media floppy A.FD`, `--media cassette T.K7`, `--media cartridge C.ROM`, `--media none` | `"media": "floppy351"`, `"image"`, `"image2"` | — |
| CD90-351 3.5" drive 0 / 1 | `--floppy A.FD` / `--floppy2 B.FD` | `"floppy"` / `"floppy2"` | `floppy` / `floppy2` |
| controller | `--controller cd90_351\|cd90_640` | `"floppyController"` | `floppy_controller` |
| cassette, cartridge | `--cassette`, `--cart` | `"cassette"`, `"cartridge"` | `cassette`, `cartridge` |
| extra MAME arguments | `--mame-arg ARG` (repeatable) | `"mameArgs": [...]` | — |

Example: `python3 tools/debugger/pc128dbg.py examples/TURTJOY-edit.BAS --media floppy351 media/KEYJOY.FD`.
In VS Code, the configurations `debug current file with media (choose)` and
`bare machine with media (choose)` ask for the media kind and image, like the MAME session task.
The task `PC128: debugger REPL (current file, with media)` does the same in a terminal.

The second drive needs `cd90_351`. With a cartridge the boot menu is skipped. The windowed machine
uses the key mapping in `tools/mame-cfg` (F11 = MAME menu, F12 = exit), copied to `build/dbg-cfg`.
With a floppy controller, `banks` also lists its ROM bank (`extension:cd90_351:rom_bank`), and
$A000-$A7BF is shown as the controller ROM.

## Architecture

```
VS Code ──DAP/stdio──> tools/debugger/dap.py ─┐
terminal ─────────────> tools/debugger/pc128dbg.py ─┼─> commands.Session ──TCP──> pc128_dbg.lua (inside MAME)
MCP (mcp_server.py) ──> debug_* tools ─────────┘        │
                                                   m6809.py   disassembler (SWI services decoded)
                                                   symbols.py ROM correlation + symbol tables
                                                   asm.py     live / file assembly with lwasm
```

`pc128_dbg.lua` runs inside MAME (`-debugger script -autoboot_script`) and serves a line protocol on
`127.0.0.1:$PC128_DBG_PORT`: registers, memory per bank, breakpoints, watchpoints, run control,
keyboard typing, snapshots. `client.py` speaks the protocol; `commands.py` holds the `Session` and
the command interpreter all front ends use.

## Commands

Type them in the VS Code debug console, the REPL or `debug_command`. `help` prints this list.

| Group | Command | Meaning |
|---|---|---|
| State | `r` / `regs [REG=VAL ...]` | registers, CC flags, location; set with `r X=9000 CC=50` |
| | `banks` | MAME bank entries and what is mapped where |
| | `where [ADDR]` | location: RAM page / ROM page + ROM offset, nearest symbol |
| | `line` | current BASIC line (or the line about to run) |
| | `bt` | heuristic call stack (return addresses on S) |
| Memory | `m` / `dump ADDR[@view] [LEN]` | hex dump |
| | `d` / `dis [ADDR[@view]] [N]` | disassemble with symbols |
| Patch | `a` / `asm ADDR[@view] CODE` | assemble and store: `a 9000 LDA #1 \| SWI PUTC \| RTS` |
| | `hex ADDR[@view] BYTES` | store bytes: `hex 9000 86 41 3F 02 39` |
| | `str ADDR[@view] "TEXT"` | store a string (`\n` = $0D, `\0`, `\xNN`) |
| | `fill ADDR[@view] LEN BYTE` | fill memory |
| Breaks | `bp [ADDR [if COND]]` | set / list breakpoints |
| | `bl LINE [if COND]` | break when BASIC line LINE is about to run |
| | `bc N\|all`, `be N`, `bd N` | clear / enable / disable |
| | `wp ADDR [LEN] [r\|w\|rw] [if COND]`, `wc N\|all` | watchpoints |
| Run | `g` / `c` / `go [ADDR]` | continue |
| | `s` / `step [N]` | step into |
| | `n` / `over` | step over JSR/BSR/LBSR and `SWI` + service byte |
| | `out` / `finish` | run until the current subroutine returns |
| | `until ADDR` | run to ADDR |
| | `nl` / `nextline` | run to the next BASIC line |
| | `stop` / `pause`, `wait [SECS]` | break in; wait for a stop (default 30 s) |
| | `status` | `running`, or why and where the machine stopped |
| Other | `sym [REGEX]`, `sym load FILE` | search / load symbols |
| | `type TEXT` | type on the keyboard, line by line like the harness, and wait until done (`\r` = ENTER) |
| | `key TEXT` | post keys immediately, no pacing |
| | `snap`, `reset [hard]`, `throttle on\|off` | screenshot (window mode), reset, emulation speed |
| | `load FILE.asm\|FILE.bas [noexec]` | assemble+load+EXEC, or type+RUN |
| | `mame COMMAND` | raw MAME debugger command |

Aliases: `x` = `m`, `u` = `d`, `poke` = `hex`, `b` = `bp`, `h` / `?` = `help`.

**Addresses**: `9000`, `$9000`, `&H9000`, `0x9000`, `#36864` (decimal), symbols (`PUTC`, `KW_PRINT+3`),
registers (`PC`, `X`, `Y`, `U`, `S`; `.` = PC) and sums (`X+10`). `D` is not a register here, it is a hex digit.

**Views** (`@view`, for reading/writing a bank that isn't mapped right now):
`@1`..`@6` BASIC `BANK n` at $6000-$9FFF (RAM page n+1), `@p0`..`@p7` RAM page, `@mon0`/`@mon1`
monitor ROM, `@b128.0`/`@b128.1` BASIC 128 ROM, `@b1.0`/`@b1.1` BASIC 1 ROM, `@cram0..7` cartridge-space RAM,
`@cpu` (default: whatever the CPU sees). ROM writes are refused.

**Bank-qualified breakpoints**: prefix a page, `bp mon0:F6D9`, `bp b128.1:D04B`. The ROMs at
$B000-$EFFF and $F000-$FFFF are switched constantly; a qualified breakpoint only stops when that
page is mapped. Symbols carry their page, so `bp PUTC` is qualified automatically.

**Conditions** use MAME expression syntax; numbers are hex by default: `bp 9010 if a==41 && x>9000`.
Unknown symbols are rejected when the breakpoint is set.

## Banking and BASIC 128

- BASIC 128 swaps its two ROM pages (`b128.0`/`b128.1` at $B000-$EFFF) and maps RAM page 2 (`BANK 1`,
  the program text at $6001) at $6000-$9FFF while it works. Programs started with `EXEC` run with
  `BANK 6` (RAM page 7) mapped. The debugger therefore loads `.asm` programs into `BANK 6`
  (`default_bank` in `config.json`). Use `@6` to look at your program's data while stopped inside BASIC.
- Current BASIC line: the word at `$2131` (`$FFFF` = direct mode). The interpreter sets it at
  `b128.1:$D01E` (`STU <$31`, U = the number of the line about to run). BASIC line breakpoints are
  breakpoints there with condition `u==LINE`. In VS Code, `.bas` breakpoints, `F10`/`F11`
  (next line) and the "BASIC line N" stack frame all build on this.

## ROM correlation and symbols

Every address is located on the current banking: video RAM, RAM, RAM page n (BASIC BANK), ROM page
(`mon0`, `mon1`, `b1.0`, `b1.1`, `b128.0`, `b128.1`, plus the offset in `pc128.rom`), extension ROM,
I/O. Symbols are looked up in that page, so the same CPU address gives different names depending on
which ROM is mapped. Sources:

- `tools/debugger/symbols/pc128.sym`: monitor entry points, SWI services, system variables, BASIC 128
  internals, I/O registers.
- BASIC keywords decoded from the ROM: `KW_PRINT`, `KW_EXEC`, ... (statement handlers in `b128.1`).
- The loaded program's labels (lwasm symbol dump).
- Your own files: `--sym FILE` (REPL), `"symbols": [...]` (launch.json), `sym load FILE`.

`.sym` format, one `ADDRESS NAME` per line, `;` comments:

```
mon0:F6D9    PUTC        ; print character in B
b128.1:D01E  B_SETLINE
9F00         MYBUF
```

The page prefix is a page (`mon0`, `b128.1`, `p7`, `ext`, ...) or `rom:XXXX` (offset in `pc128.rom`).
Without a prefix the symbol applies everywhere. lwasm `--symbol-dump` files (`name EQU $XXXX`) load too.

## Live patching

```
a 9F80@6 LDA #$41 | SWI PUTC | loop: BRA loop     ; assemble 3 instructions into BANK 6
hex 9F90 48 45 4C 4C 4F                           ; bytes
str 9FA0 "HELLO\n\0"                              ; string, \n -> $0D
r PC=9F80                                         ; and run it
```

`|` separates lines, `label:` defines a label, `SWI NAME` / `SWI $xx` emits `SWI` + the service
byte, and debugger symbols are available to the code. The assembled bytes and their disassembly are
printed back.

## VS Code

Launch attributes: `program` (`.asm` or `.bas`, optional), `stopOnEntry`, `noExec`, `headless`, `boot`,
`symbols`, and the media attributes `media`/`image`/`image2`, `floppy`, `floppy2`, `floppyController`,
`cassette`, `cartridge`, `mameArgs` (see [Media](#media-floppy-cassette-cartridge)). Supported features:

- breakpoints in `.asm` and `.bas` files, conditional too (MAME syntax)
- function breakpoints: `PUTC`, `F6D9`, `mon0:F6D9`, `line 40`
- data breakpoints (watchpoints) from the Variables view, and instruction breakpoints in the
  Disassembly view
- Variables:
  - Registers: editable, CC expanded into flags
  - Location / ROM: page, ROM offset, symbol, source line
  - Banking
  - Stack: words on S with symbols
  - BASIC: current line, line about to run, text pointer
- Memory view (hex editor) and the Disassembly view, both annotated with symbols
- Debug console: every command above

Stepping in a `.asm` file is per instruction (`F10` steps over subroutine calls and SWI services).
Stopped at a BASIC line, `F10`/`F11` run to the next BASIC line. Use the Disassembly view for
instruction steps inside the interpreter.

## Tests

`python3 -m unittest tests.test_debugger` runs the offline tests:
- disassembler round trip through lwasm
- assembler, parsers and symbols
- DAP framing and launch media attributes
- media choices (`pc128.media_from_kind` / `mame_media_args`, errors such as a second drive on
  `cd90_640`), bank listing with the floppy controller bank

`PC128_LIVE_TESTS=1 python3 -m unittest tests.test_debugger` also boots MAME headless and checks
breakpoints, stepping, watchpoints, live patching, BASIC line breakpoints and, with a copy of
`media/KEYJOY.FD`, `LOADM "KEYJOY"` from the floppy.
