# 数据库模型

## 1. 存储概况

- 数据库类型：`SQLite`
- 数据文件：`data/ecom.db`
- 数据目录还包含：
  - `data/cookies/`
  - `data/profiles/`
  - `data/screenshots/`
- 当前数据库由 `backend/models/数据库.py` 统一建表与初始化。
- 轻量表结构定义位于：
  - `backend/models/表结构.py`
  - `backend/models/店铺模型.py`
  - `backend/models/流程模型.py`
  - `backend/models/定时任务模型.py`
- 当前项目暂无独立数据库迁移工具或迁移命令。

## 2. 表结构

### 2.1 `shops`

- **用途**：存储店铺基础信息、浏览器配置、邮箱配置和状态信息。

| 字段 | 含义 |
| --- | --- |
| `id` | 店铺唯一标识 |
| `name` | 店铺名称 |
| `username` | 登录用户名 |
| `password` | 登录密码 |
| `proxy` | 店铺级代理地址 |
| `user_agent` | 浏览器 User-Agent |
| `profile_dir` | 浏览器用户目录路径 |
| `cookie_path` | Cookie 文件路径 |
| `status` | 店铺状态 |
| `last_login` | 最后登录时间 |
| `smtp_host` | 邮箱服务器地址 |
| `smtp_port` | 邮箱服务器端口 |
| `smtp_user` | 邮箱用户名 |
| `smtp_pass` | 邮箱密码 |
| `smtp_protocol` | 邮箱协议 |
| `remark` | 备注 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### 2.2 `flows`

- **用途**：存储可复用流程模板，供后续批量任务或定时调度编排使用。

| 字段 | 含义 |
| --- | --- |
| `id` | 流程唯一标识 |
| `name` | 流程名称 |
| `steps` | 流程步骤 JSON 数组 |
| `description` | 流程描述 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

`steps` 使用 JSON 数组存储，数组元素结构如下：

```json
[
  {
    "task": "登录",
    "on_fail": "continue"
  }
]
```

其中 `on_fail` 支持：

- `skip_shop`
- `continue`
- `log_and_skip`
- `retry:N`
- `abort`

### 2.3 `execution_schedules`

- **用途**：存储流程的定时执行计划与目标店铺集合。

| 字段 | 含义 |
| --- | --- |
| `id` | 计划唯一标识 |
| `name` | 计划名称 |
| `flow_id` | 关联流程 ID |
| `shop_ids` | 目标店铺 ID 的 JSON 数组 |
| `concurrency` | 并发数 |
| `interval_seconds` | 固定间隔秒数 |
| `cron_expr` | Cron 表达式 |
| `overlap_policy` | 重叠执行策略 |
| `enabled` | 是否启用，`1/0` |
| `last_run_at` | 上次运行时间 |
| `next_run_at` | 下次运行时间 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### 2.4 `task_logs`

- **用途**：记录任务执行过程与结果。

| 字段 | 含义 |
| --- | --- |
| `id` | 自增日志 ID |
| `task_id` | 任务唯一 ID |
| `shop_id` | 关联店铺 ID |
| `task_name` | 任务名称 |
| `status` | 任务状态 |
| `params` | 任务参数 |
| `result` | 执行结果 |
| `error` | 错误信息 |
| `screenshot` | 截图路径 |
| `started_at` | 开始时间 |
| `finished_at` | 结束时间 |
| `created_at` | 创建时间 |

### 2.5 `operation_logs`

- **用途**：记录系统与业务操作日志。

| 字段 | 含义 |
| --- | --- |
| `id` | 自增日志 ID |
| `shop_id` | 关联店铺 ID |
| `level` | 日志级别 |
| `source` | 日志来源 |
| `message` | 日志消息 |
| `detail` | 详细信息 |
| `created_at` | 创建时间 |

## 3. 关联关系

- `task_logs.shop_id` 在业务上指向 `shops.id`
- `operation_logs.shop_id` 在业务上指向 `shops.id`
- `execution_schedules.flow_id` 在建表时声明为外键，指向 `flows.id`
- `task_logs.shop_id` 与 `operation_logs.shop_id` 当前仍属于逻辑关联而非数据库级强约束

## 4. 命名风格

- 数据库表名与字段名统一使用英文 `snake_case`
- 这与后端 Python 中文命名规则分离：
  - Python 代码中文
  - SQL 层英文

## 5. 与业务模块的关系

- `shops`
  - 由 `backend/services/店铺服务.py` 读写
  - 供浏览器服务、邮箱服务、任务服务读取店铺配置
- `flows`
  - 当前已完成模型定义、JSON 校验与建表接入
  - 独立的服务层与 API 入口当前项目暂无此内容
- `execution_schedules`
  - 当前已完成模型定义、店铺列表序列化与建表接入
  - 独立的服务层与 API 入口当前项目暂无此内容
- `task_logs`
  - 由 `backend/services/任务服务.py`、`backend/services/日志服务.py` 维护
  - 供 `TaskMonitor` 页面和任务查询接口读取
- `operation_logs`
  - 由 `backend/services/日志服务.py` 维护
  - 供 `LogViewer` 页面与日志接口读取

## 6. 接口数据模型补充

除 SQLite 表外，`backend/models/数据结构.py` 还定义了 API 使用的 Pydantic 数据结构。

### 6.1 通用模型

- `统一响应`
- `分页响应`

### 6.2 业务请求/响应模型

- 店铺相关：
  - `店铺创建请求`
  - `店铺更新请求`
  - `店铺响应`
- 任务相关：
  - `任务执行请求`
  - `任务日志响应`
- Cookie 相关：
  - `Cookie导入请求`
- 浏览器相关：
  - `浏览器初始化配置`
  - `浏览器实例响应`
- 日志相关：
  - `操作日志响应`
- 系统相关：
  - `系统配置请求`
  - `Redis连接测试请求`
  - `系统配置响应`
  - `健康检查响应`

## 7. 当前缺失项

- 数据库迁移工具：当前项目暂无此内容
- ORM 框架：当前项目暂无此内容，当前以 `aiosqlite` + 原生 SQL 为主
