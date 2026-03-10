# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Ball Spinner Controller
# Builds a --onedir bundle for macOS, Windows, and Linux.
# Run:  pyinstaller BallSpinnerController.spec

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# ---------------------------------------------------------------------------
# Platform-specific icon
# ---------------------------------------------------------------------------
if sys.platform == 'darwin':
    icon_file = 'Icons/BSC_Icon.icns'   # produced by CI icon-conversion step
elif sys.platform == 'win32':
    icon_file = 'Icons/BSC_Icon.ico'    # produced by CI icon-conversion step
else:
    icon_file = 'Icons/BSC_Icon.png'

# ---------------------------------------------------------------------------
# Collect entire packages so Qt plugins, pyqtgraph colormap data, etc.
# are all included automatically.
# ---------------------------------------------------------------------------
pyqt6_datas,   pyqt6_binaries,   pyqt6_hiddens   = collect_all('PyQt6')
pyqtgraph_datas, pyqtgraph_binaries, pyqtgraph_hiddens = collect_all('pyqtgraph')
numpy_datas,   numpy_binaries,   numpy_hiddens   = collect_all('numpy')
gpiozero_datas, gpiozero_binaries, gpiozero_hiddens = collect_all('gpiozero')
colorzero_datas, colorzero_binaries, colorzero_hiddens = collect_all('colorzero')
pywt_datas,    pywt_binaries,    pywt_hiddens    = collect_all('pywt')

# ---------------------------------------------------------------------------
# Application data files (non-Python assets that must ship with the bundle)
# ---------------------------------------------------------------------------
import glob

ui_files  = [(f, 'frontend') for f in glob.glob('frontend/*.ui')]
qss_files = [('frontend/style.qss', 'frontend')]
icon_data = [('Icons', 'Icons')]

all_datas = (
    ui_files
    + qss_files
    + icon_data
    + pyqt6_datas
    + pyqtgraph_datas
    + numpy_datas
    + gpiozero_datas
    + colorzero_datas
    + pywt_datas
)

all_binaries = (
    pyqt6_binaries
    + pyqtgraph_binaries
    + numpy_binaries
    + gpiozero_binaries
    + colorzero_binaries
    + pywt_binaries
)

all_hiddens = (
    pyqt6_hiddens
    + pyqtgraph_hiddens
    + numpy_hiddens
    + gpiozero_hiddens
    + colorzero_hiddens
    + pywt_hiddens
    + [
        # PyQt6 dynamic UI loading
        'PyQt6.uic',
        'PyQt6.sip',
        # gpiozero mock pin factory used by SimMotor
        'gpiozero.pins.mock',
        'gpiozero.pins.native',
        # Other app dependencies
        'requests',
        'certifi',
        'urllib3',
        'charset_normalizer',
        'idna',
        # Local packages
        'logs.logger_config',
        'ErrorHandling.ErrorHandling',
        # Motor interface + SimMotor (used on all platforms)
        'backend.motors.iMotor',
        'backend.motors.SimMotor',
        # Driver scripts
        'backend.drivers.ShotScript',
        'backend.drivers.DiagnosticScript',
    ]
)

# ---------------------------------------------------------------------------
# Modules to exclude from the bundle entirely.
# Pi-hardware packages and the real motor drivers are never used on desktop.
# ---------------------------------------------------------------------------
excluded_modules = [
    # Pi GPIO stacks
    'lgpio',
    'pigpio',
    'spidev',
    'RPi',
    'RPi.GPIO',
    # VESC / serial (Pi motor hardware)
    'pyvesc',
    'crcmod',
    'serial',
    # Real motor drivers (Pi-only)
    'backend.motors.BDCMotor',
    'backend.motors.StepMotor',
    'backend.motors.StepScript',
    'backend.motors.USBBDCMotor',
    # Dev / test
    'pytest',
    'pytest_qt',
    '_pytest',
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddens,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # --onedir: binaries live next to the exe
    name='BallSpinnerController',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                  # no terminal window on desktop
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BallSpinnerController',
)

# macOS .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Ball Spinner Controller.app',
        icon=icon_file,
        bundle_identifier='com.ballspinner.controller',
        info_plist={
            'CFBundleDisplayName': 'Ball Spinner Controller',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSBluetoothAlwaysUsageDescription': 'Required to connect to SmartDot sensors.',
        },
    )
