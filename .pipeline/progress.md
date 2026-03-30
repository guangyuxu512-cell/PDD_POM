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
