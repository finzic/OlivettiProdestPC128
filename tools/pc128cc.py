#!/usr/bin/env python3
"""pc128cc - build C (+ 6809 assembly) programs for the Olivetti Prodest PC128 with CMOC.

    python3 tools/pc128cc.py hello.c                    # -> build/pc128-c/hello/hello.bin
    python3 tools/pc128cc.py main.c sprite.asm -o game.bin --org 7000
    python3 tools/pc128cc.py hello.c --run              # build and run in the emulator
    python3 tools/pc128cc.py hello.c --fd media/C.FD    # put HELLO.BIN on a floppy image
    python3 tools/pc128cc.py --lib                      # (re)build libolivetti.a only

Sources may be .c (compiled by CMOC) or .asm/.s (assembled by lwasm as relocatable objects:
use SECTION code / EXPORT _name / ENDSECTION). Every program is linked against the
"standard Olivetti library" in pc128-c/ (include/olivetti.h, lib/libolivetti.a).

A main .c file can carry build directives in a comment, e.g.
    // pc128cc: sources=sprite.asm,util.c org=7000 limit=9F00 opt=-O0

The result is a DECB binary to be loaded at `org` and started with EXEC &Hxxxx; when main()
returns the program goes back to BASIC. A .sym file (one `name addr` per line) and a
.lines file (addr -> C source line) are written next to it for the debugger.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "debugger"))

PROJECT = ROOT / "pc128-c"
INCDIR = PROJECT / "include"
LIBSRC = PROJECT / "lib"
BUILD = ROOT / "build" / "pc128-c"
LIBBUILD = BUILD / "lib"
LIBNAME = "olivetti"
TOOL_DIRS = [ROOT / "tools" / ".local" / "cmoc-0.1.100" / "bin",
             ROOT / "tools" / ".local" / "lwtools-4.24" / "bin"]
DEFAULT_ORG = 0x6000
DEFAULT_LIMIT = 0x9F00

LST_RE = re.compile(r"^(?:(?P<addr>[0-9A-F]{4}) (?P<bytes>[0-9A-F]+)?)?\s+\((?P<file>[^)]*)\):(?P<line>\d+)\s?(?P<src>.*)$")
CLINE_RE = re.compile(r"^\*\s+Line\s+(?P<file>.+?):(?P<line>\d+):")
CFUNC_RE = re.compile(r"^\*\s+FUNCTION\s+\S+\(\): defined at (?P<file>.+?):(?P<line>\d+)")
SECTION_RE = re.compile(r"^\s+SECTION\s+(\S+)", re.I)
ENDSECTION_RE = re.compile(r"^\s+ENDSECTION\b|^\s+ENDS\b", re.I)
MAP_SECTION_RE = re.compile(r"^Section: (\S+) \((\S+)\) load at ([0-9A-F]+), length ([0-9A-F]+)")
MAP_SYMBOL_RE = re.compile(r"^Symbol: (\S+) \((\S+)\) = ([0-9A-F]+)")
DIRECTIVE_RE = re.compile(r"pc128cc:\s*(.*)")


class CBuildError(Exception):
    pass


@dataclass
class ListLine:
    """Same shape as tools/debugger/asm.ListLine (addr, data, file, line, source)."""
    addr: int
    data: bytes
    file: str
    line: int
    source: str


@dataclass
class CBuildResult:
    segments: list                                   # [(addr, bytes)]
    entry: int | None
    binary: Path
    lines: list = field(default_factory=list)        # [ListLine] with C (or asm) file/line
    symbols: dict = field(default_factory=dict)      # name -> addr ("_main" and "main")
    warnings: str = ""
    map_file: Path | None = None
    org: int = DEFAULT_ORG
    end: int = DEFAULT_ORG

    @property
    def size(self):
        return sum(len(d) for _, d in self.segments)


# --------------------------------------------------------------------------- toolchain

def tool_env():
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([str(d) for d in TOOL_DIRS if d.is_dir()] + [env.get("PATH", "")])
    return env


def which(name):
    return shutil.which(name, path=tool_env()["PATH"])


def check_toolchain():
    missing = [n for n in ("cmoc", "lwasm", "lwlink", "lwar") if not which(n)]
    if missing:
        raise CBuildError("missing %s: run tools/setup-lwasm.sh and tools/setup-cmoc.sh" % ", ".join(missing))


def _run(cmd, cwd=None):
    try:
        p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=tool_env(),
                           cwd=str(cwd) if cwd else None, timeout=300)
    except FileNotFoundError as e:
        raise CBuildError("%s not found: run tools/setup-cmoc.sh" % cmd[0]) from e
    out = (p.stdout + p.stderr).strip()
    if p.returncode != 0:
        raise CBuildError(out or "%s failed (exit %d)" % (Path(str(cmd[0])).name, p.returncode))
    return out


def compile_c(src: Path, workdir: Path, objname: str, cflags=()):
    """CMOC -c: produces workdir/<objname>.o plus .s and .lst (kept with -i)."""
    workdir.mkdir(parents=True, exist_ok=True)
    obj = workdir / (objname + ".o")
    # cmoc names the intermediate files after the source; copy-free trick: compile then rename
    out = _run(["cmoc", "--thommo", "-c", "-i", "--intdir=%s" % workdir, "-I", INCDIR, *cflags,
                "-o", obj, src.resolve()])
    lst = workdir / (src.stem + ".lst")
    if src.stem != objname and lst.exists():
        lst.replace(workdir / (objname + ".lst"))
        s = workdir / (src.stem + ".s")
        if s.exists():
            s.replace(workdir / (objname + ".s"))
    return obj, workdir / (objname + ".lst"), out


def assemble_obj(src: Path, workdir: Path, objname: str, aflags=()):
    workdir.mkdir(parents=True, exist_ok=True)
    obj, lst = workdir / (objname + ".o"), workdir / (objname + ".lst")
    out = _run(["lwasm", "--6809", "--format=obj", "--pragma=undefextern", "-I", INCDIR, "-I", src.parent,
                "--list=%s" % lst, "-o", obj, *aflags, src.resolve()])
    return obj, lst, out


def compile_source(src: Path, workdir: Path, objname: str, cflags=()):
    ext = src.suffix.lower()
    if ext == ".c":
        return compile_c(src, workdir, objname, cflags)
    if ext in (".asm", ".s", ".a09"):
        return assemble_obj(src, workdir, objname)
    raise CBuildError("don't know how to build %s (expected .c, .asm or .s)" % src)


# --------------------------------------------------------------------------- library

def library_sources():
    return sorted(p for p in LIBSRC.iterdir() if p.suffix.lower() in (".c", ".asm")) if LIBSRC.is_dir() else []


def library_path():
    return LIBBUILD / ("lib%s.a" % LIBNAME)


def build_library(force=False, verbose=False):
    """Compile pc128-c/lib/* into build/pc128-c/lib/libolivetti.a (only when stale)."""
    check_toolchain()
    lib = library_path()
    srcs = library_sources()
    deps = srcs + sorted(INCDIR.glob("*.h")) + sorted(INCDIR.glob("*.inc"))
    if not force and lib.exists() and all(p.stat().st_mtime <= lib.stat().st_mtime for p in deps):
        return lib
    LIBBUILD.mkdir(parents=True, exist_ok=True)
    for old in LIBBUILD.glob("*"):
        if old.is_file():
            old.unlink()
    objs = []
    for src in srcs:
        obj, _lst, out = compile_source(src, LIBBUILD, src.stem)
        if verbose and out:
            print(out, file=sys.stderr)
        objs.append(obj)
    if not objs:
        raise CBuildError("no library sources in %s" % LIBSRC)
    _run(["lwar", "-c", lib, *objs])
    return lib


def library_listings():
    """{object name: (lst path, source path)} for the library objects."""
    out = {}
    for src in library_sources():
        lst = LIBBUILD / (src.stem + ".lst")
        if lst.exists():
            out[src.stem + ".o"] = (lst, src.resolve())
    return out


# --------------------------------------------------------------------------- listing / map parsing

def parse_map(text):
    sections, symbols = {}, {}
    for ln in text.splitlines():
        m = MAP_SECTION_RE.match(ln)
        if m:
            sections[(m.group(1), os.path.basename(m.group(2)))] = (int(m.group(3), 16), int(m.group(4), 16))
            continue
        m = MAP_SYMBOL_RE.match(ln)
        if m and not m.group(1).startswith("\\"):
            symbols[m.group(1)] = int(m.group(3), 16)
    return sections, symbols


def parse_object_listing(text, objname, sections, src_path=None, is_c=True):
    """Relocate a CMOC/lwasm object listing to absolute addresses using the link map.

    For CMOC output, each instruction is attributed to the most recent `* Line file.c:N:` marker.
    For hand-written asm, the listing's own line number in `src_path` is used.
    """
    out, cur_section, cfile, cline, last, own_line = [], None, None, None, None, None
    for raw in text.splitlines():
        m = LST_RE.match(raw)
        if not m:
            if last is not None and re.match(r"^\s{5}[0-9A-F]+\s*$", raw):
                last.data += bytes.fromhex(raw.strip())
            continue
        src = m.group("src")
        if not is_c and src_path is not None and str(src_path).endswith(m.group("file").strip().lstrip(".")):
            own_line = int(m.group("line"))
        if SECTION_RE.match(src):
            cur_section = SECTION_RE.match(src).group(1)
            continue
        if ENDSECTION_RE.match(src):
            cur_section = None
            continue
        if is_c:
            mm = CLINE_RE.match(src.strip()) or CFUNC_RE.match(src.strip())
            if mm:
                cfile, cline = mm.group("file"), int(mm.group("line"))
                continue
        hexbytes = m.group("bytes")
        if not hexbytes or cur_section is None:
            last = None
            continue
        base = sections.get((cur_section, objname))
        if base is None:
            last = None
            continue
        addr = base[0] + int(m.group("addr"), 16)
        if is_c:
            if cfile is None:
                last = None
                continue
            file = cfile if os.path.isabs(cfile) else str((INCDIR / cfile))
            last = ListLine(addr, bytes.fromhex(hexbytes), file, cline, src.strip())
        else:
            # lwasm truncates the file name from the left; other names are INCLUDEd files/macros
            if own_line is None:
                last = None
                continue
            last = ListLine(addr, bytes.fromhex(hexbytes), str(src_path), own_line, src)
        out.append(last)
    return out


# --------------------------------------------------------------------------- program build

def read_directives(path: Path):
    opts = {}
    try:
        head = path.read_text(errors="replace").splitlines()[:40]
    except OSError:
        return opts
    for ln in head:
        m = DIRECTIVE_RE.search(ln)
        if not m:
            continue
        for tok in m.group(1).split():
            if "=" in tok:
                k, v = tok.split("=", 1)
                opts.setdefault(k.strip().lower(), []).append(v.strip().rstrip("*/").strip())
    return opts


def _hex(v):
    return int(str(v).replace("$", "").replace("&H", "").replace("0x", ""), 16) if isinstance(v, str) else int(v)


def build(sources, out=None, org=None, limit=None, cflags=(), defines=(), verbose=False):
    """Build a program; returns CBuildResult. `sources[0]` is the main file (names the output)."""
    check_toolchain()
    sources = [Path(s).resolve() for s in sources]
    if not sources:
        raise CBuildError("no sources")
    for s in sources:
        if not s.exists():
            raise CBuildError("%s: no such file" % s)
    main = sources[0]
    directives = read_directives(main) if main.suffix.lower() == ".c" else {}
    for extra in directives.get("sources", []):
        for name in extra.split(","):
            p = (main.parent / name.strip()).resolve()
            if name.strip() and p not in sources:
                sources.append(p)
    if org is None:
        org = _hex(directives["org"][-1]) if "org" in directives else DEFAULT_ORG
    if limit is None:
        limit = _hex(directives["limit"][-1]) if "limit" in directives else DEFAULT_LIMIT
    cflags = list(cflags) + ["-D%s" % d for d in defines]
    for f in directives.get("opt", []):
        cflags += f.split(",")
    lib = build_library(verbose=verbose)

    work = BUILD / main.stem
    work.mkdir(parents=True, exist_ok=True)
    binary = Path(out).resolve() if out else work / (main.stem + ".bin")
    binary.parent.mkdir(parents=True, exist_ok=True)

    lib_objs = set(library_listings())
    objs, user, msgs, seen = [], [], [], set()
    for src in sources:
        name = src.stem
        while name in seen or (name + ".o") in lib_objs:
            name += "_"
        seen.add(name)
        obj, lst, msg = compile_source(src, work, name, cflags)
        if msg:
            msgs.append(msg)
        objs.append(obj)
        user.append((name + ".o", lst, src, src.suffix.lower() == ".c"))

    has_c_main = any(s.suffix.lower() == ".c" for s in sources)
    if not has_c_main:
        raise CBuildError("the first source must be a .c file containing main()")
    crt = LIBBUILD / "ol_crt.o"            # always linked: its constructor sets up printf's '\n'
    link = ["cmoc", "--thommo", "-i", "--intdir=%s" % work, "-o", binary,
            "--org=%04X" % org, "--limit=%04X" % limit, *objs, crt, "-L", LIBBUILD, "-l" + LIBNAME]
    msg = _run(link)
    if msg:
        msgs.append(msg)

    map_file = work / (binary.stem + ".map")
    if not map_file.exists():
        cands = sorted(work.glob("*.map"), key=lambda p: p.stat().st_mtime)
        if not cands:
            raise CBuildError("linker produced no .map file")
        map_file = cands[-1]
    sections, symbols = parse_map(map_file.read_text(errors="replace"))

    import pc128
    segs, entry = pc128.parse_decb(binary.read_bytes())
    segs = [(a, bytes(d)) for a, d in segs]
    end = max((a + len(d) for a, d in segs), default=org)
    pend = symbols.get("program_end")
    if pend is not None:
        end = max(end, pend)

    lines = []
    for objname, lst, src, is_c in user:
        if lst.exists():
            lines += parse_object_listing(lst.read_text(errors="replace"), objname, sections, src, is_c)
    for objname, (lst, src) in library_listings().items():
        lines += parse_object_listing(lst.read_text(errors="replace"), objname, sections, src,
                                      src.suffix.lower() == ".c")
    lines.sort(key=lambda l: l.addr)

    syms = {}
    for name, addr in symbols.items():
        if "@" in name or name.startswith(("l_", "s_")):
            continue
        syms[name] = addr
        if name.startswith("_") and len(name) > 1 and name[1:] not in symbols:
            syms[name[1:]] = addr

    (binary.with_suffix(".sym")).write_text("".join("%-24s %04X\n" % (n, a) for n, a in sorted(syms.items(), key=lambda t: t[1])))
    (binary.with_suffix(".lines")).write_text("".join("%04X %s:%d\n" % (l.addr, l.file, l.line) for l in lines))
    res = CBuildResult(segs, entry, binary, lines, syms, "\n".join(msgs), map_file, org, end)
    if end > limit:
        raise CBuildError("program ends at $%04X, past the limit $%04X" % (end, limit))
    return res


# --------------------------------------------------------------------------- CLI

def put_on_floppy(binary: Path, image: Path, name=None):
    fdtool = ROOT / "tools" / "fdtool.py"
    name = (name or binary.stem).upper()[:8]
    cmd = [sys.executable, fdtool, "put", image, binary, "--as", name + ".BIN"]
    return _run(cmd)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="*", type=Path, help=".c / .asm sources (first one holds main())")
    ap.add_argument("-o", "--output", type=Path, help="output .bin (default build/pc128-c/<main>/<main>.bin)")
    ap.add_argument("--org", help="load/entry address, hex (default 6000)")
    ap.add_argument("--limit", help="highest address the program may reach, hex (default 9F00)")
    ap.add_argument("-D", dest="defines", action="append", default=[], help="preprocessor define")
    ap.add_argument("-O", dest="opt", choices=["0", "1", "2"], help="CMOC optimisation level")
    ap.add_argument("--lib", action="store_true", help="(re)build libolivetti.a and exit")
    ap.add_argument("--run", action="store_true", help="run the program in the emulator (pc128.py c)")
    ap.add_argument("--fd", type=Path, help="copy the binary onto this .fd floppy image")
    ap.add_argument("--map", action="store_true", help="print the symbol map")
    ap.add_argument("-v", "--verbose", action="store_true")
    a, rest = ap.parse_known_args(argv)
    try:
        if a.lib:
            print(build_library(force=True, verbose=a.verbose))
            if not a.sources:
                return 0
        if not a.sources:
            ap.error("no sources")
        res = build(a.sources, a.output, _hex(a.org) if a.org else None, _hex(a.limit) if a.limit else None,
                    ["-O" + a.opt] if a.opt else [], a.defines, a.verbose)
    except CBuildError as e:
        print("pc128cc: error:\n%s" % e, file=sys.stderr)
        return 1
    if res.warnings:
        print(res.warnings, file=sys.stderr)
    print("%s: $%04X-$%04X (%d bytes), EXEC &H%04X" % (res.binary, res.org, res.end - 1, res.size, res.entry or res.org))
    if a.map:
        for n, v in sorted(res.symbols.items(), key=lambda t: t[1]):
            if not n.startswith("_"):
                print("  %04X %s" % (v, n))
    if a.fd:
        print(put_on_floppy(res.binary, a.fd))
    if a.run:
        cmd = [sys.executable, ROOT / "pc128.py", "c", a.sources[0], *rest]
        return subprocess.call([str(c) for c in cmd])
    return 0


if __name__ == "__main__":
    sys.exit(main())
