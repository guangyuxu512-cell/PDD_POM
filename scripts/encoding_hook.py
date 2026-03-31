"""PyInstaller 运行时钩子：强制 UTF-8 输出编码。"""
import io
import os
import sys


def _切换到UTF8(流, 原始流):
    if 流 is None:
        return 流

    编码 = getattr(流, "encoding", "")
    if isinstance(编码, str) and 编码.lower() == "utf-8":
        if hasattr(流, "reconfigure"):
            try:
                流.reconfigure(errors="replace")
            except Exception:
                pass
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


os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

sys.stdout = _切换到UTF8(sys.stdout, sys.__stdout__)
sys.stderr = _切换到UTF8(sys.stderr, sys.__stderr__)
