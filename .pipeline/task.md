### 需求复述

后端 `提供单页应用()` 返回 `index.html` 时没有 `Cache-Control` 头，导致 Electron Chromium 缓存旧 HTML，每次前端 build 后必须手动清缓存才能看到新 UI。

### 假设与约束

- 只改 `index.html` 的返回头，`/assets/` 下的静态文件带 hash 命名，不需要改
- 不改动其他路由逻辑

### 文件：`backend/main.py`

### 具体修改

找到 `挂载前端静态资源()` 函数内的 `提供单页应用()` 路由处理函数，最后一行：

```python
return FileResponse(str(前端目录 / "index.html"))
```

替换为：

```python
响应 = FileResponse(str(前端目录 / "index.html"), media_type="text/html")
响应.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
响应.headers["Pragma"] = "no-cache"
响应.headers["Expires"] = "0"
return 响应
```

同时，函数中间还有一处直接返回静态文件的地方：

```python
if 目标文件.exists() and 目标文件.is_file():
    return FileResponse(str(目标文件))
```

这里**不需要改**（因为 assets 文件有 hash，可以被缓存）。

### 验收方式

1. `npm run build`（前端）
2. 启动后端 `python -m backend.main`
3. 启动 Electron `npx electron .`
4. 看到新 UI ✅
5. 再次 `npm run build` 改一个文字 → 重启 Electron（不清缓存）→ 能看到新文字 ✅
6. 用浏览器 DevTools 检查 `http://127.0.0.1:8000/` 响应头，确认有 `Cache-Control: no-cache, no-store, must-revalidate`

---

## Codex 任务 2：Redis 连接池改造（P0）

### 需求复述

`execute_service.py` 中每次调用 Redis 都创建新连接再关闭，一个批次执行过程中会产生上百次 TCP 握手，严重影响性能。改为连接池单例。

### 假设与约束

- 同步连接池用 `redis.ConnectionPool`，异步连接池用 `redis.asyncio.ConnectionPool`
- 连接池在模块级别初始化，生命周期跟随进程
- 不改变任何函数签名和外部调用方式
- `__all__` 导出列表不变

### 文件：`backend/services/execute_service.py`

### 具体修改

**步骤 1：在文件顶部 import 区域之后、常量定义之前，添加连接池单例：**

```python
# ── Redis 连接池（模块级单例）──
_同步连接池 = redis.ConnectionPool.from_url(配置实例.REDIS_URL, decode_responses=True)
_异步连接池 = aioredis.ConnectionPool.from_url(配置实例.REDIS_URL, decode_responses=True)
```

**步骤 2：改造 `同步获取Redis客户端()` 函数：**

```python
def 同步获取Redis客户端() -> redis.Redis:
    """获取同步 Redis 客户端（复用连接池）。"""
    return redis.Redis(connection_pool=_同步连接池)
```

**步骤 3：改造 `执行服务` 类中的 `_获取异步Redis客户端()` 方法：**

```python
async def _获取异步Redis客户端(self):
    """获取异步 Redis 客户端（复用连接池）。"""
    return aioredis.Redis(connection_pool=_异步连接池)
```

**步骤 4：改造所有异步模块级函数中 `aioredis.from_url(...)` 的调用。** 涉及以下 3 个函数：

- `设置取消标记()`
- `检查取消标记()`
- `清除取消标记()`

每个函数中，将：

```python
客户端 = aioredis.from_url(配置实例.REDIS_URL, decode_responses=True)
```

替换为：

```python
客户端 = aioredis.Redis(connection_pool=_异步连接池)
```

**步骤 5：移除所有 `finally: 客户端.close()` 块。**

连接池模式下，调用 `close()` 会把连接归还池，不会真的断开 TCP。但为了代码一致性和避免混淆：

- **同步函数**（`同步读取批次状态`、`同步写入批次状态`、`同步设置取消标记`、`同步检查取消标记`、`同步清除取消标记`、`尝试发送批次完成回调`）：保留 `finally: 客户端.close()` 不变（连接池模式下 close 是归还连接，安全）
- **异步函数**（`设置取消标记`、`检查取消标记`、`清除取消标记`）：将 finally 块简化为：

```python
finally:
    await 客户端.aclose()
```

- **`执行服务` 类的 `_关闭异步Redis客户端()` 方法**：简化为：

```python
async def _关闭异步Redis客户端(self, 客户端) -> None:
    """关闭异步 Redis 客户端（归还连接池）。"""
    await 客户端.aclose()
```

### 验收方式

1. 启动 Redis + 后端 + Celery Worker
2. 创建一个 5 店铺 × 3 步骤的批次执行
3. 执行前后用 `redis-cli INFO clients` 查看 `connected_clients`：
    - **改造前**：执行过程中 connected_clients 会飙升到 20+
    - **改造后**：connected_clients 始终保持在 2-4（同步池 + 异步池 + pubsub）
4. 执行完成后功能正常，无报错

---

## Codex 任务 3：`_FROZEN_TASK_MODULES` 自动生成（P1）

### 需求复述

`tasks/registry.py` 中 `_FROZEN_TASK_MODULES` 是硬编码列表，每新增一个 task 文件都要手动维护。如果忘了加，打包后的 exe 会缺少任务注册，导致生产环境崩溃。改为 build 时自动生成。

### 假设与约束

- 在 `backend.spec` 的 PyInstaller 构建阶段自动扫描 `tasks/` 目录
- 生成一个 `tasks/_frozen_modules.py` 文件，内容是模块名列表
- `registry.py` 在 frozen 模式下读取该文件，非 frozen 模式仍用 `pkgutil` 动态扫描
- `_frozen_modules.py` 应加入 `.gitignore`

### 文件修改

**文件 1：`backend.spec` — 在顶部 import 后添加自动生成逻辑：**

在 `from PyInstaller.utils.hooks import collect_all` 之后，`额外二进制 = []` 之前，插入：

```python
import os
from pathlib import Path

# ── 自动生成 frozen task 模块列表 ──
_tasks_dir = Path("tasks")
_排除模块 = {
    "__init__", "registry", "task_registry", "base_task",
    "celery_app", "bridge_task", "execute_task", "scheduled_task",
    "async_utils", "_frozen_modules",
}
_task_modules = sorted([
    f.stem for f in _tasks_dir.glob("*.py")
    if f.stem not in _排除模块 and not f.stem.startswith("_")
])
_frozen_file = _tasks_dir / "_frozen_modules.py"
_frozen_file.write_text(
    f"# 此文件由 backend.spec 自动生成，请勿手动编辑\nMODULES = {_task_modules!r}\n",
    encoding="utf-8",
)
print(f"[spec] 已生成 {_frozen_file}，模块: {_task_modules}")
```

同时在 `额外导入` 列表中添加一行：

```python
'tasks._frozen_modules',
```

**文件 2：`tasks/registry.py` — 改造 `_列出任务模块()` 函数：**

删除整个 `_FROZEN_TASK_MODULES` 硬编码列表，然后将 `_列出任务模块()` 修改为：

```python
def _列出任务模块() -> list[str]:
    """列出 tasks 目录下需要自动导入的任务模块。"""
    if getattr(sys, "frozen", False):
        try:
            from tasks._frozen_modules import MODULES
            return list(MODULES)
        except ImportError:
            logger.warning("[任务注册] 未找到 _frozen_modules.py，回退到硬编码列表")
            # 兜底：万一 _frozen_modules.py 丢失，用空列表（会导致无任务可用）
            return []

    模块目录 = Path(__file__).resolve().parent
    模块列表: list[str] = []

    for 模块信息 in pkgutil.iter_modules([str(模块目录)]):
        if 模块信息.name in 排除模块:
            continue
        模块列表.append(模块信息.name)

    模块列表.sort()
    return 模块列表
```

**文件 3：`.gitignore` — 添加一行：**

```
tasks/_frozen_modules.py
```

### 验收方式

1. 在 `tasks/` 下新建一个测试文件 `tasks/test_dummy_task.py`（内容随意，比如空的 `pass`）
2. 运行 `pyinstaller backend.spec`
3. 检查生成的 `tasks/_frozen_modules.py`，确认包含 `test_dummy_task`
4. 打包后运行 exe，确认任务注册表包含所有 task（包括 test_dummy_task）
5. 删除测试文件，再次打包，确认 `_frozen_modules.py` 不再包含它
6. 非打包模式（`python -m backend.main`）仍用 `pkgutil` 动态扫描，不受影响