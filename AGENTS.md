# Working with the PC128 emulator

This project targets the Olivetti Prodest PC128 (Thomson MO6, 6809 CPU).
You can run code on an emulated machine with the `pc128` MCP tools, or from a terminal with `pc128.py`.

## Tools
- `run_basic(code, dump?, done_addr?, run_frames?)`: Thomson BASIC 128, numbered lines.
- `run_asm(code, dump?, done_addr?, run_frames?)`: 6809 assembly in lwasm syntax.

Both boot a fresh machine every call (a few seconds) and return registers, memory dumps and a screenshot.

## Conventions
- The screen is graphical: you cannot read printed text back. Put results in RAM and read them with `dump`
  (for example `["9F00:16"]`, hex address, decimal length). Look at the screenshot for visual output.
- Finish every test program by writing a non-zero byte to a done address (suggested `$9F01`) and pass
  `done_addr="9F01"`, otherwise the run lasts the full `run_frames`.
- Assembly: `ORG $9000`, `END label` for the entry point, end with `BRA *`. User RAM is roughly `$2000-$9FFF`;
  I/O registers start at `$A7C0`, so don't use `$A000+` for code or data.
- BASIC: uppercase keywords, `&H` for hex, no blank lines. `NEW` and `RUN` are added for you.
- If a run fails at stage `assemble`, fix the source using the error text; at stage `emulator` or `launch`,
  report the message to the user rather than retrying blindly.
