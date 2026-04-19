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

configure_vnc() {
    local vnc_service="vncserver-x11-serviced.service"

    if ! command -v raspi-config >/dev/null 2>&1; then
        echo "raspi-config not found; skipping automatic VNC enable."
        return
    fi

    echo "Enabling VNC via raspi-config..."
    if run_cmd sudo raspi-config nonint do_vnc 0; then
        echo "VNC interface enabled."
    else
        echo "Warning: failed to enable VNC with raspi-config."
        return
    fi

    if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files "$vnc_service" --no-legend 2>/dev/null | grep -q "$vnc_service"; then
        echo "Ensuring VNC service is enabled and running..."
        run_cmd sudo systemctl enable "$vnc_service"
        run_cmd sudo systemctl restart "$vnc_service"
    else
        echo "VNC service unit not found; verify VNC server package is installed."
    fi
}

echo "=== BallSpinner Pi Install ==="

echo "Updating system packages and installing dependencies..."
run_cmd sudo apt-get update
run_cmd sudo apt-get install -y git build-essential swig liblgpio-dev bluetooth bluez libbluetooth-dev libudev-dev libboost-all-dev python3-venv rfkill

if prompt_yes_no "Enable VNC for remote desktop access now?" "Y"; then
    configure_vnc
fi

CONFIG_FILE="/boot/firmware/config.txt"
if prompt_yes_no "Set GPIO defaults low for BCM 5 and 6 in /boot/firmware/config.txt?" "Y"; then
    if [[ -f "$CONFIG_FILE" ]]; then
        echo "Updating GPIO defaults in $CONFIG_FILE..."
        run_cmd sudo cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
        TMP_FILE="/tmp/ballspinner_config.txt"
        run_cmd sudo awk 'BEGIN{skip=0} /^# >>> BallSpinner GPIO defaults >>>/{skip=1; next} /^# <<< BallSpinner GPIO defaults <<</{skip=0; next} !skip{print}' "$CONFIG_FILE" > "$TMP_FILE"
        run_cmd sudo mv "$TMP_FILE" "$CONFIG_FILE"
        run_cmd sudo bash -c "cat <<'EOF' >> '$CONFIG_FILE'
# >>> BallSpinner GPIO defaults >>>
gpio=5,6=op,dl
# <<< BallSpinner GPIO defaults <<<
EOF"
        echo "GPIO defaults set. Reboot required to apply boot-time defaults."
    else
        echo "Config file not found: $CONFIG_FILE"
    fi
fi

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
    if [[ ! -d "$SDK_ROOT/.git" ]]; then
        if prompt_yes_no "MetaWear-SDK-Python exists but is not a git repo. Replace with fresh clone?" "Y"; then
            backup_dir="${SDK_ROOT}.bak.$(date +%Y%m%d%H%M%S)"
            run_cmd mv "$SDK_ROOT" "$backup_dir"
            echo "Cloning MetaWear-SDK-Python..."
            run_cmd git clone --recurse-submodules git@github.com:mbientlab/MetaWear-SDK-Python.git "$SDK_ROOT"
        else
            echo "MetaWear-SDK-Python repo is required. Aborting."
            exit 1
        fi
    else
        echo "MetaWear-SDK-Python already present."
        run_cmd git -C "$SDK_ROOT" submodule update --init --recursive
    fi
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
        HOST_ARCH="$(uname -m)"
        if [[ "$HOST_ARCH" == "aarch64" || "$HOST_ARCH" == "arm64" ]]; then
            run_cmd sed -i 's/-marm//g' Makefile
            if grep -q '^ARCH=' Makefile; then
                run_cmd sed -i 's/^ARCH=.*/ARCH=-march=armv8-a/' Makefile
            else
                echo 'ARCH=-march=armv8-a' >> Makefile
            fi
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
export LD_LIBRARY_PATH="$METAWEAR_LIB:$BLEPP_LIB:$WARBLE_BUILD${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CFLAGS="-I$METAWEAR_HEADERS -I$BLEPP_HEADERS"
export LDFLAGS="-L$METAWEAR_LIB -L$BLEPP_LIB -L$WARBLE_BUILD"

echo "Installing PyWarble..."
WARBLE_PY_LIB_DIR="$PYWARBLE_DIR/mbientlab/warble"
if [[ -d "$WARBLE_PY_LIB_DIR" ]]; then
    run_cmd rm -f "$WARBLE_PY_LIB_DIR"/libwarble.so*
fi
run_cmd "$VENV_DIR/bin/pip" install "$PYWARBLE_DIR"

echo "Installing MetaWear-SDK-Python..."
METAWEAR_PY_LIB_DIR="$SDK_ROOT/mbientlab/metawear"
if [[ -d "$METAWEAR_PY_LIB_DIR" ]]; then
    run_cmd rm -f "$METAWEAR_PY_LIB_DIR"/libmetawear.so*
fi
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
    echo "Unit tests failed with exit code $TEST_EXIT. Continuing to autostart setup."
else
    echo "Unit tests passed."
fi

echo "Configuring autostart (desktop) for startup.sh..."
run_cmd chmod +x "$REPO_DIR/startup.sh"
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

if prompt_yes_no "Reboot now to apply autostart and GPIO defaults?" "Y"; then
    run_cmd sudo reboot
else
    echo "Reboot when ready to apply autostart and GPIO defaults."
fi
