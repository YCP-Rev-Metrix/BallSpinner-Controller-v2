#!/bin/bash
echo "this is our startup script!"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"

echo "performing bluetooth magic commands so we can connect to the pi"

PYTHON_BIN="$REPO_DIR/venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
    PYTHON_BIN="$(command -v python3)"
fi

echo "ensure python has permission to use the bluetooth hardware"
sudo setcap cap_net_raw+eip "$(readlink -f "$PYTHON_BIN")"

#echo "restart the bluetooth service"
#sudo systemctl restart bluetooth
#echo "waiting 3 seconds"
#sleep 3

cd "$REPO_DIR"

echo "Current directory $(pwd)"

if [[ -f "$REPO_DIR/venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$REPO_DIR/venv/bin/activate"
else
    echo "Warning: venv not found, using system python."
fi

while true; do
    if "$PYTHON_BIN" "$REPO_DIR/main.py"; then
        echo "main.py finished successfully."
        break                 # exit the loop
    else
        echo "main.py failed (exit $?)."
        echo "Please ensure the E-Stop is not pressed."
        echo "Press ENTER to retry or Ctrl-C to quit."
        read -r              # wait for the user to hit Enter
    fi
done