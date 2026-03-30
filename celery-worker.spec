# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules

datas = []
hiddenimports = ['tasks', 'browser', 'backend', 'pages', 'pdd_selectors']
datas += collect_data_files('tasks')
datas += collect_data_files('browser')
datas += collect_data_files('backend')
datas += collect_data_files('pages')
datas += collect_data_files('pdd_selectors')
hiddenimports += collect_submodules('tasks')
hiddenimports += collect_submodules('browser')
hiddenimports += collect_submodules('backend')
hiddenimports += collect_submodules('pages')
hiddenimports += collect_submodules('pdd_selectors')
hiddenimports += collect_submodules('celery')
hiddenimports += collect_submodules('kombu')


a = Analysis(
    ['scripts/pyinstaller_celery_entry.py'],
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
    name='celery-worker',
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
