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
and the expected workspace configuration files. If the local `lwasm` is missing and its
build prerequisites are available, the checker runs `setup-lwasm.sh` automatically.

The checker reports missing prerequisites and exits non-zero; it does not install system
packages or Python packages. On Debian or Ubuntu, install the system packages with:

```bash
sudo apt update
sudo apt install curl tar make build-essential python3 python3-pip python3-venv mame
```

`mame-tools` is optional; the workspace only requires the `mame` executable.

Install MCP into the workspace virtual environment. Both the VS Code and Claude Code MCP
configurations launch the server with this interpreter, so installing MCP into a different
Python environment will not make it available to the server:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install mcp
```

The `mame` executable and the ROM set configured by `machine` and `rompath` in `config.json`
Place the DCMOTO ROM downloads `pc128.rom` and `cd90-640.rom` in `src-rom/`. The environment
checker validates and prepares them in the ignored, repository-local `roms/` directory: the PC128
image is split into `roms/pro128/`, and the CD90 image is copied unchanged to `roms/cd90-640.rom`.
The `mame` executable and the ROM set configured by `machine` and `rompath` in `config.json`
are both required to run the emulator. See [../docs/mame-pc128.md](../docs/mame-pc128.md)
for the ROM file details. When using the floppy controller, its `cd90-640.rom` is already copied
into the configured ROM path by the checker.

LWTOOLS is downloaded as source and compiled locally. Its executable is placed under
`tools/.local/`; both that directory and the suggested `.venv/` are excluded by
`.gitignore`, so generated binaries and installed Python packages are not committed.