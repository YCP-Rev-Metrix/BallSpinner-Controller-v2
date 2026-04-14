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

PYTEST_ARGS=()
if [[ "${RUN_GUI_TESTS:-}" != "1" ]]; then
	PYTEST_ARGS+=(
		--ignore "tests/unit/test_analysis_mode_bandpass.py"
		--ignore "tests/unit/test_gui_interactions_unit.py"
		--ignore "tests/unit/test_gui_windows.py"
		--ignore "tests/unit/test_wavelet_dialog.py"
		--ignore "tests/unit/test_wavelet_helper_widget.py"
	)
fi

$PYTHON_CMD -m pytest tests/unit/ -v --tb=short "${PYTEST_ARGS[@]}" "$@"

echo ""
echo "=========================================="
echo "Unit tests complete!"
echo "=========================================="
