"""PyInstaller Celery Worker 入口。"""
import os
import sys
from pathlib import Path

# 仅在开发模式下注入项目根目录；冻结模式由 PyInstaller 自动处理。
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tasks.celery_app import celery_app


def 构建Worker参数() -> list[str]:
    """根据环境变量组装 Worker 启动参数。"""
    参数 = ["worker", "-P", "solo", "-l", os.getenv("CELERY_LOG_LEVEL", "INFO")]
    队列 = os.getenv("CELERY_QUEUES", "").strip()
    if 队列:
        参数.extend(["-Q", 队列])
    return 参数


if __name__ == "__main__":
    celery_app.worker_main(构建Worker参数())
