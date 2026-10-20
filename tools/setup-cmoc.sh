#!/bin/sh
# Build the CMOC 6809 C compiler into tools/.local/cmoc-$VERSION (no root needed).
#
# Requirements: curl, tar, make, a C/C++ compiler, and GNU bison + flex
# (CMOC's configure insists on them). If bison/flex are missing and you
# cannot run `sudo apt install bison flex`, this script fetches the Debian
# packages with `apt-get download` and unpacks them locally.
set -eu

TOOLS_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VERSION=${CMOC_VERSION:-0.1.100}
LOCAL_DIR="$TOOLS_DIR/.local"
INSTALL_DIR="$LOCAL_DIR/cmoc-$VERSION"
CMOC="$INSTALL_DIR/bin/cmoc"
LWBIN="$LOCAL_DIR/lwtools-4.24/bin"
HOSTDEPS="$LOCAL_DIR/hostdeps"
ARCHIVE_URL="http://sarrazip.com/dev/cmoc-$VERSION.tar.gz"

if [ -x "$CMOC" ]; then
    printf 'cmoc already installed: %s\n' "$CMOC"
    exit 0
fi

for command in curl tar make; do
    if ! command -v "$command" >/dev/null 2>&1; then
        printf 'Required command not found: %s\n' "$command" >&2
        exit 1
    fi
done
if ! command -v "${CXX:-c++}" >/dev/null 2>&1; then
    printf 'A C++ compiler is required (install g++).\n' >&2
    exit 1
fi

# CMOC's build compiles its runtime library with lwasm/lwar, and cmoc itself
# calls lwasm and lwlink, so a complete LWTOOLS must be on PATH.
"$TOOLS_DIR/setup-lwasm.sh"
PATH="$LWBIN:$HOSTDEPS/usr/bin:$PATH"
export PATH

if ! command -v bison >/dev/null 2>&1 || ! command -v flex >/dev/null 2>&1; then
    if ! command -v apt-get >/dev/null 2>&1; then
        printf 'GNU bison and flex are required; please install them.\n' >&2
        exit 1
    fi
    printf 'bison/flex not found: unpacking Debian packages into %s\n' "$HOSTDEPS"
    DEB_DIR=$(mktemp -d "${TMPDIR:-/tmp}/cmoc-debs.XXXXXX")
    (cd "$DEB_DIR" && apt-get download bison flex m4 libfl2 libfl-dev)
    mkdir -p "$HOSTDEPS"
    for deb in "$DEB_DIR"/*.deb; do
        dpkg -x "$deb" "$HOSTDEPS"
    done
    rm -rf "$DEB_DIR"
fi
# A relocated bison needs to find its skeletons and m4.
if [ -d "$HOSTDEPS/usr/share/bison" ]; then
    BISON_PKGDATADIR="$HOSTDEPS/usr/share/bison"
    M4="$HOSTDEPS/usr/bin/m4"
    export BISON_PKGDATADIR M4
fi

TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/cmoc-$VERSION.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM

printf 'Downloading CMOC %s...\n' "$VERSION"
curl --fail --location --silent --show-error "$ARCHIVE_URL" --output "$TMP_DIR/cmoc.tar.gz"
tar -xzf "$TMP_DIR/cmoc.tar.gz" -C "$TMP_DIR"
SOURCE_DIR="$TMP_DIR/cmoc-$VERSION"

printf 'Building CMOC %s...\n' "$VERSION"
(
    cd "$SOURCE_DIR"
    ./configure --prefix="$INSTALL_DIR"
    make
    make install
)

if [ ! -x "$CMOC" ]; then
    printf 'CMOC build did not produce %s\n' "$CMOC" >&2
    exit 1
fi
printf 'Installed local CMOC: %s\n' "$CMOC"
printf 'It needs lwasm/lwlink on PATH: export PATH="%s:$PATH"\n' "$LWBIN"
