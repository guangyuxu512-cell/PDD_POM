# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules

datas = []
hiddenimports = ['backend', 'uvicorn.logging', 'uvicorn.protocols.http']
datas += collect_data_files('backend')
datas += collect_data_files('tasks')
hiddenimports += collect_submodules('backend')
hiddenimports += collect_submodules('tasks')
hiddenimports += collect_submodules('celery')
hiddenimports += collect_submodules('kombu')
hiddenimports += collect_submodules('browser')


a = Analysis(
    ['entry_backend.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
