#!/bin/bash
# Run integration tests only
# Integration tests use real components and test complete workflows
# These tests may require actual hardware/components or may be marked as skipped

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Use the virtual environment Python
PYTHON_CMD="$SCRIPT_DIR/venv/bin/python"

echo "=========================================="
echo "Running INTEGRATION TESTS"
echo "=========================================="
echo ""

$PYTHON_CMD -m pytest tests/integration/ -v --tb=short "$@"

echo ""
echo "=========================================="
echo "Integration tests complete!"
echo "=========================================="
