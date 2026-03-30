# 代码风格与命名规范

## 1. 总体原则

- 保持现有分层结构，避免在 `api/`、`services/`、`models/`、`browser/`、`pages/`、`tasks/` 之间混写职责。
- Python 使用 4 空格缩进。
- 公共函数尽量补充类型标注。
- 仓库已有大量中文文件名与中文领域术语，除非做整体重构，否则保持现有风格一致。

## 2. Python 命名规范

- 后端所有 Python 文件名、类名、函数名、变量名、注释，一律使用中文。
- 适用目录：
  - `backend/`
  - `browser/`
  - `pages/`
  - `tasks/`
  - `tests/`
- 已确认示例：
  - `backend/services/任务服务.py`
  - `backend/services/店铺服务.py`
  - `browser/管理器.py`
  - `pages/基础页.py`
  - `tasks/登录任务.py`
  - `tests/单元测试/测试_任务服务.py`

## 3. Python 命名边界

- 以下内容保持英文，不要翻译：
  - Python 关键字
  - 魔术方法
  - 装饰器名本体外的第三方 API 调用
  - Playwright / asyncio / Celery / FastAPI 等第三方库方法
  - URL 路由路径
  - JSON 字段名
  - 数据库表名和字段名
  - 环境变量名
  - 配置文件名

## 4. 前端命名规范

- 前端 `TypeScript` / `Vue` 代码保持英文命名。
- 使用 `<script setup lang="ts">` 风格。
- 页面、组件使用 `PascalCase`：
  - `Dashboard.vue`
  - `ShopManage.vue`
  - `BrowserManager.vue`
  - `TaskMonitor.vue`
  - `LogViewer.vue`
  - `Settings.vue`
  - `ShopCard.vue`
  - `StatusBadge.vue`
- 工具函数与状态仓库使用 `camelCase`。
- 前端接口调用统一走 `frontend/src/api/index.ts` 封装。

## 5. API 路由与协议命名

- API 路径使用英文、小写、资源型命名：
  - `/api/shops`
  - `/api/tasks`
  - `/api/logs`
  - `/api/browser`
  - `/api/system`
- JSON 字段名保持英文：
  - `code`
  - `data`
  - `msg`
- API 统一响应必须使用：
  - `成功()`
  - `失败()`

## 6. 数据库命名规范

- SQLite 中的表名和字段名保持英文。
- 当前表名：
  - `shops`
  - `task_logs`
  - `operation_logs`
- 不要将数据库表名和字段名改成中文。

## 7. 分层约束

### 7.1 API 层

- 负责接收请求、调用服务层、返回统一响应。
- 不要在 API 层编排复杂业务逻辑。

### 7.2 Services 层

- 负责业务编排、异常封装、服务协调。
- 这里是主要业务逻辑承载层。

### 7.3 POM 层

- 只负责页面元素与页面动作。
- 不要在 POM 中写业务逻辑。
- 与页面交互时优先走 `基础页.安全点击()`、`基础页.安全填写()` 等封装。

### 7.4 Task 层

- 负责任务执行与调度桥接。
- 不要在 Task 中写页面选择器。
- 任务 `执行` 方法必须加 `@自动回调`。

## 8. 测试命名规范

- 使用 `pytest` 与 `pytest-asyncio`。
- 测试文件命名应遵循：
  - `test_*.py`
  - `测试_*.py`
- 当前仓库主要使用中文测试文件名，例如：
  - `测试_登录任务.py`
  - `测试_Celery桥接.py`

## 9. 常见红线

- 不要直接调用 `page.click()` / `page.fill()` 作为常规交互入口。
- 不要在 API 中手写不统一的 JSON 结构。
- 不要把后端命名改成英文，也不要把前端命名改成中文。
- 不要把硬编码配置直接写进代码。
- 不要复用不同店铺的 `BrowserContext`。
