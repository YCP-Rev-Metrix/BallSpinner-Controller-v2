#!/bin/bash
echo "this is our startup script!"

echo "sleeping to let pi get ready"

echo "setting the display variable"
export DISPLAY=:0


cd /home/ballz/BallSpinner-Controller-v2/

echo "Current directory $(pwd)"

source venv/bin/activate

python3 main.py
