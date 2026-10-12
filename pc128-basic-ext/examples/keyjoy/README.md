# KEYJOY: keyboard as joystick (PC128 BASIC 128)

A PC128 version of the "games with one or two players on the keyboard" routine from
*L'interpréteur BASIC TO7-70/TO9* (part 4, pp.151-156). The book's routine and this one share an
idea, not code. Both read the keyboard matrix directly from machine code, so a game loop gets the
same values as `STICK`. That avoids the `INKEY$` problems: one key at a time, auto-repeat delay,
beeps.

## Usage

```basic
10 CLEAR ,&H9EFF
20 LOADM "KEYJOY"
30 DEFUSR0=&H9F00
40 K=USR0(0)            ' argument ignored
50 D=K AND 15           ' 0 none, 1 up, 2 up-right, 3 right, ... 8 up-left (as STICK)
60 IF K AND 128 THEN BEEP   ' SPACE = fire
```

A single function returns both values. Bits 0-3 hold the direction and bit 7 means Space is
held. One call reads everything, and the two fields don't overlap, so `AND 15` and `AND 128`
separate them. The decoded values are also left in RAM, so after the call `PEEK` gives them without
arithmetic, which is faster in BASIC.

The code is position independent, and its results sit at fixed offsets from the start address `B`
(the same scheme as KEYJOY2 below):

| Offset | Content |
|---|---|
| `B+0` | entry point (`BRA`), the `USR` address |
| `B+2` | signature `KJ` |
| `B+4` | direction, `STICK` code 0-8 (arrow keys) |
| `B+5` | fire, 0 or 1 (Space) |
| `B+6` | code (97 bytes in all, with the tables) |

```basic
30 B=&H9F00:DEFUSR0=B
40 K=USR0(0):D=PEEK(B+4):F=PEEK(B+5)
```

To load it elsewhere, pass LOADM the offset from `$9F00`; for `$5000` that is `&HB100`:
`CLEAR ,&H4FFF : LOADM "KEYJOY",&HB100 : B=&H5000 : DEFUSR0=B`. The same bytes result from assembling at
`$9F00` and at `$5000`, and `make test` repeats a subset of the key tests at `$5000`. The only absolute
address is the PIA port at `$A7C1`.

| Keys held | Result |
|---|---|
| none | 0 |
| ↑ / ↑→ / → / ↓→ / ↓ / ↓← / ← / ↑← | 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 |
| Space | +128 |
| 3 or more arrows, or ↑+↓ | 0 for the direction |

## How it works

- **Keyboard matrix** (from MAME's `mo6_sys_portb_in` and the `pro128` keyboard map): the routine
  writes `(column << 4) | (line << 1)` to the system PIA port B at `$A7C1`. Bit 7 of the same port
  then reads 0 while that key is down.
  - Space: line 0, column 4.
  - →, ↓, ←, ↑: line 1, columns 3, 4, 5, 6.
- **Scanning:** the four arrows are read into a 4-bit mask (up, right, down, left). A 16-byte table
  turns the mask into the `STICK` value. Combinations that can't happen, such as ↑+↓ or three keys,
  map to 0.
- **Interrupts:** IRQ and FIRQ are masked during the scan, because the monitor scans the same
  matrix on its 50 Hz interrupt. The previous port B value is restored afterwards.
- **USR convention** (PC128 manual pp.346-347): on return the integer is at `2,X` and A = 2
  (integer). X, S and DP are left unchanged.
- **Placement:** the code is 97 bytes at `$9F00`, reserved with `CLEAR ,&H9EFF`, in the RAM bank
  BASIC currently uses (bank 6 by default).

## KEYJOY2: two players on one keyboard

[keyjoy2.asm](keyjoy2.asm) scans ten keys in one call and stores the decoded result in four bytes, so
BASIC decodes with `PEEK` instead of `AND` and division. In MAME `PEEK` was about 5 times faster than
`AND` and `/256` on a packed 16-bit value, and about 3 times faster than a lookup table.

```basic
10 CLEAR ,&H9EFF
20 LOADM "KEYJOY2"
30 B=&H9F00:DEFUSR0=B
40 K=USR0(0)                 ' scan; argument ignored
50 D1=PEEK(B+4):F1=PEEK(B+5)  ' player 1 direction 0-8 (STICK codes), fire 0/1
60 D2=PEEK(B+6):F2=PEEK(B+7)  ' player 2
```

The code is position independent, and every address is an offset from the start address `B`:

| Offset | Content | Keys |
|---|---|---|
| `B+0` | entry point (`BRA`), the `USR` address | |
| `B+2` | signature `K2` | |
| `B+4` | player 1 direction | arrow keys |
| `B+5` | player 1 fire | Enter |
| `B+6` | player 2 direction | W up, D right, S down, A left |
| `B+7` | player 2 fire | Space |
| `B+8` | code (138 bytes in all, with the tables) | |

To load it elsewhere, pass LOADM the offset from `$9F00`; for `$5000` that is `&HB100`:

```basic
CLEAR ,&H4FFF : LOADM "KEYJOY2",&HB100 : B=&H5000 : DEFUSR0=B
```

The same bytes result from assembling at `$9F00` and at `$5000` (checked with `cmp`), and `make test2`
repeats a subset of the key tests at `$5000`. The only absolute address is the PIA port at `$A7C1`.

`USR0` also returns player 1 as KEYJOY does (direction, +128 with Enter). Two bytes cannot hold both
players with eight directions and fire (2 x 18 states = 324 > 256), which is why the result is four bytes.
Scan codes for the QWERTY PC128 map (W `$4A`, A `$56`, S `$46`, D `$36`, Enter `$68`, Space `$40`) come
from MAME's `pro128_keyboard`. [demo2.bas](demo2.bas) moves a `*` and a `+`.

## Build and test

```bash
make         # keyjoy.fd and keyjoy2.fd, built by BASIC 128 itself in MAME
make test    # LOADM from keyjoy.fd, hold each key combination, check USR0(0) and the PEEK bytes at $9F00 and $5000
make test2   # the same for keyjoy2.fd: 15 combinations at $9F00 and 4 at $5000, both players at once
```

The disk is produced entirely inside the emulator ([keyjoy.py](keyjoy.py)):

1. Start from a blank `.fd` image, then run `DSKINI 0`.
2. Type a DATA/POKE loader generated by `../../../tools/bin2bas.py --no-exec`, run it, then
   `SAVEM "KEYJOY",&H9F00,...`.
3. Type [demo.bas](demo.bas), then `SAVE "DEMO"`.

None of our tools writes the disk structure, so a disk-format mistake can't affect the result.
[`fdtool.py`](../../../tools/fdtool.py) is still useful for reading such disks (`ls`, `get`).

Test result (MAME `pro128`, BASIC 128, keys held with MAME's input system):

```
none 0 | UP 1 | UP+RIGHT 2 | RIGHT 3 | DOWN+RIGHT 4 | DOWN 5 | DOWN+LEFT 6
LEFT 7 | UP+LEFT 8 | SPACE 128 | UP+SPACE 129 | UP+DOWN+LEFT 0      all OK
```

## Notes from the investigation

- **ASCII `.BAS` files on disk use 255 data bytes per sector** (byte 256 is `$00`), and so do
  binary files. An earlier `fdtool` filled all 256 bytes. The demo's ASCII copy lost one character
  per sector and stopped with a syntax error. `fdtool` is fixed, but this is why the build now goes
  through BASIC.
- **`<` and `>` show as `(` and `)` in `LIST`.** That is the PC128 screen font, not data corruption.
- **Holding keys in tests:** don't press them until `RUN` has been typed. A held key interrupts the
  emulated typing, and only `R` arrives.
- **Demo:** the star stays off the last screen row, because printing in the bottom-right cell
  scrolls the screen.
- **Demo screenshots looked blank while keys were held.** The demo drew the star at the start of the
  loop and erased it at the end, so it was visible only for a small part of each iteration. Both demos
  now erase and redraw back to back, and the star stays visible while moving.
- **Typing into the emulator:** a typed line that ends in `)` makes the next line lose its first
  character, so the demos avoid it (a trailing `:REM` or a different last statement). The old
  `demo.bas` ended line 100 with `)`, so its line 110 was probably stored as line 10.
- **Hex constants above `&H7FFF` are floating point in BASIC 128**, so `K AND &H8000` gives Overflow.
  Use `-32768`.
