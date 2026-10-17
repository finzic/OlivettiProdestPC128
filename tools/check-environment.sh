#!/bin/sh
set -u

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
FAILURES=0
USER_COMMANDS=""
SYSTEM_PACKAGES_NEEDED=0

ok() {
    printf 'OK: %s\n' "$1"
}

fail() {
    printf 'MISSING: %s\n' "$1" >&2
    FAILURES=$((FAILURES + 1))
}

add_user_command() {
    if [ -n "$USER_COMMANDS" ]; then
        USER_COMMANDS="$USER_COMMANDS
$1"
    else
        USER_COMMANDS=$1
    fi
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

PYTHON_AVAILABLE=0
PYTHON_READY=0
if check_command python3; then
    PYTHON_AVAILABLE=1
    if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
        ok "Python 3.10 or newer"
        PYTHON_READY=1
    else
        fail "Python 3.10 or newer (mcp_server.py requires it)"
        SYSTEM_PACKAGES_NEEDED=1
    fi
else
    SYSTEM_PACKAGES_NEEDED=1
fi

MCP_PYTHON="$ROOT/.venv/bin/python"
if [ "$PYTHON_READY" -eq 1 ]; then
    if [ -x "$MCP_PYTHON" ] && PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" "$MCP_PYTHON" -c 'import mcp_server' >/dev/null 2>&1; then
        ok "MCP server imports in the workspace virtual environment"
    else
        printf 'Setting up the workspace Python environment.\n'
        if python3 -m venv "$ROOT/.venv" && \
            "$MCP_PYTHON" -m pip install mcp && \
            PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" "$MCP_PYTHON" -c 'import mcp_server' >/dev/null 2>&1; then
            ok "MCP server environment created and verified"
        else
            fail "could not create a working MCP environment in .venv"
            SYSTEM_PACKAGES_NEEDED=1
            add_user_command "\"$MCP_PYTHON\" -m pip install mcp"
        fi
    fi
else
    fail "MCP server environment requires Python 3.10 or newer"
fi

BUILD_PREREQUISITES=1
for command in curl tar make; do
    if ! check_command "$command"; then
        BUILD_PREREQUISITES=0
        SYSTEM_PACKAGES_NEEDED=1
    fi
done

CC_COMMAND=${CC:-cc}
if command -v "$CC_COMMAND" >/dev/null 2>&1; then
    ok "C compiler $CC_COMMAND ($(command -v "$CC_COMMAND"))"
else
    fail "C compiler (install build-essential, or set CC)"
    BUILD_PREREQUISITES=0
    SYSTEM_PACKAGES_NEEDED=1
fi

CONFIG_VALID=1
if [ "$PYTHON_AVAILABLE" -eq 1 ] && ! python3 -m json.tool "$ROOT/config.json" >/dev/null 2>&1; then
    fail "valid JSON in config.json"
    CONFIG_VALID=0
elif [ "$PYTHON_AVAILABLE" -eq 0 ]; then
    CONFIG_VALID=0
fi

if [ "$CONFIG_VALID" -eq 1 ]; then
    MAME=$(python3 - "$ROOT/config.json" mame <<'PY'
import json, sys
print(json.load(open(sys.argv[1])).get(sys.argv[2], "mame"))
PY
)
    LOCAL_MAME="$ROOT/tools/.local/mame/mame_thomson/thomson"
    if [ "$MAME" = "mame" ]; then
        MAME=$LOCAL_MAME
    fi
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

    ROM_FILES_READY=1
    for file in \
        roms/pro128/pro128.iw01 roms/pro128/basico.iw02 \
        roms/pro128/basico-0.rom roms/pro128/pro128-0.rom \
        roms/pro128/basico-1.rom roms/pro128/pro128-1.rom \
        roms/pro128/basico-2.rom roms/pro128/basico-3.rom \
        roms/cd90_351/cd-351-0.rom roms/cd90_351/cd-351-1.rom \
        roms/cd90_351/cd-351-2.rom roms/cd90_351/cd-351-3.rom; do
        if [ ! -s "$ROOT/$file" ]; then
            ROM_FILES_READY=0
        fi
    done

    if [ "$ROM_FILES_READY" -eq 1 ]; then
        ok "prepared ROM files already exist; skipping ROM preparation"
        ROMS_READY=1
    elif [ "$PYTHON_AVAILABLE" -eq 1 ] && python3 "$ROOT/tools/prepare-roms.py"; then
        ok "PC128 and CD90 ROM files prepared in roms/"
        ROMS_READY=1
    else
        fail "prepare ROM files from src-rom/"
        ROMS_READY=0
        add_user_command "python3 \"$ROOT/tools/prepare-roms.py\""
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
        fail "MAME executable '$MAME' (build the patched MAME with tools/prepare-mame.sh)"
        SYSTEM_PACKAGES_NEEDED=1
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

if [ "$SYSTEM_PACKAGES_NEEDED" -eq 1 ]; then
    if [ -n "$USER_COMMANDS" ]; then
        USER_COMMANDS="sudo apt install curl tar make build-essential python3 python3-pip python3-venv mame
$USER_COMMANDS"
    else
        USER_COMMANDS="sudo apt install curl tar make build-essential python3 python3-pip python3-venv mame"
    fi
fi

if [ "$FAILURES" -eq 0 ]; then
    printf '\nEnvironment check passed.\n'
    if [ -n "$USER_COMMANDS" ]; then
        printf '\nCommands to run:\n%s\n' "$USER_COMMANDS"
    fi
    exit 0
fi

printf '\nEnvironment check found %s issue(s).\n' "$FAILURES" >&2
if [ -n "$USER_COMMANDS" ]; then
    printf '\nCommands to run:\n%s\n' "$USER_COMMANDS"
fi
exit 1
