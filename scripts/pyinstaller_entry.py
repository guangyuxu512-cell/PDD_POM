"""PyInstaller 后端入口：启动 FastAPI。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

from backend.main import app
from backend.config import 配置实例


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=配置实例.BACKEND_PORT, loop="asyncio")
