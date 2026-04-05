# AGENTS.md

本文件是仓库级速览。详细规则与背景请按需查看 `docs/` 下的专题文档。

## 技术栈概要

- 后端：`Python` + `FastAPI` + `Uvicorn` + `Pydantic` + `aiosqlite`
- 浏览器自动化：`Playwright` 控制本地 `Chrome`
- 任务队列：`Celery` + `Redis`
- 前端：`Vue 3` + `Vite` + `TypeScript` + `Vue Router` + `Pinia`
- 数据库：`SQLite`，默认文件为 `data/ecom.db`
- 外部能力：验证码平台、邮箱 `IMAP/SMTP`、Agent 回调、Agent 心跳
- 部署形态：当前以本地运行 + 局域网访问 + 外部 Agent 集成为主
- 运行时配置：优先存放在 `settings` 表，通过 `backend/config.py` 的 `配置实例` 统一读取；不要新增对 `.env` 的运行时依赖

## 命名规范

- 后端 `Python` 代码使用中文命名：
  - 文件名、类名、函数名、变量名、注释均保持中文
  - 例如：`backend/services/task_service.py`、`pages/base_page.py`
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
- 与页面交互时，优先通过 `pages/base_page.py` 中的安全方法封装操作
- API 响应统一走 `成功()` / `失败()`，响应结构固定为 `{code, data, msg}`
- 任务统一走 `backend/services/task_service.py` 的统一执行入口
- Agent 回调与心跳遵循现有 Worker / FastAPI 职责边界：
  - Worker 负责桥接执行任务
  - FastAPI 主进程负责启动和停止心跳服务
- Service 文件应围绕单一业务轴组织；如果一个文件同时混入 Redis 状态、数据库同步、流程编排、派发、取消等多类职责，后续改动优先拆分
- 共享解析、导入、归一化逻辑应提取到 shared util 或专门 service；不要跨服务调用别人的 `_私有方法`
- API 层只做协议适配和参数整理，不要通过 monkey patch 或赋值的方式改写 service 内部方法
- Celery 同步任务桥接异步逻辑时，统一复用 `tasks/async_utils.py`
- 前端当前主路由容器为 `/shops`、`/business`、`/data`、`/monitor`、`/browser`、`/settings`
- `/flows`、`/execute`、`/schedules`、`/task-params`、`/logs`、`/tasks` 当前是兼容跳转入口，不再是主导航结构

## 当前技术债提醒

- `backend/services/execute_service.py`
  - 当前体量过大，混合了 Redis 状态缓存、批次状态同步、流程预检、任务派发、停止取消等职责
- `backend/services/task_service.py`
  - 当前体量过大，混合了任务记录、流程上下文、浏览器生命周期、执行续跑等职责
- `backend/services/flow_input_service.py`
  - 直接复用了 `task_params_service` 的多个 `_私有方法`，说明共享导入解析层缺失
- `backend/api/task_api.py`
  - `/execute-internal` 里存在运行时改写 `任务服务` 内部方法的兼容实现，不应继续扩散
- `frontend/src/views/BatchExecute.vue`
  - 容器页体量偏大，同时仓库中仍保留 `frontend/src/views/batch-execute/*` 遗留片段，存在重复实现和清理不足的问题

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
- 不要把硬编码配置直接写进代码，统一走 `settings` 表与 `backend/config.py`
- 不要跨服务调用 `_私有方法`
- 不要在 API 层通过赋值或 monkey patch 改写 service 内部行为
- 不要重复实现 `_运行异步任务` 一类的 Celery 异步桥接助手，优先复用 `tasks/async_utils.py`
- 不要长期保留无路由、无导入、无说明的遗留组件或兼容层
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
  - 项目概述、分层设计、目录结构、入口文件、核心模块、技术债热点
- `docs/api-spec.md`
  - 路由清单、统一响应、请求模型、分页协议、错误处理、认证现状
- `docs/database.md`
  - SQLite 表结构、字段说明、关联关系、Pydantic 数据模型
- `docs/coding-style.md`
  - 代码风格、命名边界、分层约束、共享逻辑抽取规则
- `docs/callback.md`
  - Celery Worker、Redis、Agent 回调、心跳机制、通信边界
- `docs/testing.md`
  - 测试框架、测试目录、回归范围、命名规则、当前测试策略
- `docs/frontend.md`
  - 前端路由、容器页结构、页面职责、公共组件、遗留页面现状
- `docs/deployment.md`
  - 运行时配置来源、依赖安装、启动命令、数据目录与部署说明

## 阅读顺序建议

- 想了解系统结构：先看 `docs/architecture.md`
- 想改后端接口：再看 `docs/api-spec.md` 与 `docs/database.md`
- 想改前端页面：看 `docs/frontend.md` 与 `docs/coding-style.md`
- 想改 Worker / Agent：看 `docs/callback.md`
- 想跑环境或排查配置：看 `docs/deployment.md`
- 想补测试或做回归：看 `docs/testing.md`
