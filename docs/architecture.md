# 架构设计

## 1. 项目概述

- 项目名称：`抖店自动化工具`
- 一句话介绍：面向本地运营场景的抖店自动化系统，提供店铺管理、浏览器自动化、任务执行、运行监控和 Worker/Agent 协作能力
- 主要使用者：
  - 需要维护多店铺账号、浏览器状态和执行批量流程的运营人员
  - 需要排查任务、日志、队列和配置问题的技术人员

## 2. 整体架构

```text
Vue 3 前端
  -> FastAPI 接口层
    -> services 业务层
      -> models 数据与配置层（SQLite + settings 表）
      -> browser 浏览器管理层
      -> pages 页面对象层（POM）
      -> tasks 任务层（Celery / Worker）
        -> Redis（broker / backend）
        -> 外部 Agent 回调 / 心跳
```

- `frontend/` 负责交互界面与请求发起
- `backend/api/` 负责路由入口与协议封装
- `backend/services/` 负责业务逻辑编排
- `backend/models/` 负责数据库与数据结构
- `browser/` 负责浏览器管理、回调、验证码、恢复
- `pages/` 负责页面对象封装
- `tasks/` 负责 Celery Worker 初始化、桥接和统一执行入口
- `backend/config.py` + `settings` 表负责运行时配置读取

## 3. 当前入口文件

- FastAPI 应用：`backend/main.py`
- 路由注册：`backend/api/router.py`
- 配置代理：`backend/config.py`
- Celery 应用：`tasks/celery_app.py`
- Worker 任务入口：
  - `tasks/bridge_task.py`
  - `tasks/execute_task.py`
  - `tasks/scheduled_task.py`
- 前端入口：`frontend/src/main.ts`
- 前端路由：`frontend/src/router/index.ts`
- 前端主布局：`frontend/src/App.vue`

## 4. 目录与职责

- `backend/api/`
  - 负责接口协议、参数校验、统一响应封装
- `backend/services/`
  - 负责业务编排、状态流转、数据库与外部能力协调
- `backend/models/`
  - 负责 SQLite 初始化、数据结构定义、settings 表读写
- `browser/`
  - 负责 Playwright 浏览器实例、恢复、反检测、验证码、任务回调
- `pages/`
  - 负责页面元素与页面操作封装，不承载业务流程判断
- `tasks/`
  - 负责 Worker 初始化、同步桥接异步任务、统一任务分发
- `frontend/src/views/`
  - 负责页面容器与业务交互
- `tests/`
  - 负责后端单元测试、接口回归、前端静态回归、打包与运行时回归

## 5. 前端页面组织

当前路由定义位于 `frontend/src/router/index.ts`。

- `/`
  - 重定向到 `/shops`
- `/shops`
  - `ShopManage.vue`
- `/business`
  - `BusinessManage.vue`
  - 组合 `FlowManage.vue`、`BatchExecute.vue`、`ScheduleManage.vue`
- `/data`
  - `DataManage.vue`
  - 当前内嵌 `TaskParamsManage.vue`
- `/monitor`
  - `MonitorManage.vue`
  - 组合 `LogViewer.vue`、`TaskMonitor.vue`
- `/browser`
  - `BrowserManager.vue`
- `/settings`
  - `SystemSettings.vue`
- `/dashboard`
  - `Dashboard.vue`
- 兼容跳转路由：
  - `/flows -> /business?tab=flow`
  - `/execute -> /business?tab=execute`
  - `/schedules -> /business?tab=schedule`
  - `/task-params -> /data?tab=params`
  - `/logs -> /monitor?tab=logs`
  - `/tasks -> /monitor?tab=monitor`

说明：

- `Settings.vue` 仍留在仓库中，但当前主路由已切换到 `SystemSettings.vue`
- `FlowManage.vue`、`BatchExecute.vue`、`ScheduleManage.vue`、`TaskMonitor.vue`、`LogViewer.vue` 仍是有效页面模块，但由容器页承载

## 6. 关键调用链

- 批量执行链路：
  - `frontend/src/views/BatchExecute.vue`
  - -> `backend/api/execute_api.py`
  - -> `backend/services/execute_service.py`
  - -> `backend/services/task_service.py`
  - -> `tasks/execute_task.py` / `tasks/bridge_task.py`
- 流程输入集链路：
  - `frontend/src/views/BatchExecute.vue`
  - -> `frontend/src/api/flowInputs.ts`
  - -> `backend/api/flow_input_api.py`
  - -> `backend/services/flow_input_service.py`
- 系统设置链路：
  - `frontend/src/views/SystemSettings.vue`
  - -> `backend/api/settings_api.py`
  - -> `backend/utils/settings.py`
  - -> `settings` 表 / `backend/config.py`
- Worker 桥接链路：
  - Celery Worker
  - -> `tasks/bridge_task.py`
  - -> `backend/services/task_service.py`
  - -> 页面对象层 / 浏览器层 / 回调层

## 7. 当前技术债与热点

以下内容描述的是当前现状，不是推荐模式。

- `backend/services/execute_service.py`
  - 当前约 1532 行
  - 混合 Redis 连接管理、批次状态缓存、流程预检、运行项同步、批量派发、停止取消等职责
- `backend/services/task_service.py`
  - 当前约 1360 行
  - 混合任务记录、流程上下文准备、任务执行、浏览器生命周期、流程步骤续跑等职责
- `backend/services/flow_input_service.py`
  - 直接依赖 `task_params_service` 的多个 `_私有方法`
  - 暗示 CSV/XLSX 解析、字段规范化、店铺标识解析等共享层缺失
- `backend/api/task_api.py`
  - `/execute-internal` 存在对 `任务服务` 内部方法的运行时替换
  - 说明接口层和服务层耦合过深
- `tasks/bridge_task.py` 与 `tasks/scheduled_task.py`
  - 仍保留重复的 `_运行异步任务`
  - 与 `tasks/async_utils.py` 已有通用实现重复
- `frontend/src/views/BatchExecute.vue`
  - 当前约 561 行
  - 同时仓库保留 `frontend/src/views/batch-execute/` 遗留片段，存在重复实现与清理不足

## 8. 目标架构约束

- Service 层按业务轴拆分，避免继续堆叠到超大文件
- 共享导入、解析、字段归一化逻辑应落在可复用的 shared util/service，而不是跨服务调 `_私有方法`
- API 层只保留协议适配，不再通过 monkey patch 修正 service 行为
- Celery 同步桥接异步逻辑统一复用 `tasks/async_utils.py`
- 前端容器页负责路由与 tab 组合，复杂表单、面板、状态时间线继续拆分为子组件或 composable
