# Running the Olivetti Prodest PC128 in MAME

This note describes how MAME was set up on Linux (MAME 0.264, Ubuntu/Debian package) to emulate the
Olivetti Prodest PC128. It is used for testing the BASIC extension project in `pc128-basic-ext/`.

## 1. Install MAME

```bash
sudo apt update
sudo apt install mame mame-tools
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

The ROMs are kept in `~/mame`. To split the image into a `pro128` folder there:

```bash
mkdir -p ~/mame/pro128 && cd ~/mame/pro128
R=~/olivetti/ROM/pc128.rom
dd if=$R of=basico-0.rom bs=4096 skip=0  count=3 status=none
dd if=$R of=pro128-0.rom bs=4096 skip=3  count=1 status=none
dd if=$R of=basico-1.rom bs=4096 skip=4  count=3 status=none
dd if=$R of=pro128-1.rom bs=4096 skip=7  count=1 status=none
dd if=$R of=basico-2.rom bs=4096 skip=8  count=4 status=none
dd if=$R of=basico-3.rom bs=4096 skip=12 count=4 status=none
mame -rompath ~/mame -verifyroms pro128      # should report "romset pro128 is good"
```

The ROMs are copyrighted. Keep them out of the git repository (`ROM/` is listed in `.gitignore`).

## 4. Configuration (`~/.mame/mame.ini`)

Generate the default configuration file once:

```bash
mkdir -p ~/.mame && cd ~/.mame
mame -createconfig
```

Then edit these lines in `~/.mame/mame.ini`:

```ini
rompath          $HOME/mame
window           1
confirm_quit     0
ui_active        1
```

- `rompath`: the ROMs live in `~/mame` instead of MAME's default `roms` folder.
- `confirm_quit 0`: without it, clicking the window's X opens a quit prompt inside the emulated screen,
  and the captured keyboard can't answer it. MAME seemed not to close.
- `ui_active 1`: see the next section.

The same settings work as command-line options:

```bash
mame pro128 -rompath ~/mame -window -noconfirm_quit -ui_active
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
python3 tools/rom_scan.py --rom ~/mame/pro128/basico-2.rom@0xB000 \
                          --rom ~/mame/pro128/basico-3.rom@0xB000
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
mame pro128 -rompath ~/mame -window -noconfirm_quit -ui_active

# without mouse capture
mame pro128 -rompath ~/mame -window -noconfirm_quit -ui_active -nomouse

# debugging session
mame pro128 -rompath ~/mame -window -noconfirm_quit -ui_active -debug
```
