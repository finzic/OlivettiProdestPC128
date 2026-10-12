# OlivettiProdestPC128
A Repo containing wiki and code for our beloved 8-bit machine

## Documentation

- [PC128 system calls and ROM calling reference](docs/pc128-system-calls.md)
- [Configuration of local environment][docs/mame-pc128.md]

# PC128 harness: run BASIC and 6809 code from VS Code

Lets you (or a coding assistant) run code on an emulated **Olivetti Prodest PC128** (a Thomson MO6)
using **MAME**, which is scriptable. DCMOTO itself has no automation interface, so it is not used.

Each run boots a fresh machine, runs your code, then returns:
CPU registers, memory dumps you asked for, and a screenshot. A run takes a few seconds.

## Setup

1. Install **MAME** and put the Thomson ROM sets where MAME can find them (`rompath` in `config.json`).
2. Check the machine name: `mame -listxml | grep -i -E "pc128|mo6"`. Set `machine` in `config.json` if it differs.
3. For assembly: install **LWTOOLS** (`lwasm`) and make sure it is on PATH (or set `lwasm` in `config.json`).
4. For the MCP server: `pip install mcp` (works with mcp 1.x and 2.x).

## Use it

**VS Code tasks** (`Terminal > Run Task`, files in `.vscode/tasks.json`)
- `PC128: run BASIC (current file)`
- `PC128: run ASM (current file)`
- `PC128: run ASM (choose memory dump)`

**Command line**
```
python3 pc128.py asm   examples/hello.asm --done-addr 9F01 --dump 9F00:16
python3 pc128.py basic examples/hello.bas  --done-addr 9F01 --dump 9F00:16
```

**Coding assistant (MCP)**: `.vscode/mcp.json` (VS Code / Copilot) and `.mcp.json` (Claude Code)
register the server `pc128` with two tools, `run_basic` and `run_asm`. `AGENTS.md` tells the
assistant how to use them.

## How it works

- `pc128.py` prepares the job (assembles with `lwasm --format=decb`, or prepares the BASIC lines),
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

## Known caveats (not verified on a real MAME install)

- MAME was not available where this was built. The Lua script, runner and MCP tools were tested against
  a mocked MAME and a mocked `lwasm`. First run on your machine may need small adjustments.
- If typed BASIC does not appear on screen, the machine may not map natural keyboard characters; try
  raising `boot_frames` first (the BASIC prompt must be up before typing starts).
- `headless: true` adds `-video none`; screenshots may not be produced in that mode.
- Lua API differences between MAME versions are handled for the frame callback and `manager.machine`;
  register names (`PC`, `S`, `U`, `X`, `Y`, `A`, `B`, `DP`, `CC`) are assumed for the 6809 core.
- Each call starts from a cold boot. There is no persistent session.



[localEnvReference]: docs/mame-pc128.md