# 代码风格与命名规范

## 1. 总体原则

- 保持现有分层结构，避免在 `api/`、`services/`、`models/`、`browser/`、`pages/`、`tasks/` 之间混写职责
- Python 使用 4 空格缩进
- 公共函数尽量补充类型标注
- 仓库已有大量中文文件名与中文领域术语，除非做整体重构，否则保持现有风格一致
- 当前仓库已经存在少数超大文件，这些是技术债，不是建议模式；后续修改时优先拆分而不是继续堆叠

## 2. Python 命名规范

- 后端所有 Python 文件名、类名、函数名、变量名、注释，一律使用中文
- 适用目录：
  - `backend/`
  - `browser/`
  - `pages/`
  - `tasks/`
  - `tests/`
- 示例：
  - `backend/services/task_service.py`
  - `backend/services/execute_service.py`
  - `browser/manager.py`
  - `pages/base_page.py`
  - `tasks/execute_task.py`

## 3. Python 命名边界

- 以下内容保持英文，不要翻译：
  - Python 关键字
  - 魔术方法
  - 第三方库 API
  - URL 路由路径
  - JSON 字段名
  - 数据库表名和字段名
  - 环境变量名
  - 配置文件名

## 4. 前端命名规范

- 前端 `TypeScript` / `Vue` 代码保持英文命名
- 使用 `<script setup lang="ts">` 风格
- 页面、组件使用 `PascalCase`
- 工具函数与状态仓库使用 `camelCase`
- 当前主页面容器：
  - `ShopManage.vue`
  - `BusinessManage.vue`
  - `DataManage.vue`
  - `MonitorManage.vue`
  - `BrowserManager.vue`
  - `SystemSettings.vue`
- 前端接口调用统一走 `frontend/src/api/` 下的封装层

## 5. 配置与数据来源

- 运行时配置统一通过 `settings` 表与 `backend/config.py` 的 `配置实例` 读取
- 不要为新功能重新引入 `.env` 作为主运行时配置来源
- 不要在代码中散落硬编码配置值

## 6. 分层约束

### 6.1 API 层

- 负责接收请求、调用服务层、返回统一响应
- 不要在 API 层编排复杂业务逻辑
- 不要在 API 层通过给 service 实例赋值的方式改写内部方法

### 6.2 Services 层

- 负责业务编排、异常封装、服务协调
- 一个 service 文件应尽量围绕单一业务轴组织
- 如果一个 service 同时处理存储、状态缓存、流程编排、外部调用和取消控制，后续改动优先拆分
- 不要跨 service 调用别人的 `_私有方法`
- 共享 CSV/XLSX 解析、字段规范化、店铺标识解析等逻辑，应提取到 shared util 或专门 service

### 6.3 Models 层

- 负责数据库模型、Pydantic 数据结构和持久化相关基础能力
- 不要在 models 层写业务编排逻辑

### 6.4 POM 层

- 只负责页面元素与页面动作
- 不要在 POM 中写业务逻辑
- 与页面交互时优先走 `基础页.安全点击()`、`基础页.安全填写()` 等封装

### 6.5 Task 层

- 负责任务执行与调度桥接
- 不要在 Task 中写页面选择器
- 任务 `执行` 方法必须加 `@自动回调`
- Celery 同步任务调用异步逻辑时，统一复用 `tasks/async_utils.py`

### 6.6 前端视图层

- 容器页负责路由、tab、页面组合
- 表单、时间线、状态面板、复杂请求编排应继续拆到子组件或 composable
- 对于像 `BatchExecute.vue` 这类已偏大的页面，新增需求时优先拆分，不要再继续堆到单文件中
- 无路由、无导入的遗留组件应尽快删除，或明确标注其兼容用途

## 7. API 路由与协议命名

- API 路径使用英文、小写、资源型命名
- JSON 字段名保持英文
- API 统一响应必须使用：
  - `成功()`
  - `失败()`

## 8. 数据库命名规范

- SQLite 中的表名和字段名保持英文
- 不要将数据库表名和字段名改成中文

## 9. 测试命名规范

- 使用 `pytest` 与 `pytest-asyncio`
- 测试文件命名遵循：
  - `test_*.py`
  - `测试_*.py`
- 新增功能或修复缺陷时，优先补针对性回归测试

## 10. 常见红线

- 不要直接调用 `page.click()` / `page.fill()` 作为常规交互入口
- 不要在 API 中手写不统一的 JSON 结构
- 不要把后端命名改成英文，也不要把前端命名改成中文
- 不要把运行时配置写回 `.env` 驱动主流程
- 不要复用不同店铺的 `BrowserContext`
- 不要把兼容层、历史遗留代码当成新代码模板继续复制
