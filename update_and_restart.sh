#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

# 1) project directory
PROJECT_DIR="BallSpinner-Controller-v2"

# 2) change directory
cd "$PROJECT_DIR"

echo "In $(pwd), pulling latest from GitHub..."

# 3) update from GitHub
git fetch --all --prune
# adjust branch as needed (main/master)
git pull --ff-only origin main

# 4) restart; adjust to your actual service restart command
if [ -x "./restartbluetooth.sh" ]; then
  echo "Running restartbluetooth.sh..."
  ./restartbluetooth.sh
else
  echo "No restart script found in project root. Please run your restart command manually."
fi

echo "Update + restart done."
