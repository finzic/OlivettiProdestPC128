# Olivetti Prodest PC128 System Calls and ROM Calling Reference

This document consolidates the currently recoverable low-level interface of the **Olivetti Prodest PC128**, which is hardware-compatible with the **Thomson MO6** and shares the same MC6809E execution model. It focuses on the externally callable ROM services, the monitor SWI gateway used by BASIC-backed services, and the ROM-visible subsystems used by BASIC 128.

Because this repository does not yet contain a ROM disassembly, this reference distinguishes between:

- **Confirmed** facts recovered from emulator source, public assembler code, and token tables.
- **Reconstructed** mappings that are strongly implied by those sources.
- **Unknown** details that still need an annotated PC128 ROM disassembly.

## 1. System architecture

### CPU

- **CPU:** Motorola **MC6809E**
- **Clock:** ~1 MHz
- **Machine family:** Thomson MO6 / Olivetti Prodest PC128

### Memory map

The most consistent externally documented map for the PC128/MO6 is:

| Range | Purpose | Status |
|---|---|---|
| `$0000-$1FFF` | video RAM, shape plane / video page window | confirmed |
| `$2000-$5FFF` | fixed user/system RAM | confirmed |
| `$6000-$9FFF` | banked RAM page selected through `$A7E5` | confirmed |
| `$A000-$A7BF` | extension ROM window (disk / network controller ROMs) | confirmed |
| `$A7C0-$A7FF` | memory-mapped I/O | confirmed |
| `$B000-$EFFF` | cartridge ROM or BASIC ROM bank | confirmed |
| `$F000-$FFFF` | monitor / BIOS ROM bank | confirmed |

### Main I/O regions

| Range | Device |
|---|---|
| `$A7C0-$A7C3` | system PIA 6821 |
| `$A7CC-$A7CF` | music/game PIA 6821 |
| `$A7DA-$A7DD` | palette + video mode registers |
| `$A7E4-$A7E7` | gate-array banking and status |
| `$A7F0-$A7FF` | expansion devices |

## 2. How ROM routines are called

### 2.1 Monitor SWI gateway

The PC128 monitor exposes its system services through a **`SWI` + service-byte** convention:

```asm
    ; JSR-style monitor call
    SWI
    FCB   service_code
```

Two service-code families are documented:

- **`$00-$42`**: **JSR-style** services. They return to the caller.
- **`$80-$C2`**: **JMP-style** services. They tail-call into the monitor service and do **not** preserve the same return path.

This is the main mechanism used by Thomson/MO6 monitor wrappers and by machine code that wants to access the same services that BASIC uses.

### 2.2 Direct ROM entry points

The controller ROM also exposes a small direct-entry jump table in the `$A000` area:

```asm
    JSR   $A004   ; example: disk sector read
```

These calls are controller-specific rather than generic monitor calls.

### 2.3 Calling BASIC-backed services from machine code

For code intended to cooperate with BASIC:

1. let BASIC initialise the machine state,
2. use the **monitor SWI gateway** for screen, keyboard, cassette, disk, joystick, palette, and serial services,
3. enter machine code from BASIC with `EXEC` after a `LOADM`, for example:

```basic
CLEAR,&H2FFF:LOADM"CASS:",R:EXEC
```

That is the documented path used by published PC128/MO6 software.

## 3. Monitor system-call set

The following service bytes are documented in MO6-compatible public assembler headers.

### 3.1 JSR-style monitor services (`$00-$42`)

| Code | Name | Meaning |
|---|---|---|
| `$00` | `MENU` | return to menu |
| `$02` | `PUTC` | display one character |
| `$04` | `FRM0` | write colour memory |
| `$06` | `FRM1` | write shape memory |
| `$08` | `BIIP` | beep |
| `$0A` | `GETC` | keyboard read |
| `$0C` | `KTST` | fast keyboard test |
| `$0E` | `DRAW` | draw a line segment |
| `$10` | `PLOT` | set or clear a pixel |
| `$12` | `CHPL` | write a character-cell pixel |
| `$14` | `GETP` | read pixel colour |
| `$16` | `LPIN` | read light-pen button |
| `$18` | `GETL` | read light-pen position |
| `$1A` | `GETS` | screen read |
| `$1C` | `JOYS` | read joysticks |
| `$1E` | `NOTE` | sound/music generation |
| `$20` | `K7CO` | cassette read/write |
| `$22` | `K7MO` | cassette motor on/off |
| `$24` | `PRCO` | parallel interface |
| `$26` | `DKCO` | floppy controller |
| `$28` | `DKBOOT` | boot from disk |
| `$2A` | `DKFMT` | format disk |
| `$2C` | `ALLOB` | allocate one block |
| `$2E` | `ALLOD` | allocate start block |
| `$30` | `ECRSE` | write one sector |
| `$32` | `FINTR` | end transfer |
| `$34` | `LECFA` | read FAT |
| `$36` | `MAJCL` | update cluster |
| `$38` | `RECFI` | search file |
| `$3A` | `RECUP` | reclaim occupied space |
| `$3C` | `SETP` | program palette |
| `$3E` | `MOUSEB` | read mouse buttons |
| `$40` | `MOUSE` | read mouse position |
| `$42` | `RSCO` | RS-232 service |

### 3.2 JMP-style monitor services (`$80-$C2`)

These use the same semantic names but with bit 7 set:

| Code range | Meaning |
|---|---|
| `$80+$00` .. `$80+$42` | `JMP_MENU` .. `JMP_RSCO` |

For example:

- `JMP_PUTC = $82`
- `JMP_GETC = $8A`
- `JMP_SETP = $BC`

### 3.3 Practical calling examples

#### Print one character

Public MO6 monitor macros load the character into **register `B`** before calling `PUTC`:

```asm
    LDB   #'A'
    SWI
    FCB   $02          ; PUTC
```

This register contract is **confirmed** by published monitor wrapper macros.

#### Program the palette

Public wrappers for `SETP` load:

- `A` with a selector,
- `X` and `Y` with additional arguments,
- then invoke service `$3C`.

The exact argument meaning is **not fully documented** in public sources, but the register use is confirmed by wrapper code.

## 4. Direct ROM entry points in the controller ROM

The ROM window at `$A000-$A7BF` contains directly callable controller routines:

| Address | Name | Meaning |
|---|---|---|
| `$A004` | `DKCONT` | read sector |
| `$A007` | `DKBOOT` | boot |
| `$A00A` | `DKFMT` | format |
| `$A00D` | `LECFA` | read FAT |
| `$A010` | `RECFI` | search file |
| `$A010` | `RECUP` | reclaim file space |
| `$A010` | `ECRSE` | sector write |
| `$A019` | `ALLOD` | catalog/file allocation |
| `$A01C` | `ALLOB` | block allocation |
| `$A01F` | `MAJCL` | cluster update |
| `$A022` | `FINTR` | end transfer |
| `$A025` | `QDDSTD` | QDD standard functions |
| `$A028` | `QDDSYS` | QDD system functions |

The triple alias at `$A010` is source-documented but still needs ROM-disassembly confirmation to distinguish the exact entry semantics.

## 5. Calling conventions

### 5.1 6809 register usage

The public PC128/MO6 calling surface is 6809-native:

- 8-bit arguments commonly use `A` or `B`
- 16-bit arguments use `D`, `X`, `Y`, or `U`
- monitor wrappers show `PUTC` using `B`
- monitor wrappers show `SETP` using `A`, `X`, and `Y`

### 5.2 SWI stack protocol

`SWI` uses the normal MC6809 software-interrupt mechanism:

- the CPU vectors through `$FFFA-$FFFB`,
- the monitor consumes the byte immediately following `SWI`,
- the service handler dispatches according to that selector.

### 5.3 Error signalling

Public headers name the services but do **not** publish a complete flag/register error contract for each call. In practice:

- disk and cassette services are stateful and interact with monitor workspace,
- higher-level BASIC code is expected to translate controller failures into BASIC I/O errors,
- exact carry/zero-flag conventions still require a PC128 ROM disassembly.

## 6. Graphics subsystem

### 6.1 Video pages

- Up to **4 video pages**
- one graphic line is always described in **40 GPL units**
- one GPL corresponds to two bytes in video memory, separated by `$2000`

### 6.2 Documented video mode values

The video mode register is written through `$A7DC`.

| Value | Mode | Resolution | Colours | Status |
|---|---|---|---|---|
| default / `$00` | standard graphics/text family | 320×200 | 16 | confirmed |
| `$21` | `BITMAP4` | 320×200 | 4 | confirmed |
| `$41` | alternate 4-colour mode | 320×200 | 4 | confirmed |
| `$59` | half-width alternate 4-colour mode | 160×200 | 4 | confirmed |
| `$2A` | 80-column / high-resolution mode | 640×200 | 2 | confirmed |
| `$7B` | `BITMAP16` | 160×200 | 16 | confirmed |
| `$24` | page 1 view | 320×200 | 2 | confirmed |
| `$25` | page 2 view | 320×200 | 2 | confirmed |
| `$26` | overlay mode | 320×200 | 2 over 2 pages | confirmed |
| `$3E` | half overlay | 160×200 | 2 | confirmed |
| `$3F` | overlay3 | 160×200 | 4 over 4 pages | confirmed |
| `$5B` | alternate 16-colour encoding | 160×200 | 16 | confirmed |

### 6.3 VRAM layout

Two important layouts are externally documented:

- **shape / form plane** at the base page
- **colour plane** at base + `$2000`

In sprite tools and image converters:

- row stride is **160 bytes**
- pixel address is `y * $A0 + (x >> 1)` in nibble-based packed modes

### 6.4 Graphics-related ROM services used by BASIC

| Service | BASIC-side use |
|---|---|
| `PLOT` | `PSET`, `POINT`, low-level graphics |
| `DRAW` | `LINE`, `DRAW`, parts of `BOX`, `CIRCLE`, `PAINT` |
| `GETS` | block/screen reads, sprite-style capture |
| `FRM0` / `FRM1` | direct form/colour memory access |
| `SETP` | `PALETTE`, colour management |
| `GETL` / `LPIN` | `PEN`, `INPEN` |
| `MOUSE` / `MOUSEB` | `MOUSE`, `INMOUSE`, `MTRIG` |

## 7. Sound subsystem

### 7.1 Hardware

- 1-bit buzzer through the system PIA
- 6-bit DAC through `$A7CD`
- DAC enable/control through `$A7CF`

### 7.2 DAC initialisation pattern

Published PC128 code uses:

```asm
    LDA   $A7CF
    ANDA  #$FB
    STA   $A7CF
    LDB   #$3F
    STB   $A7CD
    ORA   #$04
    STA   $A7CF
```

This is the clearest documented way to enable full-range DAC playback on the PC128.

### 7.3 Sound-related ROM services used by BASIC

| Service | BASIC-side use |
|---|---|
| `BIIP` | `BEEP` |
| `NOTE` | `PLAY` and note generation |

## 8. Cassette and disk I/O

### 8.1 Cassette monitor services

| Service | Meaning |
|---|---|
| `K7CO` | cassette read/write |
| `K7MO` | cassette motor on/off |

### 8.2 K7 block structure

The emulator-documented K7 byte stream is:

| Field | Meaning |
|---|---|
| `01 3C` | block header |
| type byte | `00` start-of-file, `01` data, `FF` end-of-file |
| size byte | payload size |
| payload | `size` bytes |
| CRC byte | block checksum |

Blocks are separated by `FF` filler bytes.

### 8.3 Disk monitor services

| Service | Meaning |
|---|---|
| `DKCO` | floppy controller access |
| `DKBOOT` | boot from disk |
| `DKFMT` | format disk |
| `ALLOB` / `ALLOD` | allocation |
| `LECFA` | FAT read |
| `MAJCL` | cluster update |
| `RECFI` | file search |
| `RECUP` | free-space recovery |
| `ECRSE` | sector write |
| `FINTR` | transfer end |

### 8.4 Floppy filesystem layout

Public Thomson tooling documents:

#### Sector 1

- bytes `0-7`: floppy name

#### Sector 2

- FAT
- `FF` = free block
- `FB` = reserved block
- `00-BF` = allocated block, points to next block
- `C1-C8` = last block in file, low nibble = number of used sectors

#### Sectors 3-16

- directory
- 32-byte entries
- includes filename, extension, type, format flag, first block, last-sector byte count, comment, date

## 9. Interrupt handling

### 9.1 Standard 6809 vectors

| Vector | Address |
|---|---|
| `SWI3` | `$FFF2-$FFF3` |
| `SWI2` | `$FFF4-$FFF5` |
| `FIRQ` | `$FFF6-$FFF7` |
| `IRQ` | `$FFF8-$FFF9` |
| `SWI` | `$FFFA-$FFFB` |
| `NMI` | `$FFFC-$FFFD` |
| `RESET` | `$FFFE-$FFFF` |

### 9.2 Monitor workspace pointers

Public MO6-compatible headers document these monitor RAM vectors:

| Address | Name | Meaning |
|---|---|---|
| `$2061` | `TIMERPT` | timer IRQ routine pointer |
| `$2063` | `IRQSEMAPHORE` | IRQ semaphore |
| `$2064` | `IRQPT` | IRQ routine pointer |
| `$2067` | `FIRQPT` | FIRQ routine pointer |

### 9.3 Observed behaviour

- MO-family IRQ activity is tied to frame/timer service in public emulator code.
- Public PC128 startup code hooks a custom ISR through `$2061`.
- Exact monitor-installed handler addresses in ROM remain unknown without disassembly.

## 10. BASIC ROM internal routines

No public PC128 ROM listing currently exposes a complete absolute-address table for internal BASIC helper routines. What can be recovered confidently is the **subsystem split** used by BASIC 128.

### 10.1 Console / parser / execution core

Used by keywords such as:

- `PRINT`, `INPUT`, `USING`, `TAB(`, `SPC(`, `LOCATE`, `CLS`, `CONSOLE`
- control-flow keywords like `FOR`, `NEXT`, `WHILE`, `DO`, `LOOP`, `IF`, `THEN`, `ELSE`, `ON`, `GOTO`, `GOSUB`, `RETURN`

These rely on the BASIC interpreter core plus monitor services like `PUTC` and `GETC`.

### 10.2 Graphics core

Used by:

- `PSET`, `LINE`, `BOX`, `CIRCLE`, `PAINT`, `DRAW`, `RESET`, `WINDOW`, `PATTERN`
- `POINT`, `SCREEN`, `GR$`, `PALETTE`, `ROT`, `SHOW`, `ZOOM`

These ultimately rely on monitor graphics services: `PLOT`, `DRAW`, `GETP`, `GETS`, `SETP`, `GETL`, `LPIN`, `MOUSE`, `MOUSEB`.

### 10.3 Sound / input core

Used by:

- `BEEP`, `PLAY`
- `STICK`, `STRIG`, `PTRIG`, `MTRIG`
- `INKEY$`, `KEY`, `MOUSE`, `INMOUSE`

These map onto `BIIP`, `NOTE`, `JOYS`, keyboard services, and mouse services.

### 10.4 Storage / device core

Used by:

- `MOTOR`, `EXEC`, `SAVE`, `LOAD`, `MERGE`, `OPEN`, `CLOSE`
- `DSKINI`, `DSKO$`, `DSKL`, `DSKI$`, `KILL`, `NAME`, `FIELD`, `LSET`, `RSET`, `PUT`, `GET`, `VERIFY`, `DEVICE`, `DIR`, `FILES`, `WRITE`, `UNLOAD`, `BACKUP`, `COPY`, `SEARCH`, `DENSITY`

These depend on the cassette, disk, and controller ROM services listed above.

### 10.5 String / numeric / conversion core

Used by:

- `SGN`, `INT`, `ABS`, `FRE`, `SQR`, `LOG`, `EXP`, `COS`, `SIN`, `TAN`, `ATN`
- `LEN`, `STR$`, `VAL`, `ASC`, `CHR$`, `LEFT$`, `RIGHT$`, `MID$`, `INSTR`, `STRING$`, `SPACE$`, `CRUNCH$`, `EVAL`
- `PEEK`, `POKE`, `VARPTR`, `USR`, `CINT`, `CSNG`, `CDBL`, `CVI`, `CVS`, `CVD`, `MKI$`, `MKS$`, `MKD$`, `HEX$`, `OCT$`

These are interpreter-internal routines; their absolute PC128 ROM entry addresses remain unknown.

## 11. BASIC 128 to ROM-service cross-reference

The table below lists the BASIC 128 keyword families currently recoverable from public token tables and maps them to the monitor service or interpreter family they depend on.

### 11.1 Statements

| BASIC keywords | ROM service or routine family |
|---|---|
| `PRINT`, `CONSOLE`, `LOCATE`, `CLS` | `PUTC`, `GETC`, console interpreter core |
| `PSET`, `LINE`, `BOX`, `CIRCLE`, `PAINT`, `DRAW`, `RESET`, `WINDOW`, `PATTERN` | `PLOT`, `DRAW`, `GETS`, graphics interpreter core |
| `COLOR`, `ATTRB`, `PALETTE` | `FRM0`, `FRM1`, `SETP`, graphics interpreter core |
| `PEN`, `INPEN` | `GETL`, `LPIN` |
| `MOUSE`, `INMOUSE` | `MOUSE`, `MOUSEB` |
| `BEEP`, `PLAY` | `BIIP`, `NOTE` |
| `MOTOR` | `K7MO` |
| `SAVE`, `LOAD`, `MERGE` | cassette/disk BASIC storage core, `K7CO`, `DKCO` |
| `OPEN`, `CLOSE`, `PUT`, `GET`, `VERIFY`, `WRITE` | BASIC file-I/O core over `DKCO` / `K7CO` |
| `DSKINI`, `DSKO$`, `KILL`, `NAME`, `FIELD`, `LSET`, `RSET`, `DEVICE`, `DIR`, `FILES`, `UNLOAD`, `BACKUP`, `COPY`, `SEARCH`, `DENSITY` | BASIC-DOS core over `DKCO`, `DKFMT`, `ALLOB`, `ALLOD`, `LECFA`, `MAJCL`, `RECFI`, `RECUP`, `ECRSE`, `FINTR` |
| `EXEC` | BASIC machine-code launcher, commonly used after `LOADM` |
| `FOR`, `NEXT`, `DATA`, `DIM`, `READ`, `LET`, `GO`, `RUN`, `IF`, `RESTORE`, `RETURN`, `REM`, `'`, `STOP`, `ELSE`, `TRON`, `TROFF`, `DEFSTR`, `DEFINT`, `DEFSNG`, `DEFDBL`, `ON`, `WAIT`, `ERROR`, `RESUME`, `AUTO`, `DELETE`, `CONT`, `LIST`, `CLEAR`, `INTERVAL`, `KEY`, `NEW`, `TO`, `SUB`, `FN`, `USING`, `OFF`, `THEN`, `NOT`, `STEP`, `DO`, `LOOP`, `EXIT`, `CHAINE`, `COMMON`, `FWD`, `TURTLE` | interpreter core; exact entry points still unknown |

### 11.2 Functions and operators

| BASIC keywords | ROM service or routine family |
|---|---|
| `INKEY$`, `INPUT`, `CSRLIN`, `POS` | keyboard/console interpreter core, `GETC`, `KTST` |
| `POINT`, `SCREEN`, `GR$` | `GETP`, `GETS`, graphics interpreter core |
| `STICK`, `STRIG`, `PTRIG` | `JOYS` |
| `MTRIG` | mouse/button input core |
| `PEEK` | memory read helper |
| `VARPTR`, `USR` | BASIC machine-code bridge / memory helper |
| `LEN`, `STR$`, `VAL`, `ASC`, `CHR$`, `LEFT$`, `RIGHT$`, `MID$`, `INSTR`, `SPACE$`, `STRING$`, `CRUNCH$`, `EVAL`, `FKEY$` | string interpreter core |
| `SGN`, `INT`, `ABS`, `FRE`, `SQR`, `LOG`, `EXP`, `COS`, `SIN`, `TAN`, `ATN`, `MIN(`, `MAX(`, `RND`, `FIX`, `CINT`, `CSNG`, `CDBL` | numeric / floating-point interpreter core |
| `HEX$`, `OCT$`, `CVI`, `CVS`, `CVD`, `MKI$`, `MKS$`, `MKD$` | conversion helper core |
| `EOF`, `DSKL`, `DSKI$`, `LOC`, `LOF`, `BANK`, `HEAD`, `ROT`, `SHOW`, `ZOOM`, `TRACE` | file/device or graphics helper core; exact entry points still unknown |
| `+`, `-`, `*`, `/`, `^`, `AND`, `OR`, `XOR`, `EQV`, `IMP`, `MOD`, `@`, `>`, `=`, `<` | expression evaluator core |

### 11.3 Token-set note

Public Thomson token tables note that **`DENSITY` is missing on MO6 BASIC 128**, even though it exists in generic BASIC 128 token listings. PC128-specific confirmation still requires ROM extraction from the actual PC128 image.

## 12. Known gaps

The following are still missing from public PC128-specific documentation:

1. the exact monitor handler addresses behind the SWI vector,
2. a complete register-by-register contract for every service,
3. a true absolute-address listing of internal BASIC helper routines,
4. the final PC128-specific keyword differences versus generic MO6 BASIC 128.

The next useful step for this repository is therefore a **documented disassembly of the PC128 ROM** so the symbolic service names above can be tied to exact ROM addresses.

## 13. Source basis used for this reconstruction

- `wide-dot/6809-game-builder`, `engine/system/mo6/map.const.asm`
- `wide-dot/6809-game-builder`, `engine/system/mo6/monitor/monitor.macro.asm`
- `mamedev/mame`, `src/mame/thomson/thomson.cpp`
- `mamedev/mame`, `src/mame/thomson/to_video.cpp`
- `mamedev/mame`, `src/lib/formats/thom_cas.cpp`
- `mamedev/mame`, `src/tools/imgtool/modules/thomson.cpp`
- `dinoflorenzi/PC128OP`
- `w4ller/olitracker_2v`
- `Zlika/theodore`
