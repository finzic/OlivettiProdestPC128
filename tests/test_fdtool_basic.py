import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from basic_codec import (BasicCodecError, detokenize_file, is_native_basic,
                         load_token_table, tokenize_source)
from fdtool import Disk


class BasicCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.tokens = load_token_table()
        except BasicCodecError as exc:
            raise unittest.SkipTest(str(exc))

    def test_all_rom_words_round_trip(self):
        spellings = []
        for word in self.tokens.by_word:
            if word != "?" and word not in spellings:
                spellings.append(word)
        source = "\n".join("%d %s" % (i + 1, word) for i, word in enumerate(spellings))
        encoded = tokenize_source(source, self.tokens)
        decoded = detokenize_file(encoded, self.tokens)
        self.assertEqual(tokenize_source(decoded, self.tokens), encoded)

    def test_asterisk_uses_rom_input_token_in_all_contexts(self):
        encoded = tokenize_source("10 DIR *.BAS\n20 KILL *.BAS\n30 COPY *.BAS TO X.BAS\n40 X=2*3", self.tokens)
        self.assertEqual(encoded.count(b"\xc9"), 4)
        self.assertEqual(tokenize_source(detokenize_file(encoded, self.tokens), self.tokens), encoded)
        self.assertEqual(self.tokens.by_bytes[b"\xec"], "*")

    def test_native_basic_header_and_numbered_source(self):
        encoded = tokenize_source("10 PRINT \"OK\"\n20 DO\n30 LOOP", self.tokens)
        self.assertTrue(is_native_basic(encoded))
        self.assertEqual(detokenize_file(encoded, self.tokens),
                         '10 PRINT "OK"\n20 DO\n30 LOOP\n')
        high_lines = tokenize_source("256 PRINT 256\n1000 PRINT 1000\n63999 PRINT 63999", self.tokens)
        self.assertEqual(detokenize_file(high_lines, self.tokens),
                         "256 PRINT 256\n1000 PRINT 1000\n63999 PRINT 63999\n")
        self.assertEqual(tokenize_source(detokenize_file(high_lines, self.tokens), self.tokens), high_lines)
        with self.assertRaisesRegex(BasicCodecError, "direct statement"):
            tokenize_source("PRINT \"not numbered\"", self.tokens)

    def test_folder_pack_defaults_to_basic_b_and_supports_save_a(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            folder = temp / "input"
            folder.mkdir()
            native = tokenize_source("10 PRINT \"NATIVE\"", self.tokens)
            (folder / "NATIVE.BAS").write_bytes(native)
            (folder / "TEXT.BAS").write_text('1000 PRINT "TEXT"\n63999 PRINT "CITTÀ"\n', encoding="latin-1")
            binary = bytes((0, 1, 2, 0xFF))
            (folder / "CODE.BIN").write_bytes(binary)
            disk_path = temp / "PACKED.FD"
            subprocess.run([sys.executable, str(ROOT / "tools/fdtool.py"), "pack",
                            str(folder), str(disk_path), "--tracks", "80"],
                           check=True, capture_output=True, text=True)
            disk = Disk(disk_path.read_bytes(), tracks=80)
            entries = {(name + "." + ext): (kind, flag, first, last)
                       for _, name, ext, kind, flag, first, last in disk.files()}
            self.assertEqual(set(entries), {"NATIVE.BAS", "TEXT.BAS", "CODE.BIN"})
            self.assertEqual(entries["NATIVE.BAS"][0:2], (0, 0))
            self.assertEqual(disk.read(entries["NATIVE.BAS"][2], entries["NATIVE.BAS"][3]), native)
            self.assertEqual(entries["TEXT.BAS"][0:2], (0, 0))
            text_data = disk.read(entries["TEXT.BAS"][2], entries["TEXT.BAS"][3])
            self.assertTrue(is_native_basic(text_data))
            self.assertEqual(detokenize_file(text_data, self.tokens),
                             '1000 PRINT "TEXT"\n63999 PRINT "CITTÀ"\n')
            self.assertEqual(entries["CODE.BIN"][0], 2)
            self.assertEqual(disk.read(entries["CODE.BIN"][2], entries["CODE.BIN"][3]), binary)

            ascii_path = temp / "ASCII.FD"
            subprocess.run([sys.executable, str(ROOT / "tools/fdtool.py"), "pack",
                            str(folder), str(ascii_path), "--tracks", "80",
                            "--basic-format", "ascii"], check=True,
                           capture_output=True, text=True)
            ascii_disk = Disk(ascii_path.read_bytes(), tracks=80)
            ascii_entry = next((kind, flag, first, last)
                               for _, name, ext, kind, flag, first, last in ascii_disk.files()
                               if name == "TEXT" and ext == "BAS")
            ascii_data = ascii_disk.read(ascii_entry[2], ascii_entry[3])
            self.assertEqual(ascii_entry[:2], (0, 0xFF))
            self.assertTrue(ascii_data.startswith(b"\r\n"))
            self.assertIn(b'1000 PRINT "TEXT"\r\n', ascii_data)
            self.assertIn(b'63999 PRINT "CITT\xc0"\r\n', ascii_data)

    def test_put_explicit_type_ascii_uses_basic_a_framing(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            source = temp / "TEXT.BAS"
            source.write_text('10 PRINT "TEXT"\n20 END\n')
            disk_path = temp / "PUT.FD"
            subprocess.run([sys.executable, str(ROOT / "tools/fdtool.py"), "new",
                            str(disk_path), "--tracks", "80"], check=True,
                           capture_output=True, text=True)
            subprocess.run([sys.executable, str(ROOT / "tools/fdtool.py"), "put",
                            str(disk_path), str(source), "--type", "0", "--ascii",
                            "--tracks", "80"], check=True, capture_output=True, text=True)
            disk = Disk(disk_path.read_bytes(), tracks=80)
            entry = next((kind, flag, first, last) for _, name, ext, kind, flag, first, last in disk.files()
                         if name == "TEXT" and ext == "BAS")
            self.assertEqual(entry[:2], (0, 0xFF))
            payload = disk.read(entry[2], entry[3])
            self.assertTrue(payload.startswith(b"\r\n"))
            self.assertIn(b'10 PRINT "TEXT"\r\n', payload)

    def test_put_plain_bas_defaults_to_native_basic_b(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            source = temp / "TEXT.BAS"
            source.write_text('1000 PRINT "TEXT"\n63999 END\n')
            disk_path = temp / "PUT.FD"
            subprocess.run([sys.executable, str(ROOT / "tools/fdtool.py"), "new",
                            str(disk_path), "--tracks", "80"], check=True,
                           capture_output=True, text=True)
            subprocess.run([sys.executable, str(ROOT / "tools/fdtool.py"), "put",
                            str(disk_path), str(source), "--tracks", "80"],
                           check=True, capture_output=True, text=True)
            disk = Disk(disk_path.read_bytes(), tracks=80)
            entry = next((kind, flag, first, last) for _, name, ext, kind, flag, first, last in disk.files()
                         if name == "TEXT" and ext == "BAS")
            payload = disk.read(entry[2], entry[3])
            self.assertEqual(entry[:2], (0, 0))
            self.assertTrue(is_native_basic(payload))
            self.assertEqual(detokenize_file(payload, self.tokens),
                             '1000 PRINT "TEXT"\n63999 END\n')


if __name__ == "__main__":
    unittest.main()
