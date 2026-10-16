#!/usr/bin/env bash
# Prepare a local MAME build with CD 90-351 (THMFC1) write support for the PC128.
#
# Usage: tools/prepare-mame.sh [--no-build] [--jobs N] [TARGET_DIR]
#   TARGET_DIR  default: tools/.local/mame
#
# Clones MAME at the commit the patch was made against (mame-patch/BASE_COMMIT),
# applies mame-patch/*.patch and builds the "thomson" subtarget. The result is
# TARGET_DIR/mame_thomson/thomson, which pc128.py and tools/run-mame.sh pick up automatically.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATCH_DIR="$ROOT/mame-patch"
TARGET="$ROOT/tools/.local/mame"
BUILD=1
JOBS="$(nproc 2>/dev/null || echo 4)"
(( JOBS > 6 )) && JOBS=6
MAME_URL="${MAME_URL:-https://github.com/mamedev/mame.git}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-build) BUILD=0 ;;
    --jobs) JOBS="$2"; shift ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) TARGET="$(realpath -m "$1")" ;;
  esac
  shift
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing tool: $1 ($2)" >&2; exit 1; }; }
need git "install git"
need python3 "MAME's build needs Python 3"
if [[ $BUILD -eq 1 ]]; then
  need make "install build-essential"
  need g++ "install build-essential (GCC 12+ or clang 14+)"
  pkg-config --exists sdl2 2>/dev/null || echo "Warning: SDL2 development files not found; on Debian/Ubuntu: sudo apt install libsdl2-dev libsdl2-ttf-dev libfontconfig-dev libpulse-dev" >&2
fi

BASE="$(tr -d '[:space:]' < "$PATCH_DIR/BASE_COMMIT")"
mkdir -p "$TARGET"

if [[ ! -d "$TARGET/.git" ]]; then
  echo "== Fetching MAME $BASE into $TARGET"
  git -C "$TARGET" init -q
  git -C "$TARGET" remote add origin "$MAME_URL"
fi
if ! git -C "$TARGET" cat-file -e "$BASE^{commit}" 2>/dev/null; then
  git -C "$TARGET" fetch --depth 1 origin "$BASE"
fi
# Keep local edits out of the way only if the tree is clean; otherwise stop.
if [[ -n "$(git -C "$TARGET" status --porcelain --untracked-files=no | grep -v 'thmfc1\.\(cpp\|h\)$' || true)" ]]; then
  echo "$TARGET has unrelated local changes; refusing to touch it." >&2; exit 1
fi
git -C "$TARGET" checkout -q -f "$BASE"
git -C "$TARGET" checkout -q -- src/devices/machine/thmfc1.cpp src/devices/machine/thmfc1.h

echo "== Applying patches"
for p in "$PATCH_DIR"/*.patch; do
  git -C "$TARGET" apply --whitespace=nowarn "$p"
  echo "applied $(basename "$p")"
done
for f in thmfc1.cpp thmfc1.h; do
  cmp -s "$TARGET/src/devices/machine/$f" "$PATCH_DIR/src/devices/machine/$f" \
    || { echo "$f differs from mame-patch/src copy; regenerate the patch" >&2; exit 1; }
done

if [[ $BUILD -eq 0 ]]; then
  echo "Patched source ready in $TARGET (build skipped)."; exit 0
fi

echo "== Building (SUBTARGET=thomson, -j$JOBS); this takes a while"
cp "$PATCH_DIR/thomson.flt" "$TARGET/src/mame/thomson/thomson.flt"
make -C "$TARGET" SUBTARGET=thomson SOURCEFILTER=src/mame/thomson/thomson.flt USE_QTDEBUG=0 -j"$JOBS"
echo
echo "Done: $TARGET/mame_thomson/thomson"
