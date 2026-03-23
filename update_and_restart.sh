#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

# 1) project directory
PROJECT_DIR="BallSpinner-Controller-v2"

# 2) change directory
cd "$PROJECT_DIR"

echo "In $(pwd), pulling latest from GitHub..."

# adjust branch as needed (main/master)
git pull 

echo "Update complete. Rebooting now..."
# requires sudo (or run as root)
sudo reboot



