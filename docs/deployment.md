# 部署与环境配置

## 1. 技术栈详细版本

### 1.1 后端

- 语言：`Python`
- 版本说明：
  - 仓库未通过 `pyproject.toml` 显式锁定版本
  - 当前环境缓存痕迹显示为 Python `3.12`
- 框架与库：
  - `fastapi`
  - `uvicorn[standard]`
  - `playwright`
  - `celery`
  - `redis>=5.0.0`
  - `httpx`
  - `python-dotenv`
  - `pydantic`
  - `pydantic-settings`
  - `aiosqlite`
  - `cryptography`
  - `pytest`
  - `pytest-asyncio`

### 1.2 前端

- `vue ^3.5.25`
- `vue-router ^5.0.3`
- `pinia ^3.0.4`
- `vite ^7.3.1`
- `typescript ~5.9.3`
- `@vitejs/plugin-vue ^6.0.2`
- `vue-tsc ^3.1.5`

### 1.3 数据与外部依赖

- 数据库：`SQLite`
- 队列/缓存：`Redis`
- 浏览器：本地 `Chrome` + `Playwright`
- 外部服务：
  - 验证码平台
  - 邮箱 `IMAP/SMTP`
  - Agent 回调
  - Agent 心跳
  - 抖店网页

## 2. 环境变量

环境变量定义集中在 `backend/配置.py`，通过 `.env` 读取。

| 变量名 | 默认值 | 是否必填 | 用途 |
| --- | --- | --- | --- |
| `REDIS_URL` | `redis://localhost:6379/0` | 否 | Celery broker/backend 与 Redis 测试地址 |
| `CHROME_PATH` | `None` | 否 | 本地 Chrome 可执行文件路径 |
| `MAX_BROWSER_INSTANCES` | `5` | 否 | 浏览器实例池上限 |
| `CAPTCHA_PROVIDER` | `capsolver` | 否 | 验证码服务商选择 |
| `CAPTCHA_API_KEY` | `None` | 条件必填 | 使用第三方验证码服务时需要 |
| `DEFAULT_PROXY` | `None` | 否 | 默认代理配置 |
| `LOG_LEVEL` | `INFO` | 否 | 日志等级 |
| `DATA_DIR` | `./data` | 否 | 数据目录根路径 |
| `ENCRYPTION_KEY` | `None` | 强烈建议配置 | 店铺敏感信息加解密；未配置时服务层会生成临时密钥，重启后可能导致解密不一致 |
| `FRONTEND_PORT` | `3000` | 否 | 前端端口配置项 |
| `BACKEND_PORT` | `8000` | 否 | 后端端口配置项 |
| `AGENT_CALLBACK_URL` | `None` | 条件必填 | 开启 Agent 回调时需要 |
| `AGENT_MACHINE_ID` | `None` | 条件必填 | 开启心跳上报时需要 |
| `AGENT_HEARTBEAT_URL` | `None` | 条件必填 | 开启心跳上报时需要 |

## 3. 本地开发与启动

### 3.1 安装依赖

- 安装后端依赖：

```bash
pip install -r requirements.txt
```

- 安装前端依赖：

```bash
cd frontend && npm install
```

### 3.2 启动服务

- 启动 FastAPI：

```bash
python -m uvicorn backend.启动入口:app --reload
```

- 启动 Celery Worker：

```bash
celery -A tasks.celery应用 worker --loglevel=info
```

- 按 `CLAUDE.md` 约束推荐的 Worker 启动方式：

```bash
celery -A tasks.celery应用 worker -Q machine_a -P solo
```

- 启动前端开发环境：

```bash
cd frontend && npm run dev
```

- 前端构建：

```bash
cd frontend && npm run build
```

## 4. 运行时依赖与目录

- `data/ecom.db`
  - SQLite 主数据库
- `data/cookies/`
  - Cookie 文件
- `data/profiles/`
  - 浏览器用户目录
- `data/screenshots/`
  - 截图输出目录
- Redis
  - Celery broker/backend
- 本地 Chrome
  - Playwright 驱动对象

## 5. 外部集成配置

### 5.1 Redis

- 用途：
  - Celery broker/backend
  - 系统设置中的连接测试
- 关键配置：
  - `REDIS_URL`

### 5.2 本地 Chrome 与 Playwright

- 用途：
  - 驱动浏览器自动化流程
- 关键配置：
  - `CHROME_PATH`
  - `MAX_BROWSER_INSTANCES`
  - `DEFAULT_PROXY`

### 5.3 第三方验证码平台

- 当前代码出现的提供商：
  - `capsolver`
  - `2captcha`
  - `超级鹰`
- 关键配置：
  - `CAPTCHA_PROVIDER`
  - `CAPTCHA_API_KEY`
- 说明：
  - 部分提供商目前更接近接口占位或兼容入口，接入深度以实际代码实现为准。

### 5.4 邮箱 IMAP / SMTP

- 相关逻辑：
  - `backend/services/邮箱服务.py`
- 主要依赖店铺表中的邮箱配置字段：
  - `smtp_host`
  - `smtp_port`
  - `smtp_user`
  - `smtp_pass`
  - `smtp_protocol`

### 5.5 Agent 回调与心跳

- 回调配置：
  - `AGENT_CALLBACK_URL`
- 心跳配置：
  - `AGENT_MACHINE_ID`
  - `AGENT_HEARTBEAT_URL`

## 6. 部署现状

- 当前仓库主要表现为本地部署 + 局域网访问 + 外部 Agent 协作模式。
- 需要本地可用的 Chrome、Redis、SQLite 文件目录与 `.env` 配置。
- `Dockerfile`：当前项目暂无此内容
- `docker-compose.yml`：当前项目暂无此内容
- 群晖部署脚本：当前项目暂无此内容
- 云服务部署脚本：当前项目暂无此内容

## 7. 迁移与脚本现状

- 数据库迁移命令：当前项目暂无此内容
- `pyproject.toml`：当前项目暂无此内容
- `.env.example`：当前项目暂无此内容

## 8. 安全与忽略项

- 禁止提交：
  - `.env`
  - `data/`
  - `frontend/dist/`
  - `node_modules/`
- 对外共享示例数据前应脱敏：
  - 账号密码
  - Redis 地址
  - Cookie
  - 浏览器配置目录
  - 数据库快照

## 9. 页面目标地址

- 当前代码内确认的抖店页面地址：
  - 登录页：`https://fxg.jinritemai.com/login/common`
  - 首页：`https://fxg.jinritemai.com/ffa/mshop/homepage/index`
