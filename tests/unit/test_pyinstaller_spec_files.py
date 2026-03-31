from pathlib import Path


项目根目录 = Path(__file__).resolve().parents[2]


def 读取文件(路径: str) -> str:
    return (项目根目录 / 路径).read_text(encoding="utf-8")


def test_backend_spec_显式收集关键模块且移除_collect_submodules():
    spec内容 = 读取文件("backend.spec")

    assert "pathex=['.']" in spec内容
    assert "from pathlib import Path" in spec内容
    assert "_frozen_file = _tasks_dir / \"_frozen_modules.py\"" in spec内容
    assert "MODULES = {_task_modules!r}" in spec内容
    assert "'tasks._frozen_modules'" in spec内容
    assert "('.env', '.')" not in spec内容
    assert "contents_directory='.'" in spec内容
    assert "'backend.api.task_api'" in spec内容
    assert "'backend.api.settings_api'" in spec内容
    assert "'backend.services.task_service'" in spec内容
    assert "'backend.utils.settings'" in spec内容
    assert "'browser.task_callback'" in spec内容
    assert "'pages.publish_product_page'" in spec内容
    assert "'pdd_selectors.selector_config'" in spec内容
    assert "for pkg in ['uvicorn', 'fastapi', 'starlette', 'celery', 'kombu', 'amqp', 'redis']:" in spec内容
    assert "collect_submodules" not in spec内容


def test_frozen_task_modules_会被_gitignore_忽略():
    gitignore内容 = 读取文件(".gitignore")

    assert "tasks/_frozen_modules.py" in gitignore内容


def test_celery_worker_spec_显式收集关键模块且移除_collect_submodules():
    spec内容 = 读取文件("celery-worker.spec")

    assert "pathex=['.']" in spec内容
    assert "'tasks.execute_task'" in spec内容
    assert "'backend.services.execute_service'" in spec内容
    assert "'backend.models.database'" in spec内容
    assert "'backend.utils.settings'" in spec内容
    assert "'browser.manager'" in spec内容
    assert "'pages.wechat_page'" in spec内容
    assert "for pkg in ['celery', 'kombu', 'amqp', 'redis']:" in spec内容
    assert "collect_submodules" not in spec内容


def test_Electron_打包路径改为_onedir_子目录结构():
    主进程文件 = 读取文件("electron/main.js")

    assert "const packagedBackendExe = path.join(rootDir, 'python-backend', 'backend', 'backend.exe')" in 主进程文件
    assert "const packagedCeleryExe = path.join(rootDir, 'python-backend', 'celery-worker', 'celery-worker.exe')" in 主进程文件
    assert "const packagedBackendExe = path.join(rootDir, 'python-backend', 'backend.exe')" not in 主进程文件
    assert "const packagedCeleryExe = path.join(rootDir, 'python-backend', 'celery-worker.exe')" not in 主进程文件
