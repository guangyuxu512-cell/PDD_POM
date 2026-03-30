任务目标：修复 PyInstaller 打包后 backend.exe 无法启动的问题

需要修改的文件：
- scripts/pyinstaller_entry.py
- backend/config.py
- backend/models/database.py
- electron/main.js

具体实现：

1. scripts/pyinstaller_entry.py — 添加启动前诊断和 .env 路径修正：

   import os, sys
   from pathlib import Path

   if not getattr(sys, "frozen", False):
       sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

   # ★ 打包模式：将 cwd 切换到 exe 所在目录，确保相对路径一致
   if getattr(sys, "frozen", False):
       os.chdir(Path(sys.executable).resolve().parent)

   # ★ 捕获启动异常，写入 crash.log 方便排查
   try:
       import uvicorn
       from backend.main import app
       from backend.config import 配置实例
   except Exception as e:
       crash_log = Path(sys.executable).resolve().parent / "crash.log"
       crash_log.write_text(f"Import failed: {e}", encoding="utf-8")
       raise

   if __name__ == "__main__":
       uvicorn.run(app, host="127.0.0.1", port=配置实例.BACKEND_PORT, loop="asyncio")

2. backend/config.py — 让 .env 搜索更健壮：

   def _解析env路径() -> Path:
       if getattr(sys, "frozen", False):
           # 优先 exe 同级，然后往上两级找（兼容 Electron 打包结构）
           候选列表 = [
               Path(sys.executable).resolve().parent / ".env",
               Path(sys.executable).resolve().parent.parent / ".env",
               Path.cwd() / ".env",
           ]
           for 候选 in 候选列表:
               if 候选.exists():
                   return 候选
           return 候选列表[0]  # 默认回退
       return Path(__file__).resolve().parent.parent / ".env"

3. backend/models/database.py — 将相对路径改为基于可执行文件的绝对路径：

   def _获取数据目录() -> Path:
       if getattr(sys, "frozen", False):
           return Path(sys.executable).resolve().parent / "data"
       return Path(__file__).resolve().parent.parent / "data"

   数据库路径 = _获取数据目录() / "ecom.db"

4. electron/main.js — 打包模式下将 cwd 设为 exe 所在目录：

   // 修改 startBackend() 中的打包分支：
   backendProcess = spawn(packagedBackendExe, [], {
     cwd: path.dirname(packagedBackendExe),  // ★ 改为 exe 所在目录
     env: createProcessEnv(),
   })

   // 同理修改 startCelery()：
   celeryProcess = spawn(packagedCeleryExe, [], {
     cwd: path.dirname(packagedCeleryExe),  // ★ 改为 exe 所在目录
     env: celeryEnv,
   })

5. 确保 .env 文件被复制到打包输出目录：
   在 backend.spec 的 额外数据 中添加：
   额外数据 = [
       ('.env', '.'),   # ★ 将 .env 复制到 exe 同级
       ('pdd_selectors', 'pdd_selectors'),
       ('pages', 'pages'),
   ]

验收方式：
- pyinstaller backend.spec 打包无报错
- 直接双击 dist/backend/backend.exe，控制台输出 "Application startup complete"
- 如果启动失败，查看 dist/backend/crash.log 获取具体错误
- 通过 Electron 启动，后端和 Celery Worker 都正常运行