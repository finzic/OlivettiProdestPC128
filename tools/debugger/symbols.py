"""Address -> location/symbol correlation for the PC128 (MAME pro128 driver).

A CPU address only means something together with the current bank configuration. `Locator`
turns (address, banks) into a Location: which ROM page / RAM page / I/O block the CPU sees there,
plus the offset inside the 64 KB BASIC+monitor ROM image (pro128.iw01 + basico.iw02).

Symbols are keyed by *space* so a name only matches when the right page is mapped:

    rom:3000        offset in the 64 KB ROM image
    mon0:F6D9       monitor page 0 at $F000-$FFFF   (= rom:3000 + $6D9)
    mon1:F19F       monitor page 1
    b128.0:D808     BASIC 128 page 0 at $B000-$EFFF (= rom:8000 + ...)
    b128.1:D04B     BASIC 128 page 1
    b1.0:C000       BASIC 1 page 0 at $C000-$EFFF
    b1.1:C000       BASIC 1 page 1
    ext:A004        any floppy-controller extension ROM at $A000-$A7BF
    cd351.2:A112    one specific CD90-351 ROM page
    21C0            plain CPU address (RAM, I/O, or anything not ROM-specific)
    p3:6000         RAM page 3 at $6000-$9FFF (BASIC BANK 2)

Symbol file lines:  `<key> <NAME> [; comment]`, '#' or ';' start comments.
"""
from __future__ import annotations

import bisect
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BUILTIN_SYM = HERE / "symbols" / "pc128.sym"

# CPU base address -> ROM image offset for each named ROM page
ROM_PAGES = {
    "b1.0": (0xC000, 0x0000, 0x3000),
    "mon0": (0xF000, 0x3000, 0x1000),
    "b1.1": (0xC000, 0x4000, 0x3000),
    "mon1": (0xF000, 0x7000, 0x1000),
    "b128.0": (0xB000, 0x8000, 0x4000),
    "b128.1": (0xB000, 0xC000, 0x4000),
}

EXT_ROMS = {"cd351.0": "cd-351-0.rom", "cd351.1": "cd-351-1.rom", "cd351.2": "cd-351-2.rom",
            "cd351.3": "cd-351-3.rom", "cd640": "cd90-640.rom"}


def rom_page_of(offset):
    for name, (base, off, size) in ROM_PAGES.items():
        if off <= offset < off + size:
            return name, base + offset - off
    return None, None


@dataclass
class Location:
    addr: int
    kind: str              # vram, ram, page, io, ext, rom, cart, unknown
    space: str             # symbol space: "ram", "p3", "mon1", "b128.1", "cd351.0", "io", ...
    rom_offset: int | None = None
    detail: str = ""

    def describe(self):
        s = self.detail or self.space
        if self.rom_offset is not None:
            s += " (rom:%04X)" % self.rom_offset
        return s


class Locator:
    """Maps a CPU address to what is actually mapped there, given MAME bank entries."""

    def __init__(self, ext_rom=None):
        self.ext_rom = ext_rom     # name from EXT_ROMS or None (set by identify_ext)

    def locate(self, addr, banks):
        addr &= 0xFFFF
        b = banks or {}
        if addr < 0x2000:
            return Location(addr, "vram", "vram", detail="video RAM (%s)" % ("colour" if b.get("bank1", 0) else "pixels"))
        if addr < 0x6000:
            return Location(addr, "ram", "ram", detail="RAM")
        if addr < 0xA000:
            page = b.get("bank7", 0) if addr < 0x8000 else b.get("bank8", 0)
            basic = " = BASIC BANK %d" % (page - 1) if 2 <= page <= 7 else ""
            return Location(addr, "page", "p%d" % page, detail="RAM page %d%s" % (page, basic))
        if addr < 0xA7C0:
            name = self.ext_rom or "ext"
            return Location(addr, "ext", name, detail="extension ROM %s" % name)
        if addr < 0xA800:
            return Location(addr, "io", "io", detail="I/O")
        if addr < 0xB000:
            return Location(addr, "unknown", "unmapped", detail="unmapped")
        if addr < 0xF000:
            e = b.get("bank10" if addr < 0xC000 else "bank11", 0)
            off = None
            if addr < 0xC000:
                if e == 5:
                    off = 0x3000 + addr - 0xB000
                elif e in (6, 7):
                    off = 0x8000 + (e - 6) * 0x4000 + addr - 0xB000
            else:
                if e in (4, 5):
                    off = (e - 4) * 0x4000 + addr - 0xC000
                elif e in (6, 7):
                    off = 0x9000 + (e - 6) * 0x4000 + addr - 0xC000
            if e >= 8:
                return Location(addr, "ram", "cram%d" % (e - 8), detail="RAM in cartridge space (page %d)" % (e - 8))
            if off is None:
                return Location(addr, "cart", "cart", detail="cartridge (bank %d)" % e)
            page, _ = rom_page_of(off)
            return Location(addr, "rom", page or "rom", off, detail="ROM %s" % page)
        e = b.get("bank9", 0)
        off = 0x3000 + e * 0x4000 + addr - 0xF000
        return Location(addr, "rom", "mon%d" % e, off, detail="monitor ROM mon%d" % e)

    def identify_ext(self, sample, roms_dir):
        """Pick the extension ROM whose start matches `sample` (bytes read at $A000)."""
        self.ext_rom = None
        if not sample or not roms_dir:
            return None
        for name, fn in EXT_ROMS.items():
            p = Path(roms_dir) / fn
            if p.exists() and p.read_bytes()[:len(sample)] == bytes(sample):
                self.ext_rom = name
                break
        return self.ext_rom


@dataclass
class Symbol:
    space: str
    addr: int              # CPU address (rom-space symbols are converted to page:CPU address)
    name: str
    comment: str = ""
    size: int | None = None


KEY_RE = re.compile(r"^(?:(?P<space>[A-Za-z][\w.]*):)?\$?(?P<addr>[0-9A-Fa-f]{1,5})$")


def parse_key(key):
    m = KEY_RE.match(key)
    if not m:
        raise ValueError("bad symbol address %r" % key)
    space = (m.group("space") or "any").lower()
    addr = int(m.group("addr"), 16)
    if space == "rom":
        page, cpu = rom_page_of(addr)
        if page is None:
            raise ValueError("ROM offset out of range: %s" % key)
        return page, cpu
    if space in ("ram", "cpu"):
        space = "any"
    return space, addr & 0xFFFF


class SymbolTable:
    def __init__(self):
        self.by_space = {}       # space -> {addr: [Symbol]}
        self._sorted = {}
        self.by_name = {}

    def add(self, space, addr, name, comment="", size=None):
        sym = Symbol(space, addr, name, comment, size)
        syms = self.by_space.setdefault(space, {}).setdefault(addr, [])
        syms[:] = [s for s in syms if s.name != name] + [sym]
        self._sorted.pop(space, None)
        self.by_name[name.upper()] = sym
        return sym

    def _addrs(self, space):
        if space not in self._sorted:
            self._sorted[space] = sorted(self.by_space.get(space, {}))
        return self._sorted[space]

    def load_file(self, path):
        n = 0
        for raw in Path(path).read_text(errors="replace").splitlines():
            line = raw.strip()
            if not line or line[0] in "#;":
                continue
            text, _, comment = line.partition(";")
            parts = text.split()
            if len(parts) < 2:
                continue
            space, addr = parse_key(parts[0])
            self.add(space, addr, parts[1], comment.strip())
            n += 1
        return n

    def load_lwasm_symbols(self, path, space="any"):
        """lwasm --symbol-dump output: `NAME EQU $1234` lines."""
        n = 0
        for line in Path(path).read_text(errors="replace").splitlines():
            m = re.match(r"^\s*([A-Za-z_.@?$][\w.@?$]*)\s+(?:EQU|equ)\s+\$?([0-9A-Fa-f]+)", line)
            if m:
                self.add(space, int(m.group(2), 16) & 0xFFFF, m.group(1), "program")
                n += 1
        return n

    def spaces_for(self, loc):
        if loc.kind == "rom":
            return [loc.space]
        if loc.kind == "ext":
            return [loc.space, "ext"] if loc.space != "ext" else ["ext"]
        if loc.kind == "page":
            return [loc.space, "any"]
        return ["any"]

    def lookup(self, loc, max_dist=0x200):
        """Nearest symbol at or before loc.addr in a space visible at that location: (Symbol, offset)."""
        best = None
        for sp in self.spaces_for(loc):
            addrs = self._addrs(sp)
            i = bisect.bisect_right(addrs, loc.addr) - 1
            if i < 0:
                continue
            addr = addrs[i]
            sym = self.by_space[sp][addr][0]
            off = loc.addr - addr
            limit = sym.size if sym.size is not None else max_dist
            if off >= limit and off != 0:
                continue
            if best is None or off < best[1]:
                best = (sym, off)
        return best

    def exact(self, loc):
        r = self.lookup(loc, max_dist=1)
        return r[0] if r and r[1] == 0 else None

    def find(self, name):
        return self.by_name.get(name.upper())

    def names_like(self, pattern):
        rx = re.compile(pattern, re.I)
        out = []
        for d in self.by_space.values():
            out += [s for syms in d.values() for s in syms if rx.search(s.name)]
        return sorted(out, key=lambda s: (s.space, s.addr))


def fmt_symbol(hit):
    if not hit:
        return ""
    sym, off = hit
    return sym.name if off == 0 else "%s+$%X" % (sym.name, off)


# ------------------------------------------------------------ ROM-derived --
def load_rom_image(roms_dir):
    d = Path(roms_dir)
    a, b = d / "pro128.iw01", d / "basico.iw02"
    if a.exists() and b.exists():
        data = a.read_bytes() + b.read_bytes()
        if len(data) == 0x10000:
            return data
    return None


def basic_keyword_symbols(rom, table=0xB0E5, names=0xD808):
    """Statement keyword handlers: names in b128.0 at $D808, dispatch table in b128.1 at $B0E5."""
    if not rom:
        return []
    rd0 = lambda a: rom[0x8000 + a - 0xB000]
    rd1 = lambda a: rom[0xC000 + a - 0xB000]
    words, cur, a = [], b"", names
    while a < 0xEFFF and len(words) < 0x80:
        c = rd0(a)
        a += 1
        if c == 0:
            break
        cur += bytes([c & 0x7F])
        if c & 0x80:
            words.append(cur.decode("latin-1"))
            cur = b""
    out = []
    for i, w in enumerate(words):
        ta = table + 2 * i
        if ta + 1 >= 0xF000:
            break
        target = (rd1(ta) << 8) | rd1(ta + 1)
        if target in (0xB8F4,) or not 0xB000 <= target < 0xF000:
            continue
        name = "KW_" + re.sub(r"[^A-Z0-9]", "_", w.upper()).strip("_")
        out.append(("b128.1", target, name, "BASIC statement %s (token $%02X)" % (w, 0x80 + i)))
    return out


def build_default(cfg=None, extra_files=()):
    """Builtin symbols + ROM-derived BASIC keyword handlers + user files."""
    st = SymbolTable()
    if BUILTIN_SYM.exists():
        st.load_file(BUILTIN_SYM)
    roms_dir = None
    if cfg and cfg.get("rompath"):
        rp = Path(cfg["rompath"])
        roms_dir = (rp if rp.is_absolute() else ROOT / rp) / cfg.get("machine", "pro128")
    if roms_dir is None:
        roms_dir = ROOT / "roms" / "pro128"
    rom = load_rom_image(roms_dir)
    for sp, addr, name, comment in basic_keyword_symbols(rom):
        if not st.find(name):
            st.add(sp, addr, name, comment)
    for f in extra_files:
        p = Path(f)
        if p.suffix.lower() in (".json",):
            for k, v in json.loads(p.read_text()).items():
                st.add(*parse_key(k), v)
        elif "EQU" in p.read_text(errors="replace")[:4000].upper():
            st.load_lwasm_symbols(p)
        else:
            st.load_file(p)
    return st, roms_dir, rom
