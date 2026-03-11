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

## 2. 当前页面路由

路由定义位于 `frontend/src/router/index.ts`。

| 路径 | 路由名 | 页面文件 | 作用 |
| --- | --- | --- | --- |
| `/` | `Dashboard` | `frontend/src/views/Dashboard.vue` | 仪表盘 |
| `/shops` | `ShopManage` | `frontend/src/views/ShopManage.vue` | 店铺管理 |
| `/browser` | `BrowserManager` | `frontend/src/views/BrowserManager.vue` | 浏览器管理 |
| `/tasks` | `TaskMonitor` | `frontend/src/views/TaskMonitor.vue` | 任务监控 |
| `/logs` | `LogViewer` | `frontend/src/views/LogViewer.vue` | 日志查看 |
| `/settings` | `Settings` | `frontend/src/views/Settings.vue` | 系统设置 |

## 3. 主布局

- 主布局位于 `frontend/src/App.vue`
- 布局结构：
  - 左侧固定侧边栏
  - 中间内容区 `router-view`
  - 全局 `Toast` 组件
- 侧边栏导航项：
  - 仪表盘
  - 店铺管理
  - 浏览器
  - 任务监控
  - 日志
  - 设置

## 4. 页面职责

### 4.1 `Dashboard.vue`

- 展示系统概览数据
- 对应角色是总览入口页

### 4.2 `ShopManage.vue`

- 管理店铺列表
- 承接店铺创建、编辑、删除、打开浏览器、检查状态等操作
- 与后端 `店铺接口` 紧密对应

### 4.3 `BrowserManager.vue`

- 管理浏览器实例与浏览器初始化配置
- 查看当前运行中的浏览器状态

### 4.4 `TaskMonitor.vue`

- 查看任务列表与任务状态
- 触发任务执行
- 取消或清理任务记录

### 4.5 `LogViewer.vue`

- 查看日志列表
- 通过日志接口和 SSE 获取运行日志

### 4.6 `Settings.vue`

- 查看系统配置
- 测试 Redis 连接
- 查看健康检查结果

## 5. 公共组件

目录：`frontend/src/components/`

- `BrowserStatus.vue`
  - 浏览器实例状态展示
- `ConfirmDialog.vue`
  - 通用确认弹窗
- `HelloWorld.vue`
  - 默认示例组件，业务价值有限
- `LogTable.vue`
  - 日志表格展示
- `Modal.vue`
  - 通用弹窗容器
- `ShopCard.vue`
  - 店铺卡片
- `StatCard.vue`
  - 仪表盘统计卡片
- `StatusBadge.vue`
  - 状态标签
- `Toast.vue`
  - 全局消息提示

## 6. 前端数据层

- `frontend/src/api/index.ts`
  - 前端统一请求封装入口
- `frontend/src/api/mock.ts`
  - Mock 数据
- `frontend/src/stores/`
  - Pinia 状态仓库目录
- `frontend/src/utils/`
  - 工具函数目录

## 7. 页面与后端关系

- `ShopManage.vue`
  - 对接 `/api/shops` 相关接口
- `BrowserManager.vue`
  - 对接 `/api/browser` 相关接口
- `TaskMonitor.vue`
  - 对接 `/api/tasks` 相关接口
- `LogViewer.vue`
  - 对接 `/api/logs` 相关接口
- `Settings.vue`
  - 对接 `/api/system` 相关接口

## 8. 命名与实现约束

- 前端命名保持英文，不要使用中文命名变量、函数、组件文件。
- 组件使用 `PascalCase`。
- 页面放在 `views/`，复用组件放在 `components/`。
- 接口调用统一通过 `api/index.ts` 封装。
- API 响应格式固定为 `{code, data, msg}`。

## 9. 当前缺失项

- 前端 SSR：当前项目暂无此内容
- 前端自动化测试：当前项目暂无此内容
- 额外页面分组权限控制：当前项目暂无此内容
