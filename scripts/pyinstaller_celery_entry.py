"""PyInstaller Celery Worker 入口。"""
import io
import os
import sys
from pathlib import Path

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

def _切换到UTF8(流, 原始流):
    if 流 is None:
        return 流

    if hasattr(流, "reconfigure"):
        try:
            流.reconfigure(encoding="utf-8", errors="replace")
            return 流
        except Exception:
            pass

    缓冲区 = getattr(流, "buffer", None)
    if 流 is 原始流 and 缓冲区 is not None:
        return io.TextIOWrapper(缓冲区, encoding="utf-8", errors="replace", line_buffering=True)

    return 流


if getattr(sys, "frozen", False):
    sys.stdout = _切换到UTF8(sys.stdout, sys.__stdout__)
    sys.stderr = _切换到UTF8(sys.stderr, sys.__stderr__)

# 仅在开发模式下注入项目根目录；冻结模式由 PyInstaller 自动处理。
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tasks.celery_app import celery_app


def 构建Worker参数() -> list[str]:
    """根据系统设置组装 Worker 启动参数。"""
    from backend.config import 配置实例

    return ["worker", "-P", "solo", "-l", str(配置实例.LOG_LEVEL or "INFO")]


if __name__ == "__main__":
    celery_app.worker_main(构建Worker参数())
