"""Live assembly for the debugger: snippets -> bytes via lwasm, plus whole-program builds.

Snippet syntax (one instruction per line, or several separated by " | "):
    LDA #$41 | SWI PUTC | RTS
    loop: DEC $9F00 | BNE loop
`SWI $02` / `SWI PUTC` are expanded to SWI + FCB service byte (PC128 monitor convention).
Debugger symbols used in a snippet (e.g. `JSR B_GETEXPR`) are defined automatically.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
import pc128  # noqa: E402

from m6809 import SWI_SERVICES  # noqa: E402

WORK = ROOT / "build" / "dbg-asm"
SERVICE_BY_NAME = {v.upper(): k for k, v in SWI_SERVICES.items()}
LIST_RE = re.compile(r"^(?P<addr>[0-9A-F]{4}) (?P<bytes>[0-9A-F]+)?\s+\((?P<file>[^)]*)\):(?P<line>\d+)\s?(?P<src>.*)$")
IDENT_RE = re.compile(r"[A-Za-z_.@?][\w.@?$]*")


class AsmError(Exception):
    pass


@dataclass
class ListLine:
    addr: int
    data: bytes
    file: str
    line: int
    source: str


@dataclass
class AsmResult:
    segments: list            # [(addr, bytes)]
    entry: int | None
    lines: list = field(default_factory=list)       # [ListLine]
    symbols: dict = field(default_factory=dict)     # name -> addr
    warnings: str = ""

    @property
    def size(self):
        return sum(len(d) for _, d in self.segments)


def _lwasm(cfg, src, extra=()):
    WORK.mkdir(parents=True, exist_ok=True)
    out, lst, sym = WORK / (src.stem + ".bin"), WORK / (src.stem + ".lst"), WORK / (src.stem + ".sym")
    for f in (out, lst, sym):
        f.unlink(missing_ok=True)
    try:
        p = subprocess.run([cfg["lwasm"], "--6809", "--format=decb", "--output=%s" % out, "--list=%s" % lst,
                            "--symbol-dump=%s" % sym, *extra, str(src)],
                           capture_output=True, text=True, timeout=60, cwd=str(src.parent))
    except FileNotFoundError:
        raise AsmError("lwasm not found (%r). Run tools/setup-lwasm.sh first." % cfg["lwasm"])
    msg = (p.stdout + p.stderr).strip()
    if p.returncode != 0 or not out.exists():
        raise AsmError(msg or "assembler failed")
    segs, entry = pc128.parse_decb(out.read_bytes())
    lines = parse_listing(lst.read_text(errors="replace")) if lst.exists() else []
    syms = {}
    if sym.exists():
        for ln in sym.read_text().splitlines():
            m = re.match(r"^(\S+)\s+EQU\s+\$([0-9A-Fa-f]+)", ln)
            if m:
                syms[m.group(1)] = int(m.group(2), 16)
    return AsmResult([(a, bytes(d)) for a, d in segs], entry, lines, syms, msg)


def parse_listing(text):
    out = []
    last = None
    for raw in text.splitlines():
        m = LIST_RE.match(raw)
        if m:
            data = bytes.fromhex(m.group("bytes") or "")
            last = ListLine(int(m.group("addr"), 16), data, m.group("file").strip(), int(m.group("line")),
                            m.group("src"))
            out.append(last)
        elif last is not None and re.match(r"^\s{5}[0-9A-F]+\s*$", raw):
            last.data += bytes.fromhex(raw.strip())    # continuation of long FCC/FCB data
    return out


def expand_swi(line):
    m = re.match(r"^(\s*(?:[\w.@?$]+:?\s+)?)SWI\s+(\S+)(.*)$", line, re.I)
    if not m:
        return [line]
    arg = m.group(2)
    if arg.startswith(";"):
        return [line]
    code = SERVICE_BY_NAME.get(arg.upper())
    if code is None:
        code = pc128.parse_int(arg.replace("$", "0x")) if re.match(r"^\$?[0-9A-Fa-f]+$|^0x", arg) else None
    if code is None:
        return [line]
    return [m.group(1) + "SWI", "        FCB $%02X%s" % (code, m.group(3))]


def snippet_source(text, org, symtab=None):
    """Normalise a debugger snippet into an lwasm source file assembled at `org`."""
    raw_lines = []
    for chunk in text.replace("\r", "").split("\n"):
        raw_lines += [p for p in re.split(r"\s\|\s", chunk)]
    body, labels = [], set()
    for ln in raw_lines:
        s = ln.strip()
        if not s:
            continue
        m = re.match(r"^([A-Za-z_.@?][\w.@?$]*):\s*(.*)$", s)
        if m:
            labels.add(m.group(1).upper())
            body.append(m.group(1))
            s = m.group(2)
            if not s:
                continue
        body += ["        " + x.strip() for x in expand_swi(s)]
    defs = []
    if symtab is not None:
        used = set()
        for ln in body:
            code = ln.split(";")[0]
            code = re.sub(r'"[^"]*"|\'.', "", code)
            for t in IDENT_RE.findall(code)[1:] if ln.startswith(" ") else []:
                used.add(t)
        for t in sorted(used):
            if t.upper() in labels or t.upper() in ("A", "B", "D", "X", "Y", "U", "S", "PC", "PCR", "CC", "DP"):
                continue
            sym = symtab.find(t)
            if sym is not None:
                defs.append("%s EQU $%04X" % (t, sym.addr))
    return "\n".join(defs + ["        ORG $%04X" % org] + body) + "\n"


def assemble_snippet(text, org, cfg, symtab=None):
    src = WORK / "snippet.asm"
    WORK.mkdir(parents=True, exist_ok=True)
    src.write_text(snippet_source(text, org, symtab))
    try:
        res = _lwasm(cfg, src)
    except AsmError as e:
        msg = str(e).replace(str(src), "snippet")
        raise AsmError(msg)
    if not res.segments:
        raise AsmError("snippet produced no bytes")
    return res


def assemble_file(path, cfg):
    """Assemble a program file; listing lines keep the real file paths for source breakpoints."""
    path = Path(path).resolve()
    res = _lwasm(cfg, path)
    candidates = [path] + [p.resolve() for p in path.parent.rglob("*") if p.suffix.lower() in (".asm", ".inc", ".s", ".a09")]
    cache = {}
    for ln in res.lines:
        key = ln.file
        if key not in cache:
            hit = next((str(c) for c in candidates if str(c).endswith(key) or c.name == key), key)
            cache[key] = hit
        ln.file = cache[key]
    return res


def parse_hex_bytes(text):
    """'86 01 B7 A7 C0', '8601B7A7C0', '$86,$01' -> bytes."""
    t = re.sub(r"[\s,]+", " ", text.replace("$", "").replace("0x", "").replace("0X", "")).strip()
    out = bytearray()
    for group in t.split(" "):
        if not group:
            continue
        if len(group) % 2:
            group = "0" + group
        try:
            out += bytes.fromhex(group)
        except ValueError:
            raise AsmError("bad hex bytes: %r" % text)
    return bytes(out)


def parse_string(text):
    """Quoted string with C escapes (\\n -> $0D for the PC128, \\0, \\xNN); unquoted text taken literally."""
    t = text.strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        t = t[1:-1]
    out = bytearray()
    i = 0
    while i < len(t):
        c = t[i]
        if c == "\\" and i + 1 < len(t):
            n = t[i + 1]
            i += 2
            if n == "n" or n == "r":
                out.append(0x0D)
            elif n == "0":
                out.append(0)
            elif n == "t":
                out.append(9)
            elif n == "x" and i + 2 <= len(t):
                out.append(int(t[i:i + 2], 16))
                i += 2
            else:
                out += n.encode("latin-1")
            continue
        out += c.encode("latin-1")
        i += 1
    return bytes(out)
