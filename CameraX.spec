# -*- mode: python ; coding: utf-8 -*-
import os

import onvif
from PyInstaller.utils.hooks import collect_all

datas = [("assets/icon.ico", "assets"), ("assets/icon.png", "assets")]
binaries = []
hiddenimports = []

# These packages ship WSDL/XSD data files (onvif, zeep) or dynamic imports
# (wsdiscovery) that PyInstaller's static analysis won't find on its own.
for pkg in ("onvif", "wsdiscovery", "zeep"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# onvif-zeep looks up its WSDL files at runtime relative to its own module
# path: dirname(dirname(onvif/client.py)) + "/wsdl". In the installed package
# that's a sibling of the "onvif" folder (site-packages/wsdl), so
# collect_all("onvif") above never picks it up. Bundle it at the bundle root
# so it lands at sys._MEIPASS/wsdl, matching what onvif expects when frozen.
onvif_wsdl_dir = os.path.join(os.path.dirname(os.path.dirname(onvif.__file__)), "wsdl")
datas.append((onvif_wsdl_dir, "wsdl"))

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="CameraX",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
)
