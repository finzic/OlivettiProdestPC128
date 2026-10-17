#!/usr/bin/env python3
"""Encode and decode PC128 BASIC files using the locally supplied ROM tables."""
from dataclasses import dataclass
from pathlib import Path

from rom_scan import find_tables

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROM = ROOT / "src-rom" / "pc128.rom"


class BasicCodecError(ValueError):
    pass


@dataclass(frozen=True)
class TokenTable:
    by_bytes: dict
    by_word: dict


def _rom_bank(rom_path=None):
    path = Path(rom_path) if rom_path else DEFAULT_ROM
    if path.is_file():
        data = path.read_bytes()
        if len(data) == 0x10000:
            return data[0x8000:0xC000]
        if len(data) == 0x4000:
            return data
        raise BasicCodecError("PC128 ROM must be 65536 bytes or a 16384-byte BASIC bank: %s" % path)
    bank_path = ROOT / "roms" / "pro128" / "basico-2.rom"
    if bank_path.is_file() and bank_path.stat().st_size == 0x4000:
        return bank_path.read_bytes()
    raise BasicCodecError("PC128 ROM unavailable; provide src-rom/pc128.rom or roms/pro128/basico-2.rom")


def load_token_table(rom_path=None):
    tables = find_tables(_rom_bank(rom_path), 0xB000)
    first = [entry[2] for entry in tables if len(entry[2]) == 82]
    second = [entry[2] for entry in tables if len(entry[2]) == 103]
    if len(first) != 1 or len(second) != 1:
        raise BasicCodecError("expected PC128 BASIC tables with 82 statements and 103 extended words")

    by_bytes = {bytes((0x80 + i,)): word for i, word in enumerate(first[0])}
    extended = second[0]
    by_bytes.update({bytes((0xD3 + i,)): word for i, word in enumerate(extended[:38])})
    by_bytes[bytes((0xD2,))] = "@"
    by_bytes.update({bytes((0xFF, 0x80 + i)): word for i, word in enumerate(extended[38:])})
    by_word = {}
    for code, word in by_bytes.items():
        by_word.setdefault(word, []).append(code)
    by_word["?"] = by_word["PRINT"]
    return TokenTable(by_bytes, by_word)


def is_native_basic(data):
    if (len(data) < 10 or data[0] != 0xFF or
            int.from_bytes(data[1:3], "big") != len(data) - 2 or data[3] != 0):
        return False
    pos = 4
    previous_line = -1
    records = 0
    while pos < len(data):
        if data[pos] == 0:
            return records > 0 and not any(data[pos:])
        record_size = data[pos]
        if record_size < 5 or pos + record_size > len(data):
            return False
        line_number = int.from_bytes(data[pos + 1:pos + 3], "big")
        if line_number <= previous_line or line_number > 63999:
            return False
        if data[pos + record_size - 2:pos + record_size] != b"\x00\x00":
            return False
        previous_line = line_number
        records += 1
        pos += record_size
    return False


def _line_number(line, line_index, max_number):
    stripped = line.lstrip()
    digits = 0
    while digits < len(stripped) and stripped[digits].isdigit():
        digits += 1
    if not digits:
        raise BasicCodecError("line %d is a direct statement; BASIC file lines need line numbers" % line_index)
    number = int(stripped[:digits])
    if number > max_number:
        raise BasicCodecError("line number %d exceeds the limit (%d)" % (number, max_number))
    rest = stripped[digits:]
    if rest and not rest[0].isspace():
        raise BasicCodecError("line %d needs a separator after its line number" % line_index)
    return number, rest.lstrip()


def _tokenize_body(source, table, line_number):
    words = sorted((word for word in table.by_word if word != "?"), key=len, reverse=True)
    out = bytearray()
    i = 0
    quoted = False
    comment = False
    data_mode = False
    while i < len(source):
        char = source[i]
        if char == '"':
            out.extend(char.encode("latin-1"))
            quoted = not quoted
            i += 1
            continue
        if quoted or comment or data_mode:
            out.extend(char.encode("latin-1"))
            if data_mode and char == ":":
                data_mode = False
            i += 1
            continue

        word = next((candidate for candidate in words
                     if source[i:i + len(candidate)].upper() == candidate), None)
        if word is not None:
            out.extend(table.by_word[word][0])
            i += len(word)
            if word in ("REM", "'"):
                comment = True
            elif word == "DATA":
                data_mode = True
            continue

        char = char.upper()
        try:
            out.extend(char.encode("latin-1"))
        except UnicodeEncodeError as exc:
            raise BasicCodecError("line %d contains a character outside the PC128 character set" % line_number) from exc
        i += 1
    if quoted:
        raise BasicCodecError("line %d has an unterminated string" % line_number)
    return bytes(out)


def _source_lines(source, table, max_number):
    if isinstance(source, bytes):
        try:
            source = source.decode("latin-1")
        except UnicodeDecodeError as exc:
            raise BasicCodecError("BASIC source is not Latin-1 text") from exc
    lines = []
    seen = set()
    for index, raw in enumerate(source.replace("\r\n", "\n").replace("\r", "\n").split("\n"), 1):
        if not raw.strip():
            continue
        number, body = _line_number(raw, index, max_number)
        if number in seen:
            raise BasicCodecError("duplicate BASIC line number %d" % number)
        seen.add(number)
        lines.append((number, _tokenize_body(body, table, number)))
    if not lines:
        raise BasicCodecError("BASIC source has no numbered lines")
    return lines


def validate_source(source, table):
    return _source_lines(source, table, 63999)


def tokenize_source(source, table):
    lines = _source_lines(source, table, 63999)
    records = []
    for number, token_body in lines:
        size = len(token_body) + 5
        if size > 0xFF:
            raise BasicCodecError("BASIC line %d is too long" % number)
        records.append(bytes((size,)) + number.to_bytes(2, "big") + token_body + b"\x00\x00")
    stream = b"".join(records) + b"\x00"
    size = len(stream) + 2
    if size > 0xFFFF:
        raise BasicCodecError("tokenized BASIC program exceeds 65535 bytes")
    return b"\xFF" + size.to_bytes(2, "big") + b"\x00" + stream


def _space_before(text):
    return bool(text) and (text[-1].isalnum() or text[-1] in "$#")


def _space_after(word, following):
    return ((word[0].isalpha() or word == "'") and bool(following) and
            (following.isalnum() or following == '"') and not word.endswith("("))


def _decode_body(body, table, line_number):
    out = []
    i = 0
    quoted = False
    comment = False
    data_mode = False
    while i < len(body):
        byte = body[i]
        if quoted or comment or data_mode or byte < 0x80:
            try:
                char = bytes((byte,)).decode("latin-1")
            except UnicodeDecodeError as exc:
                raise BasicCodecError("invalid character on line %d" % line_number) from exc
            out.append(char)
            if char == '"' and not comment and not data_mode:
                quoted = not quoted
            if data_mode and char == ":":
                data_mode = False
            i += 1
            continue

        if byte == 0xFF:
            code = body[i:i + 2]
            i += 2
        else:
            code = bytes((byte,))
            i += 1
        word = table.by_bytes.get(code)
        if word is None:
            raise BasicCodecError("unknown token %s on BASIC line %d" % (code.hex(" ").upper(), line_number))
        following = chr(body[i]) if i < len(body) and body[i] < 0x80 else ""
        if (word[0].isalnum() or word[0] in "'") and _space_before("".join(out)):
            out.append(" ")
        out.append(word)
        if _space_after(word, following):
            out.append(" ")
        if word in ("REM", "'"):
            comment = True
        elif word == "DATA":
            data_mode = True
    return "".join(out)


def detokenize_file(data, table):
    if not is_native_basic(data):
        raise BasicCodecError("not a PC128 tokenized BASIC file")
    lines = []
    p = 4
    while p < len(data):
        if data[p:] == b"\x00":
            break
        if p + 1 > len(data):
            raise BasicCodecError("truncated BASIC record header at offset %d" % p)
        size = data[p]
        if size < 5 or p + size > len(data):
            raise BasicCodecError("invalid BASIC record size %d at offset %d" % (size, p))
        line_number = int.from_bytes(data[p + 1:p + 3], "big")
        body = data[p + 3:p + size - 2]
        if data[p + size - 2:p + size] != b"\x00\x00":
            raise BasicCodecError("missing BASIC line terminator at offset %d" % p)
        lines.append("%d %s" % (line_number, _decode_body(body, table, line_number)))
        p += size
    if not lines:
        raise BasicCodecError("tokenized BASIC file has no line records")
    return "\n".join(lines) + "\n"


def basic_ascii_bytes(source):
    if isinstance(source, bytes):
        try:
            source = source.decode("latin-1")
        except UnicodeDecodeError as exc:
            raise BasicCodecError("BASIC source is not Latin-1 text") from exc
    lines = [line.rstrip() for line in source.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]
    if not lines:
        raise BasicCodecError("BASIC source has no numbered lines")
    return b"\r\n" + b"".join(line.encode("latin-1") + b"\r\n" for line in lines)
