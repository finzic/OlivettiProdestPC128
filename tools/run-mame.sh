#!/usr/bin/env bash
# Usage: run-mame.sh <floppy|floppy351|cassette|cartridge|none> [image] [image2 (floppy351 only)]
set -eu
cd "$(dirname "$0")/.."
kind="${1:-none}"
img="${2:-}"
# tools/mame-cfg remaps UI keys: F11 = MAME menu, F12 = exit (Esc no longer quits)
args=(pro128 -rompath ./roms -window -resolution 960x720 -nomaximize -noconfirm_quit -ui_active -throttle -speed 1.0 -cfg_directory tools/mame-cfg)

if [[ "$kind" != none ]]; then
  [[ -n "$img" && -f "$img" ]] || { echo "Image not found: '$img'" >&2; exit 1; }
  img="$(realpath "$img")"
fi

case "$kind" in
  floppy)   args+=(-extension cd90_640 -flop1 "$img") ;;
  floppy351)
    # 3.5" CD90-351: needs 80-track images; optional 3rd arg = image for the second drive (2:/3:)
    args+=(-extension cd90_351 -flop1 "$img")
    [[ -n "${3:-}" ]] && args+=(-extension:cd90_351:thmfc1:1 dd90_352 -flop2 "$(realpath "$3")")
    ;;
  cassette) args+=(-cassette "$img") ;;
  cartridge) args+=(-cart "$img") ;;
  none)     ;;
  *) echo "Unknown media: $kind" >&2; exit 1 ;;
esac

MAME=mame
[[ -x tools/.local/mame/mame_thomson/thomson ]] && MAME=tools/.local/mame/mame_thomson/thomson
exec "$MAME" "${args[@]}"
