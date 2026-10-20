"""pc128cc (C toolchain) tests.

Parser tests run anywhere. Build tests need CMOC + LWTOOLS (tools/setup-lwasm.sh, tools/setup-cmoc.sh).
Live tests boot MAME headless: PC128_LIVE_TESTS=1 python3 -m unittest tests.test_pc128cc
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "debugger"))

import pc128cc  # noqa: E402

try:
    pc128cc.check_toolchain()
    HAVE_CMOC = True
except pc128cc.CBuildError:
    HAVE_CMOC = False
LIVE = os.environ.get("PC128_LIVE_TESTS") == "1"
EXAMPLES = ROOT / "pc128-c" / "examples"

MAP = """\
Section: start (/w/build/prog.o) load at 6000, length 000E
Section: code (/w/build/prog.o) load at 6100, length 0020
Section: code (/w/build/util.o) load at 6120, length 0010
Symbol: _main (/w/build/prog.o) = 6100
Symbol: _helper (/w/build/util.o) = 6120
Symbol: \\L0001 (/w/build/prog.o) = 6105
"""

C_LISTING = """\
                      (uild/prog/prog.s):00001                 SECTION code
                      (uild/prog/prog.s):00002 * FUNCTION main(): defined at /w/prog.c:5
0000 3440             (uild/prog/prog.s):00003 _main   PSHS    U
                      (uild/prog/prog.s):00004 * Line /w/prog.c:6: function call: f()
0002 BD0000           (uild/prog/prog.s):00005         JSR     _f
0005 35C0             (uild/prog/prog.s):00006         PULS    U,PC
                      (uild/prog/prog.s):00007         ENDSECTION
"""

ASM_LISTING = """\
                      (           util.asm):00001         INCLUDE "olivetti.inc"
                      (           util.asm):00002         SECTION code
0000 C641             (           util.asm):00003 _helper LDB     #'A'
                      (           util.asm):00004         SYSCALL PUTC
0002 3F               (       olivetti.inc):00011         SWI
0003 02               (       olivetti.inc):00012         FCB     2
0004 39               (           util.asm):00005         RTS
                      (           util.asm):00006         ENDSECTION
"""


class ParserTests(unittest.TestCase):
    def test_parse_map(self):
        sections, symbols = pc128cc.parse_map(MAP)
        self.assertEqual(sections[("code", "prog.o")], (0x6100, 0x20))
        self.assertEqual(sections[("code", "util.o")], (0x6120, 0x10))
        self.assertEqual(symbols["_main"], 0x6100)
        self.assertNotIn("\\L0001", symbols)

    def test_c_listing_lines(self):
        sections, _ = pc128cc.parse_map(MAP)
        lines = pc128cc.parse_object_listing(C_LISTING, "prog.o", sections)
        self.assertEqual([(l.addr, l.line) for l in lines], [(0x6100, 5), (0x6102, 6), (0x6105, 6)])
        self.assertTrue(all(l.file == "/w/prog.c" for l in lines))
        self.assertEqual(lines[1].data, bytes.fromhex("BD0000"))

    def test_asm_listing_macro_lines(self):
        sections, _ = pc128cc.parse_map(MAP)
        lines = pc128cc.parse_object_listing(ASM_LISTING, "util.o", sections, Path("/w/util.asm"), is_c=False)
        # the SYSCALL expansion (from olivetti.inc) belongs to the invoking line 4
        self.assertEqual([(l.addr, l.line) for l in lines], [(0x6120, 3), (0x6122, 4), (0x6123, 4), (0x6124, 5)])

    def test_directives(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.c"
            p.write_text("/* pc128cc: sources=a.asm,b.c org=7000\n * pc128cc: opt=-O0 */\nint main(void){return 0;}\n")
            opts = pc128cc.read_directives(p)
        self.assertEqual(opts["sources"], ["a.asm,b.c"])
        self.assertEqual(opts["org"], ["7000"])
        self.assertEqual(opts["opt"], ["-O0"])


@unittest.skipUnless(HAVE_CMOC, "cmoc/lwtools not installed (tools/setup-cmoc.sh)")
class BuildTests(unittest.TestCase):
    def test_build_mixed_example(self):
        with tempfile.TemporaryDirectory() as d:
            res = pc128cc.build([EXAMPLES / "mixed.c"], out=Path(d) / "mixed.bin")
            self.assertTrue(res.binary.is_file())
        self.assertEqual(res.entry, 0x6000)
        for name in ("main", "_main", "sum_bytes", "put_stars", "ol_putc", "counter"):
            self.assertIn(name, res.symbols)
        files = {Path(l.file).name for l in res.lines}
        self.assertTrue({"mixed.c", "asmlib.asm", "ol_text.asm", "ol_print.c"} <= files, files)
        main_lines = {l.line for l in res.lines if l.file.endswith("mixed.c")}
        self.assertIn(25, main_lines)                       # s = sum_bytes(data, sizeof data);
        self.assertLessEqual(res.end, 0x9F00)

    def test_all_examples_build(self):
        for src in sorted(EXAMPLES.glob("*.c")):
            with self.subTest(src.name), tempfile.TemporaryDirectory() as d:
                pc128cc.build([src], out=Path(d) / "x.bin")

    def test_compile_error(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.c"
            p.write_text("int main(void) { return undefined_name; }\n")
            with self.assertRaises(pc128cc.CBuildError):
                pc128cc.build([p], out=Path(d) / "bad.bin")


@unittest.skipUnless(LIVE and HAVE_CMOC, "set PC128_LIVE_TESTS=1 (and install cmoc) to boot MAME")
class LiveCTests(unittest.TestCase):
    def test_c_source_breakpoint_and_stepping(self):
        from commands import Session
        s = Session()
        s._quiet = True
        try:
            s.start(window=False, log=lambda *_: None)
            s.load_program(EXAMPLES / "mixed.c", stop_on_entry=True, log=lambda *_: None)
            self.assertTrue(s.wait_stopped(30))
            self.assertIn("mixed.c:25", s.execute("bp mixed.c:25"))
            s.go()
            self.assertTrue(s.wait_stopped(20))
            self.assertEqual(Path(s.program_source_at(s.regs()["PC"])[0]).name, "mixed.c")
            self.assertEqual(s.program_source_at(s.regs()["PC"])[1], 25)
            s.execute("bc all")
            s.step_source(over=True)
            self.assertEqual(s.program_source_at(s.regs()["PC"])[1], 26)
            for _ in range(3):
                s.step_source(over=True)
            self.assertEqual(s.program_source_at(s.regs()["PC"])[1], 30)
            s.step_source(over=False)                       # into put_stars (asmlib.asm)
            src = s.program_source_at(s.regs()["PC"])
            self.assertEqual(Path(src[0]).name, "asmlib.asm")
            self.assertEqual(s.regs()["PC"], s.symbols.find("put_stars").addr)
            s.execute("wp 9F01 1 w")
            s.go()
            self.assertTrue(s.wait_stopped(30))
            self.assertEqual(s.client.read_bytes(0x9F10, 4, "6"), bytes.fromhex("0164000A"))
        finally:
            s.close()


if __name__ == "__main__":
    unittest.main()
