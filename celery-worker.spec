# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

额外二进制 = []
额外数据 = [
    ('scripts/encoding_hook.py', 'scripts'),
    ('pdd_selectors', 'pdd_selectors'),
    ('pages', 'pages'),
]
额外导入 = [
    # ── tasks ──
    'tasks',
    'tasks.after_sale_task',
    'tasks.async_utils',
    'tasks.base_task',
    'tasks.bridge_task',
    'tasks.celery_app',
    'tasks.execute_task',
    'tasks.flash_sale_task',
    'tasks.login_task',
    'tasks.promotion_task',
    'tasks.publish_replace_image_task',
    'tasks.publish_similar_product_task',
    'tasks.registry',
    'tasks.scheduled_task',
    'tasks.task_registry',
    # ── backend（celery worker 也可能依赖 config） ──
    'backend',
    'backend.config',
    'backend.logging_config',
    'backend.services',
    'backend.services.after_sale_queue_service',
    'backend.services.browser_service',
    'backend.services.execute_service',
    'backend.services.metrics_service',
    'backend.models',
    'backend.models.database',
    'backend.models.data_structure',
    'backend.models.settings_model',
    'backend.utils',
    'backend.utils.crypto',
    'backend.utils.settings',
    # ── browser ──
    'browser',
    'browser.anti_detection',
    'browser.captcha_recognition',
    'browser.manager',
    'browser.recovery',
    'browser.session_monitor',
    'browser.slider_captcha',
    'browser.task_callback',
    'browser.user_dir_factory',
    # ── pages ──
    'pages',
    'pages.after_sale_page',
    'pages.base_page',
    'pages.desktop_base_page',
    'pages.flash_sale_page',
    'pages.login_page',
    'pages.product_list_page',
    'pages.promotion_page',
    'pages.publish_product_page',
    'pages.wechat_page',
    # ── pdd_selectors ──
    'pdd_selectors',
    'pdd_selectors.after_sale_page_selector',
    'pdd_selectors.base_page_selector',
    'pdd_selectors.desktop_selector_config',
    'pdd_selectors.flash_sale_page_selector',
    'pdd_selectors.login_page_selector',
    'pdd_selectors.product_list_page_selector',
    'pdd_selectors.promotion_page_selector',
    'pdd_selectors.publish_product_page_selector',
    'pdd_selectors.selector_config',
    'pdd_selectors.wechat_selector',
    # ── 第三方 ──
    'nest_asyncio',
    'aiosqlite',
    'cryptography',
    'httpx',
    'celery.fixups',
    'celery.fixups.django',
    'celery.app.amqp',
    'celery.app.events',
    'celery.app.task',
    'celery.backends',
    'celery.backends.redis',
]

for pkg in ['celery', 'kombu', 'amqp', 'redis']:
    tmp_datas, tmp_binaries, tmp_hiddenimports = collect_all(pkg)
    额外数据 += tmp_datas
    额外二进制 += tmp_binaries
    额外导入 += tmp_hiddenimports

a = Analysis(
    ['scripts/pyinstaller_celery_entry.py'],
    pathex=['.'],
    binaries=额外二进制,
    datas=额外数据,
    hiddenimports=额外导入,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['scripts/encoding_hook.py'],
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
