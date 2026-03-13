**Task 33：Celery Worker 通过 HTTP 委托主进程执行任务 — 解决双进程浏览器冲突**

---

**一、做什么**

当前 Celery Worker 在自己的进程里直接调用 `任务服务实例.统一执行任务()`，会尝试自己 launch Chrome，跟主进程（FastAPI）已打开的 Chrome 抢同一个 profile 目录导致冲突。改为：Worker 通过 HTTP 请求主进程的 API 来执行任务，由主进程里已有的浏览器实例完成实际操作。

---

**二、涉及文件**

1. `backend/api/任务接口.py` — 新增内部执行接口 `POST /api/tasks/execute-internal`，供 Worker 调用
2. `tasks/执行任务.py` — 改为通过 HTTP 调主进程执行，不再直接调 `任务服务实例.统一执行任务()`
3. `backend/配置.py` — 新增 `API_BASE_URL` 配置项（主进程地址，默认 `http://localhost:8000`）

---

**三、流程**

**第1步：新增内部执行接口**

在 `backend/api/任务接口.py` 中新增：

```
POST /api/tasks/execute-internal
```

请求体：

```json
{
  "shop_id": "xxx",
  "task_name": "限时限量",
  "params": { ... },
  "flow_param_id": 123  // 可选
}
```

接口逻辑：

- 同步创建 task_log 记录
- 调用 `任务服务实例.统一执行任务(task_id, shop_id, task_name, params, 来源="worker")`
- **等待执行完成后**返回结果（这是同步阻塞接口，不是 fire-and-forget）
- 返回格式：`{ "task_id": "xxx", "shop_id": "xxx", "task_name": "xxx", "status": "completed/failed", "result": "...", "error": "..." }`

注意：这个接口是内部接口，只供 Worker 调用，不需要前端调用。接口要支持较长的超时（任务可能跑几分钟）。

**第2步：修改 Celery 执行任务**

改造 `tasks/执行任务.py` 中的 `执行任务()` 函数：

**改造前**（直接调任务服务）：

```python
任务记录 = _运行异步任务(任务服务实例.创建任务记录(...))
执行结果 = _运行异步任务(任务服务实例.统一执行任务(...))
```

**改造后**（通过 HTTP 调主进程）：

```python
import httpx
from backend.配置 import 配置实例

API_BASE_URL = getattr(配置实例, 'API_BASE_URL', 'http://localhost:8000')

# 构建请求体
请求体 = {
    "shop_id": shop_id,
    "task_name": task_name,
    "params": 任务参数,
}
if flow_param_id is not None:
    请求体["flow_param_id"] = flow_param_id

# 通过 HTTP 调主进程执行
with httpx.Client(timeout=httpx.Timeout(1800.0, connect=10.0)) as client:
    响应 = client.post(f"{API_BASE_URL}/api/tasks/execute-internal", json=请求体)
    响应.raise_for_status()
    执行结果 = 响应.json().get("data", {})
```

这样 Worker 不再需要 Playwright、浏览器管理器或任何浏览器相关的依赖。

**第3步：Worker 中的 flow_params 处理**

执行前读取 flow_params 和执行后回写 step_results 的逻辑有两种处理方式：

- **方案A（推荐）**：把 flow_params 的读取和回写也放到主进程的 execute-internal 接口中处理。Worker 只传 `flow_param_id`，主进程负责读 flow_params → 注入 flow_context → 执行任务 → 回写 step_results。
- **方案B**：Worker 仍然通过数据库读写 flow_params（SQLite 支持多进程读），执行任务部分委托主进程。

采用**方案A**：

- execute-internal 接口收到 `flow_param_id` 后：
    1. 读取 flow_params 记录，获取 params + step_results
    2. 调用 `流程参数服务实例.获取步骤上下文(flow_param_id, task_name)` 合并为 flow_context
    3. 注入到 `店铺配置["flow_context"]`
    4. 执行任务
    5. 成功后调用 `流程参数服务实例.回写步骤结果(flow_param_id, task_name, 结果, step_index)`
    6. 返回结果

Worker 的 `执行任务()` 函数简化为：

1. 更新批次状态（step running）
2. HTTP POST 到主进程
3. 根据响应更新批次状态（step completed/failed）
4. 根据 on_fail 策略决定是否继续链路

**第4步：配置项**

在 `backend/配置.py` 中新增：

```python
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
```

**第5步：清理 Worker 中不再需要的代码**

`tasks/执行任务.py` 中可以移除：

- `_运行异步任务` 函数（或保留给其他场景）
- `_在线程中执行临时协程` 函数
- `nest_asyncio` 的 import 和 apply
- 对 `任务服务实例` 的直接导入（改为 HTTP 调用）

但保留：

- `初始化Worker环境()` 调用（初始化任务注册表用于校验）
- 批次状态更新（`同步更新批次店铺状态`）— 这个走 Redis，不涉及浏览器
- `on_fail` 策略判断逻辑

---

**四、关键元素**

- 新接口：`POST /api/tasks/execute-internal`
- 配置项：`API_BASE_URL`（默认 `http://localhost:8000`）
- HTTP 超时：connect=10s，总超时=1800s（与现有 `任务执行超时秒` 一致）
- Worker 不再导入 Playwright 或浏览器管理器
- 批次状态更新仍走 Redis（`同步更新批次店铺状态`），不受影响

---

**五、约束**

1. **不修改前端代码**
2. **不修改主进程的任务服务逻辑** — `统一执行任务()` 方法保持不变，只是调用方从 Worker 直调变成通过 HTTP 调
3. **execute-internal 是同步阻塞接口** — 必须等任务执行完再返回，不能 fire-and-forget。Worker 需要拿到执行结果来判断 on_fail 策略
4. **保持 Celery chain 的链路控制** — on_fail 的 abort/continue/retry 逻辑仍在 Worker 端判断
5. **保持批次状态更新** — 走 Redis pub/sub，不受 HTTP 委托影响
6. **严格按流程步骤执行，不要自行添加步骤**
7. **后端 Python 中文命名**