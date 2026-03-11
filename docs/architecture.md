# 架构设计

## 1. 项目概述

- **项目名称**：`抖店自动化工具`
- **一句话介绍**：这是一个围绕抖店账号管理、浏览器自动化登录、任务执行、日志监控与 Agent 桥接而构建的本地化自动化系统。
- **核心业务场景**：
  - 管理多个店铺账号及其邮箱、Cookie、浏览器配置
  - 通过 Playwright 控制本地 Chrome 打开店铺并执行登录任务
  - 通过 FastAPI 暴露管理接口，供前端页面调用
  - 通过 Celery + Redis 接收桥接任务，与外部 Agent 对接
  - 通过日志流和心跳机制进行过程监控
- **目标用户**：
  - 从 `frontend/src/views/ShopManage.vue`、`TaskMonitor.vue`、`BrowserManager.vue`、`Settings.vue` 的功能划分来看，目标用户是需要在本地维护抖店店铺、执行自动化登录/任务并查看运行状态的运营或技术人员。

## 2. 整体架构关系

```text
Vue 3 前端
  -> FastAPI 接口层
    -> services 业务层
      -> models 数据层（SQLite）
      -> browser 浏览器管理层
      -> pages 页面对象层（POM）
      -> tasks 任务层（Celery / Worker）
        -> Redis（broker / backend）
        -> 外部 Agent 回调 / 心跳
```

- `frontend/` 负责交互界面与请求发起
- `backend/api/` 负责路由入口与协议封装
- `backend/services/` 负责业务逻辑
- `backend/models/` 负责数据库与 Pydantic 数据结构
- `browser/` 负责浏览器管理、反检测、验证码、回调
- `pages/` 负责页面对象封装
- `tasks/` 负责任务注册、统一桥接、Celery Worker 初始化
- `data/ecom.db` 用于持久化店铺、任务日志、操作日志

## 3. 项目结构

```text
douyin/
├─ .claude/                         # 本地角色规则与协作说明
│  ├─ architect.md                 # 架构角色规则
│  ├─ backend-builder.md           # 后端开发规则
│  ├─ frontend-builder.md          # 前端开发规则
│  ├─ settings.local.json          # 本地配置
│  └─ validator.md                 # 测试/审查规则
├─ .pipeline/                      # 流水线过程文档
│  ├─ final -report.md             # 最终报告草稿
│  ├─ fixes.md                     # 修复记录
│  ├─ progress.md                  # 开发进度记录
│  ├─ review.md                    # 审查记录
│  └─ task.md                      # 当前任务说明
├─ .pytest_cache/                  # 根级 pytest 缓存
│  └─ v/                           # pytest 版本缓存目录
├─ .roles/                         # 角色化协作规则
│  ├─ builder/                     # 开发执行者规则
│  ├─ fixer/                       # 修复者规则
│  └─ reviewer/                    # 审查者规则
├─ backend/                        # FastAPI 后端
│  ├─ api/                         # 接口路由层
│  ├─ models/                      # 数据结构与数据库访问
│  ├─ services/                    # 业务服务层
│  ├─ __pycache__/                 # Python 缓存
│  ├─ 启动入口.py                  # 后端主入口
│  └─ 配置.py                      # 配置读取与默认值
├─ browser/                        # 浏览器管理与辅助能力
│  ├─ __pycache__/                 # Python 缓存
│  ├─ __init__.py                  # 包初始化
│  ├─ 任务回调.py                  # 自动回调装饰器与上报
│  ├─ 反检测.py                    # 反检测与模拟操作
│  ├─ 滑块验证码.py                # 滑块处理
│  ├─ 用户目录工厂.py              # 浏览器用户目录管理
│  ├─ 管理器.py                    # 浏览器实例池
│  └─ 验证码识别.py                # 第三方验证码调用
├─ data/                           # 运行期数据目录
│  ├─ cookies/                     # Cookie 文件
│  ├─ profiles/                    # 浏览器用户目录
│  ├─ screenshots/                 # 截图输出
│  └─ ecom.db                      # SQLite 数据库文件
├─ docs/                           # 主题化文档拆分目录
│  ├─ architecture.md              # 架构设计
│  ├─ api-spec.md                  # API 规范
│  ├─ database.md                  # 数据库模型
│  ├─ coding-style.md              # 代码风格
│  ├─ callback.md                  # Worker 与 Agent 通信
│  ├─ testing.md                   # 测试策略
│  ├─ frontend.md                  # 前端页面设计
│  └─ deployment.md                # 部署与环境配置
├─ frontend/                       # Vue 3 前端工程
│  ├─ .vscode/                     # 前端本地编辑器配置
│  ├─ dist/                        # 前端构建产物
│  ├─ node_modules/                # 前端依赖
│  ├─ public/                      # 静态资源
│  ├─ src/                         # 前端源码入口
│  ├─ .gitignore                   # 前端忽略规则
│  ├─ index.html                   # Vite HTML 入口
│  ├─ package-lock.json            # npm 锁文件
│  ├─ package.json                 # 前端依赖声明
│  ├─ README.md                    # Vite 默认说明
│  ├─ tsconfig.app.json            # 前端 TS 配置
│  ├─ tsconfig.json                # 前端 TS 总配置
│  ├─ tsconfig.node.json           # Node 环境 TS 配置
│  └─ vite.config.ts               # Vite 配置
├─ pages/                          # POM 页面对象层
│  ├─ __pycache__/                 # Python 缓存
│  ├─ __init__.py                  # 包初始化
│  ├─ 基础页.py                    # 页面基类与安全操作
│  └─ 登录页.py                    # 抖店登录页对象
├─ tasks/                          # Celery 任务层
│  ├─ __pycache__/                 # Python 缓存
│  ├─ celery应用.py                # Celery 应用与 Worker 初始化
│  ├─ __init__.py                  # 包初始化
│  ├─ 任务注册表.py                # 任务注册与查找
│  ├─ 桥接任务.py                  # Agent/Redis 桥接到统一执行入口
│  └─ 登录任务.py                  # 登录任务实现
├─ tests/                          # 测试目录
│  ├─ .pytest_cache/               # tests 目录下 pytest 缓存
│  ├─ __pycache__/                 # Python 缓存
│  ├─ 单元测试/                    # 单元与异步回归测试
│  ├─ conftest.py                  # pytest 夹具
│  └─ pytest.ini                   # pytest 配置
├─ .env                            # 本地环境变量文件（敏感）
├─ .gitignore                      # 根忽略规则
├─ ARCHITECTURE.md                 # 架构文档
├─ CLAUDE.md                       # 现有项目规则文档
├─ PLAN.md                         # 计划与阶段进度
├─ requirements.txt               # 后端依赖
└─ 改造进度.md                     # 改造过程记录
```

## 4. 入口文件

- 后端入口：`backend/启动入口.py`
- FastAPI 应用创建：`backend/启动入口.py` 中的 `app = 创建应用()`
- 前端入口：`frontend/src/main.ts`
- 前端路由入口：`frontend/src/router/index.ts`
- 前端请求封装入口：`frontend/src/api/index.ts`
- Celery 入口：`tasks/celery应用.py`
- Vite HTML 入口：`frontend/index.html`

## 5. 文档现状

- 根目录主 README：当前项目暂无此内容。
- `frontend/README.md` 存在，但内容为 Vite 默认说明，不是项目主说明文档。
- `CLAUDE.md` 提到过桌面壳 `PyWebView`，但当前仓库根目录未看到对应桌面入口代码，当前不能作为已确认运行链路写入实现约束。

## 6. 分层设计与职责

### 6.1 API 层

- 目录：`backend/api/`
- 文件：`店铺接口.py`、`任务接口.py`、`日志接口.py`、`浏览器接口.py`、`系统接口.py`、`路由注册.py`
- 职责：
  - 定义路由
  - 接收请求参数
  - 调用服务层
  - 返回统一响应结构

### 6.2 Services 层

- 目录：`backend/services/`
- 核心文件：
  - `店铺服务.py`
  - `浏览器服务.py`
  - `任务服务.py`
  - `日志服务.py`
  - `邮箱服务.py`
  - `系统服务.py`
  - `心跳服务.py`
- 职责：
  - 承载业务逻辑
  - 协调数据库、浏览器、任务与外部服务

### 6.3 Models 层

- 目录：`backend/models/`
- 文件：
  - `数据库.py`
  - `数据结构.py`
- 职责：
  - SQLite 建表与访问
  - Pydantic 请求/响应模型定义

### 6.4 Browser 层

- 目录：`browser/`
- 职责：
  - 浏览器实例池管理
  - 用户目录管理
  - 反检测
  - 验证码识别
  - 自动回调与上报

### 6.5 POM 层

- 目录：`pages/`
- 文件：
  - `基础页.py`
  - `登录页.py`
- 职责：
  - 封装页面元素
  - 提供安全点击、安全填写、截图等操作
  - 不写业务编排

### 6.6 Task 层

- 目录：`tasks/`
- 文件：
  - `celery应用.py`
  - `任务注册表.py`
  - `桥接任务.py`
  - `登录任务.py`
- 职责：
  - Worker 初始化
  - 任务注册与分发
  - Agent/Redis 消息桥接
  - 具体任务执行

## 7. 核心模块说明

### 7.1 店铺管理模块

- 关键文件：
  - `frontend/src/views/ShopManage.vue`
  - `backend/api/店铺接口.py`
  - `backend/services/店铺服务.py`
  - `backend/models/数据库.py`
- 职责：
  - 管理店铺基本信息、邮箱配置、Cookie、在线状态与浏览器相关操作

### 7.2 浏览器管理模块

- 关键文件：
  - `backend/services/浏览器服务.py`
  - `browser/管理器.py`
  - `browser/用户目录工厂.py`
  - `browser/反检测.py`
- 职责：
  - 初始化 Playwright
  - 打开/关闭店铺浏览器
  - 控制实例数
  - 管理用户目录

### 7.3 页面对象模块

- 关键文件：
  - `pages/基础页.py`
  - `pages/登录页.py`
- 职责：
  - 封装抖店页面元素和操作
  - 供任务层复用

### 7.4 任务执行模块

- 关键文件：
  - `backend/services/任务服务.py`
  - `tasks/任务注册表.py`
  - `tasks/登录任务.py`
  - `browser/任务回调.py`
- 职责：
  - 创建任务记录
  - 统一执行任务
  - 查找任务实现
  - 上报任务结果与步骤

### 7.5 Celery 桥接模块

- 关键文件：
  - `tasks/celery应用.py`
  - `tasks/桥接任务.py`
- 职责：
  - 接收 Worker 任务
  - 桥接到 `任务服务.统一执行任务(...)`
  - 保持 HTTP 与 Celery 入口复用同一执行逻辑

### 7.6 日志与监控模块

- 关键文件：
  - `backend/services/日志服务.py`
  - `backend/api/日志接口.py`
  - `frontend/src/views/LogViewer.vue`
- 职责：
  - 保存操作日志、任务日志
  - 向前端提供查询与 SSE 日志流

### 7.7 系统配置与健康检查模块

- 关键文件：
  - `backend/api/系统接口.py`
  - `backend/services/系统服务.py`
  - `frontend/src/views/Settings.vue`
- 职责：
  - 输出系统配置
  - 健康检查
  - 测试 Redis 连通性

### 7.8 邮箱与验证码模块

- 关键文件：
  - `backend/services/邮箱服务.py`
  - `browser/验证码识别.py`
  - `browser/滑块验证码.py`
- 职责：
  - 店铺邮箱连通性测试
  - 验证码邮件读取
  - 第三方验证码识别

### 7.9 心跳模块

- 关键文件：
  - `backend/services/心跳服务.py`
  - `backend/启动入口.py`
- 职责：
  - 定时向外部 Agent 上报当前机器在线状态

## 8. 关键调用链路

- **店铺管理链路**：
  - `frontend/src/views/ShopManage.vue`
  - → `backend/api/店铺接口.py`
  - → `backend/services/店铺服务.py`
  - → `backend/models/数据库.py`
- **前端手动触发任务链路**：
  - `frontend/src/views/TaskMonitor.vue`
  - → `POST /api/tasks/execute`
  - → `backend/services/任务服务.py`
  - → `tasks/任务注册表.py`
  - → `tasks/登录任务.py`
  - → `pages/登录页.py` / `pages/基础页.py`
  - → `browser/任务回调.py` / `backend/services/日志服务.py`
- **浏览器打开链路**：
  - `frontend/src/views/ShopManage.vue`
  - → `POST /api/shops/{shop_id}/open`
  - → `backend/services/任务服务.py`
  - → `backend/services/浏览器服务.py`
  - → `browser/管理器.py`
- **Agent 桥接链路**：
  - 外部 Agent / Redis
  - → `tasks/桥接任务.py`
  - → `backend/services/任务服务.py` 的统一执行入口
- **心跳链路**：
  - `backend/启动入口.py` `lifespan`
  - → `backend/services/心跳服务.py`
  - → `AGENT_HEARTBEAT_URL`
- **日志监控链路**：
  - `backend/services/日志服务.py`
  - → `backend/api/日志接口.py` SSE
  - → `frontend/src/views/LogViewer.vue`
