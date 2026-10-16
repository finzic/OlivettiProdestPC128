# Running the Olivetti Prodest PC128 in MAME

Historical setup note: this describes the original Linux setup with distro MAME 0.264 and the CD90-640.
For the current PC128 workspace workflow, use `tools/prepare-mame.sh` to build the pinned, patched MAME
for the original 3.5-inch CD90-351. The 5.25-inch CD90-640 remains an optional fallback; its package-install
and `~/.mame` configuration notes below may help with that older setup. The debugger and ROM-format notes
may also be useful for the BASIC extension project.

## 1. Install MAME

```bash
sudo apt update
sudo apt install mame
mame -version
```

## 2. Driver name: `pro128`, not `pc128`

MAME lists the PC128 under the name `pro128`, in the Thomson driver (`thomson/thomson.cpp`).

```bash
mame -listsource | grep -i thomson   # mo5, mo5e, mo5nr, mo6, pro128, to7, to770, to8, ...
mame -listroms pro128
```

`mo6` (Thomson MO6) is the same hardware with a French ROM. Use `pro128` so that the ROM addresses match
the real PC128.

## 3. ROM files: converting the DCMOTO ROM

MAME expects six files. The single 65536-byte ROM image from the DCMOTO site (`ROM/pc128.rom`) contains all
six, one after another. Each piece was checked against MAME's CRC values and all of them match exactly:

| Offset in `pc128.rom` | Size  | MAME file      | CRC32      |
|-----------------------|-------|----------------|------------|
| `0x0000`              | 12288 | `basico-0.rom` | `98b10d5e` |
| `0x3000`              | 4096  | `pro128-0.rom` | `a8aef291` |
| `0x4000`              | 12288 | `basico-1.rom` | `721d2124` |
| `0x7000`              | 4096  | `pro128-1.rom` | `5b3340ec` |
| `0x8000`              | 16384 | `basico-2.rom` | `135438ab` |
| `0xC000`              | 16384 | `basico-3.rom` | `2c2befa6` |

Put the two DCMOTO downloads in the repository's `src-rom/` directory:

```bash
src-rom/pc128.rom
src-rom/cd90-640.rom
```

Run the environment checker to validate and prepare them:

```bash
./tools/check-environment.sh
```

It splits `pc128.rom` into the six CRC-checked files listed above under `roms/pro128/` and copies
`cd90-640.rom` unchanged to `roms/`. If `src-rom/cd90-351.rom` (8192 bytes: four 2 KB pages, the first 1984
bytes of each used) exists, `tools/prepare-roms.py` also writes `cd-351-0..3.rom` to `roms/cd90_351/` and
`roms/pro128/`; the CD90-351 is optional (see the floppy section of the README). The local `roms/` search path is configured in `config.json`;
both `src-rom/` and generated `roms/` are ignored by Git. To verify the machine ROM set directly,
run this from the repository root:

```bash
mame -rompath ./roms -verifyroms pro128      # should report "romset pro128 is good"
```

The ROMs are copyrighted. Keep the source and generated files out of the repository's tracked files.

## 4. Configuration (`~/.mame/mame.ini`)

Generate the default configuration file once:

```bash
mkdir -p ~/.mame && cd ~/.mame
mame -createconfig
```

Then edit these lines in `~/.mame/mame.ini`:

```ini
rompath          ./roms
window           1
confirm_quit     0
ui_active        1
```

- `rompath`: when launching MAME manually from the repository root, use the local `roms/` folder.
   The harness resolves the relative path in `config.json` to an absolute repository path.
- `confirm_quit 0`: without it, clicking the window's X opens a quit prompt inside the emulated screen,
  and the captured keyboard can't answer it. MAME seemed not to close.
- `ui_active 1`: see the next section.

The same settings work as command-line options:

```bash
mame pro128 -rompath ./roms -window -noconfirm_quit -ui_active
```

## 5. Keyboard: no Scroll Lock key

The PC128 has a full keyboard, so MAME starts in "keyboard mode": all keys go to the emulated machine,
including Tab (MAME menu) and Esc (quit). The usual key to switch back is Scroll Lock, which this keyboard
does not have. There are three alternatives:

1. **`ui_active 1`** (the option chosen above): MAME's own keys stay active, so Tab and Esc go to MAME.
   The downside is that the PC128 can't receive those two keys.
2. **Remap the toggle key**: in **Tab → Input Settings → Input Assignments (general) → User Interface →
   Toggle UI**, select the entry and press another key, for example Right Ctrl. MAME saves the change in
   `~/.mame/cfg/default.cfg`.
3. **Send Scroll Lock from a terminal** (X11 only): `xdotool search --name MAME windowactivate --sync key Scroll_Lock`.

A running MAME session can also be stopped with Ctrl+C in the terminal that started it.

## 6. Mouse and lightpen: reversed axes

With the emulated mouse or lightpen, the pointer moved in the opposite direction. Fix:

1. Press **Tab** to open the menu (`ui_active` must be on, or the UI toggle key pressed).
2. Go to **Analog Controls**.
3. Set **Reverse** to On for each inverted mouse or lightpen axis (X and/or Y).

MAME saves this for this machine only, in `~/.mame/cfg/pro128.cfg`.

Use `-nomouse` when the mouse isn't needed, so MAME doesn't capture the host pointer.

## 7. Using MAME for the BASIC extension project

Start with the debugger:

```bash
mame pro128 -window -debug
```

These debugger commands are useful for filling in the `[SCAN]` addresses in
`pc128-basic-ext/src/equ_pc128.asm`:

| Command                    | Purpose                                                         |
|----------------------------|-----------------------------------------------------------------|
| `save bank.rom,b000,4000`  | Dump the ROM bank currently mapped at `$B000-$EFFF`             |
| `dasm out.asm,b000,4000`   | Disassemble a range to a file                                   |
| `bpset ADDR`               | Stop when a hook address found by `rom_scan.py` is reached      |
| `wpset 21b9,2,w`           | Stop on writes to a suspected text pointer such as `B_TXTPTR`   |
| `help`                     | List all debugger commands                                      |

ROM scan, starting from the split files:

```bash
cd ~/olivetti/pc128-basic-ext
python3 tools/rom_scan.py --rom roms/pro128/basico-2.rom@0xB000 \
                          --rom roms/pro128/basico-3.rom@0xB000
```

Which file is BASIC 128 and which is BASIC 1, and the exact base address of each bank, were not confirmed
yet. Check them with `save` in the debugger before relying on the scan output.

To load the extension, type or paste the generated BASIC loader `pc128-basic-ext/build/basext.bas` at the
BASIC prompt. MAME's paste function is in the UI menu, bound by default to Scroll Lock + Shift+Ins; with
`ui_active` on, check the binding under **Input Assignments (general)**. Another option is
`-autoboot_command`, which types text for you at startup.

## Quick reference

```bash
# normal session
mame pro128 -rompath ./roms -window -noconfirm_quit -ui_active
# without mouse capture
mame pro128 -rompath ./roms -window -noconfirm_quit -ui_active -nomouse

# debugging session
mame pro128 -rompath ./roms -window -noconfirm_quit -ui_active -debug
```
