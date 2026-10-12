#!/bin/sh
set -eu

TOOLS_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VERSION=4.24
INSTALL_DIR="$TOOLS_DIR/.local/lwtools-$VERSION"
LWASM="$INSTALL_DIR/lwasm/lwasm"
ARCHIVE_URL="https://www.lwtools.ca/releases/lwtools/lwtools-$VERSION.tar.gz"

if [ -x "$LWASM" ]; then
    printf 'lwasm already installed: %s\n' "$LWASM"
    exit 0
fi

for command in curl tar make; do
    if ! command -v "$command" >/dev/null 2>&1; then
        printf 'Required command not found: %s\n' "$command" >&2
        exit 1
    fi
done

if ! command -v "${CC:-cc}" >/dev/null 2>&1; then
    printf 'A C compiler is required (set CC or install cc).\n' >&2
    exit 1
fi

TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/lwtools-$VERSION.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM

ARCHIVE="$TMP_DIR/lwtools-$VERSION.tar.gz"
SOURCE_DIR="$TMP_DIR/lwtools-$VERSION"

printf 'Downloading LWTOOLS %s...\n' "$VERSION"
curl --fail --location --silent --show-error "$ARCHIVE_URL" --output "$ARCHIVE"
tar -xzf "$ARCHIVE" -C "$TMP_DIR"

if [ ! -f "$SOURCE_DIR/Makefile" ]; then
    printf 'Unexpected LWTOOLS archive layout: %s\n' "$SOURCE_DIR" >&2
    exit 1
fi

printf 'Building LWTOOLS %s...\n' "$VERSION"
make -C "$SOURCE_DIR" CC="${CC:-cc}"

if [ ! -x "$SOURCE_DIR/lwasm/lwasm" ]; then
    printf 'LWTOOLS build did not produce lwasm/lwasm.\n' >&2
    exit 1
fi

mkdir -p "$(dirname -- "$LWASM")"
install -m 755 "$SOURCE_DIR/lwasm/lwasm" "$LWASM"
printf 'Installed local lwasm: %s\n' "$LWASM"