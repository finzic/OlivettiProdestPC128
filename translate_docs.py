#!/usr/bin/env python3
"""OCR every PDF in src/ and produce an English text file per document.

Resumable: per-page OCR and translation results are cached, re-running only
processes missing pages.  Fully offline (Tesseract + Argos Translate).

Layout per document:
    output/<name>/OCR/page-NNN.txt        raw OCR (source language)
    output/<name>/OCR/ocr.txt             all pages concatenated
    output/<name>/English/pages/page-NNN.txt
    output/<name>/English/<name>.en.txt   final English text

Usage:  ./bin/python translate_docs.py [--only NAME ...] [--ocr-only] [--force-ocr]
"""
import argparse
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "output"

# Source language per document (default: French).
LANG_OVERRIDES = {
    "09-OlivettiProdestPc128": "it",
    "Motorola MC6809-MC6809E 8-Bit Microprocessor Programming Manual": "en",
    "M6809PM.rev0_May83": "en",
}
TESS_LANG = {"fr": "fra+eng", "it": "ita+eng", "en": "eng"}

MNEMONICS = set("""
ABX ADCA ADCB ADDA ADDB ADDD ANDA ANDB ANDCC ASL ASLA ASLB ASR ASRA ASRB BCC BCS
BEQ BGE BGT BHI BHS BITA BITB BLE BLO BLS BLT BMI BNE BPL BRA BRN BSR BVC BVS CLR
CLRA CLRB CMPA CMPB CMPD CMPS CMPU CMPX CMPY COM COMA COMB CWAI DAA DEC DECA DECB
EORA EORB EXG INC INCA INCB JMP JSR LBCC LBCS LBEQ LBGE LBGT LBHI LBHS LBLE LBLO
LBLS LBLT LBMI LBNE LBPL LBRA LBRN LBSR LBVC LBVS LDA LDB LDD LDS LDU LDX LDY LEAS
LEAU LEAX LEAY LSL LSLA LSLB LSR LSRA LSRB MUL NEG NEGA NEGB NOP ORA ORB ORCC PSHS
PSHU PULS PULU ROL ROLA ROLB ROR RORA RORB RTI RTS SBCA SBCB SEX STA STB STD STS
STU STX STY SUBA SUBB SUBD SWI SWI2 SWI3 SYNC TFR TST TSTA TSTB ORG EQU FCB FDB
FCC RMB END SETDP PC DP CC
""".split())

WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]+(?:'[A-Za-zÀ-ÿ]+)?")


# ----------------------------------------------------------------- OCR ----
def page_images(name: str, pdf: Path) -> list[Path]:
    """Reuse cached 300 DPI renders if present, otherwise render the PDF."""
    cache = OUT / name / "_debug_pages"
    imgs = sorted(cache.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[1])) if cache.is_dir() else []
    if not imgs:
        cache.mkdir(parents=True, exist_ok=True)
        print(f"  rendering {pdf.name} ...", flush=True)
        subprocess.run(["pdftoppm", "-r", "300", "-gray", "-png", str(pdf), str(cache / "page")], check=True)
        imgs = sorted(cache.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[1]))
    return imgs


def ocr_one(args):
    img, txt, tess_lang = args
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    subprocess.run(["tesseract", str(img), str(txt.with_suffix("")), "-l", tess_lang, "--psm", "3"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    if not txt.exists():
        txt.write_text("")


def ocr_document(name: str, pdf: Path, lang: str, force: bool) -> list[Path]:
    ocr_dir = OUT / name / "OCR"
    ocr_dir.mkdir(parents=True, exist_ok=True)
    imgs = page_images(name, pdf)
    jobs, txts = [], []
    for i, img in enumerate(imgs, 1):
        txt = ocr_dir / f"page-{i:03d}.txt"
        txts.append(txt)
        if force or not txt.exists():
            jobs.append((img, txt, TESS_LANG[lang]))
    if jobs:
        print(f"  OCR {len(jobs)} page(s) [{TESS_LANG[lang]}] ...", flush=True)
        with ThreadPoolExecutor(os.cpu_count()) as ex:
            list(ex.map(ocr_one, jobs))
    with open(ocr_dir / "ocr.txt", "w") as f:
        for i, t in enumerate(txts, 1):
            f.write(f"===== Page {i} =====\n{t.read_text()}\n\n")
    return txts


# ---------------------------------------------------------- classify -----
def is_code(line: str) -> bool:
    """True for assembly/BASIC listings, hex dumps, tables: keep verbatim."""
    s = line.strip()
    if not s:
        return False
    if re.match(r"^\d+\s*[A-Z]{2,}", s) and not re.search(r"[a-zà-ÿ]{4,}", s):
        return True  # BASIC line
    if asm_split(s):
        return True
    words = WORD_RE.findall(s)
    prose_words = [w for w in words if len(w) >= 3 and re.search(r"[a-zà-ÿ]", w)]
    if len(s) > 8 and len(prose_words) == 0 and not is_caps_title(s):
        return True
    non_alpha = sum(1 for c in s if not (c.isalpha() or c.isspace()))
    return len(s) > 6 and non_alpha / len(s) > 0.45


ASM_RE = re.compile(
    r"^(?P<code>\s*(?:[0-9A-F]{2,4}\s+)*(?:[A-Za-z_][\w]*\s+)?(?P<mn>[A-Z][A-Z0-9]{1,4})"
    r"(?:\s+(?P<op>[^\s]+))?)(?P<comment>\s+.*)?$")


def asm_split(s: str):
    """Return (code_part, comment) for a 6809 assembly line, else None."""
    m = ASM_RE.match(s)
    if not m or m.group("mn") not in MNEMONICS:
        return None
    op = m.group("op") or ""
    if op and re.search(r"[a-zà-ÿ]{3,}", op) and not re.search(r"[$#&,<>]", op):
        return None  # mnemonic followed by a plain word: it's prose
    if op == "" and m.group("comment") is None and len(s.split()) > 1:
        return None
    return m.group("code"), (m.group("comment") or "")


def is_caps_title(s: str) -> bool:
    words = WORD_RE.findall(s)
    return (len(words) >= 2 and s == s.upper() and not re.search(r"\d{2,}|[$#&=]", s)
            and not all(w in MNEMONICS for w in words)
            and sum(len(w) >= 3 for w in words) >= 2)


def blocks(text: str):
    """Yield (kind, text): kind in {'prose','title','code','blank'}."""
    para: list[str] = []

    def flush():
        if para:
            joined = ""
            for ln in para:
                if joined.endswith("-") and not joined.endswith(" -"):
                    joined = joined[:-1] + ln.lstrip()
                else:
                    joined = (joined + " " + ln.strip()).strip()
            para.clear()
            return ("prose", joined)
        return None

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            b = flush()
            if b:
                yield b
            yield ("blank", "")
        elif is_code(line):
            b = flush()
            if b:
                yield b
            yield ("code", line)
        elif is_caps_title(line.strip()) and len(line.strip()) < 70:
            b = flush()
            if b:
                yield b
            yield ("title", line.strip())
        else:
            para.append(line)
    b = flush()
    if b:
        yield b


# --------------------------------------------------------- translate -----
_translator = None


def _get_translator(lang):
    global _translator
    if _translator is None:
        import argostranslate.translate as at
        langs = {l.code: l for l in at.get_installed_languages()}
        _translator = langs[lang].get_translation(langs["en"])
    return _translator


def translate_page(args):
    src_txt, dst_txt, lang = args
    tr = _get_translator(lang)
    out: list[str] = []
    for kind, text in blocks(src_txt.read_text()):
        if kind == "blank":
            if out and out[-1] != "":
                out.append("")
        elif kind == "code":
            parts = asm_split(text.strip())
            comment = parts[1].strip() if parts else ""
            if comment and len(re.findall(r"[a-zà-ÿ]{3,}", comment)) >= 1:
                lead = text[:len(text) - len(text.lstrip())]
                out.append(f"{lead}{parts[0].strip():<24} ; {tr.translate(comment)}")
            else:
                out.append(text)
        elif kind == "title":
            out.append(tr.translate(text.capitalize()).upper())
        else:
            try:
                out.append(tr.translate(text))
            except Exception as e:  # keep going; mark the paragraph
                out.append(f"[UNTRANSLATED: {e}] {text}")
    dst_txt.write_text("\n".join(out).strip() + "\n")
    return dst_txt


def translate_document(name: str, txts: list[Path], lang: str, workers: int):
    en_dir = OUT / name / "English"
    pages_dir = en_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    dsts = [pages_dir / t.name for t in txts]
    if lang == "en":
        for s, d in zip(txts, dsts):
            d.write_text(s.read_text())
    else:
        jobs = [(s, d, lang) for s, d in zip(txts, dsts) if not d.exists()]
        if jobs:
            print(f"  translating {len(jobs)} page(s) {lang}->en ...", flush=True)
            with Pool(workers) as pool:
                for n, _ in enumerate(pool.imap_unordered(translate_page, jobs), 1):
                    if n % 10 == 0 or n == len(jobs):
                        print(f"    {n}/{len(jobs)}", flush=True)
    final = en_dir / f"{name}.en.txt"
    with open(final, "w") as f:
        f.write(f"# {name} -- English text (machine translation from '{lang}' OCR)\n\n")
        for i, d in enumerate(dsts, 1):
            f.write(f"===== Page {i} =====\n{d.read_text()}\n\n")
    print(f"  -> {final.relative_to(ROOT)}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="document base names to process")
    ap.add_argument("--ocr-only", action="store_true")
    ap.add_argument("--force-ocr", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    os.environ.setdefault("ARGOS_INTRA_THREADS", str(max(1, (os.cpu_count() or 4) // a.workers)))
    pdfs = sorted(SRC.glob("*.pdf"))
    if a.only:
        pdfs = [p for p in pdfs if p.stem in a.only]
    if not pdfs:
        sys.exit("no PDFs selected")
    for pdf in pdfs:
        name = pdf.stem
        lang = LANG_OVERRIDES.get(name, "fr")
        print(f"[{name}] source language: {lang}", flush=True)
        txts = ocr_document(name, pdf, lang, a.force_ocr)
        if not a.ocr_only:
            translate_document(name, txts, lang, a.workers)


if __name__ == "__main__":
    main()
