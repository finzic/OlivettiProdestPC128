# Investigating BASIC 128 extension points (PC128)

This applies the method from *L'interpréteur BASIC TO7-70/TO9* to the PC128's BASIC 128. It runs MAME's
debugger from a script, without opening the debugger window.

## Tool

```bash
cd pc128-basic-ext/investigate
python3 investigate.py vectors                          # RAM hook rows (RTS/JMP/JSR)
python3 investigate.py dasm D040 40 --rombank 1         # disassemble ROM (bank 0 = basico-2, 1 = basico-3)
python3 investigate.py peek 2770 20                     # hex dump of live memory
python3 investigate.py trace --line "10 FOO 5" --bp D04B --frames 40
python3 investigate.py run --load x.bin --exec --line "10 HELLO" --peek 5F00:2
python3 investigate.py run --fd disk.fd --line 'LOADM "SLOT",,R' --line '@WAIT 200' ...
```

- `@WAIT n` pauses typing for n frames. Use it after slow commands such as `DSKINI` (about 3000
  frames), `LOAD` and `SAVE`.
- Output goes to `out/`: `trace.log`, `trace_summary.txt`, `breakpoints.txt`, `dasm.asm`,
  `peek.txt` and `screen.png`.

## Findings (verified in MAME, BASIC 128 on `pro128`)

| Item | PC128 BASIC 128 | TO7-70/TO9 (book) |
|---|---|---|
| Direct page | `$21` | `$61` |
| CHRGET / CHRGOT | `JSR <$C0` (`$21C0`) / `$21C6` | `JSR <$B2` |
| Text pointer | `$21C7-$21C8` (operand of the CHRGET code in RAM) | `$61B9` |
| Statement dispatcher | `$D04B` (ROM bank 1) | `$2B35` |
| Hook before every statement | `$27C7` (RTS) | — |
| Statement dispatch table pointer | `$2773` (= `$B0E5`) | `$6204` |
| Unknown `$FF xx` statement hook | `$27CA` (RTS), A = second byte | `$6273` |
| Keyword descriptors (tokenizer) | `$2770` / `$2775`, 10 bytes apart | `$6287` |
| Hook row (all RTS after boot) | `$27C4-$2812`, 3 bytes each | `$62xx` |
| Free RAM after boot | `$2D20-$5FBF` (stack top ≈ `$5FE0`) | |

**Keyword descriptors:** each one is 5 bytes: word count, keyword table address, dispatch address. The
tokenizer at `$CF77` walks two chains, starting at `$2770` (statements) and `$2775` (`$FF`-prefixed
words), stepping 10 bytes each time and stopping at a count of 0. After boot:

- `$2770`: `$79` (121 words), `$D808`, `$B0E5`.
- `$277A`: count 0, the **empty extension slot**. Its dispatch word `$277D` is the vector the
  dispatcher uses for tokens `$F9-$FE` (`JMP [$277D]`).
- `$2775`: `$41` (65 words), `$D9ED`, `$B03D`.
- `$277F`: count 0.

**Adding statements without patching any ROM routine** ([experiments/slot_test.asm](experiments/slot_test.asm)):
1. Store the word count at `$277A`, the keyword table address at `$277B` and the handler address at `$277D`.
2. The new words are tokenized as `$F9`, `$FA`, … and `LIST` shows them back by name.
3. The handler is entered with A = token and the text pointer on the token. It ends with
   `JMP $21C0` (CHRGET), whose `RTS` returns to the interpreter. For anything that isn't ours, jump
   to the old `$277D` value (`$B8F4`, syntax error).

Tested: `LOADM "SLOT",,R` from a `.fd` disk, then `10 HELLO:BYE`, `LIST` and `RUN` all work.

## Floppy (.fd)

- MAME needs `-extension cd90_640` (or `"floppy": "disk.fd"` in `config.json`) plus
  `cd90-640.rom` in the ROM path.
- Disk geometry is 40 tracks × 16 sectors × 256 bytes. A 163840-byte image has one side; a
  327680-byte image has two sides, interleaved per track.
- [../tools/fdtool.py](../tools/fdtool.py) has `new`, `put`, `ls` and `get`. Its output matches
  disks formatted by BASIC 128 (`DSKINI`).

## Still to investigate

- The extension slot gives 6 tokens (`$F9-$FE`). More words need the second chain (`$277F`) or the
  `$27CA` hook.
- Functions (as opposed to statements): the dispatch word of the `$2775` descriptor (`$B03D`) and its
  empty successor at `$277F`/`$2782`.
- ROM routines for evaluating expressions and converting integers, needed for commands that take
  arguments. Trace `POKE` (token `$AA`) to find them.
