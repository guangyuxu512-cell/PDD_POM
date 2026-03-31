import io
import os
import runpy
import sys
import types
from pathlib import Path
from types import SimpleNamespace


项目根目录 = Path(__file__).resolve().parents[2]


def _创建文本流(编码: str) -> io.TextIOWrapper:
    return io.TextIOWrapper(io.BytesIO(), encoding=编码, errors="replace")


def _准备后端依赖(monkeypatch) -> None:
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


def _准备Celery依赖(monkeypatch) -> None:
    tasks包 = types.ModuleType("tasks")
    tasks包.__path__ = []

    celery模块 = types.ModuleType("tasks.celery_app")
    celery模块.celery_app = SimpleNamespace(worker_main=lambda *args, **kwargs: None)

    monkeypatch.setitem(sys.modules, "tasks", tasks包)
    monkeypatch.setitem(sys.modules, "tasks.celery_app", celery模块)


def _读取文件(路径: str) -> str:
    return (项目根目录 / 路径).read_text(encoding="utf-8")


class 测试_打包日志编码:
    def test_runtime_hook_强制设置_utf8_环境变量与流编码(self, monkeypatch):
        monkeypatch.setattr(sys, "stdout", _创建文本流("gbk"))
        monkeypatch.setattr(sys, "stderr", _创建文本流("gbk"))
        monkeypatch.delenv("PYTHONUTF8", raising=False)
        monkeypatch.delenv("PYTHONIOENCODING", raising=False)

        runpy.run_path(str(项目根目录 / "scripts" / "encoding_hook.py"))

        assert os.environ["PYTHONUTF8"] == "1"
        assert os.environ["PYTHONIOENCODING"] == "utf-8"
        assert (sys.stdout.encoding or "").lower() == "utf-8"
        assert (sys.stderr.encoding or "").lower() == "utf-8"

    def test_后端入口_冻结模式强制切换_utf8_输出(self, monkeypatch, tmp_path: Path):
        _准备后端依赖(monkeypatch)
        monkeypatch.setattr(sys, "stdout", _创建文本流("gbk"))
        monkeypatch.setattr(sys, "stderr", _创建文本流("gbk"))
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(tmp_path / "backend.exe"), raising=False)
        monkeypatch.chdir(项目根目录)
        monkeypatch.delenv("PYTHONUTF8", raising=False)
        monkeypatch.delenv("PYTHONIOENCODING", raising=False)

        runpy.run_path(str(项目根目录 / "scripts" / "pyinstaller_entry.py"))

        assert os.environ["PYTHONUTF8"] == "1"
        assert os.environ["PYTHONIOENCODING"] == "utf-8"
        assert (sys.stdout.encoding or "").lower() == "utf-8"
        assert (sys.stderr.encoding or "").lower() == "utf-8"

    def test_Celery入口_冻结模式强制切换_utf8_输出(self, monkeypatch):
        _准备Celery依赖(monkeypatch)
        monkeypatch.setattr(sys, "stdout", _创建文本流("gbk"))
        monkeypatch.setattr(sys, "stderr", _创建文本流("gbk"))
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.delenv("PYTHONUTF8", raising=False)
        monkeypatch.delenv("PYTHONIOENCODING", raising=False)

        runpy.run_path(str(项目根目录 / "scripts" / "pyinstaller_celery_entry.py"))

        assert os.environ["PYTHONUTF8"] == "1"
        assert os.environ["PYTHONIOENCODING"] == "utf-8"
        assert (sys.stdout.encoding or "").lower() == "utf-8"
        assert (sys.stderr.encoding or "").lower() == "utf-8"

    def test_spec_注册_encoding_hook_运行时钩子(self):
        backend_spec内容 = _读取文件("backend.spec")
        worker_spec内容 = _读取文件("celery-worker.spec")

        assert "('scripts/encoding_hook.py', 'scripts')" in backend_spec内容
        assert "runtime_hooks=['scripts/encoding_hook.py']" in backend_spec内容
        assert "('scripts/encoding_hook.py', 'scripts')" in worker_spec内容
        assert "runtime_hooks=['scripts/encoding_hook.py']" in worker_spec内容

    def test_electron_日志管道显式按_utf8_解码(self):
        主进程文件 = _读取文件("electron/main.js")

        assert "PYTHONUTF8: '1'" in 主进程文件
        assert "PYTHONIOENCODING: 'utf-8'" in 主进程文件
        assert "child.stdout?.setEncoding('utf8')" in 主进程文件
        assert "child.stderr?.setEncoding('utf8')" in 主进程文件
