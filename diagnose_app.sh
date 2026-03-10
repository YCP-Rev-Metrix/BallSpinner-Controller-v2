#!/bin/bash
# Diagnostic script to troubleshoot BallSpinnerController app launch issues
# Usage: ./diagnose_app.sh /path/to/BallSpinnerController.app

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 /path/to/BallSpinnerController.app"
    exit 1
fi

APP_PATH="$1"
APP_BIN="$APP_PATH/Contents/MacOS/BallSpinnerController"

if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: App not found at $APP_PATH"
    exit 1
fi

if [ ! -f "$APP_BIN" ]; then
    echo "ERROR: Executable not found at $APP_BIN"
    exit 1
fi

mkdir -p app_diagnostics

echo "╔════════════════════════════════════════════════════════════════╗"
echo "  BallSpinnerController Diagnostic Report"
echo "╚════════════════════════════════════════════════════════════════╝"

echo ""
echo "📋 SYSTEM INFORMATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
uname -a
echo "Python version:"
python3 --version
echo "Qt version in PATH:"
python3 -c "from PyQt6.QtCore import QT_VERSION_STR; print('PyQt6:', QT_VERSION_STR)" 2>/dev/null || echo "PyQt6 not available in Python"

echo ""
echo "📦 APP EXECUTABLE DETAILS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Path: $APP_BIN"
file "$APP_BIN"
ls -lh "$APP_BIN"

echo ""
echo "🔐 CODE SIGNATURE & ENTITLEMENTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Signature verification:"
codesign -v "$APP_BIN" && echo "✓ Valid signature" || echo "✗ Invalid signature"
echo ""
echo "Signature details (verbose):"
codesign -dvvv "$APP_BIN" 2>&1 | grep -E "Authority|Identifier|Code|Signature" || true
echo ""
echo "Entitlements:"
codesign -d --entitlements :- "$APP_BIN" 2>&1 || echo "(No entitlements)"

echo ""
echo "📚 LINKED LIBRARIES & DEPENDENCIES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Direct dependencies (otool -L):"
otool -L "$APP_BIN" | head -20

echo ""
echo "Looking for missing libraries (starts with @loader_path or /usr/local):"
otool -L "$APP_BIN" | grep -E "@loader_path|/usr/local" || echo "(All standard system paths)"

echo ""
echo "🔗 BUNDLED FRAMEWORKS & LIBRARIES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Frameworks:"
find "$APP_PATH" -name "*.framework" -type d 2>/dev/null | head -10 || echo "(None found)"
echo ""
echo "Shared libraries:"
find "$APP_PATH" -name "*.dylib" -o -name "*.so" 2>/dev/null | head -10 || echo "(None found)"

echo ""
echo "🧪 LAUNCH TEST 1: HEADLESS MODE (QT_QPA_PLATFORM=offscreen)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
export QT_QPA_PLATFORM=offscreen
chmod +x "$APP_BIN"
if timeout 5 "$APP_BIN" > app_diagnostics/headless_output.log 2>&1; then
    echo "✓ Headless mode: Success"
else
    EXIT_CODE=$?
    echo "✗ Headless mode: Failed (exit code: $EXIT_CODE)"
fi
echo "Output:"
head -50 app_diagnostics/headless_output.log

echo ""
echo "🧪 LAUNCH TEST 2: GUI MODE (default)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
unset QT_QPA_PLATFORM
if timeout 5 "$APP_BIN" > app_diagnostics/gui_output.log 2>&1; then
    echo "✓ GUI mode: Success"
else
    EXIT_CODE=$?
    echo "✗ GUI mode: Failed (exit code: $EXIT_CODE)"
fi
echo "Output:"
head -50 app_diagnostics/gui_output.log

echo ""
echo "🧪 LAUNCH TEST 3: WITH DEBUG OUTPUT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
export DYLD_PRINT_LIBRARIES=1
export QT_DEBUG_PLUGINS=1
if timeout 5 "$APP_BIN" > app_diagnostics/debug_output.log 2>&1; then
    echo "✓ Debug mode: Success"
else
    EXIT_CODE=$?
    echo "✗ Debug mode: Failed (exit code: $EXIT_CODE)"
fi
echo "Output (first 100 lines):"
head -100 app_diagnostics/debug_output.log

echo ""
echo "🧪 LAUNCH TEST 4: USING 'open' COMMAND"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Running: open -W '$APP_PATH' --args"
if timeout 5 open -W "$APP_PATH" --args > app_diagnostics/open_output.log 2>&1; then
    echo "✓ open command: Success"
else
    EXIT_CODE=$?
    echo "✗ open command: Failed (exit code: $EXIT_CODE)"
fi
echo "Output:"
cat app_diagnostics/open_output.log || echo "(No output)"

echo ""
echo "📝 SYSTEM LOGS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Recent crash logs:"
log show --predicate 'process == "BallSpinnerController"' --last 10m 2>/dev/null | head -50 || echo "(No recent logs)"

echo ""
echo "✅ DIAGNOSTICS COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Detailed logs saved to: app_diagnostics/"
ls -lh app_diagnostics/

echo ""
echo "📋 Next steps:"
echo "1. Review the output above for any error messages"
echo "2. Check app_diagnostics/*.log files for detailed output"
echo "3. Look for missing library dependencies (red flags: @loader_path, /usr/local)"
echo "4. If you see architecture mismatches, verify your Mac CPU (Apple Silicon vs Intel)"
echo "5. Share the full output with the developers"
