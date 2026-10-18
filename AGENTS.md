# Working with the PC128 emulator

This project targets the Olivetti Prodest PC128 (Thomson MO6, 6809 CPU).
You can run code on an emulated machine with the `pc128` MCP tools, or from a terminal with `pc128.py`.

## Tools
- `run_basic(code, dump?, done_addr?, run_frames?)`: PC128 BASIC 128 (boot menu choice set by `menu_key` in config.json), numbered lines.
- `run_asm(code, dump?, done_addr?, run_frames?)`: 6809 assembly in lwasm syntax.

Both boot a fresh machine every call (a few seconds) and return registers, memory dumps and a screenshot.

Interactive debugging keeps one machine alive across calls (see `docs/debugger.md`):
- `debug_start(code?, kind="asm"|"basic", program?, stop_on_entry=True, breakpoints?, window=False,
  floppy?, floppy2?, floppy_controller?, cassette?, cartridge?)`
  boots, loads the program (asm via `EXEC` from BANK 6, BASIC typed and `RUN`) and stops at entry.
  Mount media the program needs (e.g. `floppy="media/KEYJOY.FD"` for `LOADM "KEYJOY"`); unset media fall back to config.json.
  Example breakpoints: `["PUTC", "9010 if a==41", "line 40"]`.
- `debug_command(command, wait_seconds=10)` runs debugger commands:
  - inspect: `r`, `m 9F00@6 16`, `d`, `where`, `bt`, `banks`, `line`
  - patch: `a 9F80@6 LDA #$41 | SWI PUTC | RTS`, `hex`, `str`
  - breakpoints: `bp`, `bl`, `wp`
  - run: `s`, `n`, `out`, `g`, `until`, `nl`
  - other: `snap`, `help`
  Run commands wait for the next stop and report registers plus the current instruction with its ROM symbol.
- `debug_stop()` closes the machine.

## Conventions
- The screen is graphical: you cannot read printed text back. Put results in RAM and read them with `dump`
  (for example `["9F00:16"]`, hex address, decimal length). Look at the screenshot for visual output.
- BASIC 128 banks `$6000-$9FFF`: `BANK n` (n=1..6) selects RAM page n+1; the power-on bank is 6.
  Dumps and `done_addr` in that range read bank 6 unless you add `@n` (e.g. `"9F00:16@3"`, `"9F01@3"`)
  or `@cpu` for whatever the CPU currently sees.
- Finish every test program by writing a non-zero byte to a done address (suggested `$9F01`) and pass
  `done_addr="9F01"`, otherwise the run lasts the full `run_frames`.
- Assembly: `ORG $9000`, `END label` for the entry point, end with `BRA *`. User RAM is roughly `$2000-$9FFF`;
  I/O registers start at `$A7C0`, so don't use `$A000+` for code or data.
- BASIC: uppercase keywords, `&H` for hex, no blank lines. `NEW` and `RUN` are added for you.
- If a run fails at stage `assemble`, fix the source using the error text; at stage `emulator` or `launch`,
  report the message to the user rather than retrying blindly.
