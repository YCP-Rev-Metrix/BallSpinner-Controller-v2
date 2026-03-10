# macOS App Launch Troubleshooting Guide

## Summary of Changes

I've enhanced the GitHub Actions build workflow with comprehensive diagnostics and created tools to help identify why your app fails to launch when built via CI.

### 1. ✅ Enhanced GitHub Actions Workflow (`build.yml`)

**New diagnostic steps added:**
- **Architecture Check** - Shows if the built app is arm64 (Apple Silicon) or x86_64 (Intel)
- **Code Signature Verification** - Validates code signing and entitlements
- **Dependency Analysis** - Lists all linked libraries and bundled frameworks
- **Multiple Launch Tests**:
  - Headless mode (QT_QPA_PLATFORM=offscreen)
  - GUI mode (standard launch)
  - Debug output capture with DYLD_PRINT_LIBRARIES
- **Diagnostic Log Upload** - Artifacts saved so you can review them after the build

### 2. 📋 Diagnostic Script (`diagnose_app.sh`)

Created a shell script to run detailed diagnostics on your app **after** you download it from GitHub Actions.

**Usage:**
```bash
cd /path/to/downloaded/BallSpinnerController.app
/path/to/repo/diagnose_app.sh /path/to/BallSpinnerController.app
```

**What it checks:**
- System architecture and versions
- Executable details (file type, size, permissions)
- Code signature validity and entitlements
- Linked libraries and frameworks
- Multiple launch scenarios (headless, GUI, debug)
- macOS system logs
- Generates detailed logs in `app_diagnostics/` folder

---

## Next Steps

### Step 1: Run the GitHub Actions Workflow
1. Push your changes to GitHub (workflow file is already updated)
2. Go to your GitHub repo → **Actions** tab
3. Find the latest "Build Executables" workflow run
4. **Download all artifacts**, especially:
   - `BallSpinnerController-macOS-app` (the built app)
   - `build-diagnostics` (logs from the CI build)

### Step 2: Review CI Diagnostics
1. Extract the `build-diagnostics` artifact
2. Check these log files for error clues:
   - `macos-launch.log` - Headless mode output
   - `macos-gui-launch.log` - GUI mode output

**Look for:**
- Missing library error messages
- Qt plugin loading failures
- Architecture warnings
- Permission/code-signing errors

### Step 3: Run Local Diagnostics
1. Extract the app from the ZIP: `unzip BallSpinnerController-macOS.zip`
2. Run the diagnostic script:
   ```bash
   ./diagnose_app.sh ./BallSpinnerController.app
   ```
3. Review the output for:
   - ✓ Red flags: Missing libraries, code signing issues
   - ✓ Architecture mismatch (arm64 vs x86_64)
   - ✓ Qt plugin failures
   - ✓ Framework not found errors

### Step 4: Share Findings

Common issues to look for:

| Issue | Cause | Fix |
|-------|-------|-----|
| "dyld: Library not loaded" | Missing dependency not bundled | Add to PyInstaller hiddenimports |
| "Mach-O, arm64" on Intel Mac | Architecture mismatch | Rebuild targeting correct arch |
| Code signature invalid | Entitlements conflict | Review `entitlements.plist` in workflow |
| "No such file or directory" in Qt | Missing Qt plugins | Verify PyQt6 in spec file collects all plugins |
| Permission denied | Executable not marked executable | Check `chmod +x` in workflow |

---

## Quick Debug: Manual Launch Tests

If you want to test the downloaded app without running the full script:

```bash
# Test 1: Check if it's a valid executable
file BallSpinnerController.app/Contents/MacOS/BallSpinnerController

# Test 2: Try launching in terminal (shows errors)
/path/to/BallSpinnerController.app/Contents/MacOS/BallSpinnerController

# Test 3: Launch with debug output
DYLD_PRINT_LIBRARIES=1 /path/to/BallSpinnerController.app/Contents/MacOS/BallSpinnerController 2>&1 | head -100

# Test 4: Check code signature
codesign -dvvv /path/to/BallSpinnerController.app
```

---

## Potential Causes & Fixes

### 🔸 Issue: Silent Failure (App Asks Permission, Then Exits)

**Likely causes:**
1. **Qt Environment Plugin** - Qt can't find a usable GUI plugin in headless environment
   - Fix: Ensure PyQt6 plugins are bundled (check in `BallSpinnerController.app/Contents/Frameworks`)

2. **Library Loading Failure** - A dependency can't be loaded at runtime
   - Fix: Run diagnostic script to spot missing .dylib files

3. **Code Signing Entitlements** - Entitlements conflict with Qt/PyQt6's requirements
   - Fix: Remove `com.apple.security.cs.allow-jit` if present, keep only what's needed

4. **Architecture Mismatch** - Built for wrong architecture
   - Check: What's your Mac CPU? (Apple Silicon M1/M2/M3 or Intel?)
   - Fix: Rebuild workflow if GitHub runner is different architecture

### 🔹 Issue: Missing Frameworks After Build

If the diagnostics show missing PyQt6 frameworks:
- Verify PyInstaller spec uses `collect_all('PyQt6')`
- Ensure `PyQt6` is in `requirements.txt` (not just PyQt6-Qt6)

### 📌 Issue: Works Locally But Not in CI

Common causes:
- **Python version mismatch** - Local Python 3.10, CI uses 3.11 (or vice versa)
- **Architecture mismatch** - Local is arm64, CI defaults to x86_64
- **Missing dependencies** - Installed locally but not in requirements.txt
- **Platform detection** - Code assumes Raspberry Pi when not

---

## Files Changed

- ✅ `.github/workflows/build.yml` - Enhanced with diagnostics
- ✅ `diagnose_app.sh` - New diagnostic script (already executable)

---

## Questions?

If diagnostics show a specific error, please share:
1. Output of `diagnose_app.sh` (or the specific error log)
2. Output of `uname -m` (to confirm your Mac's architecture)
3. Which GitHub Actions logs show errors (macos-launch.log or macos-gui-launch.log)
