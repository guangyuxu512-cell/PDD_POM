scripts/pyinstaller_entry.py 和 scripts/pyinstaller_celery_entry.py 中使用 sys.path.insert(0, Path(__file__).resolve().parent.parent) 来定位项目根目录。在 PyInstaller 冻结模式下 __file__ 指向打包后的路径，导致 from backend.main import app 报 ModuleNotFoundError: No module named 'backend'。
PyInstaller --onedir 模式会自动将 _internal/ 加入 sys.path，--add-data 的内容也在 _internal/ 下，无需手动修改路径。
任务
修改以下两个文件，让 sys.path.insert 仅在非冻结（开发）模式下执行：
文件 1：scripts/pyinstaller_entry.py
替换整个文件内容为：
"""PyInstaller 后端入口：启动 FastAPI。"""
import sys
from pathlib import Path

# 仅在开发模式下手动添加项目根目录；冻结模式由 PyInstaller 自动处理
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

from backend.main import app
from backend.config import 配置实例
​
if name == "main":
uvicorn.run(app, host="127.0.0.1", port=配置实例.BACKEND_PORT, loop="asyncio")

### 文件 2：`scripts/pyinstaller_celery_entry.py`

**替换整个文件内容为：**

​
"""PyInstaller Celery Worker 入口。"""
import os
import sys
from pathlib import Path
仅在开发模式下手动添加项目根目录；冻结模式由 PyInstaller 自动处理
if not getattr(sys, 'frozen', False):
sys.path.insert(0, str(Path(file).resolve().parent.parent))
from tasks.celery_app import celery_app
def 构建Worker参数() -> list[str]:
"""根据环境变量组装 Worker 启动参数。"""
参数 = ["worker", "-P", "solo", "-l", os.getenv("CELERY_LOG_LEVEL", "INFO")]
队列 = os.getenv("CELERY_QUEUES", "").strip()
if 队列:
参数.extend(["-Q", 队列])
return 参数
if name == "main":
celery_app.worker_main(构建Worker参数())

---

### 验收方式

1. **开发模式验证**（不影响现有功能）：
​
cd E:pdd_zd
python scripts/pyinstaller_entry.py
期望：Uvicorn 正常启动在 127.0.0.1:8000

2. **PyInstaller 打包验证**：
​
pyinstaller --noconfirm --onedir --name backend --distpath ./python-backend-dist --add-data "pdd_selectors;pdd_selectors" --add-data "pages;pages" --add-data "tasks;tasks" --add-data "backend;backend" --hidden-import tasks.pdd_task --hidden-import celery.app.task scripts/pyinstaller_entry.py
& ".python-backend-distbackendbackend.exe"
期望：Uvicorn 正常启动，无 ModuleNotFoundError

### 改动范围

- `scripts/pyinstaller_entry.py` — 仅在第 5 行添加 `if not getattr(sys, 'frozen', False):` 条件判断
- `scripts/pyinstaller_celery_entry.py` — 同上，第 7 行添加条件判断
- **不涉及其他文件**