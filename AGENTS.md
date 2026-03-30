# AGENTS.md

本文件是仓库级速览。详细规则与背景请按需查看 `docs/` 下的专题文档。

## 技术栈概要

- 后端：`Python` + `FastAPI` + `Uvicorn` + `Pydantic` + `aiosqlite`
- 浏览器自动化：`Playwright` 控制本地 `Chrome`
- 任务队列：`Celery` + `Redis`
- 前端：`Vue 3` + `Vite` + `TypeScript` + `Vue Router` + `Pinia`
- 数据库：`SQLite`，默认文件为 `data/ecom.db`
- 外部能力：验证码平台、邮箱 `IMAP/SMTP`、Agent 回调、Agent 心跳
- 部署形态：当前以本地运行 + 局域网访问 + 外部 Agent 集成为主；`Docker` 相关文件当前项目暂无此内容

## 命名规范

- 后端 `Python` 代码使用中文命名：
  - 文件名、类名、函数名、变量名、注释均保持中文
  - 例如：`backend/services/任务服务.py`、`pages/基础页.py`
- 前端 `TypeScript` / `Vue` 代码使用英文命名：
  - 页面和组件使用 `PascalCase`
  - 工具函数、状态仓库、普通变量使用 `camelCase`
- 以下内容保持英文，不要翻译：
  - URL 路由路径
  - JSON 字段名
  - 数据库表名和字段名
  - 环境变量名
  - 第三方库 API

## 架构核心原则

- 保持分层清晰：`api -> services -> models / browser / pages / tasks`
- `POM` 层只封装页面元素和页面操作，不写业务编排
- `Task` 层负责任务执行，不在其中定义页面选择器
- 与页面交互时，优先通过 `pages/基础页.py` 中的安全方法封装操作
- API 响应统一走 `成功()` / `失败()`，响应结构固定为 `{code, data, msg}`
- 任务统一走 `backend/services/任务服务.py` 的统一执行入口
- Agent 回调与心跳遵循现有 Worker / FastAPI 职责边界：
  - Worker 负责桥接执行任务
  - FastAPI 主进程负责启动和停止心跳服务

## 协作规范

- 当前主分支可见为 `master`
- 当前项目暂无明确的多分支协作策略文档
- Commit 风格延续简短中文说明，如 `优化细节`、`当前进度：Prompt 23完成`
- 每次改动后至少同步：
  - `PLAN.md`
  - `改造进度.md`
- 仓库还维护角色化流程文档：
  - `.pipeline/progress.md`
  - `.pipeline/review.md`
  - `.pipeline/fixes.md`
- 角色化职责分工：
  - `.roles/builder/AGENTS.md`：开发执行者，写代码并记录 `.pipeline/progress.md`
  - `.roles/reviewer/AGENTS.md`：代码审查者，只找问题并记录 `.pipeline/review.md`
  - `.roles/fixer/AGENTS.md`：问题修复者，按清单修复并记录 `.pipeline/fixes.md`
- Git 层面的 PR 模板和正式评审流程文档：当前项目暂无此内容
- 测试命令：`python -m pytest -c tests/pytest.ini -q`
- 前端常用命令：
  - `cd frontend && npm install`
  - `cd frontend && npm run dev`
  - `cd frontend && npm run build`

## 禁止事项

- 不要把后端 `Python` 命名改成英文
- 不要在前端 `TypeScript` / `Vue` 中使用中文命名
- 不要在 API 中手写任意 JSON 响应，统一使用 `成功()` / `失败()`
- 不要在 `POM` 层写业务逻辑
- 不要在 `Task` 层写页面选择器
- 不要直接把常规交互写成裸 `page.click()` / `page.fill()`
- 不要复用不同店铺的 `BrowserContext`
- 不要把数据库表名、字段名、URL 路由路径、JSON 字段名改成中文
- 不要把硬编码配置直接写进代码，统一走 `.env` 与 `backend/配置.py`
- 不要遗漏任务 `执行` 方法上的 `@自动回调`
- 不要让 Worker 与 HTTP 分叉出两套不同的任务执行逻辑
- 不要在 Worker 端编排状态机或流程逻辑
- 不要在 Celery Worker 中启动心跳服务
- 不要把 Celery Worker 池改回 `prefork`；当前约束是 `-P solo`
- 不要提交以下内容：
  - `.env`
  - `data/`
  - `frontend/dist/`
  - `node_modules/`

## docs 目录索引

- `docs/architecture.md`
  - 项目概述、分层设计、目录结构、入口文件、核心模块、调用链路
- `docs/api-spec.md`
  - 路由清单、统一响应、请求模型、分页协议、错误处理、认证现状
- `docs/database.md`
  - SQLite 表结构、字段说明、关联关系、Pydantic 数据模型
- `docs/coding-style.md`
  - 代码风格、命名边界、分层约束、文件放置规范
- `docs/callback.md`
  - Celery Worker、Redis、Agent 回调、心跳机制、通信边界
- `docs/testing.md`
  - 测试框架、测试文件、覆盖范围、命名规则、当前测试现状
- `docs/frontend.md`
  - 前端路由、页面职责、公共组件、布局和数据流
- `docs/deployment.md`
  - 技术栈详细版本、环境变量、依赖安装、启动命令、部署说明

## 阅读顺序建议

- 想了解系统结构：先看 `docs/architecture.md`
- 想改后端接口：再看 `docs/api-spec.md` 与 `docs/database.md`
- 想改前端页面：看 `docs/frontend.md` 与 `docs/coding-style.md`
- 想改 Worker / Agent：看 `docs/callback.md`
- 想跑环境或排查配置：看 `docs/deployment.md`
- 想补测试或做回归：看 `docs/testing.md`
