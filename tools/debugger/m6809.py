"""MC6809 disassembler (Motorola syntax, lwasm compatible). Standard library only.

    disassemble(read, addr) -> Insn          read(addr) returns one byte
    disassemble_bytes(data, addr) -> Insn

PC128 / MO6 convention: SWI is followed by a monitor service byte, so it is decoded as a
2-byte instruction ("SWI" + "FCB $xx") with the service name in the comment.
"""
from dataclasses import dataclass, field

# Monitor SWI services (docs/pc128-system-calls.md); bit 7 set = JMP-style variant.
SWI_SERVICES = {
    0x00: "MENU", 0x02: "PUTC", 0x04: "FRM0", 0x06: "FRM1", 0x08: "BIIP", 0x0A: "GETC",
    0x0C: "KTST", 0x0E: "DRAW", 0x10: "PLOT", 0x12: "CHPL", 0x14: "GETP", 0x16: "LPIN",
    0x18: "GETL", 0x1A: "GETS", 0x1C: "JOYS", 0x1E: "NOTE", 0x20: "K7CO", 0x22: "K7MO",
    0x24: "PRCO", 0x26: "DKCO", 0x28: "DKBOOT", 0x2A: "DKFMT", 0x2C: "ALLOB", 0x2E: "ALLOD",
    0x30: "ECRSE", 0x32: "FINTR", 0x34: "LECFA", 0x36: "MAJCL", 0x38: "RECFI", 0x3A: "RECUP",
    0x3C: "SETP", 0x3E: "MOUSEB", 0x40: "MOUSE", 0x42: "RSCO",
}


def swi_service_name(code):
    name = SWI_SERVICES.get(code & 0x7F)
    if name is None:
        return None
    return ("JMP_" + name) if code & 0x80 else name


# mode: inh imm8 imm16 dir ext idx rel8 rel16 tfr pshs pshu
_P1 = {}
_P2 = {}
_P3 = {}


def _mem_group(base, names, table=_P1):
    """names[i] for opcodes base+i in direct/indexed/extended form (base = 0x00 / 0x60 / 0x70 style)."""
    for i, n in enumerate(names):
        if n:
            table[base + i] = (n, None)


def _alu(table, base, names, imm16=()):
    # base = 0x80 (A) or 0xC0 (B): imm, +0x10 dir, +0x20 idx, +0x30 ext
    for i, n in enumerate(names):
        if not n:
            continue
        imm_mode = "imm16" if i in imm16 else "imm8"
        if n in ("STA", "STB", "STD", "STX", "STU", "JSR", "STY", "STS"):
            imm_mode = None
        if imm_mode:
            table[base + i] = (n, imm_mode)
        table[base + 0x10 + i] = (n, "dir")
        table[base + 0x20 + i] = (n, "idx")
        table[base + 0x30 + i] = (n, "ext")


_RMW = ["NEG", None, None, "COM", "LSR", None, "ROR", "ASR", "ASL", "ROL", "DEC", None, "INC", "TST", "JMP", "CLR"]
for _i, _n in enumerate(_RMW):
    if _n:
        _P1[0x00 + _i] = (_n, "dir")
        _P1[0x60 + _i] = (_n, "idx")
        _P1[0x70 + _i] = (_n, "ext")
        if _n != "JMP":
            _P1[0x40 + _i] = (_n + "A", "inh")
            _P1[0x50 + _i] = (_n + "B", "inh")

_P1.update({
    0x12: ("NOP", "inh"), 0x13: ("SYNC", "inh"), 0x16: ("LBRA", "rel16"), 0x17: ("LBSR", "rel16"),
    0x19: ("DAA", "inh"), 0x1A: ("ORCC", "imm8"), 0x1C: ("ANDCC", "imm8"), 0x1D: ("SEX", "inh"),
    0x1E: ("EXG", "tfr"), 0x1F: ("TFR", "tfr"),
    0x30: ("LEAX", "idx"), 0x31: ("LEAY", "idx"), 0x32: ("LEAS", "idx"), 0x33: ("LEAU", "idx"),
    0x34: ("PSHS", "pshs"), 0x35: ("PULS", "pshs"), 0x36: ("PSHU", "pshu"), 0x37: ("PULU", "pshu"),
    0x39: ("RTS", "inh"), 0x3A: ("ABX", "inh"), 0x3B: ("RTI", "inh"), 0x3C: ("CWAI", "imm8"),
    0x3D: ("MUL", "inh"), 0x3F: ("SWI", "swi"),
    0x8D: ("BSR", "rel8"),
})
_BR = ["BRA", "BRN", "BHI", "BLS", "BCC", "BCS", "BNE", "BEQ", "BVC", "BVS", "BPL", "BMI", "BGE", "BLT", "BGT", "BLE"]
for _i, _n in enumerate(_BR):
    _P1[0x20 + _i] = (_n, "rel8")
    if _i:
        _P2[0x20 + _i] = ("L" + _n, "rel16")

_alu(_P1, 0x80, ["SUBA", "CMPA", "SBCA", "SUBD", "ANDA", "BITA", "LDA", "STA",
                 "EORA", "ADCA", "ORA", "ADDA", "CMPX", "JSR", "LDX", "STX"], imm16=(3, 0xC, 0xE))
_P1[0x8D] = ("BSR", "rel8")
_alu(_P1, 0xC0, ["SUBB", "CMPB", "SBCB", "ADDD", "ANDB", "BITB", "LDB", "STB",
                 "EORB", "ADCB", "ORB", "ADDB", "LDD", "STD", "LDU", "STU"], imm16=(3, 0xC, 0xE))
_P2[0x3F] = ("SWI2", "inh")
_P3[0x3F] = ("SWI3", "inh")
for _base, _n in ((0x83, "CMPD"), (0x8C, "CMPY"), (0x8E, "LDY")):
    _P2[_base] = (_n, "imm16")
    for _k, _m in ((0x10, "dir"), (0x20, "idx"), (0x30, "ext")):
        _P2[_base + _k] = (_n, _m)
for _k, _m in ((0x10, "dir"), (0x20, "idx"), (0x30, "ext")):
    _P2[0x8F + _k] = ("STY", _m)
    _P2[0xCF + _k] = ("STS", _m)
    _P2[0xCE + _k] = ("LDS", _m)
_P2[0xCE] = ("LDS", "imm16")
for _base, _n in ((0x83, "CMPU"), (0x8C, "CMPS")):
    _P3[_base] = (_n, "imm16")
    for _k, _m in ((0x10, "dir"), (0x20, "idx"), (0x30, "ext")):
        _P3[_base + _k] = (_n, _m)

_TFR_REGS = {0: "D", 1: "X", 2: "Y", 3: "U", 4: "S", 5: "PC", 8: "A", 9: "B", 0xA: "CC", 0xB: "DP"}
_IDX_REGS = ["X", "Y", "U", "S"]
_PSH_BITS = ["CC", "A", "B", "DP", "X", "Y", None, "PC"]

CALLS = {"JSR", "BSR", "LBSR", "SWI", "SWI2", "SWI3"}
RETURNS = {"RTS", "RTI"}
JUMPS = {"JMP", "BRA", "LBRA"}


@dataclass
class Insn:
    addr: int
    length: int
    mnemonic: str
    operand: str = ""
    comment: str = ""
    target: int | None = None          # branch/jump/memory target if statically known
    raw: bytes = b""
    flags: set = field(default_factory=set)   # "call", "return", "jump", "branch", "invalid"

    @property
    def text(self):
        s = self.mnemonic + (" " + self.operand if self.operand else "")
        return s

    def __str__(self):
        hexb = " ".join("%02X" % b for b in self.raw)
        s = "%04X  %-14s %s" % (self.addr, hexb, self.text)
        if self.comment:
            s = "%-40s ; %s" % (s, self.comment)
        return s


def _s8(v):
    return v - 0x100 if v & 0x80 else v


def _s16(v):
    return v - 0x10000 if v & 0x8000 else v


def _h8(v):
    return "$%02X" % v


def _h16(v):
    return "$%04X" % v


def _signed(v):
    return ("-$%X" % -v) if v < 0 else ("$%X" % v)


def disassemble(read, addr):
    """Decode one instruction at addr. read(a) -> int byte."""
    pos = addr
    raw = []

    def fetch():
        nonlocal pos
        b = read(pos & 0xFFFF) & 0xFF
        raw.append(b)
        pos += 1
        return b

    def fetch16():
        hi = fetch()
        return (hi << 8) | fetch()

    op = fetch()
    table = _P1
    if op == 0x10:
        table, op = _P2, fetch()
    elif op == 0x11:
        table, op = _P3, fetch()
    entry = table.get(op)
    if entry is None:
        return Insn(addr, len(raw), "FCB", ",".join(_h8(b) for b in raw), "invalid opcode",
                    raw=bytes(raw), flags={"invalid"})
    name, mode = entry
    operand, comment, target, flags = "", "", None, set()

    if mode == "inh" or mode is None:
        pass
    elif mode == "imm8":
        operand = "#" + _h8(fetch())
    elif mode == "imm16":
        operand = "#" + _h16(fetch16())
    elif mode == "dir":
        v = fetch()
        operand = "<" + _h8(v)
    elif mode == "ext":
        target = fetch16()
        operand = (">" if target < 0x100 else "") + _h16(target)
    elif mode == "rel8":
        off = _s8(fetch())
        target = (pos + off) & 0xFFFF
        operand = _h16(target)
    elif mode == "rel16":
        off = _s16(fetch16())
        target = (pos + off) & 0xFFFF
        operand = _h16(target)
    elif mode == "tfr":
        pb = fetch()
        if (pb >> 4) not in _TFR_REGS or (pb & 15) not in _TFR_REGS:
            return Insn(addr, len(raw), "FCB", ",".join(_h8(b) for b in raw), "invalid register",
                        raw=bytes(raw), flags={"invalid"})
        operand = "%s,%s" % (_TFR_REGS[pb >> 4], _TFR_REGS[pb & 15])
    elif mode in ("pshs", "pshu"):
        pb = fetch()
        other = "U" if mode == "pshs" else "S"
        regs = [(_PSH_BITS[i] or other) for i in range(8) if pb & (1 << i)]
        operand = ",".join(regs)
    elif mode == "swi":
        svc = fetch()
        operand = _h8(svc)
        nm = swi_service_name(svc)
        comment = "monitor " + nm if nm else "monitor service ?"
    elif mode == "idx":
        pb = fetch()
        reg = _IDX_REGS[(pb >> 5) & 3]
        if not pb & 0x80:
            operand = "%d,%s" % (pb & 0x1F if not pb & 0x10 else (pb & 0x1F) - 32, reg)
        else:
            ind = bool(pb & 0x10)
            m = pb & 0x0F
            if m == 0x0:
                operand = ",%s+" % reg
            elif m == 0x1:
                operand = ",%s++" % reg
            elif m == 0x2:
                operand = ",-%s" % reg
            elif m == 0x3:
                operand = ",--%s" % reg
            elif m == 0x4:
                operand = ",%s" % reg
            elif m == 0x5:
                operand = "B,%s" % reg
            elif m == 0x6:
                operand = "A,%s" % reg
            elif m == 0x8:
                v = _s8(fetch())
                operand = "%s%s,%s" % ("<" if -16 <= v <= 15 else "", _signed(v), reg)
            elif m == 0x9:
                v = _s16(fetch16())
                operand = "%s%s,%s" % (">" if -128 <= v <= 127 else "", _signed(v), reg)
            elif m == 0xB:
                operand = "D,%s" % reg
            elif m == 0xC:
                off = _s8(fetch())
                target = (pos + off) & 0xFFFF
                operand = "<%s,PCR" % _h16(target)
            elif m == 0xD:
                off = _s16(fetch16())
                target = (pos + off) & 0xFFFF
                operand = ">%s,PCR" % _h16(target)
            elif m == 0xF and ind:
                target = fetch16()
                operand = _h16(target)
            else:
                return Insn(addr, len(raw), "FCB", ",".join(_h8(b) for b in raw), "invalid indexed mode",
                            raw=bytes(raw), flags={"invalid"})
            if ind:
                if m in (0x0, 0x2):
                    return Insn(addr, len(raw), "FCB", ",".join(_h8(b) for b in raw),
                                "invalid indexed mode", raw=bytes(raw), flags={"invalid"})
                operand = "[" + operand + "]"
                if m != 0xF:
                    target = None if m not in (0xC, 0xD) else target
    if name in CALLS:
        flags.add("call")
    if name in RETURNS or (name in ("PULS", "PULU") and "PC" in operand.split(",")):
        flags.add("return")
    if name in JUMPS or name in ("LBRA",):
        flags.add("jump")
    if mode in ("rel8", "rel16") and name not in ("BRA", "LBRA", "BSR", "LBSR"):
        flags.add("branch")
    return Insn(addr, len(raw), name, operand, comment, target, bytes(raw), flags)


def disassemble_bytes(data, addr, base=None):
    base = addr if base is None else base

    def read(a):
        i = (a - base) & 0xFFFF
        return data[i] if i < len(data) else 0
    return disassemble(read, addr)


def disassemble_range(read, addr, count):
    out = []
    for _ in range(count):
        ins = disassemble(read, addr)
        out.append(ins)
        addr = (addr + ins.length) & 0xFFFF
    return out
