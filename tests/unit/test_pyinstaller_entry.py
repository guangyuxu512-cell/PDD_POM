"""
PyInstaller 入口脚本回归测试
"""
import os
import runpy
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


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

    def test_后端入口_冻结模式下不注入项目根目录(self, monkeypatch, tmp_path: Path):
        """frozen 模式应保留 PyInstaller 默认 sys.path。"""
        _移除项目根目录(monkeypatch)
        _准备后端入口依赖(monkeypatch)
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(tmp_path / "backend.exe"), raising=False)
        monkeypatch.chdir(项目根目录)

        runpy.run_path(str(项目根目录 / "scripts" / "pyinstaller_entry.py"))

        assert str(项目根目录) not in sys.path

    def test_后端入口_冻结模式切换到_exe_所在目录(self, monkeypatch, tmp_path: Path):
        """frozen 模式启动前应切换 cwd 到 exe 所在目录。"""
        _移除项目根目录(monkeypatch)
        _准备后端入口依赖(monkeypatch)
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(tmp_path / "backend.exe"), raising=False)
        monkeypatch.chdir(项目根目录)

        runpy.run_path(str(项目根目录 / "scripts" / "pyinstaller_entry.py"))

        assert Path.cwd() == tmp_path

    def test_后端入口_导入失败时写入_crash_log(self, monkeypatch, tmp_path: Path):
        """打包模式导入异常时应生成 crash.log 便于排查。"""
        _移除项目根目录(monkeypatch)
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(tmp_path / "backend.exe"), raising=False)
        monkeypatch.chdir(tmp_path)

        uvicorn模块 = types.ModuleType("uvicorn")
        monkeypatch.setitem(sys.modules, "uvicorn", uvicorn模块)
        monkeypatch.delitem(sys.modules, "backend", raising=False)
        monkeypatch.delitem(sys.modules, "backend.main", raising=False)
        monkeypatch.delitem(sys.modules, "backend.config", raising=False)

        原始导入 = __import__

        def 假导入(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "backend.main":
                raise ImportError("boom")
            return 原始导入(name, globals, locals, fromlist, level)

        monkeypatch.setattr("builtins.__import__", 假导入)

        with pytest.raises(ImportError, match="boom"):
            runpy.run_path(str(项目根目录 / "scripts" / "pyinstaller_entry.py"))

        crash_log = tmp_path / "crash.log"
        assert crash_log.exists()
        文本 = crash_log.read_text(encoding="utf-8")
        assert "Import failed" in 文本
        assert "boom" in 文本

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
