# -*- mode: python ; coding: utf-8 -*-

import glob
import os

frontend_ui_files = [(f, 'frontend') for f in glob.glob('frontend/*.ui')]
frontend_style_files = [(f, 'frontend') for f in glob.glob('frontend/*.qss')]
icon_files = [(f, 'Icons') for f in glob.glob('Icons/BSC_Icon.*')]
help_files = []
for root, _dirs, files in os.walk('frontend/help'):
    for filename in files:
        if filename.endswith('.md'):
            source = os.path.join(root, filename)
            destination = root
            help_files.append((source, destination))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=
        frontend_ui_files +
        frontend_style_files +
        icon_files +
        help_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BallSpinnerController',
    icon='Icons/BSC_Icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
app = BUNDLE(
    coll,
    name='BallSpinnerController.app',
    icon='Icons/BSC_Icon.icns',
    bundle_identifier=None,
)
