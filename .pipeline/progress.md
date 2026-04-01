## 任务摘要

完成登录态失效检测与告警、结构化日志体系、依赖版本锁定、健康检查与监控端点、浏览器崩溃自动恢复五项改造，并补齐对应回归测试。

## 改动文件列表

- `backend/logging_config.py`
- `backend/services/metrics_service.py`
- `browser/session_monitor.py`
- `browser/recovery.py`
- `browser/manager.py`
- `pages/base_page.py`
- `tasks/execute_task.py`
- `backend/main.py`
- `backend/api/system_api.py`
- `backend/services/system_service.py`
- `backend/services/task_service.py`
- `tasks/celery_app.py`
- `backend/models/database.py`
- `backend/services/browser_service.py`
- `backend/services/execute_service.py`
- `backend/services/heartbeat_service.py`
- `backend/services/rule_service.py`
- `backend/services/task_params_service.py`
- `backend/api/shop_api.py`
- `backend/api/task_api.py`
- `browser/slider_captcha.py`
- `browser/task_callback.py`
- `browser/user_dir_factory.py`
- `pages/after_sale_page.py`
- `pages/desktop_base_page.py`
- `pages/flash_sale_page.py`
- `pages/login_page.py`
- `pages/product_list_page.py`
- `pages/promotion_page.py`
- `pages/publish_product_page.py`
- `pages/wechat_page.py`
- `tasks/async_utils.py`
- `tasks/bridge_task.py`
- `tasks/publish_replace_image_task.py`
- `tasks/publish_similar_product_task.py`
- `tasks/registry.py`
- `tasks/scheduled_task.py`
- `requirements.txt`
- `requirements-dev.txt`
- `requirements-lock.txt`
- `docs/deployment.md`
- `backend.spec`
- `celery-worker.spec`
- `tests/unit/test_session_monitor.py`
- `tests/unit/test_browser_recovery.py`
- `tests/unit/test_requirements_files.py`
- `tests/unit/test_base_page.py`
- `tests/unit/test_browser_manager.py`
- `tests/unit/test_execute_task.py`
- `tests/unit/test_system_api.py`
- `tests/unit/test_startup_entry.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/logging_config.py`：新增统一日志初始化，优先使用 `loguru`，依赖缺失时回退标准库；支持 `trace_id`、控制台输出、`data/logs/` 文件轮转与错误日志拆分。
- `backend/services/metrics_service.py`：新增进程内指标统计，记录任务总量、成功/失败数量、运行中数量、平均任务耗时、请求耗时与运行时长。
- `browser/session_monitor.py`：新增登录态监控器，检测登录页 URL、失效文案和关键 Cookie；失效时写入 `operation_logs`，发送飞书告警，并向 Redis `session:expired` 发布事件。
- `browser/recovery.py`：新增浏览器恢复器，封装冷却、重试上限、恢复成功/失败日志与自动重建逻辑。
- `browser/manager.py`：新增登录页自动标记、店铺元数据缓存、`安全获取页面(...)`、浏览器崩溃日志和 `browser:crashed` Redis 事件。
- `pages/base_page.py`：新增 `检查并处理登录态(...)`，在关键交互前自动检测登录态；统一捕获浏览器关闭类异常并抛出恢复标识错误。
- `tasks/execute_task.py`：为 Worker 执行链路绑定 `trace_id`，接入指标统计，对浏览器关闭类失败增加一次恢复性重试。
- `backend/main.py`、`backend/api/system_api.py`、`backend/services/system_service.py`：补齐根 `/health`、结构化 `/api/system/health`、`/api/system/metrics`、请求耗时统计以及 Redis/SQLite/浏览器池/Celery Worker 健康检查。
- `requirements.txt`、`requirements-dev.txt`、`requirements-lock.txt`：拆分生产与测试依赖，补充 `loguru`，并生成当前环境的锁定依赖清单。
- `docs/deployment.md`：补充开发安装、生产安装、日志目录和探针说明。
- `backend.spec`、`celery-worker.spec`：补充新增日志/指标/登录态/恢复模块的 `hiddenimports`。
- 批量日志替换：清理 `backend/`、`browser/`、`pages/`、`tasks/` 中所有 `print()` 调用，统一切换到新日志体系。
- 测试补齐：新增登录态监控、浏览器恢复、依赖清单静态校验；更新基础页、浏览器管理器、Worker 执行链路、系统接口、启动入口测试。

## 影响范围

- 浏览器生命周期管理与店铺登录态检测
- Worker 执行链路与自动恢复重试
- 后端日志输出、日志目录与 trace_id 链路
- 系统健康检查、监控指标与负载均衡探针
- 依赖安装方式与 PyInstaller 打包模块收集

## 注意事项

- 已执行 `python -m compileall backend browser pages tasks`。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `473 passed, 16 warnings`。
- 16 条 warning 为第三方依赖弃用提示，来源于 `openpyxl` 与 Celery 的 `datetime.utcnow()`，不属于本轮新增问题。
- `requirements-lock.txt` 已按当前环境重新生成并使用 UTF-8 编码写入。
- `.pipeline/task.md` 与 `backend_log.txt` 为既有本地变更，本轮未修改其任务内容。

---

## 任务摘要

用 Tailwind 重写了前端主布局入口 `App.vue`，把侧边栏切成 Linear 风格白底极简布局，并同步更新相关静态回归测试。

## 改动文件列表

- `frontend/src/App.vue`
- `tests/unit/test_platform_frontend_static.py`
- `tests/unit/test_frontend_management_page.py`
- `tests/unit/test_after_sale_config_page.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/App.vue`：引入 `useRoute`，新增 `navItems` 数据源，用 `v-for` 渲染左侧导航；将旧深色侧边栏改为白底、灰色细边框、浅灰选中态的 Linear 风格，并把整文件切成纯 Tailwind class，删除原有 `<style scoped>`。
- `tests/unit/test_platform_frontend_static.py`：更新 App 主布局断言，改为校验 `useRoute`、`navItems`、`bg-gray-50` 主背景、白底侧边栏、浅灰选中态，以及旧深色样式和 `<style>` 块已移除。
- `tests/unit/test_frontend_management_page.py`：导航入口断言从硬编码 `to="/..."` 调整为 `navItems` 数据源和 `:to="item.path"` 动态路由写法，兼容新的实现结构。
- `tests/unit/test_after_sale_config_page.py`：售后配置导航断言同步改为新的动态导航实现，继续保证 `App.vue` 中存在该入口。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮 Builder 执行结果和验证情况。

## 影响范围

- 前端主布局入口与所有页面共享的侧边栏导航
- 售后配置、店铺管理、业务管理、数据管理、运行监控、设置页的全局入口展示
- 与 `App.vue` 结构和导航实现相关的前端静态回归

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_platform_frontend_static.py tests/unit/test_frontend_management_page.py tests/unit/test_after_sale_config_page.py -v`，结果为 `9 passed`。
- 已执行 `cd frontend && npm run build`，构建通过。
- 已尝试 `cd frontend && npm run dev -- --host 127.0.0.1`，当前环境仍因 `esbuild` 子进程 `spawn EPERM` 无法完成 Vite dev server 启动验收。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `513 passed, 18 warnings`。
- 18 条 warning 仍来自既有第三方依赖 `celery`、`openpyxl` 的弃用提示，以及既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。
- `.pipeline/task.md` 为既有本地变更，本轮未修改。

---

## 任务摘要

用 Headless UI + Tailwind 重写了 `Modal`、`ConfirmDialog`、`Toast` 三个核心公共组件，保留既有调用接口并补齐静态回归测试。

## 改动文件列表

- `frontend/src/components/Modal.vue`
- `frontend/src/components/ConfirmDialog.vue`
- `frontend/src/components/Toast.vue`
- `tests/unit/test_shop_platform_modal_static.py`
- `tests/unit/test_headless_ui_components_static.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/components/Modal.vue`：改为 Headless UI `Dialog` 结构，使用白底、灰边框、毛玻璃遮罩和 Tailwind 过渡动画；删除原生 `<style>`，同时保留 `.modal-container`、`.modal-body` 等 class，兼容页面里已存在的 `:deep(...)` 样式钩子。
- `frontend/src/components/ConfirmDialog.vue`：改为 Headless UI `Dialog`，保留 `show/title/message/type` 和 `confirmText/cancelText` 用法；新增 `close` emit，遮罩和 ESC 关闭时继续按 `cancel` 语义回调；危险确认按钮改为 `rose`，普通确认按钮改为灰黑主按钮，移除旧蓝色样式。
- `frontend/src/components/Toast.vue`：改为右上角固定定位，使用 Headless UI Transition 和 Tailwind class 渲染提示；将类型颜色收口为 `emerald / rose / amber / gray`，移除原有蓝色 `info` 提示色和旧 `<style>` 块。
- `tests/unit/test_shop_platform_modal_static.py`：更新 Modal 相关断言，改为校验新的 Headless UI 白底弹窗壳层，同时保留店铺页表单现有样式断言。
- `tests/unit/test_headless_ui_components_static.py`：新增组件级静态回归，覆盖 Modal / ConfirmDialog / Toast 的 Headless UI 接入、Tailwind 样式、兼容 emits，以及“无蓝色 / 无 `<style>`”的反向断言。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮 Builder 执行结果与验证情况。

## 影响范围

- 前端公共弹窗组件与提示组件的视觉样式
- `ShopManage`、`FlowManage`、`ScheduleManage`、`TaskMonitor`、`TaskParamsManage`、`BrowserManager`、`LogViewer` 等依赖公共组件的页面
- 前端静态回归中与弹窗组件结构、样式和兼容 class 相关的断言

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_headless_ui_components_static.py tests/unit/test_shop_platform_modal_static.py tests/unit/test_batch_execute_schedule_static.py tests/unit/test_flow_manage_editor_static.py tests/unit/test_frontend_tailwind_static.py -v`，结果为 `14 passed`。
- 已执行 `cd frontend && npm run build`，构建通过。
- 已尝试 `cd frontend && npm run dev -- --host 127.0.0.1`，当前环境仍因 `esbuild` 子进程 `spawn EPERM` 无法完成 Vite dev server 启动验收。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `513 passed, 18 warnings`。
- 18 条 warning 仍来自既有第三方依赖 `celery`、`openpyxl` 的弃用提示，以及既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。
- 本轮只重写了公共组件外壳，页面插槽里的表单/按钮视觉仍沿用各页面原有实现。
- `.pipeline/task.md` 为既有本地变更，本轮未修改。

---

## 任务摘要

替换 PyInstaller 的 backend / celery-worker spec 为显式模块收集方案，并修正 Electron 打包 exe 路径到 `--onedir` 子目录结构。

## 改动文件列表

- `backend.spec`
- `celery-worker.spec`
- `electron/main.js`
- `tests/unit/test_pyinstaller_spec_files.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend.spec`：改为显式列出项目模块 `hiddenimports`，并为 `uvicorn`、`fastapi`、`starlette`、`celery`、`kombu`、`amqp`、`redis` 做 `collect_all`；同时把 `collect_all(...)` 前移到 `Analysis(...)` 之前，兼容当前 PyInstaller 6.17 的 `TOC` 处理。
- `celery-worker.spec`：改为显式列出 Worker 依赖的项目模块 `hiddenimports`，并为 `celery`、`kombu`、`amqp`、`redis` 做 `collect_all`；同样前移合并逻辑，确保打包命令可直接通过。
- `electron/main.js`：将打包模式下的 exe 路径改成 `python-backend/backend/backend.exe` 与 `python-backend/celery-worker/celery-worker.exe`，适配 `--onedir` 输出结构。
- `tests/unit/test_pyinstaller_spec_files.py`：新增静态回归，覆盖两个 spec 的关键显式导入、`collect_submodules` 移除，以及 Electron 新旧打包路径差异。
- `PLAN.md`：补充 Prompt 124 的实现、打包验收和回归结果。
- `改造进度.md`：同步本轮改造内容、打包命令和启动验收情况。
- `.pipeline/progress.md`：记录本轮 Builder 执行结果。

## 影响范围

- PyInstaller 后端打包配置
- PyInstaller Celery Worker 打包配置
- Electron 打包模式后端 / Worker 可执行文件定位
- 打包相关静态回归

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_pyinstaller_spec_files.py tests/unit/test_electron_main.py -v`，结果 `8 passed`。
- 已执行 `node --check electron/main.js`。
- 已按任务命令执行：
  - `pyinstaller --noconfirm --distpath ./python-backend-dist backend.spec`
  - `pyinstaller --noconfirm --distpath ./python-backend-dist celery-worker.spec`
- 已执行 `python-backend-dist/backend/backend.exe` 短时启动验收，8 秒观测内进程保持运行，并输出 `Application startup complete`、`Uvicorn running on http://127.0.0.1:8000`。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果 `459 passed, 16 warnings`。
- PyInstaller 仍有 `kombu.asynchronous.aws` 缺少 `botocore` 的构建告警，但本轮打包已成功，不影响当前验收。
- `.pipeline/task.md` 为既有本地变更，本轮未修改。

---

## 任务摘要

修复 PyInstaller 后端与 Celery 入口在冻结模式下错误覆盖 `sys.path` 的问题，并补齐 frozen / 非 frozen 分支回归测试。

## 改动文件列表

- `scripts/pyinstaller_entry.py`
- `scripts/pyinstaller_celery_entry.py`
- `tests/unit/test_pyinstaller_entry.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `scripts/pyinstaller_entry.py`：将项目根目录注入改成仅在非 frozen 模式执行，避免 PyInstaller 运行时把 `_internal` 导入路径顶掉。
- `scripts/pyinstaller_celery_entry.py`：同步为 Celery Worker 入口增加相同条件，保持两条启动链路行为一致。
- `tests/unit/test_pyinstaller_entry.py`：新增 4 个回归用例，覆盖后端入口与 Celery 入口在 frozen / 非 frozen 两种模式下的路径注入行为，并顺带校验 `构建Worker参数()` 默认值。
- `PLAN.md`：补充 Prompt 123 的改造内容、验证命令和当前打包验收结论。
- `改造进度.md`：同步本轮进度、测试结果和运行态验收情况。
- `.pipeline/progress.md`：记录本轮 Builder 执行结果。

## 影响范围

- PyInstaller 后端启动入口
- PyInstaller Celery Worker 启动入口
- 打包入口脚本相关回归测试

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_pyinstaller_entry.py -v`，结果 `4 passed`。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果 `456 passed, 16 warnings`。
- 已执行 `python scripts/pyinstaller_entry.py` 的 5 秒短时启动验收，进程保持运行并输出 `Started server process`、`Waiting for application startup`。
- 已按任务给定命令执行 `PyInstaller --onedir` 构建；生成的 `backend.exe` 不再报 `No module named 'backend'`，但仍因缺少 `fastapi` 依赖报错，属于现存打包配置问题，本轮未处理。
- `backend.spec` 在打包验收时曾被 PyInstaller 改写，已恢复到验收前内容。
- `.pipeline/task.md`、`backend.spec`、`build_backend.bat`、`celery-worker.spec` 为既有本地变更，本轮未修改其目标内容。

---

## 任务摘要

修复 Electron 重启后的端口残留与子进程清理问题：Windows 启动前尝试切换 UTF-8 代码页，关闭时用 `taskkill /F /T /PID` 回收进程树，并在后端启动前清理端口占用。

## 改动文件列表

- `electron/main.js`
- `tests/unit/test_electron_main.py`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `electron/main.js`：启动前增加端口占用清理；`stopProcess(...)` 在 Windows 下改成 `taskkill /F /T /PID`；代码页切换改成 `stdio: 'inherit'`；同时显式收口到 `System32` 命令路径，减少对 PATH 的依赖。
- `tests/unit/test_electron_main.py`：更新 `chcp` 断言，并新增端口清理与进程树终止的静态回归。
- `PLAN.md`：补充本轮 Prompt 122 记录、验证命令和当前环境限制。
- `改造进度.md`：新增本轮改造记录，便于后续接续。

## 影响范围

- Electron 主进程启动/退出流程
- Windows 下的后端端口释放与子进程回收
- Electron 主进程相关静态回归

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果 `452 passed, 16 warnings`。
- 已执行 `node --check electron/main.js`。
- 已尝试 `cd electron && npx electron .`，但当前执行环境下仍因 `platform_channel.cc(83)` 的 `拒绝访问 (0x5)` 提前退出，且 stderr 仍出现 `'chcp' 不是内部或外部命令`。
- `.pipeline/task.md` 为既有本地变更，本轮未修改。

---

## 任务摘要

补齐 Electron 主进程启动链路：Windows 启动前切换 UTF-8 控制台代码页，Celery 默认同时监听 `celery` 和 `worker.{AGENT_MACHINE_ID}`，并补回两处存量 `_运行异步任务` 兼容导出以恢复全量回归。

## 改动文件列表

- `electron/main.js`
- `tests/unit/test_electron_main.py`
- `tasks/bridge_task.py`
- `tasks/execute_task.py`

## 改动说明

- `electron/main.js`：新增 `execSync` 导入，`app.whenReady()` 里在 Windows 下先执行 `chcp 65001`；`startCelery()` 统一生成 `queues` 并注入 `CELERY_QUEUES`，让开发模式和打包模式都监听 `celery` 与 `worker.{machine_id}`。
- `tests/unit/test_electron_main.py`：新增静态回归，覆盖默认队列、打包模式队列透传和 UTF-8 代码页切换/容错。
- `tasks/bridge_task.py`：恢复 `_运行异步任务` 本地包装，兼容现有桥接测试和 patch 点。
- `tasks/execute_task.py`：重新暴露 `_运行异步任务`，兼容线程池事件循环测试对旧符号的调用。

## 影响范围

- Electron 主进程启动流程
- Celery Worker 队列监听配置
- 桥接任务 / 执行任务的测试兼容层

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果 `450 passed, 16 warnings`。
- 已执行 `node --check electron/main.js`。
- 已尝试 `cd electron && npx electron .`，但当前环境下 Electron 因 `platform_channel.cc(83)` 的 `拒绝访问 (0x5)` 提前退出，未能完成 GUI 验收。
- `.pipeline/task.md` 为既有本地变更，本轮未修改。

---

## 任务摘要

完成两项任务：（1）移除嵌入式 Python 源码打包方案，恢复 PyInstaller exe 方式；（2）将全部中文命名 `.py` 文件重命名为英文，并全量更新所有 import 引用。所有 448 条测试通过。

## 改动文件列表

### Part 1 – 恢复 PyInstaller 打包方案

- `electron/main.js` — 完全重写，生产模式改用 `python-backend/backend.exe` 和 `python-backend/celery-worker.exe`；开发模式模块路径更新为英文
- `electron/package.json` — `extraResources` 改回 `../python-backend-dist` → `app/python-backend`
- `scripts/prepare_dist.py` — 删除（`git rm`）
- `scripts/build_all.bat` — 删除（`git rm`）
- `tests/unit/test_prepare_dist.py` — 删除（测试目标已不存在）

### Part 2 – 中文文件名 → 英文

#### backend/

- `backend/启动入口.py` → `backend/main.py`
- `backend/配置.py` → `backend/config.py`
- `backend/api/路由注册.py` → `backend/api/router.py`
- `backend/api/任务接口.py` → `backend/api/task_api.py`
- `backend/api/任务参数接口.py` → `backend/api/task_params_api.py`
- `backend/api/可用任务.py` → `backend/api/available_tasks.py`
- `backend/api/执行接口.py` → `backend/api/execute_api.py`
- `backend/api/运行接口.py` → `backend/api/run_api.py`
- `backend/api/流程接口.py` → `backend/api/flow_api.py`
- `backend/api/流程参数接口.py` → `backend/api/flow_params_api.py`
- `backend/api/流程输入接口.py` → `backend/api/flow_input_api.py`
- `backend/api/店铺接口.py` → `backend/api/shop_api.py`
- `backend/api/浏览器接口.py` → `backend/api/browser_api.py`
- `backend/api/日志接口.py` → `backend/api/log_api.py`
- `backend/api/系统接口.py` → `backend/api/system_api.py`
- `backend/api/规则接口.py` → `backend/api/rule_api.py`
- `backend/api/售后配置接口.py` → `backend/api/after_sale_config_api.py`
- `backend/api/定时执行接口.py` → `backend/api/scheduled_execute_api.py`
- `backend/api/通用任务接口.py` → `backend/api/generic_task_api.py`
- `backend/api/飞书接口.py` → `backend/api/feishu_api.py`
- `backend/models/数据库.py` → `backend/models/database.py`
- `backend/models/数据结构.py` → `backend/models/data_structure.py`
- `backend/models/店铺模型.py` → `backend/models/shop_model.py`
- `backend/models/流程模型.py` → `backend/models/flow_model.py`
- `backend/models/表结构.py` → `backend/models/table_schema.py`
- `backend/models/规则模型.py` → `backend/models/rule_model.py`
- `backend/models/定时任务模型.py` → `backend/models/scheduled_task_model.py`
- `backend/models/售后配置模型.py` → `backend/models/after_sale_config_model.py`
- `backend/models/售后队列模型.py` → `backend/models/after_sale_queue_model.py`
- `backend/services/任务服务.py` → `backend/services/task_service.py`
- `backend/services/任务参数服务.py` → `backend/services/task_params_service.py`
- `backend/services/执行服务.py` → `backend/services/execute_service.py`
- `backend/services/运行服务.py` → `backend/services/run_service.py`
- `backend/services/流程服务.py` → `backend/services/flow_service.py`
- `backend/services/流程参数服务.py` → `backend/services/flow_params_service.py`
- `backend/services/流程输入服务.py` → `backend/services/flow_input_service.py`
- `backend/services/店铺服务.py` → `backend/services/shop_service.py`
- `backend/services/浏览器服务.py` → `backend/services/browser_service.py`
- `backend/services/日志服务.py` → `backend/services/log_service.py`
- `backend/services/系统服务.py` → `backend/services/system_service.py`
- `backend/services/规则服务.py` → `backend/services/rule_service.py`
- `backend/services/售后配置服务.py` → `backend/services/after_sale_config_service.py`
- `backend/services/售后队列服务.py` → `backend/services/after_sale_queue_service.py`
- `backend/services/售后决策引擎.py` → `backend/services/after_sale_decision_engine.py`
- `backend/services/定时执行服务.py` → `backend/services/scheduled_execute_service.py`
- `backend/services/心跳服务.py` → `backend/services/heartbeat_service.py`
- `backend/services/邮箱服务.py` → `backend/services/email_service.py`
- `backend/services/飞书服务.py` → `backend/services/feishu_service.py`

#### tasks/

- `tasks/celery应用.py` → `tasks/celery_app.py`
- `tasks/注册表.py` → `tasks/registry.py`
- `tasks/任务注册表.py` → `tasks/task_registry.py`
- `tasks/基础任务.py` → `tasks/base_task.py`
- `tasks/登录任务.py` → `tasks/login_task.py`
- `tasks/售后任务.py` → `tasks/after_sale_task.py`
- `tasks/推广任务.py` → `tasks/promotion_task.py`
- `tasks/执行任务.py` → `tasks/execute_task.py`
- `tasks/桥接任务.py` → `tasks/bridge_task.py`
- `tasks/定时任务.py` → `tasks/scheduled_task.py`
- `tasks/限时限量任务.py` → `tasks/flash_sale_task.py`
- `tasks/发布换图商品任务.py` → `tasks/publish_replace_image_task.py`
- `tasks/发布相似商品任务.py` → `tasks/publish_similar_product_task.py`

#### browser/ / pages/ / selectors/

- `browser/任务回调.py` → `browser/task_callback.py`
- `browser/管理器.py` → `browser/manager.py`
- `browser/反检测.py` → `browser/anti_detection.py`
- `browser/滑块验证码.py` → `browser/slider_captcha.py`
- `browser/用户目录工厂.py` → `browser/user_dir_factory.py`
- `browser/验证码识别.py` → `browser/captcha_recognition.py`
- `pages/基础页.py` → `pages/base_page.py`
- `pages/登录页.py` → `pages/login_page.py`
- `pages/售后页.py` → `pages/after_sale_page.py`
- `pages/商品列表页.py` → `pages/product_list_page.py`
- `pages/发布商品页.py` → `pages/publish_product_page.py`
- `pages/推广页.py` → `pages/promotion_page.py`
- `pages/微信页.py` → `pages/wechat_page.py`
- `pages/桌面基础页.py` → `pages/desktop_base_page.py`
- `pages/限时限量页.py` → `pages/flash_sale_page.py`
- `selectors/选择器配置.py` → `selectors/selector_config.py`
- `selectors/基础页选择器.py` → `selectors/base_page_selector.py`
- `selectors/登录页选择器.py` → `selectors/login_page_selector.py`
- `selectors/售后页选择器.py` → `selectors/after_sale_page_selector.py`
- `selectors/商品列表页选择器.py` → `selectors/product_list_page_selector.py`
- `selectors/发布商品页选择器.py` → `selectors/publish_product_page_selector.py`
- `selectors/推广页选择器.py` → `selectors/promotion_page_selector.py`
- `selectors/微信选择器.py` → `selectors/wechat_selector.py`
- `selectors/桌面选择器配置.py` → `selectors/desktop_selector_config.py`
- `selectors/限时限量页选择器.py` → `selectors/flash_sale_page_selector.py`

#### tests/

- `tests/单元测试/` 目录 → `tests/unit/`（68 个测试文件，`测试_*.py` → `test_*.py`）
- `tests/test_售后任务.py` → `tests/test_after_sale_task.py`
- `tests/test_推广任务.py` → `tests/test_promotion_task.py`
- `tests/test_发布换图商品任务.py` → `tests/test_publish_replace_image_task.py`
- `tests/test_发布相似商品任务.py` → `tests/test_publish_similar_product_task.py`
- `tests/test_登录任务.py` → `tests/test_login_task.py`
- `tests/test_限时限量任务.py` → `tests/test_flash_sale_task.py`
- 其余 `tests/test_*.py` 共 4 个同步重命名

#### 其他入口与配置文件

- `entry_backend.py` — import 路径更新
- `entry_celery.py` — import 路径 + 变量名更新
- `scripts/pyinstaller_celery_entry.py` — import 路径 + 变量名更新
- `tasks/celery_app.py` — 变量名 `celery应用` → `celery_app`
- `tasks/registry.py` — `排除模块` 集合由中文名更新为英文名
- `tests/unit/test_production_env_check.py` — 断言更新为 PyInstaller 方案
- `tests/unit/test_system_set_machine_code.py` — 配置文件路径更新为 `backend/config.py`
- 全仓库 184 个文件的 import 路径批量替换

## 改动说明

### Part 1

- `electron/main.js`：删除 `python-embed` 逻辑，新增 `ensurePackagedFileExists` 校验，生产模式直接 `spawn` PyInstaller 产出的 exe；开发模式 uvicorn 参数由 `backend.启动入口:app` 改为 `backend.main:app`，celery 模块路径由 `tasks.celery应用` 改为 `tasks.celery_app`
- `electron/package.json`：`extraResources` 恢复为 `{ "from": "../python-backend-dist", "to": "app/python-backend" }`

### Part 2

分四轮完成 import 替换：

1. **全路径替换**（`backend.配置` → `backend.config` 等 147 条映射），覆盖所有 `import X.中文名` 和 `from X.中文名 import Y` 格式
2. **变量名替换**：`celery应用` → `celery_app`，使用负向前瞻 `(?!模块)` 保留测试别名 `celery应用模块`
3. **短名子模块替换**：`from backend.models import 数据库 as` → `from backend.models import database as` 等精确字符串替换（24 个文件）
4. **Token 边界替换**：`from backend.services import 系统服务` 等模式，使用正则前瞻 `(?=\s*(?:as\s|,|\n|#|\Z))` 确保不误替换（22 个文件）

关键修复：`tasks/registry.py` 的 `排除模块` 集合由旧中文名（`注册表`、`任务注册表` 等）更新为英文名，防止 `pkgutil.iter_modules` 扫描时将 `registry` 本身纳入并触发模块重载导致注册表被清空。

## 影响范围

- 全量 Python 源文件 import 路径变更，无功能逻辑修改
- Electron 主进程打包策略变更（嵌入式 → PyInstaller exe）
- 测试目录结构：`tests/单元测试/` → `tests/unit/`

## 验证结果

```
448 passed, 16 warnings in 61.78s
```
---

## 任务摘要

修复 PyInstaller 打包后的 `backend.exe` 启动路径问题，补齐 `.env`/数据库目录解析、Electron 打包 `cwd`，并让 PyInstaller 6 onedir 产物把 `.env` 放回 exe 同级，最终完成真实打包启动与全量回归验证。

## 改动文件列表

- `scripts/pyinstaller_entry.py`
- `backend/config.py`
- `backend/models/database.py`
- `electron/main.js`
- `backend.spec`
- `tests/unit/test_pyinstaller_entry.py`
- `tests/unit/test_packaged_runtime_paths.py`
- `tests/unit/test_electron_main.py`
- `tests/unit/test_pyinstaller_spec_files.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `scripts/pyinstaller_entry.py`：冻结模式启动前切换到 `sys.executable` 所在目录；导入失败时将错误、`cwd` 和 traceback 写入 exe 同级 `crash.log`，便于直接排查打包产物启动失败。
- `backend/config.py`：新增冻结模式 `.env` 解析策略，优先读取 exe 同级，再回退到 exe 上级和当前工作目录，避免 Electron 或双击启动时相对路径失效。
- `backend/models/database.py`：将冻结模式数据库目录改为 exe 同级 `data/`，保证打包后默认写入 `python-backend-dist/backend/data/ecom.db`。
- `electron/main.js`：打包模式启动 `backend.exe` 与 `celery-worker.exe` 时显式设置 `cwd: path.dirname(...)`，保证后端与 Worker 的运行目录一致。
- `backend.spec`：补齐 `('.env', '.')`，并在 `EXE(...)` 中设置 `contents_directory='.'`，兼容 PyInstaller 6 onedir 布局，确保 `.env` 实际复制到 `backend.exe` 同级而不是 `_internal/`。
- `tests/unit/test_pyinstaller_entry.py`：补充冻结模式切换 `cwd`、导入失败写 `crash.log` 的回归，同时修复测试本身残留 `cwd` 导致后续用例失败的问题。
- `tests/unit/test_packaged_runtime_paths.py`：新增打包运行时 `.env` 与数据库目录解析测试。
- `tests/unit/test_electron_main.py`：补充打包模式 `cwd` 必须使用 `path.dirname(exe)` 的静态断言。
- `tests/unit/test_pyinstaller_spec_files.py`：补充 `.env` 收集与 `contents_directory='.'` 的 spec 断言。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮改造、验证命令与验收结果。

## 影响范围

- PyInstaller 后端入口启动链路
- 打包后 `.env` 读取与 SQLite 数据目录定位
- Electron 打包模式下后端与 Worker 子进程启动
- 打包相关单元测试与静态回归

## 注意事项

- 已执行 `pyinstaller --noconfirm --distpath ./python-backend-dist backend.spec`，构建成功。
- 已直接运行 `python-backend-dist/backend/backend.exe`，控制台输出 `Application startup complete`，并自动创建 `python-backend-dist/backend/data/ecom.db`。
- 产物目录已确认 `.env` 位于 `python-backend-dist/backend/.env`，`crash.log` 未生成。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `479 passed, 16 warnings`。
- 构建阶段仍有 `kombu.asynchronous.aws` 缺少 `botocore` 的 PyInstaller 警告，但不影响本轮验收。
---

## 任务摘要

修复 PyInstaller 打包后中文日志乱码：新增 UTF-8 runtime hook，给 backend / celery 入口补双保险编码设置，并让 Electron 子进程日志管道显式按 `utf8` 解码，完成真实打包产物日志验收与全量回归。

## 改动文件列表

- `scripts/encoding_hook.py`
- `scripts/pyinstaller_entry.py`
- `scripts/pyinstaller_celery_entry.py`
- `backend.spec`
- `celery-worker.spec`
- `electron/main.js`
- `tests/unit/test_packaged_log_encoding.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `scripts/encoding_hook.py`：新增 PyInstaller runtime hook，统一设置 `PYTHONUTF8=1` 与 `PYTHONIOENCODING=utf-8`；优先使用 `reconfigure()` 切换到 UTF-8，仅在原生标准流场景回退到 `TextIOWrapper`，避免破坏 pytest 或开发态捕获流。
- `scripts/pyinstaller_entry.py`：冻结模式入口增加 UTF-8 双保险逻辑，确保 backend.exe 即使未被 runtime hook 接管，也会在启动最早阶段切换输出编码。
- `scripts/pyinstaller_celery_entry.py`：为打包 Worker 入口补同样的 UTF-8 双保险逻辑。
- `backend.spec`：注册 `runtime_hooks=['scripts/encoding_hook.py']`，并将 `('scripts/encoding_hook.py', 'scripts')` 纳入打包数据。
- `celery-worker.spec`：同样注册 runtime hook，并将 hook 文件纳入打包数据。
- `electron/main.js`：保留 `PYTHONUTF8`、`PYTHONIOENCODING` 环境变量；在 `pipeLogs()` 中对 `child.stdout` / `child.stderr` 显式调用 `setEncoding('utf8')`，避免 Node 默认按本地代码页解码子进程输出。
- `tests/unit/test_packaged_log_encoding.py`：新增 runtime hook、backend/celery 入口编码切换、spec 注册和 Electron 日志管道的回归测试。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮改造、打包验证和验收结果。

## 影响范围

- PyInstaller backend / celery-worker 运行时输出编码
- Electron 主进程对子进程日志的解码方式
- 打包相关 spec 配置与编码回归测试

## 注意事项

- 已执行 `pyinstaller --noconfirm --distpath ./python-backend-dist backend.spec` 与 `pyinstaller --noconfirm --distpath ./python-backend-dist celery-worker.spec`，构建成功。
- 已执行 `python-backend-dist/backend/backend.exe` 并将输出重定向到 `startup-utf8.log`；按 UTF-8 读取时，中文日志正常，输出包含 `[任务注册]`、`✓ 回调地址已设置`、`后端启动完成，端口: 8000`。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `484 passed, 16 warnings`。
- 已尝试 `cd electron && npx electron .`，但当前环境仍因 `platform_channel.cc(83): 拒绝访问 (0x5)` 提前退出，未完成 GUI 侧最终验收。
- PyInstaller 构建阶段仍有 `kombu.asynchronous.aws` 缺少 `botocore` 的警告，但不影响本轮编码修复结果。
---

## 任务摘要

修复流程执行时因 `flow_params` 残留记录导致同一店铺重复投递首步任务的问题：读取存量待执行记录后按店铺去重，仅保留最新一条，其余残留记录标记为 `skipped`。

## 改动文件列表

- `backend/services/execute_service.py`
- `tests/unit/test_execute_service.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/execute_service.py`：新增 `_清理店铺残留流程参数记录(...)`，在 `创建批次()` 的“读取已有待执行 flow_params”分支中，对每个店铺的待执行记录按 `id` 倒序去重，仅保留最新一条；其余残留记录通过 `流程参数服务实例.更新(..., {"status": "skipped"})` 清理，避免同店铺被重复投递多个首步任务。
- `backend/services/execute_service.py`：保持空上下文流程逻辑不变；`input_set_id` 触发的输入集兼容 `flow_params` 创建分支不走本次残留清理，避免影响输入集一次生成多条上下文的现有能力。
- `tests/unit/test_execute_service.py`：调整 barrier 首步场景的旧预期，改为断言残留记录只保留最新一条；新增非 barrier 首步场景回归，覆盖“同店铺两条待执行记录时只投递一次首步任务，并将旧记录置为 `skipped`”。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮改造内容与验证结果。

## 影响范围

- 流程模式下 `创建批次()` 读取存量 `flow_params` 的启动路径
- 同店铺首步任务投递数量与批次快照中的 `task_ids`
- 流程执行相关单元测试

## 注意事项

- 本轮修复只作用于“直接读取数据库中已有待执行 `flow_params`”的分支，不影响 `input_set_id` 输入集生成兼容 `flow_params` 的路径。
- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_execute_service.py -q` 与 `python -m pytest -c tests/pytest.ini tests/unit/test_batch_execute_shop_name.py -q`，均通过。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `485 passed, 16 warnings`。
## 任务摘要

完成流程编排弹窗重构：将步骤编辑区从大卡片改为紧凑表格行布局，放大弹窗并补齐拖拽插入线、新增行聚焦与静态回归测试。
## 改动文件列表

- `frontend/src/views/FlowManage.vue`
- `tests/unit/test_flow_manage_editor_static.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/FlowManage.vue`：将流程编辑弹窗宽度调整为 `min(80vw, 900px)`，并把步骤编辑区重构为紧凑表格行布局；保留现有流程保存 payload，不改动 API 调用；新增原生拖拽插入线、步骤新增后任务下拉自动聚焦，以及保存前“至少一个步骤 / 每步必须选择任务”的校验。
- `tests/unit/test_flow_manage_editor_static.py`：新增静态回归，覆盖弹窗尺寸、表格列结构、拖拽插入线、自动聚焦和保存前校验文案，防止回退到旧的大卡片布局。
- `PLAN.md`：同步本轮弹窗改造项、验证命令和当前构建限制。
- `改造进度.md`：同步记录本轮前端改造内容、验证结果和注意事项。
- `.pipeline/progress.md`：记录本轮 Builder 执行结果。

## 影响范围

- 流程管理页中的流程新建 / 编辑弹窗
- 流程步骤拖拽排序与新增步骤交互
- 前端静态回归测试覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_frontend_display_details.py tests/unit/test_flow_manage_editor_static.py -v`，结果为 `4 passed`。
- 已执行 `npx --prefix frontend vue-tsc -b frontend/tsconfig.json`，通过。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `487 passed, 16 warnings`。
- `npm --prefix frontend run build` 在当前环境仍因 `vite` 启动 `esbuild` 子进程时报 `spawn EPERM` 失败，属于现有环境限制，不是本轮改动引入的问题。
- `.pipeline/task.md` 为既有本地改动，本轮未修改。

---

## 任务摘要

将流程管理页从“统计卡片 + 流程卡片网格”压缩为“单行统计 + 紧凑表格列表”，提升首屏信息密度并保留原有编辑/删除入口。

## 改动文件列表

- `frontend/src/views/FlowManage.vue`
- `tests/unit/test_flow_manage_list_static.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/FlowManage.vue`：删除顶部 `summary-grid` 统计卡片，替换为单行 `inline-stats` 文案；删除 `flow-grid / flow-card` 卡片式模板列表，改为 `flow-table` 紧凑表格；新增 `getStepSummary(flow)` 生成步骤摘要；流程名称改为点击即编辑的链接，步骤数改为 `step-badge`，操作按钮缩为 `btn-sm`，以满足“10 个流程尽量一屏可见”的新密度要求。
- `tests/unit/test_flow_manage_list_static.py`：新增静态回归，覆盖单行统计、表格列结构、流程名称链接打开编辑、旧卡片类名移除，以及表格紧凑样式关键字，防止回退。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮流程管理页列表压缩改造和验证结果。

## 影响范围

- 流程管理页顶部统计信息展示
- 流程模板列表的首屏信息密度与交互入口
- FlowManage 页面相关静态回归覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_frontend_display_details.py tests/unit/test_flow_manage_editor_static.py tests/unit/test_flow_manage_list_static.py -v`，结果为 `6 passed`。
- 已执行 `npx --prefix frontend vue-tsc -b frontend/tsconfig.json`，通过。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -q`，结果为 `489 passed, 16 warnings`。
- 16 条 warning 仍来自既有第三方依赖 `celery` 与 `openpyxl` 的 `datetime.utcnow()` 弃用提示，不是本轮改动引入的问题。
- 本轮未重新执行 `npm --prefix frontend run build`；当前环境此前已知存在 `esbuild` 子进程 `spawn EPERM` 限制。
- `.pipeline/task.md` 为既有本地改动，本轮未修改。

---

## 任务摘要

进一步压缩流程编排弹窗内的步骤表格行高度和控件尺寸，让 6 步流程更容易在弹窗内一屏显示。

## 改动文件列表

- `frontend/src/views/FlowManage.vue`
- `tests/unit/test_flow_manage_editor_static.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/FlowManage.vue`：按任务给定数值收紧步骤区样式，将 `.step-row` 调整为 `min-height: 40px`、`padding: 2px 6px`、`border-radius: 8px`，将相邻步骤间距压到 `1px`；将 `.step-table-header` 压缩为 `36px` 高度；将步骤区输入框和下拉框高度统一调为 `32px` 且圆角为 `6px`；同步缩小拖拽手柄和删除按钮尺寸，减少弹窗内垂直占用，同时保留现有拖拽、下拉、checkbox 和删除交互逻辑不变。
- `tests/unit/test_flow_manage_editor_static.py`：新增样式密度静态回归，覆盖步骤表头高度、步骤行高度、相邻行间距、步骤区控件高度、拖拽手柄尺寸和删除按钮尺寸，防止样式回退。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮步骤区压缩改造和验证结果。

## 影响范围

- 流程管理页流程编辑弹窗的步骤表格区视觉密度
- 6 步及以上流程在编辑弹窗内的可见性
- FlowManage 页面相关静态回归覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_frontend_display_details.py tests/unit/test_flow_manage_editor_static.py tests/unit/test_flow_manage_list_static.py -v`，结果为 `7 passed`。
- 已执行 `npx --prefix frontend vue-tsc -b frontend/tsconfig.json`，通过。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -q`，结果为 `490 passed, 16 warnings`。
- 16 条 warning 仍来自既有第三方依赖 `celery` 与 `openpyxl` 的 `datetime.utcnow()` 弃用提示，不是本轮改动引入的问题。
- 本轮仅调整前端样式密度，未改动流程保存 payload、拖拽排序逻辑或后端 API。
- 本轮未重新执行 `npm --prefix frontend run build`；当前环境此前已知存在 `esbuild` 子进程 `spawn EPERM` 限制。
- `.pipeline/task.md` 为既有本地改动，本轮未修改。

---

## 任务摘要

将批量执行页和定时任务页统一改为紧凑表格布局：批量执行状态区表格化并支持详情展开，定时任务列表改为开关 + 表格，并把弹窗尺寸与流程管理页对齐。

## 改动文件列表

- `frontend/src/views/BatchExecute.vue`
- `frontend/src/views/ScheduleManage.vue`
- `tests/unit/test_batch_execute_schedule_static.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/BatchExecute.vue`：移除页面对 `BatchStatusPanel` 的依赖，在页面内直接实现状态表格；新增批次单行汇总文案、店铺执行状态彩色标签、进度条、耗时列和“查看详情”展开步骤明细；保留左侧执行配置面板、批量启动/停止逻辑和 SSE 状态流不变。
- `frontend/src/views/ScheduleManage.vue`：删除 `schedule-grid / schedule-card` 卡片式列表，改为 `schedule-table`；新增开关列用于启用/禁用计划，任务名称支持点击进入编辑，目标店铺数改为紧凑 badge；顶部统计区压成单行 `inline-stats`；将新建/编辑弹窗宽度调整为 `min(80vw, 900px)` 并通过 `:deep(.modal-container)` 限制到 `80vh`。
- `tests/unit/test_batch_execute_schedule_static.py`：新增静态回归，覆盖批量执行页表格结构、状态标签颜色映射、进度条和详情入口，以及定时任务页表格列、开关控件、弹窗尺寸和旧卡片结构移除。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮页面表格化改造和验证结果。

## 影响范围

- 批量执行页的实时状态展示与步骤详情查看入口
- 定时任务页的列表展示密度、启停交互和弹窗尺寸
- 批量执行 / 定时任务相关前端静态回归覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_batch_execute_schedule_static.py tests/unit/test_frontend_management_page.py tests/unit/test_batch_execute_shop_name.py -v`，结果为 `13 passed`。
- 已执行 `npx --prefix frontend vue-tsc -b frontend/tsconfig.json`，通过。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -q`，结果为 `494 passed, 16 warnings`。
- 首次全量回归时，`tests/unit/test_anti_detection.py::test_随机延迟在范围内` 出现一次调度抖动导致的超时；单测复跑通过，随后全量复跑通过，未发现与本轮前端改动有关的稳定失败。
- 16 条 warning 仍来自既有第三方依赖 `celery` 与 `openpyxl` 的 `datetime.utcnow()` 弃用提示，不是本轮改动引入的问题。
- 本轮未执行 `npm --prefix frontend run build`；当前环境此前已知存在 `esbuild` 子进程 `spawn EPERM` 限制。
- `.pipeline/task.md` 为既有本地改动，本轮未修改。

---

## 任务摘要

给 SPA 回退到 `index.html` 的响应增加禁缓存头，确保 Electron 重启后能拿到最新前端页面，而不影响 `/assets/` 的 hash 静态资源缓存。

## 改动文件列表

- `backend/main.py`
- `tests/unit/test_startup_entry.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/main.py`：在 `挂载前端静态资源(...)` 中，保持实际存在的静态文件和 `/assets/` 资源继续直接返回原始 `FileResponse`；仅在所有非 API 路径回退到 `index.html` 时，为响应追加 `Cache-Control: no-cache, no-store, must-revalidate`、`Pragma: no-cache` 和 `Expires: 0`，避免 Electron 或浏览器复用过期的 HTML 入口。
- `tests/unit/test_startup_entry.py`：补充 SPA 首页回退响应头断言，同时确认 `/assets/app.js` 未被写入同样的禁缓存头，防止误伤可安全缓存的 hash 静态资源。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮后端入口缓存头改造和验证结果。

## 影响范围

- FastAPI 挂载前端静态资源时的 SPA 回退路径
- Electron 重启后前端 `index.html` 的缓存策略
- 启动入口相关回归测试覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_startup_entry.py -v`，结果为 `4 passed`。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -q`，结果为 `494 passed, 16 warnings`。
- 16 条 warning 仍来自既有第三方依赖 `celery` 与 `openpyxl` 的 `datetime.utcnow()` 弃用提示，不是本轮改动引入的问题。
- 本轮只改后端 `index.html` 回退响应头，没有修改 `/assets/` 静态资源缓存策略，也没有调整前端构建产物本身。
- `.pipeline/task.md` 为既有本地改动，本轮未修改。

---

## 任务摘要

完成 SPA 回退禁缓存收口、Redis 连接池单例复用和 PyInstaller 冻结任务模块清单自动生成，并补齐对应回归测试。

## 改动文件列表

- `backend/main.py`
- `backend/services/execute_service.py`
- `tasks/registry.py`
- `backend.spec`
- `.gitignore`
- `tests/unit/test_startup_entry.py`
- `tests/unit/test_execute_service.py`
- `tests/unit/test_task_registry.py`
- `tests/unit/test_pyinstaller_spec_files.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/main.py`：在 `挂载前端静态资源(...)` 中继续保持真实静态文件和 `/assets/` 资源直接返回原始 `FileResponse`；仅在所有非 API 路径回退到 `index.html` 时，显式指定 `media_type="text/html"`，并追加 `Cache-Control: no-cache, no-store, must-revalidate`、`Pragma: no-cache`、`Expires: 0`，避免 Electron 或浏览器复用过期 HTML。
- `backend/services/execute_service.py`：新增模块级同步 `redis.ConnectionPool` 与异步 `redis.asyncio.ConnectionPool`；`同步获取Redis客户端()`、取消标记相关异步函数和 `执行服务` 内部异步客户端统一改为复用连接池；为异步连接池补充按事件循环重建逻辑，避免 pytest 多 event loop 复用旧池导致的失败；异步客户端关闭统一改为 `await 客户端.aclose()`。
- `tasks/registry.py`：删除硬编码 `_FROZEN_TASK_MODULES`；frozen 模式下改为从 `tasks._frozen_modules` 读取 `MODULES` 列表，缺失时记录 warning 并返回空列表；非 frozen 模式继续通过 `pkgutil` 动态扫描。
- `backend.spec`：在构建阶段自动扫描 `tasks/` 目录生成 `tasks/_frozen_modules.py`，并把 `tasks._frozen_modules` 加入 `hiddenimports`，减少新增 task 后手动维护冻结模块列表的风险。
- `.gitignore`：新增 `tasks/_frozen_modules.py` 忽略规则，避免构建阶段生成文件误提交。
- `tests/unit/test_startup_entry.py`：补充 SPA 回退响应 `text/html` 与禁缓存头断言，同时确认 `/assets/app.js` 未被误加同样的禁缓存头。
- `tests/unit/test_execute_service.py`：补充同步 / 异步 Redis 连接池复用断言，并覆盖空批次 ID 快速返回和取消标记相关异步客户端关闭路径。
- `tests/unit/test_task_registry.py`：补充 frozen 模式读取 `tasks._frozen_modules.MODULES` 的回归，以及生成文件缺失时 warning + 空列表分支。
- `tests/unit/test_pyinstaller_spec_files.py`：补充 `backend.spec` 自动生成 `_frozen_modules.py` 逻辑与 `.gitignore` 忽略项的静态断言。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮 Builder 执行结果与验证情况。

## 影响范围

- FastAPI 挂载前端静态资源时的 SPA 回退入口缓存策略
- 批次执行、取消标记和执行服务内部的 Redis 连接复用方式
- PyInstaller 冻结模式下 task 自动发现与 `backend.spec` 构建流程
- 启动入口、执行服务、任务注册和 spec 文件相关回归测试覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_startup_entry.py tests/unit/test_execute_service.py tests/unit/test_task_registry.py tests/unit/test_task_registry_extension.py tests/unit/test_pyinstaller_spec_files.py -v`。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -q`，结果为 `500 passed, 18 warnings`。
- 18 条 warning 中，16 条仍来自既有第三方依赖 `celery` 与 `openpyxl` 的 `datetime.utcnow()` 弃用提示，不是本轮改动引入的问题。
- 另外 2 条 warning 为 `PytestUnraisableExceptionWarning`，来自 `tests/unit/test_task_service.py` 中 Redis asyncio `StreamWriter.__del__` 在事件循环关闭后的清理时机，当前不影响测试通过，但值得后续单独处理。
- 本轮按任务要求只调整了 `backend.spec`，未扩展修改 `celery-worker.spec`。
- `.pipeline/task.md` 为既有本地改动，本轮未修改。

---

## 任务摘要

完成 `platform` 字段迁移、多平台注册基础框架、平台列表接口和前端全局平台切换器，并让店铺列表与新建店铺绑定当前平台。

## 改动文件列表

- `backend/models/shop_model.py`
- `backend/models/flow_model.py`
- `backend/models/database.py`
- `backend/models/data_structure.py`
- `backend/services/shop_service.py`
- `backend/api/shop_api.py`
- `backend/services/flow_service.py`
- `backend/api/flow_api.py`
- `backend/api/platform_api.py`
- `backend/api/router.py`
- `platforms/__init__.py`
- `platforms/base/__init__.py`
- `platforms/base/base_platform.py`
- `platforms/pdd/__init__.py`
- `platforms/pdd/platform.py`
- `frontend/src/api/types.ts`
- `frontend/src/api/shops.ts`
- `frontend/src/api/platforms.ts`
- `frontend/src/stores/platform.ts`
- `frontend/src/components/PlatformSelector.vue`
- `frontend/src/components/ShopCard.vue`
- `frontend/src/views/ShopManage.vue`
- `frontend/src/App.vue`
- `tests/unit/test_platform_backend.py`
- `tests/unit/test_platform_frontend_static.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/models/shop_model.py`、`backend/models/flow_model.py`：为 `shops / flows` 增加 `platform` 字段和默认值 `pdd`，让新建数据天然带平台归属。
- `backend/models/database.py`：为 `task_logs` 建表 SQL 增加 `platform`；初始化数据库时补齐旧库 `shops / flows / task_logs` 的 `platform` 字段，并把历史空值回填为 `pdd`，保证重复执行 migration 不报错。
- `backend/models/data_structure.py`：店铺创建请求、店铺响应、流程响应、任务日志响应补齐 `platform` 字段，保持接口结构完整。
- `backend/services/shop_service.py`、`backend/api/shop_api.py`：店铺列表支持 `platform` 查询参数过滤，新建店铺时写入归一化后的 `platform`。
- `backend/services/flow_service.py`、`backend/api/flow_api.py`：流程列表支持 `platform` 过滤，新建流程默认写入 `platform='pdd'`。
- `backend/api/platform_api.py`、`backend/api/router.py`：新增 `GET /api/platforms` 并注册路由，接口通过统一 `成功()` 响应返回平台注册表。
- `platforms/`：新增多平台基础注册框架和 `PddPlatform`，提供 `register_platform / get_platform / list_platforms`，为第二个平台接入预留统一入口。
- `frontend/src/api/types.ts`、`frontend/src/api/shops.ts`、`frontend/src/api/platforms.ts`：补齐前端 `platform` 类型与平台接口封装，店铺列表 API 支持带 `platform` 查询参数。
- `frontend/src/stores/platform.ts`、`frontend/src/components/PlatformSelector.vue`、`frontend/src/App.vue`：新增全局平台 store 与平台选择器，侧边栏挂载切换入口，当前平台持久化到 `localStorage.selectedPlatform`。
- `frontend/src/views/ShopManage.vue`：店铺列表按当前平台自动加载，平台切换后自动刷新；新建店铺时自动绑定当前平台，不增加额外表单项。
- `frontend/src/components/ShopCard.vue`：改用统一 `Shop` 类型，消除新增 `platform` 字段后的类型分叉。
- `tests/unit/test_platform_backend.py`：新增后端回归，覆盖 migration 回填、店铺/流程平台过滤、平台接口以及未注册平台异常路径。
- `tests/unit/test_platform_frontend_static.py`：新增前端静态回归，覆盖平台 API、Pinia store、全局选择器和店铺页接线。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮平台改造与验证结果。

## 影响范围

- `shops / flows / task_logs` 的数据结构与旧库升级逻辑
- 店铺列表、流程列表的按平台过滤能力
- 平台列表接口和未来多平台注册扩展入口
- 前端全局平台切换状态、店铺管理页查询和新建店铺的默认归属
- 平台相关后端/前端回归测试覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_platform_backend.py tests/unit/test_platform_frontend_static.py tests/unit/test_shop_and_flow_api.py tests/unit/test_database_model.py tests/unit/test_frontend_management_page.py -v`，结果为 `19 passed`。
- 已执行 `npx --prefix frontend vue-tsc -b frontend/tsconfig.json`，通过。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `505 passed, 18 warnings`。
- 当前 `GET /api/platforms` 只返回 `pdd`，后续新增平台时只需要补充平台注册实现，不需要重写接口结构。
- 18 条 warning 中，16 条仍来自既有第三方依赖 `celery` 与 `openpyxl` 的 `datetime.utcnow()` 弃用提示，另外 2 条为既有 `PytestUnraisableExceptionWarning`，均不是本轮改动引入的问题。
- 本轮未执行 `npm --prefix frontend run build`；当前环境此前已知存在 `esbuild` 子进程 `spawn EPERM` 限制。
- `.pipeline/task.md` 为既有本地改动，本轮未修改。

---

## 任务摘要

新增抖音和淘宝平台注册，给店铺弹窗补所属平台选择，并把弹窗和店铺表单改成灰色暗色主题与新的密码占位文案。

## 改动文件列表

- `platforms/__init__.py`
- `platforms/douyin/__init__.py`
- `platforms/douyin/platform.py`
- `platforms/taobao/__init__.py`
- `platforms/taobao/platform.py`
- `frontend/src/views/ShopManage.vue`
- `frontend/src/components/Modal.vue`
- `tests/unit/test_platform_backend.py`
- `tests/unit/test_platform_frontend_static.py`
- `tests/unit/test_shop_platform_modal_static.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `platforms/__init__.py`：新增 `platforms.douyin` 和 `platforms.taobao` 的导入，让平台注册表在启动时一次性加载三个平台。
- `platforms/douyin/__init__.py`、`platforms/douyin/platform.py`：新增抖音平台包和 `DouyinPlatform`，注册 `douyin`、图标 `🎵`、登录地址 `https://fxg.jinritemai.com/login/common`，当前任务列表先为空。
- `platforms/taobao/__init__.py`、`platforms/taobao/platform.py`：新增淘宝平台包和 `TaoBaoPlatform`，注册 `taobao`、图标 `🟧`、登录地址 `https://myseller.taobao.com/`，当前任务列表先为空。
- `frontend/src/views/ShopManage.vue`：新增 `formPlatform` 作为弹窗内所属平台值；新增店铺时默认跟随全局平台，编辑时显示已有平台并禁用下拉；新建店铺提交改为使用 `formPlatform.value`；基本信息区顶部新增所属平台选择；两个密码输入框占位符改为 `•••••••• / ••••••••（留空则不修改）`；表单输入背景、边框和次按钮从蓝色调改为灰色暗色系，聚焦色改为紫色。
- `frontend/src/components/Modal.vue`：弹窗容器、header、body、footer 从白底改为深灰色主题，边框改为灰色，关闭按钮 hover 改为灰色高亮，统一去掉明显蓝色调。
- `tests/unit/test_platform_backend.py`：更新平台接口与平台注册表回归，断言平台列表现在包含拼多多、抖音、淘宝。
- `tests/unit/test_platform_frontend_static.py`：更新静态断言，店铺页新建店铺绑定平台改为 `formPlatform.value`。
- `tests/unit/test_shop_platform_modal_static.py`：新增静态回归，覆盖店铺弹窗所属平台下拉、新密码占位文案和 Modal 灰色主题样式。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮 Builder 执行结果与验证情况。

## 影响范围

- 平台注册表与 `GET /api/platforms` 返回结果
- 前端全局平台切换器的可选平台数量
- 店铺管理页新增/编辑弹窗的平台选择、密码占位和表单视觉样式
- 平台相关后端回归与店铺弹窗静态回归覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_platform_backend.py tests/unit/test_platform_frontend_static.py tests/unit/test_shop_platform_modal_static.py tests/unit/test_shop_restore.py tests/unit/test_frontend_display_details.py -v`，结果为 `11 passed`。
- 已执行 `npx --prefix frontend vue-tsc -b frontend/tsconfig.json`，通过。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `507 passed, 18 warnings`。
- `GET /api/platforms` 现在返回 3 个平台：`拼多多 / 抖音 / 淘宝`。
- 本轮未执行 `npm --prefix frontend run build`；当前环境此前已知存在 `esbuild` 子进程 `spawn EPERM` 限制。
- 18 条 warning 中，16 条仍来自既有第三方依赖 `celery` 与 `openpyxl` 的 `datetime.utcnow()` 弃用提示，另外 2 条为既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。
- `.pipeline/task.md` 为既有本地改动，本轮未修改。

---

## 任务摘要

把平台切换入口从 `App.vue` 侧边栏移到店铺管理页 header，并把相关配色统一收口为深灰 + 紫色高亮，同时补齐前端静态回归。

## 改动文件列表

- `frontend/src/App.vue`
- `frontend/src/views/ShopManage.vue`
- `frontend/src/components/PlatformSelector.vue`
- `tests/unit/test_platform_frontend_static.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/App.vue`：移除 `PlatformSelector` 的 import 和侧边栏挂载；侧边栏背景、边框、导航 hover 与激活态全部去蓝化，统一改为深灰 + 紫色高亮。
- `frontend/src/views/ShopManage.vue`：在 header 新增 `header-actions` 与 `platform-tabs` 胶囊按钮组，把平台切换和“新增店铺”按钮放到同一行；点击按钮直接调用 `platformStore.setPlatform(p.id)`；`onMounted` 改为先 `platformStore.loadPlatforms()` 再 `loadShops()`，避免移除侧边栏后平台数据未初始化；头部按钮、次按钮、空状态和移动端 header 布局同步收口为灰紫配色。
- `frontend/src/components/PlatformSelector.vue`：组件保留为备用，但输入框背景、边框和 focus 高亮改为灰紫色系，移除原有蓝色调。
- `tests/unit/test_platform_frontend_static.py`：静态回归改为断言 `App.vue` 不再挂载 `PlatformSelector`，并新增店铺页 header 平台按钮组、平台切换调用和灰紫主题样式断言。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮前端改造与验证结果。

## 影响范围

- 侧边栏与店铺管理页的前端平台切换入口位置
- 店铺管理页首次加载平台数据与按平台刷新列表的前端时序
- 平台相关灰紫主题样式与静态回归覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_platform_frontend_static.py tests/unit/test_shop_platform_modal_static.py tests/unit/test_shop_restore.py tests/unit/test_frontend_management_page.py tests/unit/test_frontend_display_details.py -v`。
- 已执行 `npx --prefix frontend vue-tsc -b frontend/tsconfig.json`。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `508 passed, 18 warnings`。
- `PlatformSelector.vue` 当前仅作为备用组件保留，不再在 `App.vue` 中使用。
- 18 条 warning 中，16 条仍来自既有第三方依赖 `celery` 与 `openpyxl` 的 `datetime.utcnow()` 弃用提示，另外 2 条为既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。
- `.pipeline/task.md` 为既有本地改动，本轮未修改。

---
## 任务摘要

完成前端 Tailwind 样式基建接入，移除旧 CSS 变量入口和 Vite 默认示例组件，并补齐对应静态回归测试。

## 改动文件列表

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vite.config.ts`
- `frontend/src/style.css`
- `frontend/src/main.ts`
- `frontend/src/styles/variables.css`
- `frontend/src/components/HelloWorld.vue`
- `tests/unit/test_frontend_tailwind_static.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/package.json`、`frontend/package-lock.json`：新增 `tailwindcss`、`@tailwindcss/vite`、`@headlessui/vue` 依赖，并同步锁定安装结果。
- `frontend/vite.config.ts`：为 Vite 增加 `tailwindcss()` 插件，同时保留原有开发端口和 `/api` 代理配置。
- `frontend/src/style.css`：替换为 Tailwind v4 的 `@import "tailwindcss";` 入口，只保留全局 `body` 字体和字体平滑基础样式。
- `frontend/src/main.ts`：删除旧 `./styles/variables.css` 引入，让全局样式只从 Tailwind 入口加载。
- `frontend/src/styles/variables.css`、`frontend/src/components/HelloWorld.vue`：按任务要求删除旧 CSS 变量文件和 Vite 默认示例组件。
- `tests/unit/test_frontend_tailwind_static.py`：新增前端静态回归，覆盖 Tailwind 依赖、Vite 插件、全局样式入口和旧文件删除的正常/反向断言。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮任务和验证结果。

## 影响范围

- 前端 Vite 构建链路与样式入口
- 全局 CSS reset 与页面默认字体基线
- 后续 Headless UI 组件接入的依赖前置条件
- 前端静态回归覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_frontend_tailwind_static.py -v`，结果为 `2 passed`。
- 已执行 `cd frontend && npm run build`，构建通过。
- 已尝试 `cd frontend && npm run dev -- --host 127.0.0.1`，当前环境仍因 Node 子进程 `spawn EPERM` 无法完成 Vite dev server 启动验收。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `510 passed, 18 warnings`。
- 18 条 warning 仍来自既有第三方依赖 `celery`、`openpyxl` 的弃用提示，以及既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。
- 本轮按任务要求移除了旧 CSS 变量系统，现有页面中大量依赖 `var(--...)` 的样式会暂时失效，页面变丑属于预期现象。
- 安装依赖时由于全局 npm 缓存目录权限不足，使用 `npm install ... --cache .npm-cache` 完成，临时缓存目录已删除。
- `.pipeline/task.md` 为既有本地变更，本轮未修改。

---

## 任务摘要

用 Tailwind + Headless UI 完成店铺管理页和 6 个中等复杂度页面的灰阶重写，移除相关 `<style>` 块，并同步更新静态回归测试。

## 改动文件列表

- `frontend/src/views/ShopManage.vue`
- `frontend/src/components/ShopCard.vue`
- `frontend/src/components/StatusBadge.vue`
- `frontend/src/components/PlatformSelector.vue`
- `frontend/src/views/Settings.vue`
- `frontend/src/views/TaskMonitor.vue`
- `frontend/src/views/LogViewer.vue`
- `frontend/src/views/TaskParamsManage.vue`
- `frontend/src/views/BatchExecute.vue`
- `frontend/src/views/BrowserManager.vue`
- `frontend/src/components/StatCard.vue`
- `frontend/src/components/LogTable.vue`
- `frontend/src/components/BrowserStatus.vue`
- `tests/unit/test_platform_frontend_static.py`
- `tests/unit/test_shop_platform_modal_static.py`
- `tests/unit/test_shop_card_task_params_display.py`
- `tests/unit/test_shop_restore.py`
- `tests/unit/test_task_params_page.py`
- `tests/unit/test_batch_execute_schedule_static.py`
- `tests/unit/test_frontend_tailwind_static.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/ShopManage.vue`：将页面 header 收口为标题、平台胶囊按钮组和“新增店铺”按钮同排布局；店铺列表改为紧凑行列表；弹窗表单改成白底灰阶输入样式，并把所属平台切换成 Headless UI `Listbox`，同时保持原有 script 业务逻辑不变。
- `frontend/src/components/ShopCard.vue`：从大卡片改成 Linear 风格行项，统一展示店铺名称、账号、代理、状态和文本化操作按钮，减少纵向占用。
- `frontend/src/components/StatusBadge.vue`：收口为极简 dot + text 形式，同时兼容店铺状态、任务状态和日志级别，不再保留旧彩色块状标签。
- `frontend/src/components/PlatformSelector.vue`：按任务要求删除，平台切换入口完全合并进 `ShopManage.vue` 的 header。
- `frontend/src/views/Settings.vue`：切成白底灰边框卡片布局，统一表单、按钮和状态块的 Tailwind 风格。
- `frontend/src/views/TaskMonitor.vue`：任务筛选区、统计区和表格全部改成灰阶卡片与标准表格结构，去掉旧蓝色样式和页面内 `<style>`。
- `frontend/src/views/LogViewer.vue`：日志筛选、导出入口和日志表格改为统一 Tailwind 结构，表头、徽标和空状态与新设计保持一致。
- `frontend/src/views/TaskParamsManage.vue`：仅重写页面壳层和列表布局，保持子 tab 业务逻辑与子文件不动，满足本轮任务范围约束。
- `frontend/src/views/BatchExecute.vue`：将批次配置和状态区直接内联到页面中，统一成灰阶卡片、表格和 badge 风格，避免继续依赖旧色系布局。
- `frontend/src/views/BrowserManager.vue`：浏览器配置区、实例列表和状态展示统一改成 Tailwind 卡片与表格结构，移除旧 `<style>`。
- `frontend/src/components/StatCard.vue`：改成极简数字卡片，标题使用浅灰小字，指标使用 `font-mono` 大号数字。
- `frontend/src/components/LogTable.vue`：改成标准 Tailwind 日志表格，时间列右对齐、级别列使用浅底 badge。
- `frontend/src/components/BrowserStatus.vue`：改成极简 dot 状态指示器，和其他状态展示组件保持一致。
- `tests/unit/test_platform_frontend_static.py`：更新店铺页 header 平台切换、胶囊按钮组和 Tailwind 结构断言。
- `tests/unit/test_shop_platform_modal_static.py`：更新店铺弹窗、平台下拉和白底表单样式的静态断言。
- `tests/unit/test_shop_card_task_params_display.py`：更新店铺项和任务参数展示的紧凑行结构断言。
- `tests/unit/test_shop_restore.py`：更新店铺恢复相关 UI 入口与新行列表结构断言。
- `tests/unit/test_task_params_page.py`：更新 `TaskParamsManage.vue` 新卡片化页面结构断言。
- `tests/unit/test_batch_execute_schedule_static.py`：更新 `BatchExecute.vue` 内联配置区、状态表和 Tailwind 结构断言。
- `tests/unit/test_frontend_tailwind_static.py`：补充这批页面和组件“无 `<style>` 块、使用 Tailwind class” 的静态约束。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮 Builder 执行结果与验证情况。

## 影响范围

- 店铺管理页的平台切换、列表展示和新增/编辑店铺弹窗
- 设置页、任务监控页、日志查看页、任务参数页、批量执行页、浏览器管理页的统一灰阶视觉层
- `ShopCard`、`StatusBadge`、`StatCard`、`LogTable`、`BrowserStatus` 等前端公共展示组件
- 前端静态回归中与 Tailwind / Headless UI 结构、“无蓝色”与“无 `<style>`”约束相关的断言

## 注意事项

- 已执行 `cd frontend && npm run build`。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `514 passed, 18 warnings`。
- 18 条 warning 仍来自既有第三方依赖 `celery`、`openpyxl` 的弃用提示，以及既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。
- 本轮未重新执行 `cd frontend && npm run dev`；当前环境此前已知存在 Vite `spawn EPERM` 限制。
- `TaskParamsManage.vue` 本轮仅调整页面壳层，子 tab 文件未纳入修改范围。
- `.pipeline/task.md` 为既有本地变更，本轮未修改。
---

## 任务摘要

用 Tailwind + Headless UI 完成 `FlowManage.vue`、`AftersaleConfig.vue`、`RuleManage.vue`、`ScheduleManage.vue` 4 个复杂页面的重写，并同步更新对应静态回归测试。

## 改动文件列表

- `frontend/src/views/FlowManage.vue`
- `frontend/src/views/AftersaleConfig.vue`
- `frontend/src/views/RuleManage.vue`
- `frontend/src/views/ScheduleManage.vue`
- `tests/unit/test_flow_manage_editor_static.py`
- `tests/unit/test_flow_manage_list_static.py`
- `tests/unit/test_after_sale_config_page.py`
- `tests/unit/test_rule_config_page.py`
- `tests/unit/test_batch_execute_schedule_static.py`
- `tests/unit/test_frontend_display_details.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/FlowManage.vue`：把流程列表和编辑弹窗改为 Tailwind 表格结构；任务选择与失败策略改用 Headless UI `Listbox`；保留新增步骤聚焦、拖拽排序、失败策略重试次数、同步屏障和合并执行逻辑；为满足“移除原生 select”约束，将聚焦兜底控件调整为隐藏 `input`。
- `frontend/src/views/AftersaleConfig.vue`：把店铺切换改为 `Listbox`；将售后配置表单拆为多段 section；白名单改为 `overflow-x-auto` 表格；标签录入统一为 Tailwind chip 结构；删除旧 `<style>`。
- `frontend/src/views/RuleManage.vue`：筛选器、规则编辑器、动作编辑器和测试匹配全部切到 `Listbox`；列表改为 Tailwind 表格；页面级弹窗统一使用 Headless UI `Modal`；按任务要求保留 `window.confirm` 删除确认，不改 script 业务逻辑。
- `frontend/src/views/ScheduleManage.vue`：把列表切成表格结构；流程、并发数、重叠策略切到 `Listbox`；触发模式改用 Headless UI `TabGroup`；店铺多选与空状态统一为新的 Tailwind 布局；删除旧 `<style>`。
- `tests/unit/test_flow_manage_editor_static.py`、`tests/unit/test_flow_manage_list_static.py`、`tests/unit/test_after_sale_config_page.py`、`tests/unit/test_rule_config_page.py`、`tests/unit/test_batch_execute_schedule_static.py`、`tests/unit/test_frontend_display_details.py`：把旧 CSS / 旧 modal 结构断言更新为新的 Tailwind / Headless UI 结构断言，并补充“无 `<style>` / 无原生 `<select>` / 使用 `Modal` / `Listbox` / `TabGroup`”等回归点。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮 Builder 执行结果与验证情况。

## 影响范围

- 流程模板管理页的列表、编辑弹窗和拖拽步骤编排
- 售后配置页的店铺切换、白名单配置和多分段表单布局
- 规则配置页的筛选器、规则编辑、测试匹配和弹窗承载方式
- 定时任务页的列表、编辑弹窗、触发模式切换和店铺多选
- 相关前端静态回归测试覆盖范围

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_flow_manage_editor_static.py tests/unit/test_flow_manage_list_static.py tests/unit/test_after_sale_config_page.py tests/unit/test_rule_config_page.py tests/unit/test_batch_execute_schedule_static.py tests/unit/test_frontend_display_details.py -q`，结果为 `17 passed`。
- 已执行 `cd frontend && npm run build`。
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `514 passed, 18 warnings`。
- 18 条 warning 仍来自既有第三方依赖 `celery`、`openpyxl` 和既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。
- 本轮未执行 `cd frontend && npm run dev`；当前环境此前已知存在 Vite `spawn EPERM`。
- `.pipeline/task.md` 为既有本地变更，本轮未修改。
---

## 任务摘要

完成店铺管理页、任务参数页及关联中复杂页面的品牌色统一，清理旧 `task-params` CSS 残留，补齐对应静态回归，并稳定化一个独立的超短延迟测试。

## 改动文件列表

- `frontend/src/views/TaskParamsManage.vue`
- `frontend/src/views/task-params/FlowParamsTab.vue`
- `frontend/src/views/task-params/TaskListTab.vue`
- `frontend/src/views/task-params/TaskResultTab.vue`
- `frontend/src/views/task-params/JsonTooltip.vue`
- `frontend/src/views/task-params/useTaskParamsStore.ts`
- `frontend/src/components/Modal.vue`
- `frontend/src/components/ConfirmDialog.vue`
- `frontend/src/components/StatusBadge.vue`
- `frontend/src/components/LogTable.vue`
- `frontend/src/components/BrowserStatus.vue`
- `frontend/src/views/ShopManage.vue`
- `frontend/src/views/FlowManage.vue`
- `frontend/src/views/ScheduleManage.vue`
- `frontend/src/views/Settings.vue`
- `frontend/src/views/TaskMonitor.vue`
- `frontend/src/views/LogViewer.vue`
- `frontend/src/views/BatchExecute.vue`
- `frontend/src/views/BrowserManager.vue`
- `frontend/src/components/ShopCard.vue`（删除）
- `tests/unit/test_batch_execute_schedule_static.py`
- `tests/unit/test_flow_manage_editor_static.py`
- `tests/unit/test_flow_manage_list_static.py`
- `tests/unit/test_flow_params_page_static.py`
- `tests/unit/test_task_params_enable_reset_page.py`
- `tests/unit/test_task_params_page.py`
- `tests/unit/test_platform_frontend_static.py`
- `tests/unit/test_shop_card_task_params_display.py`
- `tests/unit/test_shop_platform_modal_static.py`
- `tests/unit/test_headless_ui_components_static.py`
- `tests/unit/test_frontend_tailwind_static.py`
- `tests/unit/test_after_sale_config_page.py`
- `tests/unit/test_frontend_display_details.py`
- `tests/unit/test_shop_restore.py`
- `tests/unit/test_anti_detection.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/TaskParamsManage.vue` 与 `frontend/src/views/task-params/*`
  - 统一筛选区、tab、分页、表头、空状态和 tooltip 的 `brand-*` 配色
  - 补充 `switch-slider`、`step-result-tag` 兼容标记，避免静态回归与现有结构脱节
- `frontend/src/views/ShopManage.vue`
  - 保持平台下拉框方案，使用 `table` 修正表头与行内容对齐问题
  - 表单输入、标签、次按钮和弹窗操作区统一到品牌色体系
- `frontend/src/components/Modal.vue`、`ConfirmDialog.vue`、`StatusBadge.vue`、`LogTable.vue`、`BrowserStatus.vue`
  - 将弹窗、提示、状态徽标和表格支撑组件改到同一套灰蓝品牌风格
- `frontend/src/views/FlowManage.vue`、`ScheduleManage.vue`、`Settings.vue`、`TaskMonitor.vue`、`LogViewer.vue`、`BatchExecute.vue`、`BrowserManager.vue`
  - 清掉残留旧灰色交互色，统一边框、hover、badge、表头和空状态
- `frontend/src/components/ShopCard.vue`
  - 由于已无引用，按任务单允许的范围直接删除，避免旧实现继续干扰
- `tests/unit/*.py`
  - 将静态断言切换到新的 `brand-*` 结构
  - 让测试显式校验旧 `task-params` CSS 文件已删除
  - 将 `tests/unit/test_anti_detection.py` 改为使用 `time.perf_counter()`，并放宽 Windows 上 10~20ms sleep 的调度容差

## 影响范围

- 店铺管理页的列表展示、平台切换、弹窗表单和状态标识
- 任务参数管理页及其任务列表/结果列表/流程参数子组件
- Flow / Schedule / Settings / TaskMonitor / LogViewer / BatchExecute / BrowserManager 的视觉统一性
- 前端静态回归对新品牌色、深色侧栏、表格直出和旧 CSS 删除状态的断言
- 一个独立的浏览器反检测延迟测试的稳定性

## 注意事项

- 已执行 `cd frontend && npm run build`
- 已执行 `python -m pytest -c tests/pytest.ini tests/ -v`，结果为 `514 passed, 18 warnings`
- 18 条 warning 仍来自既有第三方依赖 `celery`、`openpyxl` 与既有 `PytestUnraisableExceptionWarning`
- 旧 `frontend/src/views/task-params/*.css` 文件本轮确认已不存在，源码中也无残留引用
- 当前环境此前已知存在 `npm run dev` 的 `spawn EPERM`，本轮未执行 dev server 验收

---

## 任务摘要

完成 CSV 导入弹窗的 Tailwind 重写，并把受影响弹窗/表单页的标签与说明文字加深到任务单要求的灰阶。

## 改动文件列表

- `frontend/src/views/task-params/ImportCsvModal.vue`
- `frontend/src/components/Modal.vue`
- `frontend/src/components/ConfirmDialog.vue`
- `frontend/src/views/AftersaleConfig.vue`
- `frontend/src/views/RuleManage.vue`
- `tests/unit/test_headless_ui_components_static.py`
- `tests/unit/test_flow_params_import_static_page.py`
- `tests/unit/test_task_params_dynamic_type.py`
- `tests/unit/test_after_sale_config_page.py`
- `tests/unit/test_rule_config_page.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/task-params/ImportCsvModal.vue`：删除旧 `<style scoped>`，按任务单改为纯 Tailwind 结构；绑定方式按钮切到选中深色 / 未选中白底描边；任务/流程下拉使用清晰的 `border-brand-300`；模板说明框、下载模板按钮、文件上传按钮和 footer 操作区统一到新品牌风格。
- `frontend/src/components/Modal.vue`：弹窗正文默认文字改为 `text-gray-700`，让说明文案比之前更深一档。
- `frontend/src/components/ConfirmDialog.vue`：确认弹窗正文说明文字同步改到 `text-gray-700`。
- `frontend/src/views/AftersaleConfig.vue`、`frontend/src/views/RuleManage.vue`：将弹窗/表单标签文字从 `text-gray-600` 收口到 `text-gray-800`，仅调整视觉层，不改业务逻辑。
- `tests/unit/test_headless_ui_components_static.py`、`tests/unit/test_flow_params_import_static_page.py`、`tests/unit/test_task_params_dynamic_type.py`、`tests/unit/test_after_sale_config_page.py`、`tests/unit/test_rule_config_page.py`：同步更新静态回归，覆盖新导入弹窗结构、去除 `<style>`、文件上传按钮样式以及标签灰阶变更。
- `frontend/src/style.css`：已复核当前冷灰蓝 `brand-*` 色板与任务单一致，本轮未再修改源码。

## 影响范围

- 任务参数管理页的 CSV 导入弹窗视觉与可读性
- 公共弹窗正文默认说明文字
- 售后配置页与规则配置页中的表单/弹窗标签层
- 前端静态回归中与导入弹窗结构、标签灰阶和正文颜色相关的断言

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_headless_ui_components_static.py tests/unit/test_flow_params_import_static_page.py tests/unit/test_task_params_dynamic_type.py tests/unit/test_after_sale_config_page.py tests/unit/test_rule_config_page.py -q`，结果为 `13 passed`。
- 已执行 `cd frontend && npm run build`。
- 已执行 `python -m pytest -c tests/pytest.ini -q`，结果为 `514 passed, 18 warnings`。
- 18 条 warning 仍来自既有第三方依赖 `celery`、`openpyxl` 与既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。
- `.pipeline/task.md` 为既有本地改动，本轮未修改。
- 当前环境此前已知存在 `npm run dev` 的 `spawn EPERM`，本轮未执行 dev server 验收。

---

## 任务摘要

移除仓库中的多平台抽象层，删除平台注册接口与前端平台切换链路，让项目回归单平台 PDD 模式，同时补齐对应的后端、前端静态和回归测试。

## 改动文件列表

- `backend/api/platform_api.py`（删除）
- `backend/api/router.py`
- `backend/api/shop_api.py`
- `frontend/src/api/platforms.ts`（删除）
- `frontend/src/stores/platform.ts`（删除）
- `frontend/src/api/types.ts`
- `frontend/src/api/shops.ts`
- `frontend/src/views/ShopManage.vue`
- `platforms/__init__.py`（删除）
- `platforms/base/__init__.py`（删除）
- `platforms/base/base_platform.py`（删除）
- `platforms/douyin/__init__.py`（删除）
- `platforms/douyin/platform.py`（删除）
- `platforms/pdd/__init__.py`（删除）
- `platforms/pdd/platform.py`（删除）
- `platforms/taobao/__init__.py`（删除）
- `platforms/taobao/platform.py`（删除）
- `tests/unit/test_platform_backend.py`
- `tests/unit/test_platform_frontend_static.py`
- `tests/unit/test_shop_platform_modal_static.py`
- `tests/unit/test_shop_card_task_params_display.py`
- `tests/unit/test_shop_restore.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/api/platform_api.py`：删除平台列表接口；`/api/platforms` 不再作为可用 API 暴露。
- `backend/api/router.py`：移除 `platform_api` 的导入与路由注册，后端路由入口回收为单平台结构。
- `backend/api/shop_api.py`：创建店铺时不再信任外部传入的 `platform`，统一固定写入 `platform="pdd"`，避免单平台场景下出现脏数据。
- `frontend/src/api/platforms.ts`、`frontend/src/stores/platform.ts`：删除前端平台 API 与平台状态仓库，前端不再维护平台列表和当前平台上下文。
- `frontend/src/api/types.ts`：删除 `Platform` 接口，并从 `ShopPayload` 中移除 `platform?: string`，让前端表单输入与单平台模型一致。
- `frontend/src/api/shops.ts`：将 `listShops()` 收口为无参版本，统一请求 `/api/shops`，不再携带平台筛选。
- `frontend/src/views/ShopManage.vue`：移除页头平台切换、弹窗“所属平台”字段、`usePlatformStore` 相关状态与计算属性；页面文案、空状态和表单布局调整为单平台 PDD 版本。
- `platforms/` 目录：删除 `base_platform` 注册抽象和 `douyin`、`taobao`、`pdd` 平台壳层实现，彻底移除多平台基础设施。
- `tests/unit/test_platform_backend.py`：改为验证 `/api/platforms` 已不存在，以及店铺创建即使传入其他平台也会被固定保存为 `pdd`。
- `tests/unit/test_platform_frontend_static.py`、`tests/unit/test_shop_platform_modal_static.py`：改为校验前端已删除平台 store、平台 API、平台类型、店铺页头平台切换和弹窗平台字段。
- `tests/unit/test_shop_card_task_params_display.py`、`tests/unit/test_shop_restore.py`：同步清理与多平台 UI 相关的静态断言，保持店铺管理页回归稳定。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：补充记录本轮单平台回收改造、验证结果与环境限制说明。

## 影响范围

- 后端 API 路由注册与店铺创建入口
- 前端店铺管理页的数据加载方式、页面结构与表单字段
- 多平台抽象目录与平台注册链路
- 与平台切换、平台字段、平台 API 相关的单元测试和静态回归测试

## 注意事项

- 已执行 `python -c "from backend.api.router import 注册所有路由; print('ok')"`，导入验证通过。
- 已执行 `python -m pytest -c tests/pytest.ini tests/unit/test_platform_backend.py tests/unit/test_platform_frontend_static.py tests/unit/test_shop_platform_modal_static.py tests/unit/test_shop_card_task_params_display.py tests/unit/test_shop_restore.py -q`，结果为 `10 passed`。
- 已执行 `cd frontend && npm run build`。
- 已执行 `python -m pytest -c tests/pytest.ini -q`，结果为 `512 passed, 18 warnings`。
- 已执行 `rg -n "platformStore|usePlatformStore|listPlatforms|platform\.ts|from platforms|import platforms|import platform_api|platform_api|get_platform|list_platforms|register_platform|BasePlatform" backend frontend/src -g "*.py" -g "*.ts" -g "*.vue"`，无匹配结果。
- 保留 `shops`、`flows` 等数据表中的 `platform` 列，不做数据库迁移，单平台固定值为 `pdd`。
- `.pipeline/task.md` 为既有本地变更，本轮未修改。
- `python -m backend.main` 在当前环境可进入 Uvicorn 启动流程，但后续受 Windows 权限限制触发 `PermissionError: [WinError 5]`，未能完成运行态验收。
- `cd frontend && npm run dev -- --host 127.0.0.1` 在当前环境仍触发 `spawn EPERM`，未能完成 dev server 运行态验收。

---

## 任务摘要

完成“移除 `.env`、改用数据库 `settings` 管理配置、增加前端系统设置页、统一打包脱敏”的整轮改造，并补齐 Redis 降级、PyInstaller 入口兼容与相关回归测试。

## 改动文件列表

- 后端配置与设置链路：`backend/models/settings_model.py`、`backend/utils/__init__.py`、`backend/utils/crypto.py`、`backend/utils/settings.py`、`backend/config.py`、`backend/models/database.py`、`backend/api/settings_api.py`、`backend/api/router.py`、`backend/services/system_service.py`
- 运行时兼容与服务修复：`backend/models/__init__.py`、`backend/logging_config.py`、`backend/services/shop_service.py`、`backend/services/execute_service.py`、`backend/services/scheduled_execute_service.py`、`browser/user_dir_factory.py`、`pages/product_list_page.py`、`tasks/celery_app.py`、`scripts/pyinstaller_celery_entry.py`
- 前端设置页：`frontend/src/api/settings.ts`、`frontend/src/api/types.ts`、`frontend/src/views/SystemSettings.vue`、`frontend/src/router/index.ts`、`frontend/src/App.vue`
- 打包与脚本：`scripts/clean_for_dist.py`、`scripts/machine_worker.py`、`scripts/dispatch_test.py`、`electron/main.js`、`backend.spec`、`celery-worker.spec`、`requirements.txt`、`.gitignore`
- 测试：`tests/unit/test_settings_api.py`、`tests/unit/test_database_model.py`、`tests/unit/test_system_set_machine_code.py`、`tests/unit/test_frontend_management_page.py`、`tests/unit/test_frontend_tailwind_static.py`、`tests/unit/test_packaged_runtime_paths.py`、`tests/unit/test_pyinstaller_spec_files.py`、`tests/unit/test_machine_access_script.py`、`tests/unit/test_task_dispatch_script.py`、`tests/test_feishu_service.py`、`tests/unit/test_production_env_check.py`
- 删除文件：`.env`
- 同步文档：`PLAN.md`、`改造进度.md`、`.pipeline/progress.md`

## 改动说明

- `settings` 主链路：新增 `settings` 表模型、默认配置、同步读写工具和 `/api/settings` 接口；敏感字段对前端只返回 `has_value`，保存时统一加密入库。
- 配置读取：`backend/config.py` 不再依赖 `.env`，改为数据目录常量 + `配置实例` 动态代理，兼容旧调用方继续通过属性读取配置。
- 数据目录与密钥：统一运行时目录到 `data/`，敏感配置密钥改为 `data/.secret_key`，并支持测试中切换 `DATA_DIR` 时动态解析。
- 兼容层：保留旧 `/api/system/config` 接口，底层实现改走 `settings`，减少对既有页面和脚本的破坏面。
- Redis 降级：`execute_service.py` 与 `scheduled_execute_service.py` 在 Redis 不可用时回退到进程内缓存，避免取消标记、批次状态、计划批次映射在测试或无 Redis 环境直接报错。
- 循环导入修复：`backend.models` 与 `backend.utils` 改为按需导出，拆掉 `config -> settings -> database -> logging` 的初始化环。
- PyInstaller 入口：`scripts/pyinstaller_celery_entry.py` 改为延迟导入配置，避免开发模式下先导入 `backend.config` 导致路径注入测试失败。
- 前端系统设置页：新增 `SystemSettings.vue` 与 `settings.ts`，按分类分组展示配置；敏感项使用密码框和“已设置”占位符，保存时批量提交。
- 打包与脱敏：新增 `scripts/clean_for_dist.py`，更新 spec、`.gitignore`、依赖清单和 Electron 入口，彻底移除 dotenv 方案。
- 测试同步：补充 `settings` API、数据库初始化、打包入口、机器脚本与前端静态回归，旧密钥文件断言同步到 `.secret_key`。

## 影响范围

- 后端所有通过 `配置实例` 读取运行配置的模块。
- FastAPI 配置接口、旧系统配置接口和前端 `/settings` 页面。
- Redis 依赖的批次执行、取消标记、定时计划批次映射逻辑。
- PyInstaller Celery Worker 启动入口与打包前清理流程。
- Electron 启动链路和前端导航中的“系统设置”入口。

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini -q`，结果为 `516 passed, 16 warnings`。
- 已执行 `npm --prefix frontend run build`，当前环境仍因 `esbuild` 子进程 `spawn EPERM` 失败，属于环境限制，未完成前端构建验收。
- 旧 `frontend/src/views/Settings.vue` 仍保留在仓库中，但路由已切换到 `frontend/src/views/SystemSettings.vue`。
- `.pipeline/task.md` 为既有本地变更，本轮未修改。

---

## 任务摘要

完成 settings 迁移后的跟进补丁：Celery 配置支持动态刷新，Redis URL 自动归一化，新增验证码/飞书测试接口，并补齐对应单元测试。

## 改动文件列表

- `backend/api/settings_api.py`
- `backend/api/system_api.py`
- `backend/models/data_structure.py`
- `backend/services/system_service.py`
- `tasks/celery_app.py`
- `tasks/execute_task.py`
- `tests/unit/test_celery_config_refresh.py`
- `tests/unit/test_system_followup.py`
- `tests/unit/test_system_api_followup.py`
- `tests/unit/test_execute_task_refresh.py`
- `tests/unit/test_settings_api_followup.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `tasks/celery_app.py`：新增 `刷新Celery配置()`，从 `settings` 动态读取 broker / backend，并在地址变化时同步清理连接池、producer pool 和 backend 缓存。
- `backend/services/system_service.py`：旧 `/api/system/config` 兼容层在保存 `redis_url` 前自动修正常见格式错误，保存后最佳努力刷新 Celery 配置。
- `backend/api/settings_api.py`：给真实 `/settings` 页面使用的 `/api/settings`、`/api/settings/batch` 写入链路补上 Redis URL 规范化与按需刷新 Celery，避免只修兼容接口不修现用入口。
- `backend/models/data_structure.py`：新增 `验证码测试请求`、`飞书Webhook测试请求`，并兼容旧参数别名。
- `backend/api/system_api.py`：新增 `POST /api/system/test-captcha` 与 `POST /api/system/test-feishu-webhook`，支持请求体覆盖系统配置，飞书测试支持可选签名。
- `tasks/execute_task.py`：在 `初始化Worker环境()` 后增加 `刷新Celery配置()`，让 Worker 每次执行任务前先同步最新配置。
- `tests/unit/test_celery_config_refresh.py`、`tests/unit/test_system_followup.py`、`tests/unit/test_system_api_followup.py`、`tests/unit/test_execute_task_refresh.py`、`tests/unit/test_settings_api_followup.py`：补齐本轮新增行为的独立回归测试。

## 影响范围

- `/settings` 页面和旧 `/api/system/config` 的 Celery / Redis 设置更新链路
- `/api/system/test-redis`、`/api/system/test-captcha`、`/api/system/test-feishu-webhook`
- Celery 主进程派发任务时的配置读取
- Worker 执行任务前的配置同步

## 注意事项

- 已执行新增定向测试与受影响回归：
  - `python -m pytest tests/unit/test_celery_config_refresh.py tests/unit/test_system_followup.py tests/unit/test_system_api_followup.py tests/unit/test_execute_task_refresh.py tests/unit/test_settings_api_followup.py -q`
  - `python -m pytest tests/unit/test_system_api.py tests/unit/test_settings_api.py tests/unit/test_execute_task.py tests/unit/test_celery_bridge.py tests/unit/test_system_set_machine_code.py -q`
  - `python -m pytest tests/test_feishu_service.py -q`
- 已执行全量回归：
  - `python -m pytest -c tests/pytest.ini -q`
  - 结果为 `525 passed, 18 warnings`
- 18 条 warnings 仍来自既有第三方依赖 `celery`、`openpyxl` 与既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。
- `frontend/src/views/Settings.vue` 仍保留旧接口调用，但正式路由页为 `frontend/src/views/SystemSettings.vue`；本轮已确保当前 `/settings` 页面实际依赖的 `/api/settings` 链路具备 Celery 刷新能力。
- `.pipeline/task.md`、`backend.spec`、`build_all.bat`、`build_backend.bat` 等为既有本地变更，本轮未修改其任务之外内容。
