#!/usr/bin/env bash
#
# ocr_translate.sh
#
# For every PDF in a source folder:
#   1. OCRs it with Tesseract (default language: French)
#   2. Creates a dedicated target folder for that PDF
#   3. Saves the raw French OCR text, an English translation and an
#      Italian translation, each in its own subfolder
#
# Result layout:
#   <TARGET_DIR>/<pdf-basename>/French_OCR/ocr.txt
#   <TARGET_DIR>/<pdf-basename>/English/translation.txt
#   <TARGET_DIR>/<pdf-basename>/Italian/translation.txt
#
# ---------------------------------------------------------------------------
# DEPENDENCIES
#   sudo apt update
#   sudo apt install -y tesseract-ocr tesseract-ocr-fra poppler-utils
#
#   Translation engine - pick ONE of the two:
#
#   a) translate-shell (online, uses Google/Bing/Yandex - simplest, best quality)
#      sudo apt install -y translate-shell
#      (if not packaged on your release: pip install --user translate-shell
#       or download from https://github.com/soimort/translate-shell)
#
#   b) argos-translate (fully offline, no internet needed, lower quality)
#      pip install --user argostranslate
#      argospm install translate-fr_en translate-en-it   # or fr->it/en->it as needed
#      (run once: python3 -c "import argostranslate.package as p; p.update_package_index()")
#
#   Select the engine with -e trans   (default)
#                        or -e argos
# ---------------------------------------------------------------------------
#
# USAGE
#   ./ocr_translate.sh -s /path/to/source_pdfs -t /path/to/target_folder \
#                       [-l fra] [-e trans|argos] [-r 300] [-k]
#
#   -s   source folder containing the PDFs (required)
#   -t   target/output root folder (required)
#   -l   Tesseract OCR language code (default: fra)
#   -e   translation engine: trans (default) or argos
#   -r   OCR rendering DPI (default: 300; use 400+ for small/faint scans)
#   -k   keep temporary page images/text for debugging
#   -f   force re-processing even if output already exists
#
# ---------------------------------------------------------------------------

set -euo pipefail

# set $PATH=$PATH:$HOME/bin/

# ---------------------------- defaults --------------------------------
OCR_LANG="fra"
ENGINE="trans"
DPI=300
KEEP_TEMP=0
FORCE=0
SOURCE_DIR=""
TARGET_DIR=""

# ---------------------------- helpers ----------------------------------
log()  { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
    grep '^#   ' "$0" | sed 's/^#   //'
    exit 1
}

check_bin() {
    command -v "$1" >/dev/null 2>&1 || die "Required command '$1' not found. See dependency notes at the top of this script."
}

# ---------------------------- parse args --------------------------------
while getopts ":s:t:l:e:r:kfh" opt; do
    case "$opt" in
        s) SOURCE_DIR="$OPTARG" ;;
        t) TARGET_DIR="$OPTARG" ;;
        l) OCR_LANG="$OPTARG" ;;
        e) ENGINE="$OPTARG" ;;
        r) DPI="$OPTARG" ;;
        k) KEEP_TEMP=1 ;;
        f) FORCE=1 ;;
        h) usage ;;
        *) usage ;;
    esac
done

[[ -z "$SOURCE_DIR" || -z "$TARGET_DIR" ]] && usage
[[ -d "$SOURCE_DIR" ]] || die "Source folder '$SOURCE_DIR' does not exist."

case "$ENGINE" in
    trans|argos) ;;
    *) die "Unknown engine '$ENGINE' (use 'trans' or 'argos')" ;;
esac

mkdir -p "$TARGET_DIR"

# ---------------------------- dependency checks --------------------------
check_bin pdftoppm
check_bin tesseract

if ! tesseract --list-langs 2>&1 | grep -qx "$OCR_LANG"; then
    die "Tesseract language pack '$OCR_LANG' not installed (sudo apt install tesseract-ocr-$OCR_LANG)"
fi

if [[ "$ENGINE" == "trans" ]]; then
    check_bin trans
else
    check_bin ./bin/argos-translate
fi

# ---------------------------- translation function ------------------------
# Splits the input file on blank lines (paragraphs) and translates each
# paragraph separately to stay under API/engine length limits, then
# reassembles the result with blank lines preserved.
translate_file() {
    local in_file="$1" src_lang="$2" tgt_lang="$3" out_file="$4"
    : > "$out_file"

    local paragraph=""
    local first=1

    while IFS='' read -r line || [[ -n "$line" ]]; do
        if [[ -z "$line" ]]; then
            if [[ -n "$paragraph" ]]; then
                translate_paragraph "$paragraph" "$src_lang" "$tgt_lang" "$out_file" "$first"
                first=0
                paragraph=""
            fi
            printf '\n' >> "$out_file"
        else
            if [[ -z "$paragraph" ]]; then
                paragraph="$line"
            else
                paragraph="$paragraph"$'\n'"$line"
            fi
        fi
    done < "$in_file"

    # flush last paragraph if file doesn't end with a blank line
    if [[ -n "$paragraph" ]]; then
        translate_paragraph "$paragraph" "$src_lang" "$tgt_lang" "$out_file" "$first"
    fi
}

translate_paragraph() {
    local text="$1" src_lang="$2" tgt_lang="$3" out_file="$4" first="$5"
    local translated=""

    if [[ "$ENGINE" == "trans" ]]; then
        translated=$(printf '%s' "$text" \
            | trans -b -no-ansi ":${tgt_lang}" -s "$src_lang" 2>/dev/null || true)
    else
        translated=$(printf '%s' "$text" \
            | argos-translate --from-lang "$src_lang" --to-lang "$tgt_lang" 2>/dev/null || true)
    fi

    if [[ -z "$translated" ]]; then
        translated="[TRANSLATION FAILED - original text below]"$'\n'"$text"
    fi

    printf '%s\n' "$translated" >> "$out_file"
}

# ---------------------------- main processing loop ------------------------
shopt -s nullglob nocaseglob
pdf_files=("$SOURCE_DIR"/*.pdf)
shopt -u nocaseglob
shopt -u nullglob

[[ ${#pdf_files[@]} -eq 0 ]] && die "No PDF files found in '$SOURCE_DIR'"

log "Found ${#pdf_files[@]} PDF file(s) to process."

for pdf in "${pdf_files[@]}"; do
    base="$(basename "$pdf")"
    name="${base%.*}"
    out_dir="$TARGET_DIR/$name"
    fr_dir="$out_dir/French_OCR"
    en_dir="$out_dir/English"
    it_dir="$out_dir/Italian"

    if [[ -f "$fr_dir/ocr.txt" && -f "$en_dir/translation.txt" && -f "$it_dir/translation.txt" && "$FORCE" -eq 0 ]]; then
        log "SKIP (already processed): $base"
        continue
    fi

    log "Processing: $base"
    mkdir -p "$fr_dir" "$en_dir" "$it_dir"

    workdir="$(mktemp -d)"
    trap '[[ "$KEEP_TEMP" -eq 0 ]] && rm -rf "$workdir"' RETURN

    log "  Rendering pages at ${DPI} DPI..."
    pdftoppm -r "$DPI" -png "$pdf" "$workdir/page"

    page_images=("$workdir"/page-*.png)
    if [[ ${#page_images[@]} -eq 0 ]]; then
        # pdftoppm may zero-pad differently on single-page PDFs
        page_images=("$workdir"/page*.png)
    fi
    [[ ${#page_images[@]} -eq 0 ]] && { log "  WARNING: no pages rendered, skipping $base"; continue; }

    ocr_full="$fr_dir/ocr.txt"
    : > "$ocr_full"

    page_num=0
    for img in $(printf '%s\n' "${page_images[@]}" | sort -V); do
        page_num=$((page_num + 1))
        log "  OCR page $page_num/${#page_images[@]}..."
        page_txt="$workdir/page-$page_num"
        tesseract "$img" "$page_txt" -l "$OCR_LANG" --psm 3 >/dev/null 2>&1 || \
            log "  WARNING: tesseract failed on page $page_num of $base"
        printf -- '----- Page %d -----\n' "$page_num" >> "$ocr_full"
        [[ -f "${page_txt}.txt" ]] && cat "${page_txt}.txt" >> "$ocr_full"
        printf '\n\n' >> "$ocr_full"
    done

    log "  Translating to English..."
    translate_file "$ocr_full" "fr" "en" "$en_dir/translation.txt"

    log "  Translating to Italian..."
    translate_file "$ocr_full" "fr" "it" "$it_dir/translation.txt"

    [[ "$KEEP_TEMP" -eq 1 ]] && cp -r "$workdir" "$out_dir/_debug_pages"

    log "  Done: $base -> $out_dir"
done

log "All files processed. Output in: $TARGET_DIR"
