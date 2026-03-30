"""
PyInstaller 入口脚本回归测试
"""
import runpy
import sys
import types
from pathlib import Path
from types import SimpleNamespace


项目根目录 = Path(__file__).resolve().parents[2]


def _移除项目根目录(monkeypatch) -> None:
    """避免 pytest 运行时自带的项目根目录影响断言。"""
    过滤后路径 = []
    项目根目录字符串 = str(项目根目录.resolve())

    for 路径项 in sys.path:
        if not 路径项:
            continue
        try:
            if str(Path(路径项).resolve()) == 项目根目录字符串:
                continue
        except OSError:
            pass
        过滤后路径.append(路径项)

    monkeypatch.setattr(sys, "path", 过滤后路径)


def _准备后端入口依赖(monkeypatch) -> None:
    """注入后端入口脚本所需的最小依赖。"""
    backend包 = types.ModuleType("backend")
    backend包.__path__ = []

    backend主模块 = types.ModuleType("backend.main")
    backend主模块.app = object()

    backend配置模块 = types.ModuleType("backend.config")
    backend配置模块.配置实例 = SimpleNamespace(BACKEND_PORT=8000)

    uvicorn模块 = types.ModuleType("uvicorn")
    uvicorn模块.run = lambda *args, **kwargs: None

    monkeypatch.setitem(sys.modules, "backend", backend包)
    monkeypatch.setitem(sys.modules, "backend.main", backend主模块)
    monkeypatch.setitem(sys.modules, "backend.config", backend配置模块)
    monkeypatch.setitem(sys.modules, "uvicorn", uvicorn模块)


def _准备Celery入口依赖(monkeypatch) -> None:
    """注入 Celery 入口脚本所需的最小依赖。"""
    tasks包 = types.ModuleType("tasks")
    tasks包.__path__ = []

    celery模块 = types.ModuleType("tasks.celery_app")
    celery模块.celery_app = SimpleNamespace(worker_main=lambda *args, **kwargs: None)

    monkeypatch.setitem(sys.modules, "tasks", tasks包)
    monkeypatch.setitem(sys.modules, "tasks.celery_app", celery模块)


class 测试_PyInstaller入口:
    """验证开发模式与冻结模式的路径注入差异。"""

    def test_后端入口_开发模式下注入项目根目录(self, monkeypatch):
        """非 frozen 模式应手动插入项目根目录。"""
        _移除项目根目录(monkeypatch)
        _准备后端入口依赖(monkeypatch)
        monkeypatch.delattr(sys, "frozen", raising=False)

        runpy.run_path(str(项目根目录 / "scripts" / "pyinstaller_entry.py"))

        assert sys.path[0] == str(项目根目录)

    def test_后端入口_冻结模式下不注入项目根目录(self, monkeypatch):
        """frozen 模式应保留 PyInstaller 默认 sys.path。"""
        _移除项目根目录(monkeypatch)
        _准备后端入口依赖(monkeypatch)
        monkeypatch.setattr(sys, "frozen", True, raising=False)

        runpy.run_path(str(项目根目录 / "scripts" / "pyinstaller_entry.py"))

        assert str(项目根目录) not in sys.path

    def test_Celery入口_开发模式下注入项目根目录(self, monkeypatch):
        """非 frozen 模式下，Celery 入口也应手动插入项目根目录。"""
        _移除项目根目录(monkeypatch)
        _准备Celery入口依赖(monkeypatch)
        monkeypatch.delattr(sys, "frozen", raising=False)

        模块变量 = runpy.run_path(str(项目根目录 / "scripts" / "pyinstaller_celery_entry.py"))

        assert sys.path[0] == str(项目根目录)
        assert 模块变量["构建Worker参数"]() == ["worker", "-P", "solo", "-l", "INFO"]

    def test_Celery入口_冻结模式下不注入项目根目录(self, monkeypatch):
        """frozen 模式下不应重复覆盖 PyInstaller 设置的路径。"""
        _移除项目根目录(monkeypatch)
        _准备Celery入口依赖(monkeypatch)
        monkeypatch.setattr(sys, "frozen", True, raising=False)

        runpy.run_path(str(项目根目录 / "scripts" / "pyinstaller_celery_entry.py"))

        assert str(项目根目录) not in sys.path
