# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['scripts\\pyinstaller_celery_entry.py'],
    pathex=[],
    binaries=[],
    datas=[('pdd_selectors', 'pdd_selectors'), ('pages', 'pages'), ('tasks', 'tasks')],
    hiddenimports=['tasks.pdd_task', 'celery.app.task'],
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
    name='celery-worker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='celery-worker',
)
