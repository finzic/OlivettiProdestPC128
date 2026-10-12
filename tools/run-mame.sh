#!/usr/bin/env bash
# Usage: run-mame.sh <floppy|cassette|cartridge|none> [image]
set -eu
cd "$(dirname "$0")/.."
kind="${1:-none}"
img="${2:-}"
# tools/mame-cfg remaps UI keys: F11 = MAME menu, F12 = exit (Esc no longer quits)
args=(pro128 -rompath ./roms -window -noconfirm_quit -ui_active -cfg_directory tools/mame-cfg)

if [[ "$kind" != none ]]; then
  [[ -n "$img" && -f "$img" ]] || { echo "Image not found: '$img'" >&2; exit 1; }
  img="$(realpath "$img")"
fi

case "$kind" in
  floppy)   args+=(-extension cd90_640 -flop1 "$img") ;;
  cassette) args+=(-cassette "$img") ;;
  cartridge) args+=(-cart "$img") ;;
  none)     ;;
  *) echo "Unknown media: $kind" >&2; exit 1 ;;
esac

exec mame "${args[@]}"
