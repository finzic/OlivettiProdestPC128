"""Debugger tests (tools/debugger).

Offline tests need lwasm (and the ROMs for the ROM-correlation tests; skipped if missing).
Live tests boot MAME headless and take a minute or two: PC128_LIVE_TESTS=1 python3 -m unittest tests.test_debugger
"""
import base64
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "debugger"))

import pc128  # noqa: E402
import m6809  # noqa: E402
import asm as asmlib  # noqa: E402
import symbols as symlib  # noqa: E402

CFG = pc128.load_config()
HAVE_LWASM = Path(CFG.get("lwasm", "")).is_file() or shutil.which(CFG.get("lwasm", "lwasm")) is not None
try:
    symlib.load_rom_image(symlib.build_default(CFG)[1])
    HAVE_ROMS = True
except Exception:
    HAVE_ROMS = False
LIVE = os.environ.get("PC128_LIVE_TESTS") == "1"

PROGRAM = """        ORG $9000
start   LDX #msg
loop    LDB ,X+
        BEQ done
        SWI
        FCB $02
        BRA loop
done    LDA #1
        STA $9F01
        RTS
msg     FCC "HI"
        FCB 0
        END start
"""

# Every addressing mode family, page 2/3 opcodes, inter-register and stack operations.
ROUND_TRIP = """
 NEG <$10
 LDA #$12
 LDD #$1234
 LDX $1234
 STA ,X
 LDA 5,Y
 LDA -16,U
 LDA 100,S
 LDA 1000,X
 LDA ,X+
 LDA ,X++
 LDA ,-Y
 LDA ,--S
 LDA A,X
 LDA B,Y
 LDA D,U
 LDA [,X]
 LDA [1000,Y]
 LDA [$1234]
 LDA 10,PCR
 LEAX 300,PCR
 TFR X,Y
 EXG A,B
 PSHS A,B,X,PC
 PULU CC,DP,Y
 CMPY #$1234
 LDS #$5FFF
 CMPU $2000
 SWI2
 SWI3
 LBRA $9000
 LBEQ $9000
 BSR $9000
 JSR [$FFFE]
 ANDCC #$EF
 ORCC #$50
 CWAI #$EF
 MUL
 SEX
 ABX
 DAA
 RTI
"""


@unittest.skipUnless(HAVE_LWASM, "lwasm not available")
class AssemblerTests(unittest.TestCase):
    def test_disassembler_round_trip(self):
        res = asmlib.assemble_snippet(ROUND_TRIP, 0x9000, CFG)
        (org, data), = res.segments
        texts, a = [], org
        while a < org + len(data):
            ins = m6809.disassemble_bytes(data, a, org)
            self.assertNotIn("invalid", ins.flags, ins.text)
            texts.append(ins.text)
            a += ins.length
        again = asmlib.assemble_snippet("\n".join(texts), 0x9000, CFG)
        self.assertEqual(again.segments[0][1], data, "\n".join(texts))

    def test_swi_service_and_labels(self):
        res = asmlib.assemble_snippet("LDA #$41 | SWI PUTC | loop: BRA loop", 0x9F80, CFG,
                                      symlib.build_default(CFG)[0] if HAVE_ROMS else None)
        self.assertEqual(res.segments, [(0x9F80, bytes.fromhex("86413F0220FE"))])
        ins = m6809.disassemble_bytes(bytes.fromhex("3F02"), 0x9000)
        self.assertEqual(ins.length, 2)
        self.assertIn("SWI", ins.text)

    def test_assemble_file_source_map(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "prog.asm"
            p.write_text(PROGRAM)
            res = asmlib.assemble_file(p, CFG)
        self.assertEqual(res.entry, 0x9000)
        self.assertEqual(res.symbols["loop"], 0x9003)
        code = {(l.line, l.addr) for l in res.lines if l.data}
        self.assertIn((2, 0x9000), code)
        self.assertIn((5, 0x9007), code)
        self.assertTrue(all(l.file == str(p.resolve()) for l in res.lines if l.data))

    def test_bad_source_reports_error(self):
        with self.assertRaises(asmlib.AsmError):
            asmlib.assemble_snippet("LDQ #1", 0x9000, CFG)


class ParsingTests(unittest.TestCase):
    def test_hex_bytes(self):
        self.assertEqual(asmlib.parse_hex_bytes("86 01 B7A7C0"), bytes.fromhex("8601B7A7C0"))
        self.assertEqual(asmlib.parse_hex_bytes("$86,$1"), bytes.fromhex("8601"))
        with self.assertRaises(asmlib.AsmError):
            asmlib.parse_hex_bytes("ZZ")

    def test_string(self):
        self.assertEqual(asmlib.parse_string(r'"HI\n\0"'), b"HI\x0d\x00")
        self.assertEqual(asmlib.parse_string(r'"\x41B"'), b"AB")

    def test_symbol_table(self):
        t = symlib.SymbolTable()
        t.add("mon0", 0xF6D9, "PUTC")
        t.add("any", 0x9000, "start")
        hit = t.lookup(symlib.Location(0xF6DC, "rom", "mon0"))
        self.assertEqual(symlib.fmt_symbol(hit), "PUTC+$3")
        self.assertIsNone(t.lookup(symlib.Location(0xF6DC, "rom", "mon1")))
        self.assertEqual(symlib.fmt_symbol(t.lookup(symlib.Location(0x9002, "page", "p7"))), "start+$2")

    def test_locator_banking(self):
        loc = symlib.Locator()
        b = {"bank7": 7, "bank8": 7, "bank9": 0, "bank10": 7, "bank11": 7}
        self.assertEqual(loc.locate(0x9000, b).space, "p7")
        self.assertEqual(loc.locate(0xD01E, b).space, "b128.1")
        self.assertEqual(loc.locate(0xD01E, b).rom_offset, 0xE01E)
        self.assertEqual(loc.locate(0xF6D9, b).space, "mon0")
        self.assertEqual(loc.locate(0xF6D9, dict(b, bank9=1)).space, "mon1")
        self.assertEqual(loc.locate(0xA7C0, b).kind, "io")


@unittest.skipUnless(HAVE_ROMS, "PC128 ROMs not available")
class RomSymbolTests(unittest.TestCase):
    def test_default_symbols(self):
        table, _, rom = symlib.build_default(CFG)
        self.assertEqual(table.find("PUTC").addr, 0xF6D9)
        self.assertIsNotNone(table.find("KW_PRINT"), "BASIC keyword handlers decoded from the ROM")
        loc = symlib.Location(0xD01E, "rom", "b128.1", 0xE01E)
        self.assertEqual(symlib.fmt_symbol(table.lookup(loc)), "B_SETLINE")
        self.assertEqual(rom[0xE01E:0xE020], bytes.fromhex("DF31"))      # STU <$31


class DapOfflineTests(unittest.TestCase):
    def test_initialize_and_framing(self):
        import dap
        req = json.dumps({"seq": 1, "type": "request", "command": "initialize", "arguments": {}}).encode()
        rin = io.BytesIO(b"Content-Length: %d\r\n\r\n" % len(req) + req)
        out = io.BytesIO()
        dap.Adapter(rin, out).run()
        head, _, body = out.getvalue().partition(b"\r\n\r\n")
        self.assertEqual(int(head.split(b":")[1]), len(body))
        msg = json.loads(body)
        self.assertTrue(msg["success"])
        self.assertTrue(msg["body"]["supportsDisassembleRequest"])

    def test_basic_source_map(self):
        from commands import Session
        m = Session.parse_basic_source("10 PRINT\n\n 20 A=1\r\nREM\n30 END\n")
        self.assertEqual(m, {10: 1, 20: 3, 30: 5})


class MediaTests(unittest.TestCase):
    """Media choices shared by pc128.py, the REPL, the DAP adapter and MCP (same as tools/run-mame.sh)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fd = Path(self.tmp.name) / "a.fd"
        self.fd.write_bytes(b"\0" * 16)
        self.cfg = dict(CFG, floppy=None, floppy2=None, cassette=None, cartridge=None)

    def tearDown(self):
        self.tmp.cleanup()

    def test_media_from_kind(self):
        self.assertEqual(pc128.media_from_kind("floppy351", "a.fd", "b.fd"),
                         {"floppy": "a.fd", "floppy2": "b.fd", "controller": "cd90_351"})
        self.assertEqual(pc128.media_from_kind("floppy", "a.fd")["controller"], "cd90_640")
        self.assertEqual(pc128.media_from_kind("cassette", "t.k7"), {"cassette": "t.k7"})
        self.assertEqual(pc128.media_from_kind("cartridge", "c.rom"), {"cartridge": "c.rom"})
        self.assertEqual(pc128.media_from_kind("none", ""), {})
        with self.assertRaises(ValueError):
            pc128.media_from_kind("tape", "x")

    def test_mame_media_args(self):
        fd = str(self.fd)
        self.assertEqual(pc128.mame_media_args(self.cfg, {}), [])
        self.assertEqual(pc128.mame_media_args(self.cfg, {"floppy": fd, "floppy2": None}),
                         ["-extension", "cd90_351", "-flop1", fd])
        args = pc128.mame_media_args(self.cfg, {"floppy": fd, "floppy2": fd})
        self.assertIn("-flop2", args)
        self.assertEqual(pc128.mame_media_args(self.cfg, {"floppy": fd, "controller": "cd90_640"})[:2],
                         ["-extension", "cd90_640"])
        self.assertEqual(pc128.mame_media_args(self.cfg, {"cartridge": fd}), ["-cart", fd])
        for bad in ({"floppy": fd + ".missing"},
                    {"floppy": fd, "floppy2": fd, "controller": "cd90_640"},
                    {"floppy": fd, "controller": "cd90_999"}):
            with self.assertRaises(ValueError):
                pc128.mame_media_args(self.cfg, bad)

    def test_dap_launch_media(self):
        import dap
        self.assertEqual(dap.launch_media({"media": "floppy351", "image": "a.fd", "image2": ""}),
                         {"floppy": "a.fd", "floppy2": "", "controller": "cd90_351"})
        self.assertEqual(dap.launch_media({"floppy": "a.fd", "floppyController": "cd90_640", "cassette": ""}),
                         {"floppy": "a.fd", "controller": "cd90_640"})

    def test_bank_sort_with_device_banks(self):
        from commands import bank_sort_key
        b = {"bank10": 7, "extension:cd90_351:rom_bank": 0, "bank1": 0, "bank9": 1}
        self.assertEqual([k for k, _ in sorted(b.items(), key=bank_sort_key)],
                         ["bank1", "bank9", "bank10", "extension:cd90_351:rom_bank"])


@unittest.skipUnless(LIVE, "set PC128_LIVE_TESTS=1 to boot MAME")
class LiveTests(unittest.TestCase):
    def setUp(self):
        from commands import Session
        self.s = Session()
        self.s._quiet = True
        self.s.start(window=False, log=lambda *_: None)
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.s.close()
        self.tmp.cleanup()

    def test_asm_breakpoints_and_stepping(self):
        s = self.s
        p = Path(self.tmp.name) / "prog.asm"
        p.write_text(PROGRAM)
        s.load_program(p, stop_on_entry=True, log=lambda *_: None)
        self.assertTrue(s.wait_stopped(30))
        self.assertEqual(s.regs()["PC"], 0x9000)
        self.assertEqual(s.last_stop["kind"], "entry")
        s.execute("bp 9007")
        s.go()
        self.assertTrue(s.wait_stopped(10))
        self.assertEqual(s.regs()["PC"], 0x9007)
        self.assertEqual(s.last_stop["kind"], "breakpoint")
        s.step_over()                                   # over SWI $02 (2 bytes)
        self.assertEqual(s.regs()["PC"], 0x9009)
        s.execute("bc all")
        s.execute("wp 9F01 1 w")
        s.go()
        self.assertTrue(s.wait_stopped(10))
        self.assertEqual(s.last_stop["kind"], "watchpoint")
        self.assertEqual(s.client.read_bytes(0x9F01, 1, "6"), b"\x01")

    def test_live_patch(self):
        s = self.s
        s.pause()
        out = s.execute("a 9F80@6 LDA #$41 | SWI PUTC | RTS")
        self.assertIn("86 41 3F 02 39", out)
        self.assertEqual(s.client.read_bytes(0x9F80, 5, "6"), bytes.fromhex("86413F0239"))
        s.execute('str 9F90@6 "OK\\0"')
        self.assertEqual(s.client.read_bytes(0x9F90, 3, "6"), b"OK\x00")
        with self.assertRaises(Exception):
            s.execute("hex F000 12")                    # monitor ROM is read-only

    def test_basic_line_breakpoints(self):
        s = self.s
        p = Path(self.tmp.name) / "p.bas"
        p.write_text("10 A=1\n20 FOR I=1 TO 3\n30 A=A*2\n40 NEXT I\n50 POKE &H9F01,A\n")
        s.set_basic_breakpoint(40)
        s.load_program(p, log=lambda *_: None)
        self.assertTrue(s.wait_stopped(60))
        self.assertEqual(s.last_stop["kind"], "basic-line")
        self.assertEqual(s.regs()["U"], 40)
        s.execute("bc all")
        s.next_basic_line(wait=True)
        self.assertEqual(s.regs()["U"], 30)


@unittest.skipUnless(LIVE, "set PC128_LIVE_TESTS=1 to boot MAME")
@unittest.skipUnless((ROOT / "media" / "KEYJOY.FD").is_file(), "media/KEYJOY.FD not present")
class LiveFloppyTests(unittest.TestCase):
    def test_loadm_from_floppy(self):
        from commands import Session
        with tempfile.TemporaryDirectory() as tmp:
            fd = Path(tmp) / "KEYJOY.FD"                # a copy: the debugger must not touch the real disk
            shutil.copy(ROOT / "media" / "KEYJOY.FD", fd)
            p = Path(tmp) / "p.bas"
            p.write_text('10 CLEAR ,&H9EFF\n20 LOADM "KEYJOY"\n30 A=1\n')
            s = Session()
            s._quiet = True
            try:
                s.start(media={"floppy": str(fd)}, window=False, log=lambda *_: None)
                self.assertIn("-flop1", s.media_args)
                s.set_basic_breakpoint(30)
                s.load_program(p, log=lambda *_: None)
                self.assertTrue(s.wait_stopped(90))
                self.assertEqual(s.regs()["U"], 30)
                self.assertEqual(s.client.read_bytes(0x9F00, 4, "6"), bytes.fromhex("20044B4A"))
                self.assertIn("extension", s.execute("banks"))
            finally:
                s.close()


if __name__ == "__main__":
    unittest.main()
