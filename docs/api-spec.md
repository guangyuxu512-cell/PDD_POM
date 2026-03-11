# API 接口规范

## 1. 统一响应格式

- 定义文件：`backend/models/数据结构.py`
- 所有业务接口统一返回 `统一响应`

```json
{
  "code": 0,
  "data": {},
  "msg": "ok"
}
```

- 字段说明：
  - `code`：状态码，`0=成功`，`1=业务错误`
  - `data`：响应数据
  - `msg`：响应消息
- 构造函数：
  - `成功(data=None, message="ok")`
  - `失败(message, data=None)`

## 2. 分页协议

- 定义文件：`backend/models/数据结构.py`
- 分页模型：`分页响应`

```json
{
  "list": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

## 3. 错误处理与状态码

- 当前接口大量采用 `try/except` 包装业务逻辑。
- 业务失败通常仍返回 HTTP `200`，再通过 `code != 0` 与 `msg` 表达失败原因。
- 前端调用时不能只看 HTTP 状态码，需要同时判断 `code` 字段。
- 当前项目未定义更细粒度的业务错误码枚举；就现有代码而言，仅明确可确认：
  - `code=0`：成功
  - `code=1`：业务错误
- `backend/api/日志接口.py` 中存在 `SSE` 日志流接口，用于实时查看日志。

## 4. 认证与鉴权

- 当前项目暂无此内容。
- 代码层未发现 Token、Session、中间件鉴权或权限系统。
- `backend/启动入口.py` 中的跨域配置允许 `allow_origins=["*"]`，说明当前使用方式更接近局域网/内网无鉴权模式。

## 5. 路由命名风格

- 路由路径统一使用英文、小写、资源型命名。
- 接口文件使用中文命名，路由路径不使用中文。
- 当前主要路由前缀：
  - `/api/shops`
  - `/api/tasks`
  - `/api/logs`
  - `/api/browser`
  - `/api/system`

## 6. 主要路由清单

### 6.1 店铺接口

- 文件：`backend/api/店铺接口.py`
- 路由：
  - `GET /api/shops/`
  - `POST /api/shops/`
  - `GET /api/shops/{shop_id}`
  - `PUT /api/shops/{shop_id}`
  - `DELETE /api/shops/{shop_id}`
  - `POST /api/shops/{shop_id}/cookie`
  - `GET /api/shops/{shop_id}/cookie`
  - `POST /api/shops/{shop_id}/open-browser`
  - `POST /api/shops/{shop_id}/close-browser`
  - `POST /api/shops/{shop_id}/test-email`
  - `POST /api/shops/{shop_id}/read-captcha`
  - `POST /api/shops/{shop_id}/check-status`
  - `POST /api/shops/{shop_id}/open`

### 6.2 任务接口

- 文件：`backend/api/任务接口.py`
- 路由：
  - `GET /api/tasks/`
  - `POST /api/tasks/execute`
  - `GET /api/tasks/{task_id}`
  - `POST /api/tasks/{task_id}/cancel`
  - `DELETE /api/tasks/{task_id}`
  - `POST /api/tasks/history/clear`

### 6.3 日志接口

- 文件：`backend/api/日志接口.py`
- 路由：
  - `GET /api/logs/`
  - `GET /api/logs/stream`
  - `POST /api/logs/clean`
  - `DELETE /api/logs/`

### 6.4 浏览器接口

- 文件：`backend/api/浏览器接口.py`
- 路由：
  - `POST /api/browser/init`
  - `POST /api/browser/{shop_id}/open`
  - `POST /api/browser/{shop_id}/close`
  - `GET /api/browser/instances`
  - `POST /api/browser/close-all`
  - `GET /api/browser/{shop_id}/status`

### 6.5 系统接口

- 文件：`backend/api/系统接口.py`
- 路由：
  - `GET /api/system/config`
  - `POST /api/system/test-redis`
  - `GET /api/system/health`

## 7. 请求与响应模型

定义文件统一位于 `backend/models/数据结构.py`。

### 7.1 店铺相关模型

- `店铺创建请求`
  - `name`
  - `username`
  - `password`
  - `proxy`
  - `user_agent`
  - `smtp_host`
  - `smtp_port`
  - `smtp_user`
  - `smtp_pass`
  - `smtp_protocol`
  - `remark`
- `店铺更新请求`
  - `name`
  - `username`
  - `password`
  - `proxy`
  - `user_agent`
  - `status`
  - `smtp_host`
  - `smtp_port`
  - `smtp_user`
  - `smtp_pass`
  - `smtp_protocol`
  - `remark`
- `店铺响应`
  - `id`
  - `name`
  - `username`
  - `proxy`
  - `user_agent`
  - `profile_dir`
  - `cookie_path`
  - `status`
  - `last_login`
  - `smtp_host`
  - `smtp_port`
  - `smtp_user`
  - `smtp_protocol`
  - `remark`
  - `created_at`
  - `updated_at`

### 7.2 任务相关模型

- `任务执行请求`
  - `shop_id`
  - `task_name`
  - `params`
- `任务执行请求.task_name`
  - 默认值为 `登录`
  - 同时兼容 `task_name` 与 `task_type` 入参别名
- `任务日志响应`
  - `id`
  - `task_id`
  - `shop_id`
  - `task_name`
  - `status`
  - `params`
  - `result`
  - `error`
  - `screenshot`
  - `started_at`
  - `finished_at`
  - `created_at`

### 7.3 Cookie 相关模型

- `Cookie导入请求`
  - `shop_id`
  - `cookie_data`

### 7.4 浏览器相关模型

- `浏览器初始化配置`
  - `max_instances`
  - `chrome_path`
  - `default_proxy`
- `浏览器实例响应`
  - `instance_id`
  - `shop_id`
  - `shop_name`
  - `status`
  - `uptime`
  - `memory`
  - `cpu`

### 7.5 日志相关模型

- `操作日志响应`
  - `id`
  - `shop_id`
  - `level`
  - `source`
  - `message`
  - `detail`
  - `created_at`

### 7.6 系统相关模型

- `系统配置请求`
  - `redis_url`
  - `max_browser_instances`
  - `chrome_path`
  - `default_proxy`
  - `captcha_service`
  - `captcha_api_key`
- `Redis连接测试请求`
  - `redis_url`
- `系统配置响应`
  - `redis_url`
  - `max_browser_instances`
  - `chrome_path`
  - `default_proxy`
  - `captcha_service`
  - `captcha_api_key`
- `健康检查响应`
  - `status`
  - `redis`
  - `database`
  - `browser`

## 8. 协议实现约束

- API 返回必须统一使用 `成功()` / `失败()`。
- 不要在 API 中手写结构不一致的 JSON。
- 路由路径使用英文，文件命名保持中文。
- 前端接口封装入口位于 `frontend/src/api/index.ts`。
