# OlivettiProdestPC128
A Repo containing wiki and code for our beloved 8-bit machine

# PC128 harness: run BASIC and 6809 code from VS Code

Lets you (or a coding assistant) run code on an emulated **Olivetti Prodest PC128** (a Thomson MO6)
using **MAME**, which is scriptable. DCMOTO itself has no automation interface, so it is not used.

Each run boots a fresh machine, runs your code, then returns:
CPU registers, memory dumps you asked for, and a screenshot. A run takes a few seconds.

## Setup
Complete these steps before running the environment checker.

1. Install the system tools. On Debian or Ubuntu:

```bash
sudo apt update
sudo apt install curl tar make build-essential python3 python3-pip python3-venv
```

Other Linux distributions need equivalent packages. MAME is cloned and built locally in step 3;
you do not need to install the distro MAME package for the standard workflow.

2. Obtain the original DCMOTO ROM downloads and put both files in `src-rom/` at the repository
root. Create the directory if needed:

```bash
mkdir -p src-rom
```

The required paths and filenames are:

```text
src-rom/pc128.rom
src-rom/cd90-351.rom
```

This repository's primary floppy target is the CD90-351, PC128's original 3.5" drive. Optionally add
`src-rom/cd90-640.rom` (the 5.25" controller ROM) if you want the CD90-640 fallback described below.

These are the original source images, not the prepared MAME ROM files. They are copyrighted and are
not included in the repository. `tools/prepare-roms.py` validates them and creates the ignored
`roms/` files, including the 32 KB `pro128.iw01` and `basico.iw02` files required by current MAME,
the split PC128 ROM files, and the required CD90-351 ROM files. If `cd90-640.rom` is present, it also
stages the CD90-640 ROM. The environment checker creates
`.venv/` and installs MCP if needed, and builds local LWTOOLS if needed. It does not install system packages.

3. Build the patched MAME used by the standard workflow:

```bash
./tools/prepare-mame.sh
```

This clones the MAME commit pinned in `mame-patch/BASE_COMMIT`, applies the THMFC1 patch, and builds
the Thomson target under `tools/.local/mame/`. The default build uses at most 6 jobs; `--jobs N` sets
an explicit limit.

4. From the repository root, run:

```bash
./tools/check-environment.sh
```

The checker reports any remaining issue and prints commands that require manual action at the end.
See [tools/README.md](tools/README.md) for details and [docs/mame-pc128.md](docs/mame-pc128.md)
for ROM format and MAME configuration notes. Local LWTOOLS output, `.venv/`, and ROM files are
ignored by Git.

## Documentation

- [PC128 system calls and ROM calling reference](docs/pc128-system-calls.md)
- [Configuration of local environment](docs/mame-pc128.md)
- [Testing approach, harness quirks, relocation and key codes](docs/pc128-testing-notes.md)

## Use it

**VS Code tasks** (`Terminal > Run Task`, files in `.vscode/tasks.json`)
- `PC128: run BASIC (current file)`
- `PC128: run ASM (current file)`
- `PC128: run ASM (choose memory dump)`
- `PC128: start MAME session (floppy/cassette/cartridge)`: interactive MAME window with storage inserted
- `PC128: create new floppy/cassette/cartridge`: create a blank image

**Command line**
```
python3 pc128.py asm   examples/hello.asm --done-addr 9F01 --dump 9F00:16
python3 pc128.py basic examples/hello.bas  --done-addr 9F01 --dump 9F00:16
```

**Coding assistant (MCP)**: `.vscode/mcp.json` (VS Code / Copilot) and `.mcp.json` (Claude Code)
register the server `pc128` with two tools, `run_basic` and `run_asm`. `AGENTS.md` tells the
assistant how to use them.

## Interactive sessions with storage

Besides the scripted runs, you can use the emulator by hand and keep programs and data on a medium.

1. **Create an image** (task `PC128: create new floppy/cassette/cartridge`, or from a terminal):

   ```bash
    python3 tools/new-media.py floppy    media/disk.fd [--name LABEL] [--sides 1|2] [--tracks 80|40]
   python3 tools/new-media.py cassette  media/tape.wav
   python3 tools/new-media.py cartridge media/cart.rom
   ```

   | Kind | Result |
   |---|---|
    | floppy | Blank formatted `.fd`, made with `tools/fdtool.py new`: 320 KB per side with 80 tracks (3.5", CD90-351, default) or 160 KB per side with 40 tracks (5.25", CD90-640 fallback) |
   | cassette | 5 minutes of silent `.wav`; record onto it from MAME's tape controls |
   | cartridge | 16 KB `0xFF` image; read-only in MAME |

   Existing files are never overwritten. `new-media.py` only creates blank media (for a floppy it calls
   `fdtool.py new`); use `tools/fdtool.py` to add, list, read or copy files on a floppy image.

2. **Start a session** (task `PC128: start MAME session (floppy/cassette/cartridge)`, or):

   ```bash
    bash tools/run-mame.sh floppy351 media/disk80.fd [media/disk2.fd]   # primary: CD90-351, 80-track images
    bash tools/run-mame.sh floppy    media/disk40.fd                    # fallback: CD90-640, 40-track image
   bash tools/run-mame.sh cassette  media/tape.wav  # -cassette
   bash tools/run-mame.sh cartridge media/cart.rom  # -cart
   bash tools/run-mame.sh none                      # bare machine
   ```

   The image must already exist. The window runs with `-ui_active` and the key map in
   `tools/mame-cfg/default.cfg`: **F11** opens the MAME menu, **F12** exits (Esc no longer quits).
   On the emulated keyboard, **Delete** is backspace, Tab is *Stop*, Home is *Home/Clear*, and the
   PC Backspace key is the `+ *` key.

3. **Use it**: on a floppy, `SAVE`/`LOAD`/`DIR` in BASIC read and write the `.fd` file directly. The
    CD90-351 uses the patched MAME built in step 3 above. If it gives you trouble, use the optional
    CD90-640 ROM, a 40-track image, and `bash tools/run-mame.sh floppy media/disk40.fd` instead.
   To swap media while running, use Tab > File Manager (unmount, change or regenerate the file
   with `tools/fdtool.py`, mount again). Do not edit an image externally while it is mounted.

## Floppy images and `tools/fdtool.py`

`tools/fdtool.py` creates and edits `.fd` images in the Microsoft BASIC DOS format (track 20: sector 1
label, sector 2 FAT, sectors 3-16 directory). Pass `--tracks 80` to every command for 3.5" images.

```bash
python3 tools/fdtool.py new  media/d80.fd --sides 2 --tracks 80 --name LABEL
python3 tools/fdtool.py put  media/d80.fd examples/hello.bas --tracks 80 [--side 0|1]
python3 tools/fdtool.py ls   media/d80.fd --tracks 80
python3 tools/fdtool.py get  media/d80.fd HELLO.BAS out.bas --tracks 80
python3 tools/fdtool.py cp   media/disk.fd media/d80.fd --name LABEL   # 40-track to 80-track, all files
python3 tools/fdtool.py cp   media/d80.fd media/disk.fd --src-tracks 80 --dst-tracks 40
python3 tools/fdtool.py ls   media/d80.fd --tracks 80 --layout interleaved   # override the two-sided track order
```

`ls` lists every side of a two-sided image (`--side 0|1` limits it to one); `put` and `get` default to side 0.
`cp` creates the destination if it does not exist; use `--src-side`/`--dst-side` for two-sided images.
The label sector is written the way `DSKINI` and DCMOTO do: the 8-byte name, the constant bytes
`8D 5E 25` (meaning unknown), then zeros. A 327680-byte image is two sides of 40 tracks for the CD90-640
but one side of 80 tracks for the CD90-351, so the same file is read differently by each controller.

Two-sided track order (`--layout`): 40-track images are interleaved per track, as MAME 0.264 expects for the
CD90-640; 80-track images are sequential (all of side 0, then all of side 1), which is what DCMOTO loads
(tested with a 655360-byte image holding `SAVEM` dumps of RAM banks on both sides). Both are the defaults,
so `cp` from a 40-track to an 80-track image converts the order as well.

### PC128 floppy controllers in MAME

| | CD90-351 (primary) | CD90-640 (fallback) |
|---|---|---|
| Drive | Original 3.5" drive, 80 tracks, custom THMFC1 | 5.25" drive, 40 tracks, WD1770 |
| ROM | `MTD:`, 4 pages selected by `$A7D8` bits 0-1 | `DKD(`, 1 page |
| Read | side 0 of each drive verified (`0:`, `2:` for a second drive); side 1 failed on stock MAME 0.264 and has not been retested on the patched build | both sides as `0:` and `1:` |
| Write / `DSKINI` | works with the patched MAME (`tools/prepare-mame.sh`); read-only in stock MAME | works |

- Harness runs default to `cd90_351` and allow 600 menu frames for its slower boot. Set `floppy_controller` to
  `cd90_640` in `config.json` to use the fallback; it requires the optional `src-rom/cd90-640.rom`.
- **Patched MAME.** Stock MAME's `THMFC1` exits on the write and format commands and reports the write-protect
  bit inverted. `tools/prepare-mame.sh` clones MAME at the commit in `mame-patch/BASE_COMMIT`, applies
  `mame-patch/0001-*.patch` (write sector, raw write/format, read header, idle byte-ready, write-protect fix;
  the patched files are also in `mame-patch/src/`) and builds the `thomson` subtarget into `tools/.local/mame/`.
  `pc128.py` and `run-mame.sh` use that binary automatically when `mame` in `config.json` is left at `mame`.
  Needs git, python3, make, a C++17 compiler and SDL2 development files.
- Verified with it on 80-track `.fd` images (`tests/floppy351/run_all.sh`): `DSKINI`, `SAVE`/`LOAD`/`SAVEM`/`LOADM`,
  `KILL`, a whole disk of files byte-exact, `BACKUP 0 TO 0` with disk swaps, `DSKI$`/`DSKO$` on track 79, `COPY`,
  sequential files, write protect, disk change. Not verified: side 1, a real second drive, random-access files.
- To tell the controllers apart on a real machine, read `$A000`: `DKD(` is the CD90-640, `MTD:` the CD90-351.
- The disassembly of the four 351 ROM pages is in [docs/cd90-351-disasm/](docs/cd90-351-disasm/).
- Workflow: use 80-track images with the primary CD90-351. For the 5.25" CD90-640 fallback, use 40-track
  images; convert between layouts with `fdtool.py cp` when moving files between the drives or DCMOTO.

## How it works

- `pc128.py` prepares the job (assembles with the local `tools/.local/.../lwasm`, or prepares the BASIC lines),
  writes `build/job.lua` (a config table + `harness.lua`), and starts MAME with `-autoboot_script`.
- **BASIC**: after boot, lines are typed through MAME's natural keyboard: `NEW`, your lines, `RUN`.
- **Assembly**: after boot, the machine code is written straight into RAM, the CPU `PC` is set to the
  `END` label, and the program runs with BASIC out of the way.
- A run ends when the program writes a non-zero byte to `--done-addr`, or after `run_frames`
  (50 frames = 1 emulated second). Then registers, dumps and a screenshot (`out/screen.png`) are saved.

## Writing testable programs

The screen of this machine is graphical, so text can't be read back directly. Instead:
- Write results to RAM (`POKE &H9F00,x` / `STA $9F00`) and read them with `--dump 9F00:16`.
- Signal completion with a non-zero byte at the done address (`POKE &H9F01,1` / `STA $9F01`).
- Use the screenshot for anything visual.

Machine-code programs: use `ORG $9000` (user RAM is roughly `$2000-$9FFF`), `END label`, and
finish with `BRA *`.

## Known caveats

- The standard workflow uses the repo-built MAME version pinned in `mame-patch/BASE_COMMIT` (0.289).
  The system-MAME fallback and other versions have not been fully verified.
- If typed BASIC does not appear on screen, the machine may not map natural keyboard characters; try
  raising `boot_frames` first (the BASIC prompt must be up before typing starts).
- `headless: true` adds `-video none`; screenshots may not be produced in that mode.
- Lua API differences between MAME versions are handled for the frame callback and `manager.machine`;
  register names (`PC`, `S`, `U`, `X`, `Y`, `A`, `B`, `DP`, `CC`) are assumed for the 6809 core.
- Each call starts from a cold boot. There is no persistent session.



[localEnvReference]: docs/mame-pc128.md
