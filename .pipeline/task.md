背景
--collect-submodules 命令行参数无法正确收集项目自有模块（tasks、browser、pages 等）
--onedir 输出结构为 python-backend-dist/backend/backend.exe，但 main.js 期望 python-backend/backend.exe
任务 1：替换 backend.spec（项目根目录）
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['scripts/pyinstaller_entry.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('pdd_selectors', 'pdd_selectors'),
        ('pages', 'pages'),
    ],
    hiddenimports=[
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
        # ── backend ──
        'backend',
        'backend.config',
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
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# 收集第三方完整包（动态子模块太多，需要 collect_all）
from PyInstaller.utils.hooks import collect_all
for pkg in ['uvicorn', 'fastapi', 'starlette', 'celery', 'kombu', 'amqp', 'redis']:
    tmp_datas, tmp_binaries, tmp_hiddenimports = collect_all(pkg)
    a.datas += tmp_datas
    a.binaries += tmp_binaries
    a.hiddenimports += tmp_hiddenimports

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend',
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
​
任务 2：替换 celery-worker.spec（项目根目录）
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['scripts/pyinstaller_celery_entry.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('pdd_selectors', 'pdd_selectors'),
        ('pages', 'pages'),
    ],
    hiddenimports=[
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
        'backend.services',
        'backend.services.after_sale_queue_service',
        'backend.services.browser_service',
        'backend.services.execute_service',
        'backend.models',
        'backend.models.database',
        'backend.models.data_structure',
        # ── browser ──
        'browser',
        'browser.anti_detection',
        'browser.captcha_recognition',
        'browser.manager',
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
        'pydantic_settings',
        'celery.fixups',
        'celery.fixups.django',
        'celery.app.amqp',
        'celery.app.events',
        'celery.app.task',
        'celery.backends',
        'celery.backends.redis',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

from PyInstaller.utils.hooks import collect_all
for pkg in ['celery', 'kombu', 'amqp', 'redis']:
    tmp_datas, tmp_binaries, tmp_hiddenimports = collect_all(pkg)
    a.datas += tmp_datas
    a.binaries += tmp_binaries
    a.hiddenimports += tmp_hiddenimports

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
​
任务 3：修改 electron/main.js 第 32-33 行
将：
const packagedBackendExe = path.join(rootDir, 'python-backend', 'backend.exe')
const packagedCeleryExe = path.join(rootDir, 'python-backend', 'celery-worker.exe')
​
改为（适配 --onedir 子目录结构）：
const packagedBackendExe = path.join(rootDir, 'python-backend', 'backend', 'backend.exe')
const packagedCeleryExe = path.join(rootDir, 'python-backend', 'celery-worker', 'celery-worker.exe')
​
验收方式
修改完 3 个文件后：
cd E:\pdd_zd

# 清空旧文件
Remove-Item -Recurse -Force python-backend-dist\* -ErrorAction SilentlyContinue

# 用 spec 文件打包（不用写长命令了）
pyinstaller --noconfirm --distpath ./python-backend-dist backend.spec
pyinstaller --noconfirm --distpath ./python-backend-dist celery-worker.spec

# 测试 backend
& ".\python-backend-dist\backend\backend.exe"
# 期望：[后端启动完成] 端口: 8000
​
改动范围
backend.spec — 完全替换
celery-worker.spec — 完全替换
electron/main.js — 仅改第 32-33 行 exe 路径