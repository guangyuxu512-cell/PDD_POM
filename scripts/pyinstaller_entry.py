"""PyInstaller 后端入口：启动 FastAPI。"""
import io
import os
import sys
import traceback
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
