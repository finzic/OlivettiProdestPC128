# PC128 Debugger (MAME)

VS Code debug type `pc128` for the Olivetti Prodest PC128 / Thomson MO6. It runs `tools/debugger/dap.py`
from the workspace, which drives a patched MAME (see `docs/debugger.md` in the repository).

- Breakpoints in `.asm` files (assembled with lwasm), `.c` files (built with CMOC + `libolivetti`, see `pc128-c/README.md`)
  and `.bas` files (BASIC line breakpoints), conditional too
- Step over / step into by source line in C and asm programs (instruction stepping from the disassembly view)
- Function breakpoints: symbol names (`PUTC`, `B_NEWSTT`), addresses (`F6D9`), page-qualified (`mon0:F6D9`), `line 40`
- Data breakpoints (watchpoints), instruction breakpoints, disassembly view, memory view
- Variables: registers (editable, CC flags), location / ROM correlation, banking, stack, BASIC state
- Debug console: all debugger commands (`help`), e.g. `a 9F00 LDA #$41 | SWI PUTC`, `hex 9F00 12 34`, `str 9F00 "HI\0"`

Build/install: `python3 tools/vscode-pc128-debug/build.py --install` (creates `build/pc128-debug-*.vsix` and installs it).
