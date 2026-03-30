# Worker 与 Agent 回调通信机制

## 1. 目标

本机制用于把外部 Agent / Redis 发来的任务，桥接到本机统一任务执行入口，并把执行结果、步骤和机器心跳再回传给外部系统。

## 2. 关键文件

- `tasks/celery应用.py`
- `tasks/桥接任务.py`
- `backend/services/任务服务.py`
- `tasks/任务注册表.py`
- `tasks/登录任务.py`
- `browser/任务回调.py`
- `backend/services/心跳服务.py`
- `backend/启动入口.py`

## 3. 核心链路

### 3.1 Worker 桥接执行链路

```text
外部 Agent / Redis
  -> Celery Worker
    -> tasks/桥接任务.py
      -> backend/services/任务服务.py 的统一执行入口
        -> 任务注册表
          -> 具体任务（如 登录任务）
            -> 页面对象 / 浏览器服务
              -> 自动回调上报
```

### 3.2 心跳链路

```text
FastAPI lifespan
  -> backend/services/心跳服务.py
    -> AGENT_HEARTBEAT_URL
```

## 4. Worker 入口与职责

- Celery 入口：`tasks/celery应用.py`
- Worker 的职责：
  - 初始化 Celery 应用
  - 初始化或兜底任务注册表
  - 接收桥接任务
  - 在 Worker 进程中执行统一任务入口
- 推荐启动命令：

```bash
celery -A tasks.celery应用 worker -Q machine_a -P solo
```

- 关键约束：
  - 必须使用 `-P solo`
  - 不要改回 `prefork`，否则容易与 Playwright / 事件循环冲突

## 5. 统一执行入口

- 桥接函数位于 `tasks/桥接任务.py`
- 最终复用 `backend/services/任务服务.py` 的 `统一执行任务(...)`
- 统一入参围绕以下字段组织：
  - `task_id`
  - `shop_id`
  - `task_name`
  - `params`
- 这样可以保证：
  - HTTP 手动触发任务
  - Celery Worker 桥接任务
  - 使用同一套执行逻辑、日志逻辑、浏览器初始化逻辑

## 6. 自动回调机制

- 文件：`browser/任务回调.py`
- 核心能力：
  - `@自动回调` 装饰器
  - `上报()` 方法
- 任务 `执行` 方法必须加 `@自动回调`，否则 Agent 无法收到任务状态。
- 当前代码可确认的回调字段围绕以下内容组织：
  - `task`
  - `status`
  - `step`
  - `result`
  - `error`

## 7. 心跳机制

- 文件：`backend/services/心跳服务.py`
- 启动方式：
  - 只在 FastAPI 主进程的 `lifespan` 中启动
- 发送内容（按当前代码可确认）：
  - `machine_id`
  - `status: "online"`
- 发送地址：
  - `AGENT_HEARTBEAT_URL`
- 失败策略：
  - 发送失败静默忽略，不影响主服务

## 8. 配置项

### 8.1 回调相关

- `AGENT_CALLBACK_URL`
  - 任务回调地址
  - Worker 与 FastAPI 都会使用

### 8.2 心跳相关

- `AGENT_MACHINE_ID`
  - 本机唯一标识
- `AGENT_HEARTBEAT_URL`
  - 心跳接收地址

### 8.3 队列相关

- `REDIS_URL`
  - Celery broker/backend 地址

## 9. FastAPI 与 Worker 的职责边界

### 9.1 FastAPI 主进程负责

- API 提供
- 日志查询与 SSE
- 系统配置接口
- 在 `lifespan` 中：
  - 初始化任务注册表
  - 设置回调地址
  - 启动心跳服务

### 9.2 Celery Worker 负责

- 接收桥接任务
- 复用统一执行入口
- 复用任务注册表
- 执行 Playwright 相关任务

### 9.3 明确禁止

- 不要在 Worker 端启动心跳服务
- 不要在 Worker 端编排状态机或流程编排逻辑
- 不要让 Worker 与 HTTP 分叉出两套不同的任务执行逻辑

## 10. 关联日志链路

- `tasks/登录任务.py` 的执行过程通过 `@自动回调` 与日志服务同步状态
- 过程日志写入 `backend/services/日志服务.py`
- 前端通过 `backend/api/日志接口.py` 的 SSE 接口查看实时日志

## 11. 相关红线

- 不要遗漏任务 `执行` 方法上的 `@自动回调`
- 不要把 Celery Worker 池改回 `prefork`
- 不要在 Worker 中启动心跳
- 不要在 Worker 里复制一套新状态机
