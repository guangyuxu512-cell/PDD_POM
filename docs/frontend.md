# 前端页面设计

## 1. 技术与入口

- 前端目录：`frontend/`
- 源码目录：`frontend/src/`
- 技术栈：
  - `Vue 3`
  - `TypeScript`
  - `Vue Router`
  - `Pinia`
  - `Vite`
- 入口文件：
  - `frontend/src/main.ts`
  - `frontend/src/router/index.ts`
  - `frontend/src/App.vue`

## 2. 当前路由结构

路由定义位于 `frontend/src/router/index.ts`。

| 路径 | 路由名 | 页面文件 | 作用 |
| --- | --- | --- | --- |
| `/` | - | - | 重定向到 `/shops` |
| `/shops` | `ShopManage` | `frontend/src/views/ShopManage.vue` | 店铺管理 |
| `/business` | `BusinessManage` | `frontend/src/views/BusinessManage.vue` | 业务管理容器页 |
| `/data` | `DataManage` | `frontend/src/views/DataManage.vue` | 数据管理容器页 |
| `/monitor` | `MonitorManage` | `frontend/src/views/MonitorManage.vue` | 运行监控容器页 |
| `/browser` | `BrowserManager` | `frontend/src/views/BrowserManager.vue` | 浏览器管理 |
| `/settings` | `SystemSettings` | `frontend/src/views/SystemSettings.vue` | 系统设置 |
| `/dashboard` | `Dashboard` | `frontend/src/views/Dashboard.vue` | 仪表盘 |

兼容跳转路由：

| 旧路径 | 当前跳转 |
| --- | --- |
| `/flows` | `/business?tab=flow` |
| `/execute` | `/business?tab=execute` |
| `/schedules` | `/business?tab=schedule` |
| `/task-params` | `/data?tab=params` |
| `/logs` | `/monitor?tab=logs` |
| `/tasks` | `/monitor?tab=monitor` |

## 3. 页面容器关系

### 3.1 `BusinessManage.vue`

- 负责业务域 tab 切换
- 当前组合页面：
  - `FlowManage.vue`
  - `BatchExecute.vue`
  - `ScheduleManage.vue`

### 3.2 `DataManage.vue`

- 当前作为数据域容器页
- 当前直接承载：
  - `TaskParamsManage.vue`

### 3.3 `MonitorManage.vue`

- 负责监控域 tab 切换
- 当前组合页面：
  - `LogViewer.vue`
  - `TaskMonitor.vue`

### 3.4 其他独立页面

- `ShopManage.vue`
- `BrowserManager.vue`
- `SystemSettings.vue`
- `Dashboard.vue`

## 4. 主布局

- 主布局位于 `frontend/src/App.vue`
- 布局结构：
  - 左侧导航
  - 中间内容区 `router-view`
  - 全局 `Toast` 组件
- 主导航当前围绕容器页组织，而不是直接把每个业务子页都挂到一级导航

## 5. 页面职责

- `ShopManage.vue`
  - 管理店铺列表、店铺打开、状态刷新和店铺基础信息
- `BusinessManage.vue`
  - 承接流程管理、批量执行、定时任务三个业务子域
- `DataManage.vue`
  - 承接任务参数、导入数据等数据域能力
- `MonitorManage.vue`
  - 承接日志与任务监控
- `BrowserManager.vue`
  - 管理浏览器实例和浏览器相关状态
- `SystemSettings.vue`
  - 管理系统配置，并调用 Redis、验证码、飞书等测试接口

## 6. 公共组件

目录：`frontend/src/components/`

- `Modal.vue`
  - 通用弹窗容器
- `ConfirmDialog.vue`
  - 通用确认弹窗
- `Toast.vue`
  - 全局消息提示
- `StatusBadge.vue`
  - 状态标签
- `ShopCard.vue`
  - 店铺卡片
- `BrowserStatus.vue`
  - 浏览器状态展示
- `LogTable.vue`
  - 日志表格展示

## 7. 前端数据层

- `frontend/src/api/`
  - 前端 API 封装目录
- `frontend/src/stores/`
  - Pinia 状态仓库目录
- `frontend/src/utils/`
  - 工具函数目录

## 8. 当前遗留与技术债

- `frontend/src/views/Settings.vue`
  - 仍保留在仓库中，但不是当前主路由页面
- `frontend/src/views/batch-execute/ExecuteConfigPanel.vue`
  - 当前未被主页面引用
- `frontend/src/views/batch-execute/BatchStatusPanel.vue`
  - 当前未被主页面引用
- `frontend/src/views/BatchExecute.vue`
  - 体量偏大，已经承担了较多选择、状态与执行编排逻辑

以上遗留内容代表当前状态，不应继续作为新代码模板复制。

## 9. 实现约束

- 前端命名保持英文，不要使用中文命名变量、函数、组件文件
- 页面放在 `views/`，复用组件放在 `components/`
- 接口调用统一通过 `api/` 封装层发起
- API 响应格式固定为 `{code, data, msg}`
- 容器页负责路由和组合，复杂业务面板优先拆分为子组件或 composable
- 对无路由、无导入的遗留页面要么删除，要么明确标注兼容用途
