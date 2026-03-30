import sys
import os
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from backend.main import app  # 确认你的实际文件名

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)