"""PyInstaller 后端入口：启动 FastAPI。"""
import sys
from pathlib import Path

# 仅在开发模式下注入项目根目录；冻结模式由 PyInstaller 自动处理。
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

from backend.main import app
from backend.config import 配置实例


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=配置实例.BACKEND_PORT, loop="asyncio")
