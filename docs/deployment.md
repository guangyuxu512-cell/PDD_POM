# 部署与环境配置

## 1. 技术栈详细版本

### 1.1 后端

- 语言：`Python`
- 运行环境：当前仓库与测试环境主要使用 Python `3.12`
- 主要依赖：
  - `fastapi`
  - `uvicorn[standard]`
  - `playwright`
  - `celery`
  - `celery-redbeat`
  - `redis`
  - `httpx`
  - `pydantic`
  - `aiosqlite`
  - `cryptography`
  - `openpyxl`
  - `loguru`

### 1.2 前端

- `vue`
- `vue-router`
- `pinia`
- `vite`
- `typescript`

### 1.3 数据与外部依赖

- 数据库：`SQLite`
- 队列/缓存：`Redis`
- 浏览器：本地 `Chrome` + `Playwright`
- 外部服务：
  - 验证码平台
  - 邮箱 `IMAP/SMTP`
  - Agent 回调
  - Agent 心跳

## 2. 运行时配置来源

- 当前运行时配置主来源不是 `.env`
- 系统配置保存在 `settings` 表
- 代码统一通过 `backend/config.py` 的 `配置实例` 读取配置
- `frontend/src/views/SystemSettings.vue` 对应当前活跃的配置管理页面

常见配置项包括：

- `app_port`
- `api_base_url`
- `celery_broker_url`
- `celery_result_backend`
- `chrome_path`
- `max_concurrency`
- `browser_headless`
- `captcha_provider`
- `captcha_api_key`
- `agent_callback_url`
- `agent_heartbeat_url`
- `x_rpa_key`
- `feishu_webhook_url`

## 3. 本地开发与启动

### 3.1 安装依赖

```bash
pip install -r requirements.txt -r requirements-dev.txt
cd frontend && npm install
```

如需锁定安装：

```bash
pip install -r requirements-lock.txt
```

### 3.2 启动服务

- 启动 FastAPI：

```bash
python -m uvicorn backend.main:app --reload
```

- 启动 Celery Worker：

```bash
celery -A tasks.celery_app worker -P solo --loglevel=info
```

- 启动前端开发环境：

```bash
cd frontend && npm run dev
```

- 前端构建：

```bash
cd frontend && npm run build
```

## 4. 运行时目录

- `data/ecom.db`
  - SQLite 主数据库
- `data/logs/`
  - 应用日志目录
- `data/browser_profiles/`
  - 浏览器用户目录
- `data/cookies/`
  - Cookie 存储目录
- `data/screenshots/`
  - 截图输出目录

以上目录由 `backend/config.py` 在运行时按需创建。

## 5. 外部依赖说明

### 5.1 Redis

- 用途：
  - Celery broker/backend
  - 批量执行状态、Worker 协作、系统测试接口
- 关键配置：
  - `celery_broker_url`
  - `celery_result_backend`

### 5.2 Chrome 与 Playwright

- 用途：
  - 驱动抖店自动化流程
- 关键配置：
  - `chrome_path`
  - `max_concurrency`
  - `browser_headless`

### 5.3 验证码平台

- 用途：
  - 处理登录或页面交互中的验证码能力
- 关键配置：
  - `captcha_provider`
  - `captcha_api_key`

### 5.4 飞书与 Agent 集成

- 飞书：
  - `feishu_webhook_url`
  - `feishu_secret`
- Agent：
  - `agent_callback_url`
  - `agent_heartbeat_url`
  - `x_rpa_key`

## 6. 部署现状

- 当前仓库主要表现为本地部署 + 局域网访问 + 外部 Agent 协作模式
- 当前项目暂无正式 Docker 编排文件
- 健康检查与监控入口：
  - `GET /health`
  - `GET /api/system/health`
  - `GET /api/system/metrics`

## 7. 安全与忽略项

- 禁止提交：
  - `.env`
  - `data/`
  - `frontend/dist/`
  - `node_modules/`
- 对外共享示例数据前应脱敏：
  - 账号密码
  - Redis 地址
  - Cookie
  - Webhook
  - 数据库快照

## 8. 说明

- 文档中的启动命令描述当前主链路
- 如需兼容旧脚本或历史入口，应优先核对 `PLAN.md` 与 `.pipeline/progress.md` 的最近记录
