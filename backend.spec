# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all
import os
from pathlib import Path

# ── 自动生成 frozen task 模块列表 ──
_tasks_dir = Path("tasks")
_排除模块 = {
    "__init__", "registry", "task_registry", "base_task",
    "celery_app", "bridge_task", "execute_task", "scheduled_task",
    "async_utils", "_frozen_modules",
}
_task_modules = sorted([
    f.stem for f in _tasks_dir.glob("*.py")
    if f.stem not in _排除模块 and not f.stem.startswith("_")
])
_frozen_file = _tasks_dir / "_frozen_modules.py"
_frozen_file.write_text(
    f"# 此文件由 backend.spec 自动生成，请勿手动编辑\nMODULES = {_task_modules!r}\n",
    encoding="utf-8",
)
print(f"[spec] 已生成 {_frozen_file}，模块: {_task_modules}")

额外二进制 = []
额外数据 = [
    ('.env', '.'),
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
    'tasks._frozen_modules',
    'tasks.login_task',
    'tasks.promotion_task',
    'tasks.publish_replace_image_task',
    'tasks.publish_similar_product_task',
    'tasks.registry',
    'tasks.scheduled_task',
    'tasks.task_registry',
    # ── backend ──
    'backend',
    'backend.config',
    'backend.logging_config',
    'backend.main',
    'backend.api',
    'backend.api.router',
    'backend.api.after_sale_config_api',
    'backend.api.available_tasks',
    'backend.api.browser_api',
    'backend.api.execute_api',
    'backend.api.feishu_api',
    'backend.api.flow_api',
    'backend.api.flow_input_api',
    'backend.api.flow_params_api',
    'backend.api.generic_task_api',
    'backend.api.log_api',
    'backend.api.rule_api',
    'backend.api.run_api',
    'backend.api.scheduled_execute_api',
    'backend.api.shop_api',
    'backend.api.system_api',
    'backend.api.task_api',
    'backend.api.task_params_api',
    'backend.models',
    'backend.models.after_sale_config_model',
    'backend.models.after_sale_queue_model',
    'backend.models.data_structure',
    'backend.models.database',
    'backend.models.flow_model',
    'backend.models.rule_model',
    'backend.models.scheduled_task_model',
    'backend.models.shop_model',
    'backend.models.table_schema',
    'backend.services',
    'backend.services.after_sale_config_service',
    'backend.services.after_sale_decision_engine',
    'backend.services.after_sale_queue_service',
    'backend.services.browser_service',
    'backend.services.email_service',
    'backend.services.execute_service',
    'backend.services.feishu_service',
    'backend.services.flow_input_service',
    'backend.services.flow_params_service',
    'backend.services.flow_service',
    'backend.services.heartbeat_service',
    'backend.services.log_service',
    'backend.services.metrics_service',
    'backend.services.rule_service',
    'backend.services.run_service',
    'backend.services.scheduled_execute_service',
    'backend.services.shop_service',
    'backend.services.system_service',
    'backend.services.task_params_service',
    'backend.services.task_service',
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
    'openpyxl',
    'pydantic_settings',
    'httpx',
    'uiautomation',
    'celery.fixups',
    'celery.fixups.django',
    'celery.app.amqp',
    'celery.app.events',
    'celery.app.task',
    'celery.backends',
    'celery.backends.redis',
]

for pkg in ['uvicorn', 'fastapi', 'starlette', 'celery', 'kombu', 'amqp', 'redis']:
    tmp_datas, tmp_binaries, tmp_hiddenimports = collect_all(pkg)
    额外数据 += tmp_datas
    额外二进制 += tmp_binaries
    额外导入 += tmp_hiddenimports

a = Analysis(
    ['scripts/pyinstaller_entry.py'],
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
    name='backend',
    contents_directory='.',
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
    name='backend',
)
