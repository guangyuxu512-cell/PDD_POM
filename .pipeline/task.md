任务目标：彻底解决打包后日志中文乱码问题

需要修改的文件：
- scripts/pyinstaller_entry.py
- scripts/pyinstaller_celery_entry.py
- electron/main.js
- backend.spec（runtime_hooks）

具体实现：

1. 新建 scripts/encoding_hook.py（PyInstaller runtime hook）：

   """PyInstaller 运行时钩子：强制 UTF-8 输出编码。"""
   import sys
   import os
   import io

   # 强制 Python 使用 UTF-8
   os.environ["PYTHONUTF8"] = "1"
   os.environ["PYTHONIOENCODING"] = "utf-8"

   # 替换 stdout/stderr 为 UTF-8 编码
   if hasattr(sys.stdout, "buffer"):
       sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
   if hasattr(sys.stderr, "buffer"):
       sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

2. 在 backend.spec 和 celery-worker.spec 中注册 runtime hook：

   a = Analysis(
       ...
       runtime_hooks=['scripts/encoding_hook.py'],  # ★ 添加这行
       ...
   )

   同时在 额外数据 中添加：
   ('scripts/encoding_hook.py', 'scripts'),

3. 在 pyinstaller_entry.py 和 pyinstaller_celery_entry.py 的最顶部
   （在所有 import 之前）添加双保险：

   import os, sys, io
   os.environ["PYTHONUTF8"] = "1"
   os.environ["PYTHONIOENCODING"] = "utf-8"
   if getattr(sys, "frozen", False) and hasattr(sys.stdout, "buffer"):
       sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
       sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

4. electron/main.js — 确保子进程管道编码正确：

   在 createProcessEnv() 中确认已有（你已经有了，确认不要删除）：
   PYTHONUTF8: '1',
   PYTHONIOENCODING: 'utf-8',

   修改 pipeLogs 函数，显式指定解码：
   function pipeLogs(label, child) {
     child.stdout?.setEncoding('utf8')  // ★ 添加
     child.stderr?.setEncoding('utf8')  // ★ 添加
     child.stdout?.on('data', (data) => {
       process.stdout.write(`[${label}] ${data}`)
     })
     child.stderr?.on('data', (data) => {
       process.stderr.write(`[${label}] ${data}`)
     })
   }

验收方式：
- 打包后运行 backend.exe，控制台输出中文正常（如 "[后端启动完成] 端口: 8000"）
- 通过 Electron 启动，Electron 控制台中 [Backend] 和 [Celery] 前缀的日志中文正常
- 测试方法：在任意 print() 中输出中文 emoji 混合文本，如 "✓ 店铺 测试店铺 已启动"，确认无乱码