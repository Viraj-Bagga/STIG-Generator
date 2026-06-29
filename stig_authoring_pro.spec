# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for STIG Authoring Pro — Linux/Debian build

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Collect all CustomTkinter assets (themes, images, fonts)
ctk_datas = collect_data_files("customtkinter")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=ctk_datas,
    hiddenimports=[
        "customtkinter",
        "darkdetect",
        "packaging",
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "xml.etree.ElementTree",
        "xml.sax.saxutils",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="STIG-Authoring-Pro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,        # single binary output
)
