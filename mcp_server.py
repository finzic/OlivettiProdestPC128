#!/usr/bin/env python3
"""MCP server: lets a coding assistant run Thomson BASIC / 6809 code on a PC128 (MAME).

    pip install mcp        # works with mcp 1.x and 2.x
    python3 mcp_server.py        # stdio transport
"""
try:                                    # mcp >= 2
    from mcp.server.mcpserver import Image, MCPServer as FastMCP
except ImportError:                     # mcp 1.x
    from mcp.server.fastmcp import FastMCP, Image

from pc128 import format_report, run_job

mcp = FastMCP("pc128")


def _result(report: dict):
    content = [format_report(report)]
    shot = report.get("screenshot")
    if shot:
        content.append(Image(path=shot))
    return content


@mcp.tool()
def run_basic(code: str, dump: list[str] | None = None, done_addr: str | None = None,
              run_frames: int | None = None) -> list:
    """Run Thomson BASIC 128 source on an emulated Olivetti Prodest PC128 (MO6).

    The program is typed into a freshly booted machine (NEW, your lines, RUN).
    Use numbered lines. Text is uppercased outside string literals.
    Results come back as CPU registers, memory dumps and a screenshot of the screen.

    Tips: POKE results into RAM and read them with `dump`; end the program with
    POKE &H9F01,1 and pass done_addr="9F01" to stop early instead of waiting run_frames.

    Args:
        code: BASIC source, one numbered line per row.
        dump: memory ranges to read back, "HEXADDR:LENGTH", e.g. ["9F00:16"].
        done_addr: hex address; the program writes a non-zero byte there when finished.
        run_frames: max frames (50 per emulated second) to run after RUN. Default from config.
    """
    return _result(run_job("basic", code, dump, run_frames, None, done_addr))


@mcp.tool()
def run_asm(code: str, dump: list[str] | None = None, done_addr: str | None = None,
            run_frames: int | None = None) -> list:
    """Assemble 6809 source with lwasm and run it on an emulated PC128 (MO6).

    Use ORG for the load address (user RAM is roughly $2000-$9FFF; $9000 is a safe choice)
    and `END label` to set the entry point. The code is injected into RAM after the machine
    has booted, then the CPU PC is set to the entry point, so BASIC is not involved.
    Finish with `BRA *` and/or store a non-zero byte at done_addr.

    Args:
        code: lwasm-syntax 6809 assembly.
        dump: memory ranges to read back, "HEXADDR:LENGTH", e.g. ["9F00:16"].
        done_addr: hex address; the program stores a non-zero byte there when finished.
        run_frames: max frames (50 per emulated second) to run. Default from config.
    """
    return _result(run_job("asm", code, dump, run_frames, None, done_addr))


if __name__ == "__main__":
    mcp.run()
