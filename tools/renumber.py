#!/usr/bin/env python3
"""Renumber an ASCII PC128 BASIC listing and fix up line-number references.

Rewrites GOTO / GO TO / GOSUB / GO SUB / THEN / ELSE / RESTORE / RESUME / RUN /
LIST / DELETE targets (including ON ... GOTO lists and LIST/DELETE ranges).
Text inside strings, REM / ' comments and DATA statements is left untouched.

    python3 tools/renumber.py PROG.BAS                 # 10, 20, 30 ... in place
    python3 tools/renumber.py PROG.BAS --start 100 --step 5
    python3 tools/renumber.py PROG.BAS --stdout        # print, don't write
"""

import argparse
import re
import sys
from pathlib import Path

MAX_LINE = 63999

LINE_RE = re.compile(r"^(\s*)(\d+)( ?)(.*)$", re.S)
# Keywords followed by a line number (or list/range of them). Longest first.
REF_RE = re.compile(r"GO\s*TO|GO\s*SUB|THEN|ELSE|RESTORE|RESUME|RUN|LIST|DELETE", re.I)
SKIP_REST_RE = re.compile(r"REM|'", re.I)
DATA_RE = re.compile(r"DATA", re.I)
NUM_RE = re.compile(r"\s*(\d+)")


class RenumberError(Exception):
    pass


def _rewrite_numbers(body, pos, keyword, mapping, warnings, lineno):
    """Rewrite the number list following a keyword; return (text, new_pos)."""
    out = []
    ranged = keyword in ("LIST", "DELETE")
    listed = keyword.startswith("GO")  # ON x GOTO a,b,c
    while True:
        m = NUM_RE.match(body, pos)
        if m:
            old = int(m.group(1))
            if old in mapping:
                new = str(mapping[old])
            else:
                new = m.group(1)
                warnings.append("line %d: reference to missing line %d" % (lineno, old))
            out.append(m.group(0)[: m.start(1) - m.start(0)] + new)
            pos = m.end()
        sep = re.compile(r"\s*([,-])").match(body, pos)
        if sep and ((sep.group(1) == "," and listed) or (sep.group(1) == "-" and ranged)):
            out.append(sep.group(0))
            pos = sep.end()
            continue
        return "".join(out), pos


def _rewrite_body(body, mapping, warnings, lineno):
    out = []
    i = 0
    in_data = False
    while i < len(body):
        ch = body[i]
        if ch == '"':
            end = body.find('"', i + 1)
            end = len(body) if end < 0 else end + 1
            out.append(body[i:end])
            i = end
            continue
        if in_data:
            if ch == ":":
                in_data = False
            out.append(ch)
            i += 1
            continue
        if SKIP_REST_RE.match(body, i):
            out.append(body[i:])
            break
        m = DATA_RE.match(body, i)
        if m:
            in_data = True
            out.append(m.group(0))
            i = m.end()
            continue
        m = REF_RE.match(body, i)
        if m:
            out.append(m.group(0))
            keyword = re.sub(r"\s+", "", m.group(0)).upper()
            text, i = _rewrite_numbers(body, m.end(), keyword, mapping, warnings, lineno)
            out.append(text)
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def renumber(source, start=10, step=10):
    """Return (new_source, warnings)."""
    if start < 0 or step < 1:
        raise RenumberError("start must be >= 0 and step >= 1")
    lines = source.splitlines(keepends=True)
    parsed = []
    mapping = {}
    for idx, raw in enumerate(lines, 1):
        text = raw.rstrip("\r\n")
        eol = raw[len(text):]
        if not text.strip():
            parsed.append((None, raw))
            continue
        m = LINE_RE.match(text)
        if not m:
            raise RenumberError("source line %d has no line number: %r" % (idx, text))
        old = int(m.group(2))
        if old in mapping:
            raise RenumberError("duplicate line number %d (source line %d)" % (old, idx))
        new = start + step * len(mapping)
        if new > MAX_LINE:
            raise RenumberError("line numbers would exceed %d; use a smaller start/step" % MAX_LINE)
        mapping[old] = new
        parsed.append((old, (m.group(1), m.group(3), m.group(4), eol)))

    warnings = []
    out = []
    for old, data in parsed:
        if old is None:
            out.append(data)
            continue
        indent, space, body, eol = data
        body = _rewrite_body(body, mapping, warnings, old)
        out.append("%s%d%s%s%s" % (indent, mapping[old], space, body, eol))
    return "".join(out), warnings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--start", type=int, default=10)
    ap.add_argument("--step", type=int, default=10)
    ap.add_argument("--stdout", action="store_true", help="print result instead of rewriting the file")
    args = ap.parse_args(argv)

    raw = args.file.read_bytes()
    if b"\x00" in raw[:256] or raw[:1] == b"\xff":
        print("error: %s looks tokenized; renumber works on ASCII listings" % args.file, file=sys.stderr)
        return 1
    source = raw.decode("latin-1")
    try:
        result, warnings = renumber(source, args.start, args.step)
    except RenumberError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    for w in warnings:
        print("warning: " + w, file=sys.stderr)
    if args.stdout:
        sys.stdout.write(result)
    else:
        args.file.write_bytes(result.encode("latin-1"))
        print("renumbered %s (start %d, step %d)" % (args.file, args.start, args.step))
    return 0


if __name__ == "__main__":
    sys.exit(main())
