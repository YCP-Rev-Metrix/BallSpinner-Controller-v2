#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_DIR="$SCRIPT_DIR"

prompt_default() {
    local prompt="$1"
    local default_value="$2"
    local value
    read -r -p "$prompt [$default_value]: " value
    echo "${value:-$default_value}"
}

prompt_yes_no() {
    local prompt="$1"
    local default_value="$2"
    local value
    while true; do
        read -r -p "$prompt [$default_value]: " value
        value="${value:-$default_value}"
        case "$value" in
            y|Y|yes|YES) return 0 ;;
            n|N|no|NO) return 1 ;;
            *) echo "Please answer y or n." ;;
        esac
    done
}

REPO_DIR="$(prompt_default "Repo path" "$DEFAULT_REPO_DIR")"
if [[ ! -d "$REPO_DIR" ]]; then
    echo "Repo path not found: $REPO_DIR"
    exit 1
fi
REPO_DIR="$(cd "$REPO_DIR" && pwd)"

LOG_FILE="$REPO_DIR/logs/pi_install.log"
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

run_cmd() {
    echo "+ $*"
    "$@"
}

echo "=== BallSpinner Pi Install ==="

echo "Updating system packages and installing dependencies..."
run_cmd sudo apt-get update
run_cmd sudo apt-get install -y git build-essential swig liblgpio-dev bluetooth bluez libbluetooth-dev libudev-dev libboost-all-dev python3-venv rfkill

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
fi

if [[ -z "$PYTHON_BIN" ]]; then
    echo "python3 not found. Installing python3..."
    run_cmd sudo apt-get install -y python3 python3-venv
    PYTHON_BIN="python3"
fi

if command -v python3 >/dev/null 2>&1; then
    if python3 - <<'PY'
import sys
sys.exit(0 if sys.version_info >= (3, 13) else 1)
PY
    then
        echo "Detected Python >= 3.13"
    else
        if prompt_yes_no "Python < 3.13 detected. Install Python 3.13 via deadsnakes?" "N"; then
            run_cmd sudo apt-get install -y software-properties-common
            run_cmd sudo apt-get install -y --reinstall python3-launchpadlib
            run_cmd sudo add-apt-repository ppa:deadsnakes/ppa
            run_cmd sudo apt-get update
            run_cmd sudo apt-get install -y python3.13 python3.13-venv
            if command -v python3.13 >/dev/null 2>&1; then
                PYTHON_BIN="python3.13"
            fi
        else
            echo "Continuing with existing python3."
        fi
    fi
fi

VENV_DIR="$REPO_DIR/venv"
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment..."
    run_cmd "$PYTHON_BIN" -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
run_cmd "$VENV_DIR/bin/python" -m pip install --upgrade pip

echo "Installing Python dependencies..."
run_cmd "$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements-pi.txt"

SDK_ROOT="$REPO_DIR/MetaWear-SDK-Python"
PYWARBLE_DIR="$SDK_ROOT/PyWarble"
LIBBLEPP_DIR="$PYWARBLE_DIR/clibs/warble/deps/libblepp"
WARBLE_DIR="$PYWARBLE_DIR/clibs/warble"
METAWEAR_CPP_DIR="$SDK_ROOT/MetaWear-SDK-Cpp"

if [[ ! -d "$SDK_ROOT" ]]; then
    echo "Cloning MetaWear-SDK-Python..."
    run_cmd git clone --recurse-submodules git@github.com:mbientlab/MetaWear-SDK-Python.git "$SDK_ROOT"
else
    echo "MetaWear-SDK-Python already present."
fi

if [[ ! -d "$PYWARBLE_DIR" ]]; then
    echo "Cloning PyWarble..."
    run_cmd git clone --recurse-submodules https://github.com/mbientlab/PyWarble.git "$PYWARBLE_DIR"
else
    echo "PyWarble already present."
fi

if [[ -d "$LIBBLEPP_DIR" ]]; then
    echo "Building libblepp..."
    pushd "$LIBBLEPP_DIR" >/dev/null
    run_cmd ./configure
    run_cmd make
    popd >/dev/null
else
    echo "libblepp directory not found: $LIBBLEPP_DIR"
    exit 1
fi

if [[ -d "$WARBLE_DIR" ]]; then
    echo "Building warble..."
    pushd "$WARBLE_DIR" >/dev/null
    if [[ -f "Makefile" ]]; then
        if grep -q '^ARCH=' Makefile; then
            run_cmd sed -i 's/^ARCH=.*/ARCH=-march=armv8-a/' Makefile
        else
            echo 'ARCH=-march=armv8-a' >> Makefile
        fi
    fi
    run_cmd make
    popd >/dev/null
else
    echo "Warble directory not found: $WARBLE_DIR"
    exit 1
fi

JSON_HPP="$METAWEAR_CPP_DIR/src/metawear/dfu/cpp/json.hpp"
if [[ -f "$JSON_HPP" ]]; then
    if ! grep -q '<cstdint>' "$JSON_HPP"; then
        echo "Patching json.hpp to include <cstdint>..."
        tmp_file="${JSON_HPP}.tmp"
        awk 'BEGIN{added=0} {print; if(!added && $0 ~ /^#include /){print "#include <cstdint>"; added=1}}' "$JSON_HPP" > "$tmp_file"
        mv "$tmp_file" "$JSON_HPP"
    fi
else
    echo "json.hpp not found: $JSON_HPP"
    exit 1
fi

if [[ -d "$METAWEAR_CPP_DIR" ]]; then
    echo "Building MetaWear-SDK-Cpp..."
    pushd "$METAWEAR_CPP_DIR" >/dev/null
    run_cmd make CXX=g++ CXXFLAGS="-Wall -fPIC -std=c++14 -I$(pwd)/src" -j"$(nproc)"
    popd >/dev/null
else
    echo "MetaWear-SDK-Cpp directory not found: $METAWEAR_CPP_DIR"
    exit 1
fi

BLEPP_LIB="$LIBBLEPP_DIR"
BLEPP_HEADERS="$LIBBLEPP_DIR/blepp"
METAWEAR_HEADERS="$METAWEAR_CPP_DIR/src/metawear"
METAWEAR_LIB="$METAWEAR_CPP_DIR/dist/release/lib/arm"
WARBLE_BUILD="$WARBLE_DIR/dist/release/lib/arm"
if [[ ! -d "$WARBLE_BUILD" && -d "$PYWARBLE_DIR/build/lib/mbientlab/warble" ]]; then
    WARBLE_BUILD="$PYWARBLE_DIR/build/lib/mbientlab/warble"
fi

export METAWEAR_HEADERS
export METAWEAR_LIB
export BLEPP_LIB
export BLEPP_HEADERS
export WARBLE_BUILD
export LD_LIBRARY_PATH="$METAWEAR_LIB:$BLEPP_LIB:$WARBLE_BUILD:$LD_LIBRARY_PATH"
export CFLAGS="-I$METAWEAR_HEADERS -I$BLEPP_HEADERS"
export LDFLAGS="-L$METAWEAR_LIB -L$BLEPP_LIB -L$WARBLE_BUILD"

echo "Installing PyWarble..."
run_cmd "$VENV_DIR/bin/pip" install "$PYWARBLE_DIR"

echo "Installing MetaWear-SDK-Python..."
run_cmd "$VENV_DIR/bin/pip" install "$SDK_ROOT"

if prompt_yes_no "Persist MetaWear environment variables to a shell profile?" "Y"; then
    PROFILE_DEFAULT="$HOME/.bashrc"
    PROFILE_PATH="$(prompt_default "Profile to update" "$PROFILE_DEFAULT")"
    if [[ -f "$PROFILE_PATH" || "$PROFILE_PATH" == "$HOME/.bashrc" || "$PROFILE_PATH" == "$HOME/.profile" ]]; then
        if [[ -f "$PROFILE_PATH" ]] && grep -q "BallSpinner MetaWear env" "$PROFILE_PATH"; then
            tmp_profile="${PROFILE_PATH}.tmp"
            awk 'BEGIN{skip=0} /^# >>> BallSpinner MetaWear env >>>/{skip=1; next} /^# <<< BallSpinner MetaWear env <<</{skip=0; next} !skip{print}' "$PROFILE_PATH" > "$tmp_profile"
            mv "$tmp_profile" "$PROFILE_PATH"
        fi
        {
            echo "# >>> BallSpinner MetaWear env >>>"
            echo "export METAWEAR_HEADERS=\"$METAWEAR_HEADERS\""
            echo "export METAWEAR_LIB=\"$METAWEAR_LIB\""
            echo "export BLEPP_LIB=\"$BLEPP_LIB\""
            echo "export BLEPP_HEADERS=\"$BLEPP_HEADERS\""
            echo "export WARBLE_BUILD=\"$WARBLE_BUILD\""
            echo "export LD_LIBRARY_PATH=\"$METAWEAR_LIB:$BLEPP_LIB:$WARBLE_BUILD:\$LD_LIBRARY_PATH\""
            echo "export CFLAGS=\"-I$METAWEAR_HEADERS -I$BLEPP_HEADERS\""
            echo "export LDFLAGS=\"-L$METAWEAR_LIB -L$BLEPP_LIB -L$WARBLE_BUILD\""
            echo "# <<< BallSpinner MetaWear env <<<"
        } >> "$PROFILE_PATH"
        echo "Updated profile: $PROFILE_PATH"
    else
        echo "Profile not found: $PROFILE_PATH"
    fi
fi

PYTHON_REAL="$(readlink -f "$VENV_DIR/bin/python")"
echo "Ensuring Python has Bluetooth permissions..."
run_cmd sudo setcap cap_net_raw+eip "$PYTHON_REAL"

echo "Running unit tests (will continue on failure)..."
set +e
bash "$REPO_DIR/run_unit_tests.sh"
TEST_EXIT=$?
set -e
if [[ $TEST_EXIT -ne 0 ]]; then
    echo "Unit tests failed with exit code $TEST_EXIT. Continuing to startup."
else
    echo "Unit tests passed."
fi

if prompt_yes_no "Configure autostart (desktop) for startup.sh?" "N"; then
    AUTOSTART_DIR="$HOME/.config/autostart"
    run_cmd mkdir -p "$AUTOSTART_DIR"
    AUTOSTART_FILE="$AUTOSTART_DIR/RevMetrixStartupScript.desktop"
    cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=RevMetrixStartupScript
Exec=lxterminal --command="$REPO_DIR/startup.sh"
Terminal=true
EOF
    echo "Autostart file created at $AUTOSTART_FILE"
fi

echo "Starting application via startup.sh..."
run_cmd bash "$REPO_DIR/startup.sh"
