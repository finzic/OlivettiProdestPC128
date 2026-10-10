# PC128 BASIC extension

Adds new commands to the Olivetti Prodest PC128 (Thomson MO6) BASIC 128.
It uses the method from *L'interpréteur BASIC TO7-70/TO9* (`src/02-interpreteur-basic-to9.pdf`,
English text in `output/02-interpreteur-basic-to9/English/`, part 3: "new instructions/functions").

## How it works (TO7-70/TO9 → PC128)

| Step | TO7-70/TO9 (book) | PC128 |
|---|---|---|
| Keyword table pointer used by the tokenizer | RAM `$6287` | `KWPTR` – **to find** |
| New words tokenized as | `$FF,$A7+` | `$FF,NEWTOK+` (computed at install) |
| Hook reached for unknown `$FF` statement | RAM `$6273` (3 bytes) | `HOOK` – **to find** |
| Get next char (CHRGET) | `JSR <$B2` (`$61B2`) | `B_CHRGET` – probably `$21xx` |
| Text pointer | `$61B9` | `B_TXTPTR` |
| Syntax error | `$07F3` | `B_SNERR` |
| Evaluate expression | `$081A` | `B_GETEXPR` |
| Monitor calls | `JSR $E8xx` | `SWI` + `FCB code` (verified, MO6 manual p.194) |

Install (`EXEC`): copy the ROM keyword table to RAM, add `HELLO`, `BORDER`, `DOKE` and `FILL`,
redirect `KWPTR`, then patch `HOOK` with `JMP DISPATCH`. Tokens that are not ours go
to the original hook.

Every address tagged `[SCAN]` in [src/equ_pc128.asm](src/equ_pc128.asm) is a placeholder. **Do not run
the extension until you have confirmed all of them.** Addresses tagged `[DOC]` come from the MO6 manuals.

## Workflow

1. **Get a ROM dump** of your PC128 BASIC 128 banks (for example, the ROM files your
   emulator uses: DCMOTO or MAME `pc128`).
2. **Scan it**:
   `python3 tools/rom_scan.py --rom bank0.rom@0xB000 --rom bank1.rom@0xB000`.
   The scan lists:
   - keyword tables and their token numbers
   - references to each table (`LDX #table` points to the init code that sets `KWPTR`)
   - dispatch-table candidates
   - every `JSR`/`JMP` from ROM into RAM (these are the hooks)
   - the most-called routines (CHRGET, SN error, and so on)
3. **Disassemble the call sites.** Use `f9dasm` or `dasm09`, or `--dump ADDR:LEN`. For each hook,
   check the entry state that `DISPATCH` expects: A holds the second token byte, and `TXTPTR`
   points at it. Also check how many bytes are on the stack (`HOOK_STACK`). Then fill in
   `equ_pc128.asm`.
4. **Build**: `make` creates `build/basext.bin` (LOADM/DECB format), `build/basext.lst`, and
   `build/basext.bas`. The `.bas` file is a BASIC loader that POKEs the code from checksummed
   DATA lines and then EXECs it.
5. **Test in the emulator:** `HELLO`, `BORDER 4`, `DOKE &H9F00,&H1234`, `FILL &H9F00,16,0`.

`lwasm` is built locally in `.tools/`. You can also install lwtools system-wide and run
`make LWASM=lwasm`.

## Adding a command

Add a handler that ends with `jmp CMD_DONE`. Then add its address to `CMDTAB`
and its name (`fcs`) to `NEWWORDS`, at the same position in both lists. On entry, A holds the
first character after the keyword. Use `GETWORD`, `GETBYTE` and `COMMA` to parse
arguments.
