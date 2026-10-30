# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: single-file Windows build.

Produces one self-contained .exe. The app unpacks its bundled files to a temp
folder on each launch, so startup is slower than the one-folder build.
"""
from PyInstaller.utils.hooks import collect_submodules


def _keep(name):
    return ".tests" not in name and ".testing" not in name


hiddenimports = []
for package in (
    "fastapi",
    "uvicorn",
    "pydantic",
    "starlette",
    "anyio",
    "python_multipart",
    "multipart",
    "openpyxl",
    "pandas",
    "sqlalchemy",
):
    hiddenimports += collect_submodules(package, filter=_keep)

# pywebview picks its platform backend dynamically, so PyInstaller cannot see it.
hiddenimports += [
    "webview.platforms.edgechromium",
    "webview.platforms.winforms",
    "webview.platforms.win32",
]

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=[],
    datas=[("static", "static")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ES Client Manager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
