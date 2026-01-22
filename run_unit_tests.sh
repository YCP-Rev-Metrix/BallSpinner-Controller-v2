#!/bin/bash
# Run unit tests only
# Unit tests are fast and test components in isolation

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Use the virtual environment Python
PYTHON_CMD="$SCRIPT_DIR/venv/bin/python"

echo "=========================================="
echo "Running UNIT TESTS"
echo "=========================================="
echo ""

$PYTHON_CMD -m pytest tests/unit/ -v --tb=short "$@"

echo ""
echo "=========================================="
echo "Unit tests complete!"
echo "=========================================="
