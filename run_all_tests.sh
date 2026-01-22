#!/bin/bash
# Run all tests (unit + integration + any at root level)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Use the virtual environment Python
PYTHON_CMD="$SCRIPT_DIR/venv/bin/python"

echo "=========================================="
echo "Running ALL TESTS"
echo "=========================================="
echo ""

$PYTHON_CMD -m pytest tests/ -v --tb=short "$@"

echo ""
echo "=========================================="
echo "All tests complete!"
echo "=========================================="
