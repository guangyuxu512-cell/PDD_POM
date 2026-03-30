"""PyInstaller 后端入口：启动 FastAPI。"""
import os
import sys
import traceback
from pathlib import Path

# 仅在开发模式下注入项目根目录；冻结模式由 PyInstaller 自动处理。
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if getattr(sys, "frozen", False):
    os.chdir(Path(sys.executable).resolve().parent)

try:
    import uvicorn

    from backend.main import app
    from backend.config import 配置实例
except Exception as e:
    crash_log = Path(sys.executable).resolve().parent / "crash.log"
    crash_log.write_text(
        "Import failed\n"
        f"error: {e}\n"
        f"cwd: {Path.cwd()}\n"
        f"executable: {sys.executable}\n"
        f"traceback:\n{traceback.format_exc()}",
        encoding="utf-8",
    )
    raise


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=配置实例.BACKEND_PORT, loop="asyncio")
