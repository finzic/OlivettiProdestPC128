# Local LWTOOLS assembler

Run `./tools/setup-lwasm.sh` from the repository root to install LWTOOLS 4.24. The setup
script downloads the upstream source archive, builds `lwasm`, and installs the executable at
`tools/.local/lwtools-4.24/lwasm/lwasm`.

The setup requires `curl`, `tar`, `make`, and a C compiler (`cc` by default; set `CC` to use
another compiler). The downloaded source is built in a temporary directory and removed when
the script exits. The installed executable is kept under `tools/.local/`, which is ignored by
Git and should not be committed.

`pc128.py`, the BASIC extension Makefile, and the keyjoy Makefile all use this local
executable. Install it before assembling; they do not silently fall back to a system-wide
`lwasm`.

## Check the workspace environment

Run `./tools/check-environment.sh` from any directory in the repository. It checks for
Python 3.10 or newer, pip and the MCP package, the native tools needed to build LWTOOLS
(`curl`, `tar`, `make`, and a C compiler), MAME, the configured MAME machine and ROM set,
and the expected workspace configuration files. It checks the prepared local MAME build
(`tools/.local/mame/mame_thomson/thomson`); a system MAME is never used. If the local `lwasm` is missing and its
build prerequisites are available, the checker runs `setup-lwasm.sh` automatically.

The checker reports missing prerequisites and exits non-zero; it does not install system
packages or Python packages. On Debian or Ubuntu, install the system packages with:

```bash
sudo apt update
sudo apt install curl tar make build-essential python3 python3-pip python3-venv
```

Build the pinned, patched MAME locally with `./tools/prepare-mame.sh`; it is the only MAME the
repository uses (`pc128.py`, the MCP server, `run-mame.sh`, `investigate.py` and the tests all resolve
`"mame": "mame"` in `config.json` to it). `mame-tools` is optional;
its `floptool` converts
between `.fd` and MAME's `.mfi` flux images if you need that.

Install MCP into the workspace virtual environment. Both the VS Code and Claude Code MCP
configurations launch the server with this interpreter, so installing MCP into a different
Python environment will not make it available to the server:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install mcp
```

Place the DCMOTO ROM downloads `pc128.rom` and `cd90-351.rom` in `src-rom/`. The CD90-351 is the
PC128's original 3.5-inch drive and the repository's primary floppy target. The `cd90-640.rom` for the
5.25-inch fallback is optional. The environment
checker validates and prepares them in the ignored, repository-local `roms/` directory: the PC128
image is split for older MAME and staged as `pro128.iw01`/`basico.iw02` for current MAME, and the CD90
351 image is split by `tools/prepare-roms.py` into `cd-351-0..3.rom` under `roms/cd90_351/` and
`roms/pro128/`. If present, `cd90-640.rom` is copied unchanged to `roms/cd90-640.rom` and
`roms/pro128/`.
The prepared local MAME executable and the ROM set configured by
`machine` and `rompath` in `config.json` are required to run the emulator. See
[../docs/mame-pc128.md](../docs/mame-pc128.md) for the ROM file details. The checker prepares the
required CD90-351 pages; if supplied, it also copies the optional `cd90-640.rom` fallback into the ROM path.

LWTOOLS is downloaded as source and compiled locally. Its executable is placed under
`tools/.local/`; both that directory and the suggested `.venv/` are excluded by
`.gitignore`, so generated binaries and installed Python packages are not committed.
## Renumber a BASIC listing

`tools/renumber.py` renumbers an ASCII `.BAS` listing in place (default start 10, step 10) and
rewrites the line numbers after `GOTO`/`GO TO`, `GOSUB`/`GO SUB`, `THEN`, `ELSE`, `RESTORE`,
`RESUME`, `RUN`, `LIST` and `DELETE`, including `ON ... GOTO` lists and `LIST a-b` ranges. Strings,
`REM`/`'` comments and `DATA` statements are left unchanged. References to missing lines are reported
as warnings. Tokenized files are rejected.

```bash
python3 tools/renumber.py PROG.BAS --start 100 --step 5   # add --stdout to preview
```

In VS Code, run the task **PC128: renumber BASIC (current file)** or **PC128: renumber BASIC
(choose start/step)**. To bind the first task to a key, add this to your `keybindings.json`:

```json
{ "key": "ctrl+alt+r", "command": "workbench.action.tasks.runTask",
  "args": "PC128: renumber BASIC (current file)", "when": "resourceExtname =~ /\\.bas$/i" }
```

Save the file before running the task. VS Code reloads the renumbered file from disk.

## Debugger

`tools/debugger/` contains the PC128 debugger:
- `pc128dbg.py`: terminal REPL
- `dap.py`: VS Code debug adapter
- `pc128_dbg.lua`: server inside MAME
- disassembler, symbols, and the lwasm wrapper

`tools/vscode-pc128-debug/` holds the VS Code extension; `build.py --install` packages and installs it.
See `docs/debugger.md`.
