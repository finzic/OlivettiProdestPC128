# pc128-c: C for the Olivetti Prodest PC128

This folder holds a C toolchain for the Olivetti Prodest PC128 (Thomson MO6, 6809), built on
[CMOC](http://sarrazip.com/dev/cmoc.html) and LWTOOLS. It includes the **standard Olivetti
library** (`libolivetti`), which wraps the ROM MONITOR (`SWI`) and EXTRAMONITOR (`SWI2`) services
documented in [docs/pc128-system-calls.md](../docs/pc128-system-calls.md).

```
pc128-c/
  include/olivetti.h     C API (ol_* monitor, xm_* extramonitor, debug helpers)
  include/olivetti.inc   the same equates + SYSCALL / XMCALL macros for assembly modules
  lib/                   library sources (C + asm) -> build/pc128-c/lib/libolivetti.a
  examples/              hello.c, graphics.c, xmdemo.c, mixed.c + asmlib.asm
```

## Install

Both tools are built locally under `tools/.local/` and need no root access:

```bash
tools/setup-lwasm.sh      # LWTOOLS 4.24 (lwasm, lwlink, lwar)
tools/setup-cmoc.sh       # CMOC 0.1.100 (also runs setup-lwasm.sh)
```

`setup-cmoc.sh` needs curl, tar, make, a C/C++ compiler, and bison + flex.
If bison or flex is missing and you can't run `sudo apt install bison flex`, the script fetches
the Debian packages with `apt-get download` and unpacks them locally.
`tools/check-environment.sh` reports whether CMOC is installed.

## Build and run

```bash
python3 tools/pc128cc.py pc128-c/examples/hello.c              # -> build/pc128-c/hello/hello.bin
python3 tools/pc128cc.py pc128-c/examples/hello.c --run        # build + run in MAME
python3 pc128.py c pc128-c/examples/hello.c --done-addr 9F01 --dump 9F10:16
python3 tools/pc128cc.py main.c sprite.asm -o game.bin         # several sources
python3 tools/pc128cc.py hello.c --fd media/C.FD               # copy HELLO.BIN to a floppy image
make -C pc128-c                                                # library + all examples
```

On the real machine (or in a MAME session with the floppy), run it with `LOADM "HELLO",,R`,
or `LOADM "HELLO"` followed by `EXEC &H6000`.

### Build directives

The main `.c` file can name extra sources and options in a comment within its first 40 lines:

```c
/* pc128cc: sources=asmlib.asm,util.c org=6000 limit=9F00 opt=-O0 */
```

### Output files

Each build also writes these files next to the `.bin`:
- `.map`: the link map.
- `.sym`: `name addr`, one per line. C names appear both with and without the leading `_`.
- `.lines`: maps each address to its C or asm source line. The debugger uses it.

## Memory model

| Range | Use |
|---|---|
| `$6000-$9EFF` | program: code, constants, data and BSS (`--org` / `--limit`). Linked into BASIC `BANK 6`, the power-on bank. |
| `$9F00-$9FFF` | debug area: `ol_done()` writes `$9F01`; `ol_debug_byte`/`ol_debug_word(i, v)` write `$9F10+i`. |
| stack | BASIC's stack (S is about `$5FF8` at `EXEC`). |
| `$A7C0-` | I/O: don't use it. |

- The program starts with `EXEC`. Returning from `main()` (or calling `exit()`) runs the
  destructors, restores S and goes back to the BASIC `OK` prompt.
- There is no heap: `malloc` isn't set up, so use static or stack buffers.
- The CMOC standard library (`printf`, `sprintf`, `strcpy`, `memset`, ...) is linked as needed.
- `printf` prints through the monitor `PUTC`. The library's start-up code turns `\n` into CR LF.

## Mixing C and assembly

Assembly modules are relocatable lwasm objects:

```asm
        INCLUDE "olivetti.inc"          ; SYSCALL / XMCALL macros, monitor equates
        SECTION code
        EXPORT  _sum_bytes              ; C name: sum_bytes
        IMPORT  _counter                ; a C global
_sum_bytes                              ; ol_word sum_bytes(const ol_byte *p, ol_word n)
        PSHS    Y                       ; p at 4,S  n at 6,S (2,S / 4,S before the PSHS)
        ...
        PULS    Y,PC
        ENDSECTION
```

CMOC calling convention:
- Arguments are pushed right to left, each at least 16 bits. In a routine without a frame, the
  first argument is at `2,S`; a `char` argument is the low byte, at `3,S`.
- Return 8-bit values in B and 16-bit values in D.
- Preserve U, Y, S and DP. A, B, X and CC are free.
- To call C from assembly, push the arguments (16 bits each), `JSR _name`, then `LEAS n,S`.

See [examples/mixed.c](examples/mixed.c) and [examples/asmlib.asm](examples/asmlib.asm). They
show C calling asm, asm calling the monitor and calling back into C, and asm using a C global.
Inline assembly (`asm { ... }`) also works; see the CMOC manual.

## The Olivetti library

All declarations are in [include/olivetti.h](include/olivetti.h).

| Area | Functions |
|---|---|
| raw calls | `ol_swi(service, &regs)` (any monitor service), `xm_call(fn, &regs)` (any extramonitor function) |
| text | `ol_putc`, `ol_puts`, `ol_cls`, `ol_locate`, `ol_esc`, `ol_color`, `ol_bgcolor`, `ol_border`, `ol_cursor`, `ol_screen_mode`, `ol_print_uint/int/hex` |
| keyboard | `ol_getc`, `ol_ktst`, `ol_waitkey` |
| monitor graphics | `ol_plot`, `ol_moveto`, `ol_lineto`, `ol_line`, `ol_point`, `ol_screen_char`, `ol_frm0/1`, `ol_palette`, `ol_set_palette`, `ol_get_palette`, `ol_load_palette` |
| input devices | `ol_joystick`, `ol_lightpen`, `ol_lightpen_button`, `ol_mouse`, `ol_mouse_buttons` |
| sound | `ol_beep`, `ol_note`, `ol_sound_setup`, `ol_play_note` |
| I/O | `ol_printer_open/putc/close/hardcopy`, `ol_rs232`, `ol_disk` (`ol_disk_read/write`) |
| extramonitor graphics | `xm_window`, `xm_screen`, `xm_style`, `xm_moveto`, `xm_pset`, `xm_lineto`, `xm_line`, `xm_box`, `xm_ellipse`, `xm_paint`, `xm_pattern`, `xm_mig` |
| extramonitor maths | `xm_real` (BASIC 4-byte float): `xm_from_int`, `xm_to_int`, `xm_from_str`, `xm_to_str`, `xm_op` (+ - * / ^), `xm_func` (SQR, SIN, LOG ...), `xm_rnd`, `xm_hex` |
| extramonitor misc | `xm_play` (BASIC PLAY strings), `xm_errmsg` |
| memory / debug | `OL_PEEK`, `OL_POKE`, `OL_PEEKW`, `OL_POKEW`, `ol_done`, `ol_debug_byte`, `ol_debug_word`, `ol_break` |

### Extramonitor rules

- The extramonitor is in the other monitor ROM page. `xm_begin()` maps it and installs an error
  trap; `xm_call` and every `xm_*` function call `xm_begin()` for you.
- `xm_end()` maps the normal page back and restores the RAM bank register (`$A7E5`).
  `exit()` and returning from `main()` call it automatically.
- Every `xm_*` function returns the extramonitor error code: 0 means OK, otherwise it is a BASIC
  error number (for example 11, Division By Zero). `xm_errmsg` turns the code into text.
  The error does not jump back to BASIC.
- Monitor (`ol_*`) services keep working while the extramonitor is mapped.

### Notes

- With a negative coordinate the ROM `DRAW` never returns. The `ol_` line functions clamp
  negative coordinates to 0, `ol_plot` skips the point, and `ol_point` returns -1.
- BASIC's screen is cyan (colour 6) by default, so cyan text is invisible on it.

### Verification status

Verified in the emulator:
- Text, `printf` and number printing.
- Monitor graphics and the palette.
- Extramonitor graphics: boxes, fills, ellipses, XOR lines and window clipping.
- Extramonitor maths and its error trap.
- `xm_play` runs, but the sound itself wasn't checked.
- Calls from C to asm and from asm back to C.

Written from the manuals but not tested yet:
- the keyboard functions, joystick, light pen and mouse;
- printer, RS-232 and disk;
- `ol_play_note`, `xm_paint`, `xm_mig` and `xm_hex`.

## Debugging

The debugger ([docs/debugger.md](../docs/debugger.md)) builds `.c` programs with the same
driver and loads their symbols and source lines:

```bash
python3 tools/debugger/pc128dbg.py pc128-c/examples/mixed.c --stop
pc128> bp mixed.c:25        # C source line (also asm files: bp asmlib.asm:27)
pc128> bp sum_bytes         # C/asm function (with or without the leading _)
pc128> g
pc128> sn                   # next C line, stepping over calls (JSR, SWI ...)
pc128> si                   # step into a C/asm function (ROM calls are stepped over)
pc128> src                  # source around PC
pc128> bt                   # call stack: C -> asm -> C -> BASIC EXEC
pc128> s / n                # single instruction
```

- **VS Code**: press `F5` on a `.c` file (debug type `pc128`).
  - Set breakpoints in `.c` and `.asm` files.
  - Step over and step into work by source line; the disassembly view steps by instruction.
- **MCP**:
  - `run_c(code, dump, done_addr)` compiles and runs a program.
  - `debug_start(code=..., kind="c")` opens a debug session; drive it with `debug_command("sn")`
    and the other debugger commands.
- **In the program**:
  - Call `ol_break()` and put a breakpoint on it (`bp ol_break`).
  - Store values with `ol_debug_byte`/`ol_debug_word` and read them with `--dump 9F10:16`.
  - Finish with `ol_done()` and pass `--done-addr 9F01`.

Local variables are not shown by name: CMOC writes no debug information. In the listing
(`build/pc128-c/<prog>/<prog>.lst`), each variable's comment gives its offset from U (the frame
pointer).
