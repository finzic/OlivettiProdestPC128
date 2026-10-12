# PC128 testing approach and harness quirks

Facts verified with MAME 0.264 (`pro128`) and the scripted harness (`pc128.py`, `pc128-basic-ext/investigate`).

## Preferred way of testing

- **Pre-fill a reusable floppy image** with `tools/fdtool.py` (routines, demos, test programs). Do not
  format a disk or type code inside MAME.
- **Tests only type `RUN "NAME"`.** The test programs are `.bas` files on the disk. Each one `LOADM`s the
  routine, calls it, and `POKE`s the results to RAM so the harness can read them back with `--peek`.
- **Adding a test:** drop a `.bas` file into the example's `tests/` folder and run `make`. The file name,
  upper-cased, becomes the name on the disk.
- Worked example: [pc128-basic-ext/examples/keyjoy](../pc128-basic-ext/examples/keyjoy/README.md)
  (`make`, `make test`, `make test2`). Building the disk takes about a second and needs no emulator;
  only the tests run MAME.
- Floppy tooling and image formats: see the floppy section of the top-level [README](../README.md).

## BASIC typing and syntax quirks under the harness

- A typed line that **ends in `)`** makes the next typed line lose its first character. Slowing the typing
  (`line_gap_frames`) does not help. Avoid it: end the line with another statement or a trailing `:REM`.
  This once stored a demo's line 110 as line 10.
- The screen is 40 columns wide; keep lines short.
- **Hex literals above `&H7FFF` are floating point**, so `K AND &H8000` gives *Overflow*. Use `-32768`.
- **`TIMER` returns 0** under the harness. Time loops by emulated frames until the done flag is set
  (50 frames = 1 second).
- **Screenshots look blank while keys are held** if a demo draws and erases a sprite far apart in the loop.
  Erase and redraw back to back.
- The name of MAME's A key is ``A ` `` (not `A`), so `--hold "A \`"` is needed in `investigate.py`.

## Speed of decoding results in BASIC

Cost for decoding four values, per loop iteration, measured over 3000 iterations:

| Method | Cost |
|---|---|
| `AND` and `/256` on a packed 16-bit value | about 29 ms |
| lookup table `T1(K)` (byte values only) | about 18 ms |
| `PEEK` of separate bytes | about 6 ms |

So machine-code routines should store decoded values in separate RAM bytes at fixed offsets from their
start address and let BASIC `PEEK` them. Two players with eight directions and fire do not fit in one
byte (2 x 18 states = 324 > 256).

## Relocatable machine code and `LOADM`

`LOADM "file",OFFSET` loads at the file's start address plus `OFFSET`, with 16-bit wraparound:

$$\text{OFFSET} = (\text{target} - \text{start}) \bmod 65536$$

For a block assembled at `$9F00` and loaded at `$5000`: `$5000 - $9F00 = -$4F00`, and
`$10000 - $4F00 = $B100`, so `LOADM "KEYJOY",&HB100`. Also give `CLEAR ,&H4FFF` so BASIC leaves
`$5000` upward free, and `DEFUSR0=` the new base.

The code must use PC-relative addressing (`leay table,pcr`, `stb var,pcr`, relative branches). The only
absolute address should be hardware such as the PIA at `$A7C1`. Check by assembling at two origins and
comparing the output with `cmp`. Put results at fixed offsets from the start address (entry at `+0`).

## Keyboard matrix (PC128 `pro128`, QWERTY)

Scan code written to the system PIA port B (`$A7C1`) is `(column << 4) | (line << 1)`; bit 7 then reads 0
while that key is down. From MAME's `pro128_keyboard`:

| Key | Code |
|---|---|
| W | `$4A` |
| A | `$56` |
| S | `$46` |
| D | `$36` |
| Q | `$5A` |
| Enter | `$68` |
| Space | `$40` |
| arrows: up, right, down, left | `$62`, `$32`, `$42`, `$52` |

`CLRA` clears the carry flag on the 6809; use `LDA #0` when a carry has to survive.
