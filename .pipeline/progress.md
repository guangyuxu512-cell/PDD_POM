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
