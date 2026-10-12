#!/bin/sh
set -u

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
FAILURES=0

ok() {
    printf 'OK: %s\n' "$1"
}

fail() {
    printf 'MISSING: %s\n' "$1" >&2
    FAILURES=$((FAILURES + 1))
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        ok "$1 ($(command -v "$1"))"
        return 0
    fi
    fail "$1"
    return 1
}

printf 'Checking PC128 workspace: %s\n' "$ROOT"

for file in config.json pc128.py mcp_server.py harness.lua .vscode/mcp.json .mcp.json; do
    if [ -f "$ROOT/$file" ]; then
        ok "workspace file $file"
    else
        fail "workspace file $file"
    fi
done

if ! check_command python3; then
    printf '\nInstall Python 3 and rerun this checker.\n' >&2
    exit 1
fi

if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    ok "Python 3.10 or newer"
else
    fail "Python 3.10 or newer (mcp_server.py requires it)"
fi

if python3 -m pip --version >/dev/null 2>&1; then
    ok "pip for $(python3 --version)"
else
    fail "pip for python3 (install python3-pip)"
fi

if python3 - <<'PY' >/dev/null 2>&1
import os, subprocess, tempfile, venv
with tempfile.TemporaryDirectory() as directory:
    venv.create(directory, with_pip=True)
    subprocess.run([os.path.join(directory, "bin", "python"), "-m", "pip", "--version"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
PY
then
    ok "Python venv support with pip"
else
    fail "Python venv support (install python3-venv, or use another supported environment)"
fi

MCP_PYTHON="$ROOT/.venv/bin/python"
if [ -x "$MCP_PYTHON" ] && PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" "$MCP_PYTHON" -c 'import mcp_server' >/dev/null 2>&1; then
    ok "MCP server imports in the workspace virtual environment"
else
    fail "MCP server unavailable in .venv; run: python3 -m venv .venv && .venv/bin/python -m pip install mcp"
fi

BUILD_PREREQUISITES=1
for command in curl tar make; do
    if ! check_command "$command"; then
        BUILD_PREREQUISITES=0
    fi
done

CC_COMMAND=${CC:-cc}
if command -v "$CC_COMMAND" >/dev/null 2>&1; then
    ok "C compiler $CC_COMMAND ($(command -v "$CC_COMMAND"))"
else
    fail "C compiler (install build-essential, or set CC)"
    BUILD_PREREQUISITES=0
fi

CONFIG_VALID=1
if ! python3 -m json.tool "$ROOT/config.json" >/dev/null 2>&1; then
    fail "valid JSON in config.json"
    CONFIG_VALID=0
fi

if [ "$CONFIG_VALID" -eq 1 ]; then
    MAME=$(python3 - "$ROOT/config.json" mame <<'PY'
import json, sys
print(json.load(open(sys.argv[1])).get(sys.argv[2], "mame"))
PY
)
    MACHINE=$(python3 - "$ROOT/config.json" machine <<'PY'
import json, sys
print(json.load(open(sys.argv[1])).get(sys.argv[2], "pro128"))
PY
)
    ROMPATH=$(python3 - "$ROOT/config.json" rompath <<'PY'
import json, os, sys
value = json.load(open(sys.argv[1])).get(sys.argv[2], "")
print(os.path.expandvars(os.path.expanduser(value)))
PY
)
    case "$ROMPATH" in
        ""|/*) ;;
        *) ROMPATH="$ROOT/$ROMPATH" ;;
    esac

    if python3 "$ROOT/tools/prepare-roms.py"; then
        ok "PC128 and CD90 ROM files prepared in roms/"
        ROMS_READY=1
    else
        fail "prepare ROM files from src-rom/"
        ROMS_READY=0
    fi

    ROMPATH_VALID=1
    if [ -n "$ROMPATH" ] && [ ! -d "$ROMPATH" ]; then
        fail "configured MAME ROM path exists: $ROMPATH"
        ROMPATH_VALID=0
    fi

    if command -v "$MAME" >/dev/null 2>&1; then
        ok "MAME executable $MAME"
        if [ "$ROMPATH_VALID" -eq 1 ] && [ "$ROMS_READY" -eq 1 ]; then
            set -- -verifyroms "$MACHINE"
            if [ -n "$ROMPATH" ]; then
                set -- "$@" -rompath "$ROMPATH"
            fi
            if "$MAME" "$@" >/dev/null 2>&1; then
                ok "MAME machine and ROM set $MACHINE"
            else
                fail "MAME ROM set $MACHINE; see config.json and docs/mame-pc128.md"
            fi
        fi
    else
        fail "MAME executable '$MAME' (install MAME and/or set mame in config.json)"
    fi
else
    printf 'Skipping MAME and ROM checks because config.json is invalid.\n' >&2
fi

LWASM="$ROOT/tools/.local/lwtools-4.24/lwasm/lwasm"
if [ -x "$LWASM" ]; then
    ok "repository-local lwasm"
elif [ "$BUILD_PREREQUISITES" -eq 1 ]; then
    printf 'Local lwasm is absent; building it now.\n'
    if "$ROOT/tools/setup-lwasm.sh" && [ -x "$LWASM" ]; then
        ok "repository-local lwasm built successfully"
    else
        fail "local lwasm build; see tools/setup-lwasm.sh output"
    fi
else
    fail "local lwasm is absent and its build prerequisites are missing"
fi

if [ "$FAILURES" -eq 0 ]; then
    printf '\nEnvironment check passed.\n'
    exit 0
fi

printf '\nEnvironment check found %s issue(s).\n' "$FAILURES" >&2
printf 'Debian/Ubuntu system packages: sudo apt install curl tar make build-essential python3 python3-pip python3-venv mame\n' >&2
exit 1