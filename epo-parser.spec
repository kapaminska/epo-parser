# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for one-file Windows console build of epo-parser.exe."""

from PyInstaller.utils.hooks import collect_all

block_cipher = None

lxml_datas, lxml_binaries, lxml_hiddenimports = collect_all("lxml")

datas = [
    ("pdf/assets/DejaVuSans.ttf", "pdf/assets"),
] + lxml_datas

hiddenimports = [
    "lxml.etree",
    "lxml._elementpath",
    "fpdf",
    "fontTools",
    "fontTools.ttLib",
] + lxml_hiddenimports

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=lxml_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="epo-parser",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
