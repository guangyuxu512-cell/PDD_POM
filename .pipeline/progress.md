## 任务摘要

完成执行链路第一轮拆分，抽出任务参数运行时、执行上下文、流程续跑、执行状态存储和流程预检子模块，移除 `task_api` 运行时 monkey patch，并清理批量执行页遗留双实现。

## 改动文件列表

- `backend/services/import_parser_service.py`
- `backend/services/task_params_service.py`
- `backend/services/flow_input_service.py`
- `backend/services/task_service.py`
- `backend/services/task_param_runtime_service.py`
- `backend/services/task_execution_context_service.py`
- `backend/services/task_flow_service.py`
- `backend/services/execute_service.py`
- `backend/services/execute_state_store.py`
- `backend/services/execute_flow_precheck_service.py`
- `backend/api/task_api.py`
- `tasks/bridge_task.py`
- `tasks/scheduled_task.py`
- `frontend/src/views/batch-execute/ExecuteConfigPanel.vue`（删除）
- `frontend/src/views/batch-execute/BatchStatusPanel.vue`（删除）
- `frontend/src/views/batch-execute/BatchStatusPanel.css`（删除）
- `tests/unit/test_batch_execute_schedule_static.py`
- `tests/unit/test_batch_execute_shop_name.py`
- `tests/unit/test_celery_bridge.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/import_parser_service.py`：抽出 CSV/XLSX 解析、店铺标识解析、字段规范化和值转换，作为任务参数与流程输入的共享导入解析层。
- `backend/services/task_params_service.py`、`backend/services/flow_input_service.py`：改为复用共享导入解析服务，去掉跨 service 访问私有解析方法的耦合。
- `backend/services/task_service.py`：改为执行协调层，把任务参数运行时、浏览器上下文准备和流程续跑分别下沉到 `task_param_runtime_service.py`、`task_execution_context_service.py`、`task_flow_service.py`，同时保留原方法名兼容现有调用方与测试 patch。
- `backend/services/execute_service.py`：把执行状态读写下沉到 `execute_state_store.py`，把流程预检与元数据校验下沉到 `execute_flow_precheck_service.py`，主文件继续负责调度协调并保留已有导出。
- `backend/api/task_api.py`：去掉运行时 monkey patch，内部执行链路改成显式传递 `flow_context`。
- `tasks/bridge_task.py`、`tasks/scheduled_task.py`：统一改用 `tasks/async_utils.py` 进行异步桥接，避免重复实现。
- `frontend/src/views/batch-execute/*`：删除未接回主页面的遗留配置/状态面板双实现，避免后续继续分叉。
- `tests/unit/test_batch_execute_schedule_static.py`、`tests/unit/test_batch_execute_shop_name.py`、`tests/unit/test_celery_bridge.py`：同步更新静态与桥接回归断言，覆盖本轮清理后的结构。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮 Builder 改造与验证结果。

## 影响范围

- 任务参数导入与流程输入导入链路
- 任务执行上下文准备、流程续跑与浏览器复用链路
- 执行状态存储、流程预检与内部执行适配链路
- Celery 异步桥接实现
- 批量执行页遗留组件清理及其相关静态回归测试

## 注意事项

- 为控制回归面，`task_service.py` 与 `execute_service.py` 仍保留旧包装方法和既有 patch 点，本轮重点是拆分职责，不是一次性改掉全部外部依赖。
- `backend/services/execute_service.py` 仍保留批次调度与停止取消控制，后续还可以继续拆分。
- `frontend/src/views/BatchExecute.vue` 仍是偏大的容器页，本轮只删除未接入主链路的遗留双实现，没有继续拆页面。
- 本轮代码改造已完成验证：
  - `python -m pytest tests/unit/test_task_service.py tests/unit/test_task_service_browser_reuse.py tests/unit/test_execute_service.py tests/unit/test_task_api_internal_exec.py tests/unit/test_celery_bridge.py tests/unit/test_flow_input_service.py tests/unit/test_task_params_service.py tests/unit/test_batch_execute_schedule_static.py tests/unit/test_batch_execute_shop_name.py -q`
  - 结果：`64 passed, 3 warnings`
  - `python -m pytest -c tests/pytest.ini -q`
  - 结果：`525 passed, 18 warnings`
- warnings 仍来自既有第三方依赖 `celery`、`openpyxl` 与既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。

---

## 任务摘要

完成批量执行页的输入集透传修复，新增前端输入集选择与 `input_set_id` 请求字段，使导入到 `flow_input_sets / flow_input_rows` 的参数可以进入流程执行链路。

## 改动文件列表

- `frontend/src/api/flowInputs.ts`
- `frontend/src/api/types.ts`
- `frontend/src/views/BatchExecute.vue`
- `tests/unit/test_batch_execute_schedule_static.py`
- `tests/unit/test_frontend_management_page.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/api/flowInputs.ts`：新增 `listFlowInputSets()`，封装流程输入集列表接口，供批量执行页读取当前流程下的输入集。
- `frontend/src/api/types.ts`：新增 `FlowInputSet` 类型，并为 `BatchRequest` 增加 `input_set_id`，补齐前端请求模型。
- `frontend/src/views/BatchExecute.vue`：在流程模式下增加输入集加载、默认选择与提示文案；点击“开始执行”时把 `input_set_id` 一并发送给 `/api/execute/batch`；未选输入集时保持沿用旧 `flow_params` 行为。
- `tests/unit/test_batch_execute_schedule_static.py`：增加批量执行页输入集选择相关静态断言，防止后续回归时再丢掉输入集透传。
- `tests/unit/test_frontend_management_page.py`：增加 `frontend/src/api/flowInputs.ts` 导出校验，确保输入集 API wrapper 持续存在。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮 Builder 改动与验证结果。

## 影响范围

- 前端批量执行页的流程启动参数组装
- 流程输入集 `flow_input_sets / flow_input_rows` 的前端使用链路
- 与批量执行页结构和前端 API wrapper 相关的静态回归测试

## 注意事项

- 当前仓库同时保留旧 `flow_params` 与新 `flow_input_sets / flow_input_rows` 两套流程参数来源；本次仅补齐批量执行页对输入集链路的前端透传，不改动旧链路行为。
- 已执行 `python -m pytest tests/unit/test_batch_execute_schedule_static.py tests/unit/test_frontend_management_page.py tests/unit/test_execute_api.py -q`，结果为 `9 passed`。
- 已执行 `cd frontend && npm run build`，构建通过。
- 已执行 `python -m pytest -c tests/pytest.ini -q`，结果为 `525 passed, 18 warnings`。
- 18 条 warnings 仍来自既有第三方依赖 `celery`、`openpyxl` 与既有 `PytestUnraisableExceptionWarning`，不是本轮改动引入的问题。

## 浠诲姟鎽樿

瀹屾垚鐧诲綍鎬佸け鏁堟娴嬩笌鍛婅銆佺粨鏋勫寲鏃ュ織浣撶郴銆佷緷璧栫増鏈攣瀹氥€佸仴搴锋鏌ヤ笌鐩戞帶绔偣銆佹祻瑙堝櫒宕╂簝鑷姩鎭㈠浜旈」鏀归€狅紝骞惰ˉ榻愬搴斿洖褰掓祴璇曘€?
## 鏀瑰姩鏂囦欢鍒楄〃

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
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `backend/logging_config.py`锛氭柊澧炵粺涓€鏃ュ織鍒濆鍖栵紝浼樺厛浣跨敤 `loguru`锛屼緷璧栫己澶辨椂鍥為€€鏍囧噯搴擄紱鏀寔 `trace_id`銆佹帶鍒跺彴杈撳嚭銆乣data/logs/` 鏂囦欢杞浆涓庨敊璇棩蹇楁媶鍒嗐€?- `backend/services/metrics_service.py`锛氭柊澧炶繘绋嬪唴鎸囨爣缁熻锛岃褰曚换鍔℃€婚噺銆佹垚鍔?澶辫触鏁伴噺銆佽繍琛屼腑鏁伴噺銆佸钩鍧囦换鍔¤€楁椂銆佽姹傝€楁椂涓庤繍琛屾椂闀裤€?- `browser/session_monitor.py`锛氭柊澧炵櫥褰曟€佺洃鎺у櫒锛屾娴嬬櫥褰曢〉 URL銆佸け鏁堟枃妗堝拰鍏抽敭 Cookie锛涘け鏁堟椂鍐欏叆 `operation_logs`锛屽彂閫侀涔﹀憡璀︼紝骞跺悜 Redis `session:expired` 鍙戝竷浜嬩欢銆?- `browser/recovery.py`锛氭柊澧炴祻瑙堝櫒鎭㈠鍣紝灏佽鍐峰嵈銆侀噸璇曚笂闄愩€佹仮澶嶆垚鍔?澶辫触鏃ュ織涓庤嚜鍔ㄩ噸寤洪€昏緫銆?- `browser/manager.py`锛氭柊澧炵櫥褰曢〉鑷姩鏍囪銆佸簵閾哄厓鏁版嵁缂撳瓨銆乣瀹夊叏鑾峰彇椤甸潰(...)`銆佹祻瑙堝櫒宕╂簝鏃ュ織鍜?`browser:crashed` Redis 浜嬩欢銆?- `pages/base_page.py`锛氭柊澧?`妫€鏌ュ苟澶勭悊鐧诲綍鎬?...)`锛屽湪鍏抽敭浜や簰鍓嶈嚜鍔ㄦ娴嬬櫥褰曟€侊紱缁熶竴鎹曡幏娴忚鍣ㄥ叧闂被寮傚父骞舵姏鍑烘仮澶嶆爣璇嗛敊璇€?- `tasks/execute_task.py`锛氫负 Worker 鎵ц閾捐矾缁戝畾 `trace_id`锛屾帴鍏ユ寚鏍囩粺璁★紝瀵规祻瑙堝櫒鍏抽棴绫诲け璐ュ鍔犱竴娆℃仮澶嶆€ч噸璇曘€?- `backend/main.py`銆乣backend/api/system_api.py`銆乣backend/services/system_service.py`锛氳ˉ榻愭牴 `/health`銆佺粨鏋勫寲 `/api/system/health`銆乣/api/system/metrics`銆佽姹傝€楁椂缁熻浠ュ強 Redis/SQLite/娴忚鍣ㄦ睜/Celery Worker 鍋ュ悍妫€鏌ャ€?- `requirements.txt`銆乣requirements-dev.txt`銆乣requirements-lock.txt`锛氭媶鍒嗙敓浜т笌娴嬭瘯渚濊禆锛岃ˉ鍏?`loguru`锛屽苟鐢熸垚褰撳墠鐜鐨勯攣瀹氫緷璧栨竻鍗曘€?- `docs/deployment.md`锛氳ˉ鍏呭紑鍙戝畨瑁呫€佺敓浜у畨瑁呫€佹棩蹇楃洰褰曞拰鎺㈤拡璇存槑銆?- `backend.spec`銆乣celery-worker.spec`锛氳ˉ鍏呮柊澧炴棩蹇?鎸囨爣/鐧诲綍鎬?鎭㈠妯″潡鐨?`hiddenimports`銆?- 鎵归噺鏃ュ織鏇挎崲锛氭竻鐞?`backend/`銆乣browser/`銆乣pages/`銆乣tasks/` 涓墍鏈?`print()` 璋冪敤锛岀粺涓€鍒囨崲鍒版柊鏃ュ織浣撶郴銆?- 娴嬭瘯琛ラ綈锛氭柊澧炵櫥褰曟€佺洃鎺с€佹祻瑙堝櫒鎭㈠銆佷緷璧栨竻鍗曢潤鎬佹牎楠岋紱鏇存柊鍩虹椤点€佹祻瑙堝櫒绠＄悊鍣ㄣ€乄orker 鎵ц閾捐矾銆佺郴缁熸帴鍙ｃ€佸惎鍔ㄥ叆鍙ｆ祴璇曘€?
## 褰卞搷鑼冨洿

- 娴忚鍣ㄧ敓鍛藉懆鏈熺鐞嗕笌搴楅摵鐧诲綍鎬佹娴?- Worker 鎵ц閾捐矾涓庤嚜鍔ㄦ仮澶嶉噸璇?- 鍚庣鏃ュ織杈撳嚭銆佹棩蹇楃洰褰曚笌 trace_id 閾捐矾
- 绯荤粺鍋ュ悍妫€鏌ャ€佺洃鎺ф寚鏍囦笌璐熻浇鍧囪　鎺㈤拡
- 渚濊禆瀹夎鏂瑰紡涓?PyInstaller 鎵撳寘妯″潡鏀堕泦

## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m compileall backend browser pages tasks`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `473 passed, 16 warnings`銆?- 16 鏉?warning 涓虹涓夋柟渚濊禆寮冪敤鎻愮ず锛屾潵婧愪簬 `openpyxl` 涓?Celery 鐨?`datetime.utcnow()`锛屼笉灞炰簬鏈疆鏂板闂銆?- `requirements-lock.txt` 宸叉寜褰撳墠鐜閲嶆柊鐢熸垚骞朵娇鐢?UTF-8 缂栫爜鍐欏叆銆?- `.pipeline/task.md` 涓?`backend_log.txt` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀瑰叾浠诲姟鍐呭銆?
---

## 浠诲姟鎽樿

鐢?Tailwind 閲嶅啓浜嗗墠绔富甯冨眬鍏ュ彛 `App.vue`锛屾妸渚ц竟鏍忓垏鎴?Linear 椋庢牸鐧藉簳鏋佺畝甯冨眬锛屽苟鍚屾鏇存柊鐩稿叧闈欐€佸洖褰掓祴璇曘€?
## 鏀瑰姩鏂囦欢鍒楄〃

- `frontend/src/App.vue`
- `tests/unit/test_platform_frontend_static.py`
- `tests/unit/test_frontend_management_page.py`
- `tests/unit/test_after_sale_config_page.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/App.vue`锛氬紩鍏?`useRoute`锛屾柊澧?`navItems` 鏁版嵁婧愶紝鐢?`v-for` 娓叉煋宸︿晶瀵艰埅锛涘皢鏃ф繁鑹蹭晶杈规爮鏀逛负鐧藉簳銆佺伆鑹茬粏杈规銆佹祬鐏伴€変腑鎬佺殑 Linear 椋庢牸锛屽苟鎶婃暣鏂囦欢鍒囨垚绾?Tailwind class锛屽垹闄ゅ師鏈?`<style scoped>`銆?- `tests/unit/test_platform_frontend_static.py`锛氭洿鏂?App 涓诲竷灞€鏂█锛屾敼涓烘牎楠?`useRoute`銆乣navItems`銆乣bg-gray-50` 涓昏儗鏅€佺櫧搴曚晶杈规爮銆佹祬鐏伴€変腑鎬侊紝浠ュ強鏃ф繁鑹叉牱寮忓拰 `<style>` 鍧楀凡绉婚櫎銆?- `tests/unit/test_frontend_management_page.py`锛氬鑸叆鍙ｆ柇瑷€浠庣‖缂栫爜 `to="/..."` 璋冩暣涓?`navItems` 鏁版嵁婧愬拰 `:to="item.path"` 鍔ㄦ€佽矾鐢卞啓娉曪紝鍏煎鏂扮殑瀹炵幇缁撴瀯銆?- `tests/unit/test_after_sale_config_page.py`锛氬敭鍚庨厤缃鑸柇瑷€鍚屾鏀逛负鏂扮殑鍔ㄦ€佸鑸疄鐜帮紝缁х画淇濊瘉 `App.vue` 涓瓨鍦ㄨ鍏ュ彛銆?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞?Builder 鎵ц缁撴灉鍜岄獙璇佹儏鍐点€?
## 褰卞搷鑼冨洿

- 鍓嶇涓诲竷灞€鍏ュ彛涓庢墍鏈夐〉闈㈠叡浜殑渚ц竟鏍忓鑸?- 鍞悗閰嶇疆銆佸簵閾虹鐞嗐€佷笟鍔＄鐞嗐€佹暟鎹鐞嗐€佽繍琛岀洃鎺с€佽缃〉鐨勫叏灞€鍏ュ彛灞曠ず
- 涓?`App.vue` 缁撴瀯鍜屽鑸疄鐜扮浉鍏崇殑鍓嶇闈欐€佸洖褰?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_platform_frontend_static.py tests/unit/test_frontend_management_page.py tests/unit/test_after_sale_config_page.py -v`锛岀粨鏋滀负 `9 passed`銆?- 宸叉墽琛?`cd frontend && npm run build`锛屾瀯寤洪€氳繃銆?- 宸插皾璇?`cd frontend && npm run dev -- --host 127.0.0.1`锛屽綋鍓嶇幆澧冧粛鍥?`esbuild` 瀛愯繘绋?`spawn EPERM` 鏃犳硶瀹屾垚 Vite dev server 鍚姩楠屾敹銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `513 passed, 18 warnings`銆?- 18 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery`銆乣openpyxl` 鐨勫純鐢ㄦ彁绀猴紝浠ュ強鏃㈡湁 `PytestUnraisableExceptionWarning`锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

鐢?Headless UI + Tailwind 閲嶅啓浜?`Modal`銆乣ConfirmDialog`銆乣Toast` 涓変釜鏍稿績鍏叡缁勪欢锛屼繚鐣欐棦鏈夎皟鐢ㄦ帴鍙ｅ苟琛ラ綈闈欐€佸洖褰掓祴璇曘€?
## 鏀瑰姩鏂囦欢鍒楄〃

- `frontend/src/components/Modal.vue`
- `frontend/src/components/ConfirmDialog.vue`
- `frontend/src/components/Toast.vue`
- `tests/unit/test_shop_platform_modal_static.py`
- `tests/unit/test_headless_ui_components_static.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/components/Modal.vue`锛氭敼涓?Headless UI `Dialog` 缁撴瀯锛屼娇鐢ㄧ櫧搴曘€佺伆杈规銆佹瘺鐜荤拑閬僵鍜?Tailwind 杩囨浮鍔ㄧ敾锛涘垹闄ゅ師鐢?`<style>`锛屽悓鏃朵繚鐣?`.modal-container`銆乣.modal-body` 绛?class锛屽吋瀹归〉闈㈤噷宸插瓨鍦ㄧ殑 `:deep(...)` 鏍峰紡閽╁瓙銆?- `frontend/src/components/ConfirmDialog.vue`锛氭敼涓?Headless UI `Dialog`锛屼繚鐣?`show/title/message/type` 鍜?`confirmText/cancelText` 鐢ㄦ硶锛涙柊澧?`close` emit锛岄伄缃╁拰 ESC 鍏抽棴鏃剁户缁寜 `cancel` 璇箟鍥炶皟锛涘嵄闄╃‘璁ゆ寜閽敼涓?`rose`锛屾櫘閫氱‘璁ゆ寜閽敼涓虹伆榛戜富鎸夐挳锛岀Щ闄ゆ棫钃濊壊鏍峰紡銆?- `frontend/src/components/Toast.vue`锛氭敼涓哄彸涓婅鍥哄畾瀹氫綅锛屼娇鐢?Headless UI Transition 鍜?Tailwind class 娓叉煋鎻愮ず锛涘皢绫诲瀷棰滆壊鏀跺彛涓?`emerald / rose / amber / gray`锛岀Щ闄ゅ師鏈夎摑鑹?`info` 鎻愮ず鑹插拰鏃?`<style>` 鍧椼€?- `tests/unit/test_shop_platform_modal_static.py`锛氭洿鏂?Modal 鐩稿叧鏂█锛屾敼涓烘牎楠屾柊鐨?Headless UI 鐧藉簳寮圭獥澹冲眰锛屽悓鏃朵繚鐣欏簵閾洪〉琛ㄥ崟鐜版湁鏍峰紡鏂█銆?- `tests/unit/test_headless_ui_components_static.py`锛氭柊澧炵粍浠剁骇闈欐€佸洖褰掞紝瑕嗙洊 Modal / ConfirmDialog / Toast 鐨?Headless UI 鎺ュ叆銆乀ailwind 鏍峰紡銆佸吋瀹?emits锛屼互鍙娾€滄棤钃濊壊 / 鏃?`<style>`鈥濈殑鍙嶅悜鏂█銆?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞?Builder 鎵ц缁撴灉涓庨獙璇佹儏鍐点€?
## 褰卞搷鑼冨洿

- 鍓嶇鍏叡寮圭獥缁勪欢涓庢彁绀虹粍浠剁殑瑙嗚鏍峰紡
- `ShopManage`銆乣FlowManage`銆乣ScheduleManage`銆乣TaskMonitor`銆乣TaskParamsManage`銆乣BrowserManager`銆乣LogViewer` 绛変緷璧栧叕鍏辩粍浠剁殑椤甸潰
- 鍓嶇闈欐€佸洖褰掍腑涓庡脊绐楃粍浠剁粨鏋勩€佹牱寮忓拰鍏煎 class 鐩稿叧鐨勬柇瑷€

## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_headless_ui_components_static.py tests/unit/test_shop_platform_modal_static.py tests/unit/test_batch_execute_schedule_static.py tests/unit/test_flow_manage_editor_static.py tests/unit/test_frontend_tailwind_static.py -v`锛岀粨鏋滀负 `14 passed`銆?- 宸叉墽琛?`cd frontend && npm run build`锛屾瀯寤洪€氳繃銆?- 宸插皾璇?`cd frontend && npm run dev -- --host 127.0.0.1`锛屽綋鍓嶇幆澧冧粛鍥?`esbuild` 瀛愯繘绋?`spawn EPERM` 鏃犳硶瀹屾垚 Vite dev server 鍚姩楠屾敹銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `513 passed, 18 warnings`銆?- 18 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery`銆乣openpyxl` 鐨勫純鐢ㄦ彁绀猴紝浠ュ強鏃㈡湁 `PytestUnraisableExceptionWarning`锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- 鏈疆鍙噸鍐欎簡鍏叡缁勪欢澶栧３锛岄〉闈㈡彃妲介噷鐨勮〃鍗?鎸夐挳瑙嗚浠嶆部鐢ㄥ悇椤甸潰鍘熸湁瀹炵幇銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

鏇挎崲 PyInstaller 鐨?backend / celery-worker spec 涓烘樉寮忔ā鍧楁敹闆嗘柟妗堬紝骞朵慨姝?Electron 鎵撳寘 exe 璺緞鍒?`--onedir` 瀛愮洰褰曠粨鏋勩€?
## 鏀瑰姩鏂囦欢鍒楄〃

- `backend.spec`
- `celery-worker.spec`
- `electron/main.js`
- `tests/unit/test_pyinstaller_spec_files.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `backend.spec`锛氭敼涓烘樉寮忓垪鍑洪」鐩ā鍧?`hiddenimports`锛屽苟涓?`uvicorn`銆乣fastapi`銆乣starlette`銆乣celery`銆乣kombu`銆乣amqp`銆乣redis` 鍋?`collect_all`锛涘悓鏃舵妸 `collect_all(...)` 鍓嶇Щ鍒?`Analysis(...)` 涔嬪墠锛屽吋瀹瑰綋鍓?PyInstaller 6.17 鐨?`TOC` 澶勭悊銆?- `celery-worker.spec`锛氭敼涓烘樉寮忓垪鍑?Worker 渚濊禆鐨勯」鐩ā鍧?`hiddenimports`锛屽苟涓?`celery`銆乣kombu`銆乣amqp`銆乣redis` 鍋?`collect_all`锛涘悓鏍峰墠绉诲悎骞堕€昏緫锛岀‘淇濇墦鍖呭懡浠ゅ彲鐩存帴閫氳繃銆?- `electron/main.js`锛氬皢鎵撳寘妯″紡涓嬬殑 exe 璺緞鏀规垚 `python-backend/backend/backend.exe` 涓?`python-backend/celery-worker/celery-worker.exe`锛岄€傞厤 `--onedir` 杈撳嚭缁撴瀯銆?- `tests/unit/test_pyinstaller_spec_files.py`锛氭柊澧為潤鎬佸洖褰掞紝瑕嗙洊涓や釜 spec 鐨勫叧閿樉寮忓鍏ャ€乣collect_submodules` 绉婚櫎锛屼互鍙?Electron 鏂版棫鎵撳寘璺緞宸紓銆?- `PLAN.md`锛氳ˉ鍏?Prompt 124 鐨勫疄鐜般€佹墦鍖呴獙鏀跺拰鍥炲綊缁撴灉銆?- `鏀归€犺繘搴?md`锛氬悓姝ユ湰杞敼閫犲唴瀹广€佹墦鍖呭懡浠ゅ拰鍚姩楠屾敹鎯呭喌銆?- `.pipeline/progress.md`锛氳褰曟湰杞?Builder 鎵ц缁撴灉銆?
## 褰卞搷鑼冨洿

- PyInstaller 鍚庣鎵撳寘閰嶇疆
- PyInstaller Celery Worker 鎵撳寘閰嶇疆
- Electron 鎵撳寘妯″紡鍚庣 / Worker 鍙墽琛屾枃浠跺畾浣?- 鎵撳寘鐩稿叧闈欐€佸洖褰?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_pyinstaller_spec_files.py tests/unit/test_electron_main.py -v`锛岀粨鏋?`8 passed`銆?- 宸叉墽琛?`node --check electron/main.js`銆?- 宸叉寜浠诲姟鍛戒护鎵ц锛?  - `pyinstaller --noconfirm --distpath ./python-backend-dist backend.spec`
  - `pyinstaller --noconfirm --distpath ./python-backend-dist celery-worker.spec`
- 宸叉墽琛?`python-backend-dist/backend/backend.exe` 鐭椂鍚姩楠屾敹锛? 绉掕娴嬪唴杩涚▼淇濇寔杩愯锛屽苟杈撳嚭 `Application startup complete`銆乣Uvicorn running on http://127.0.0.1:8000`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋?`459 passed, 16 warnings`銆?- PyInstaller 浠嶆湁 `kombu.asynchronous.aws` 缂哄皯 `botocore` 鐨勬瀯寤哄憡璀︼紝浣嗘湰杞墦鍖呭凡鎴愬姛锛屼笉褰卞搷褰撳墠楠屾敹銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

淇 PyInstaller 鍚庣涓?Celery 鍏ュ彛鍦ㄥ喕缁撴ā寮忎笅閿欒瑕嗙洊 `sys.path` 鐨勯棶棰橈紝骞惰ˉ榻?frozen / 闈?frozen 鍒嗘敮鍥炲綊娴嬭瘯銆?
## 鏀瑰姩鏂囦欢鍒楄〃

- `scripts/pyinstaller_entry.py`
- `scripts/pyinstaller_celery_entry.py`
- `tests/unit/test_pyinstaller_entry.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `scripts/pyinstaller_entry.py`锛氬皢椤圭洰鏍圭洰褰曟敞鍏ユ敼鎴愪粎鍦ㄩ潪 frozen 妯″紡鎵ц锛岄伩鍏?PyInstaller 杩愯鏃舵妸 `_internal` 瀵煎叆璺緞椤舵帀銆?- `scripts/pyinstaller_celery_entry.py`锛氬悓姝ヤ负 Celery Worker 鍏ュ彛澧炲姞鐩稿悓鏉′欢锛屼繚鎸佷袱鏉″惎鍔ㄩ摼璺涓轰竴鑷淬€?- `tests/unit/test_pyinstaller_entry.py`锛氭柊澧?4 涓洖褰掔敤渚嬶紝瑕嗙洊鍚庣鍏ュ彛涓?Celery 鍏ュ彛鍦?frozen / 闈?frozen 涓ょ妯″紡涓嬬殑璺緞娉ㄥ叆琛屼负锛屽苟椤哄甫鏍￠獙 `鏋勫缓Worker鍙傛暟()` 榛樿鍊笺€?- `PLAN.md`锛氳ˉ鍏?Prompt 123 鐨勬敼閫犲唴瀹广€侀獙璇佸懡浠ゅ拰褰撳墠鎵撳寘楠屾敹缁撹銆?- `鏀归€犺繘搴?md`锛氬悓姝ユ湰杞繘搴︺€佹祴璇曠粨鏋滃拰杩愯鎬侀獙鏀舵儏鍐点€?- `.pipeline/progress.md`锛氳褰曟湰杞?Builder 鎵ц缁撴灉銆?
## 褰卞搷鑼冨洿

- PyInstaller 鍚庣鍚姩鍏ュ彛
- PyInstaller Celery Worker 鍚姩鍏ュ彛
- 鎵撳寘鍏ュ彛鑴氭湰鐩稿叧鍥炲綊娴嬭瘯

## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_pyinstaller_entry.py -v`锛岀粨鏋?`4 passed`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋?`456 passed, 16 warnings`銆?- 宸叉墽琛?`python scripts/pyinstaller_entry.py` 鐨?5 绉掔煭鏃跺惎鍔ㄩ獙鏀讹紝杩涚▼淇濇寔杩愯骞惰緭鍑?`Started server process`銆乣Waiting for application startup`銆?- 宸叉寜浠诲姟缁欏畾鍛戒护鎵ц `PyInstaller --onedir` 鏋勫缓锛涚敓鎴愮殑 `backend.exe` 涓嶅啀鎶?`No module named 'backend'`锛屼絾浠嶅洜缂哄皯 `fastapi` 渚濊禆鎶ラ敊锛屽睘浜庣幇瀛樻墦鍖呴厤缃棶棰橈紝鏈疆鏈鐞嗐€?- `backend.spec` 鍦ㄦ墦鍖呴獙鏀舵椂鏇捐 PyInstaller 鏀瑰啓锛屽凡鎭㈠鍒伴獙鏀跺墠鍐呭銆?- `.pipeline/task.md`銆乣backend.spec`銆乣build_backend.bat`銆乣celery-worker.spec` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀瑰叾鐩爣鍐呭銆?
---

## 浠诲姟鎽樿

淇 Electron 閲嶅惎鍚庣殑绔彛娈嬬暀涓庡瓙杩涚▼娓呯悊闂锛歐indows 鍚姩鍓嶅皾璇曞垏鎹?UTF-8 浠ｇ爜椤碉紝鍏抽棴鏃剁敤 `taskkill /F /T /PID` 鍥炴敹杩涚▼鏍戯紝骞跺湪鍚庣鍚姩鍓嶆竻鐞嗙鍙ｅ崰鐢ㄣ€?
## 鏀瑰姩鏂囦欢鍒楄〃

- `electron/main.js`
- `tests/unit/test_electron_main.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`

## 鏀瑰姩璇存槑

- `electron/main.js`锛氬惎鍔ㄥ墠澧炲姞绔彛鍗犵敤娓呯悊锛沗stopProcess(...)` 鍦?Windows 涓嬫敼鎴?`taskkill /F /T /PID`锛涗唬鐮侀〉鍒囨崲鏀规垚 `stdio: 'inherit'`锛涘悓鏃舵樉寮忔敹鍙ｅ埌 `System32` 鍛戒护璺緞锛屽噺灏戝 PATH 鐨勪緷璧栥€?- `tests/unit/test_electron_main.py`锛氭洿鏂?`chcp` 鏂█锛屽苟鏂板绔彛娓呯悊涓庤繘绋嬫爲缁堟鐨勯潤鎬佸洖褰掋€?- `PLAN.md`锛氳ˉ鍏呮湰杞?Prompt 122 璁板綍銆侀獙璇佸懡浠ゅ拰褰撳墠鐜闄愬埗銆?- `鏀归€犺繘搴?md`锛氭柊澧炴湰杞敼閫犺褰曪紝渚夸簬鍚庣画鎺ョ画銆?
## 褰卞搷鑼冨洿

- Electron 涓昏繘绋嬪惎鍔?閫€鍑烘祦绋?- Windows 涓嬬殑鍚庣绔彛閲婃斁涓庡瓙杩涚▼鍥炴敹
- Electron 涓昏繘绋嬬浉鍏抽潤鎬佸洖褰?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋?`452 passed, 16 warnings`銆?- 宸叉墽琛?`node --check electron/main.js`銆?- 宸插皾璇?`cd electron && npx electron .`锛屼絾褰撳墠鎵ц鐜涓嬩粛鍥?`platform_channel.cc(83)` 鐨?`鎷掔粷璁块棶 (0x5)` 鎻愬墠閫€鍑猴紝涓?stderr 浠嶅嚭鐜?`'chcp' 涓嶆槸鍐呴儴鎴栧閮ㄥ懡浠銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

琛ラ綈 Electron 涓昏繘绋嬪惎鍔ㄩ摼璺細Windows 鍚姩鍓嶅垏鎹?UTF-8 鎺у埗鍙颁唬鐮侀〉锛孋elery 榛樿鍚屾椂鐩戝惉 `celery` 鍜?`worker.{AGENT_MACHINE_ID}`锛屽苟琛ュ洖涓ゅ瀛橀噺 `_杩愯寮傛浠诲姟` 鍏煎瀵煎嚭浠ユ仮澶嶅叏閲忓洖褰掋€?
## 鏀瑰姩鏂囦欢鍒楄〃

- `electron/main.js`
- `tests/unit/test_electron_main.py`
- `tasks/bridge_task.py`
- `tasks/execute_task.py`

## 鏀瑰姩璇存槑

- `electron/main.js`锛氭柊澧?`execSync` 瀵煎叆锛宍app.whenReady()` 閲屽湪 Windows 涓嬪厛鎵ц `chcp 65001`锛沗startCelery()` 缁熶竴鐢熸垚 `queues` 骞舵敞鍏?`CELERY_QUEUES`锛岃寮€鍙戞ā寮忓拰鎵撳寘妯″紡閮界洃鍚?`celery` 涓?`worker.{machine_id}`銆?- `tests/unit/test_electron_main.py`锛氭柊澧為潤鎬佸洖褰掞紝瑕嗙洊榛樿闃熷垪銆佹墦鍖呮ā寮忛槦鍒楅€忎紶鍜?UTF-8 浠ｇ爜椤靛垏鎹?瀹归敊銆?- `tasks/bridge_task.py`锛氭仮澶?`_杩愯寮傛浠诲姟` 鏈湴鍖呰锛屽吋瀹圭幇鏈夋ˉ鎺ユ祴璇曞拰 patch 鐐广€?- `tasks/execute_task.py`锛氶噸鏂版毚闇?`_杩愯寮傛浠诲姟`锛屽吋瀹圭嚎绋嬫睜浜嬩欢寰幆娴嬭瘯瀵规棫绗﹀彿鐨勮皟鐢ㄣ€?
## 褰卞搷鑼冨洿

- Electron 涓昏繘绋嬪惎鍔ㄦ祦绋?- Celery Worker 闃熷垪鐩戝惉閰嶇疆
- 妗ユ帴浠诲姟 / 鎵ц浠诲姟鐨勬祴璇曞吋瀹瑰眰

## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋?`450 passed, 16 warnings`銆?- 宸叉墽琛?`node --check electron/main.js`銆?- 宸插皾璇?`cd electron && npx electron .`锛屼絾褰撳墠鐜涓?Electron 鍥?`platform_channel.cc(83)` 鐨?`鎷掔粷璁块棶 (0x5)` 鎻愬墠閫€鍑猴紝鏈兘瀹屾垚 GUI 楠屾敹銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

瀹屾垚涓ら」浠诲姟锛氾紙1锛夌Щ闄ゅ祵鍏ュ紡 Python 婧愮爜鎵撳寘鏂规锛屾仮澶?PyInstaller exe 鏂瑰紡锛涳紙2锛夊皢鍏ㄩ儴涓枃鍛藉悕 `.py` 鏂囦欢閲嶅懡鍚嶄负鑻辨枃锛屽苟鍏ㄩ噺鏇存柊鎵€鏈?import 寮曠敤銆傛墍鏈?448 鏉℃祴璇曢€氳繃銆?
## 鏀瑰姩鏂囦欢鍒楄〃

### Part 1 鈥?鎭㈠ PyInstaller 鎵撳寘鏂规

- `electron/main.js` 鈥?瀹屽叏閲嶅啓锛岀敓浜фā寮忔敼鐢?`python-backend/backend.exe` 鍜?`python-backend/celery-worker.exe`锛涘紑鍙戞ā寮忔ā鍧楄矾寰勬洿鏂颁负鑻辨枃
- `electron/package.json` 鈥?`extraResources` 鏀瑰洖 `../python-backend-dist` 鈫?`app/python-backend`
- `scripts/prepare_dist.py` 鈥?鍒犻櫎锛坄git rm`锛?- `scripts/build_all.bat` 鈥?鍒犻櫎锛坄git rm`锛?- `tests/unit/test_prepare_dist.py` 鈥?鍒犻櫎锛堟祴璇曠洰鏍囧凡涓嶅瓨鍦級

### Part 2 鈥?涓枃鏂囦欢鍚?鈫?鑻辨枃

#### backend/

- `backend/鍚姩鍏ュ彛.py` 鈫?`backend/main.py`
- `backend/閰嶇疆.py` 鈫?`backend/config.py`
- `backend/api/璺敱娉ㄥ唽.py` 鈫?`backend/api/router.py`
- `backend/api/浠诲姟鎺ュ彛.py` 鈫?`backend/api/task_api.py`
- `backend/api/浠诲姟鍙傛暟鎺ュ彛.py` 鈫?`backend/api/task_params_api.py`
- `backend/api/鍙敤浠诲姟.py` 鈫?`backend/api/available_tasks.py`
- `backend/api/鎵ц鎺ュ彛.py` 鈫?`backend/api/execute_api.py`
- `backend/api/杩愯鎺ュ彛.py` 鈫?`backend/api/run_api.py`
- `backend/api/娴佺▼鎺ュ彛.py` 鈫?`backend/api/flow_api.py`
- `backend/api/娴佺▼鍙傛暟鎺ュ彛.py` 鈫?`backend/api/flow_params_api.py`
- `backend/api/娴佺▼杈撳叆鎺ュ彛.py` 鈫?`backend/api/flow_input_api.py`
- `backend/api/搴楅摵鎺ュ彛.py` 鈫?`backend/api/shop_api.py`
- `backend/api/娴忚鍣ㄦ帴鍙?py` 鈫?`backend/api/browser_api.py`
- `backend/api/鏃ュ織鎺ュ彛.py` 鈫?`backend/api/log_api.py`
- `backend/api/绯荤粺鎺ュ彛.py` 鈫?`backend/api/system_api.py`
- `backend/api/瑙勫垯鎺ュ彛.py` 鈫?`backend/api/rule_api.py`
- `backend/api/鍞悗閰嶇疆鎺ュ彛.py` 鈫?`backend/api/after_sale_config_api.py`
- `backend/api/瀹氭椂鎵ц鎺ュ彛.py` 鈫?`backend/api/scheduled_execute_api.py`
- `backend/api/閫氱敤浠诲姟鎺ュ彛.py` 鈫?`backend/api/generic_task_api.py`
- `backend/api/椋炰功鎺ュ彛.py` 鈫?`backend/api/feishu_api.py`
- `backend/models/鏁版嵁搴?py` 鈫?`backend/models/database.py`
- `backend/models/鏁版嵁缁撴瀯.py` 鈫?`backend/models/data_structure.py`
- `backend/models/搴楅摵妯″瀷.py` 鈫?`backend/models/shop_model.py`
- `backend/models/娴佺▼妯″瀷.py` 鈫?`backend/models/flow_model.py`
- `backend/models/琛ㄧ粨鏋?py` 鈫?`backend/models/table_schema.py`
- `backend/models/瑙勫垯妯″瀷.py` 鈫?`backend/models/rule_model.py`
- `backend/models/瀹氭椂浠诲姟妯″瀷.py` 鈫?`backend/models/scheduled_task_model.py`
- `backend/models/鍞悗閰嶇疆妯″瀷.py` 鈫?`backend/models/after_sale_config_model.py`
- `backend/models/鍞悗闃熷垪妯″瀷.py` 鈫?`backend/models/after_sale_queue_model.py`
- `backend/services/浠诲姟鏈嶅姟.py` 鈫?`backend/services/task_service.py`
- `backend/services/浠诲姟鍙傛暟鏈嶅姟.py` 鈫?`backend/services/task_params_service.py`
- `backend/services/鎵ц鏈嶅姟.py` 鈫?`backend/services/execute_service.py`
- `backend/services/杩愯鏈嶅姟.py` 鈫?`backend/services/run_service.py`
- `backend/services/娴佺▼鏈嶅姟.py` 鈫?`backend/services/flow_service.py`
- `backend/services/娴佺▼鍙傛暟鏈嶅姟.py` 鈫?`backend/services/flow_params_service.py`
- `backend/services/娴佺▼杈撳叆鏈嶅姟.py` 鈫?`backend/services/flow_input_service.py`
- `backend/services/搴楅摵鏈嶅姟.py` 鈫?`backend/services/shop_service.py`
- `backend/services/娴忚鍣ㄦ湇鍔?py` 鈫?`backend/services/browser_service.py`
- `backend/services/鏃ュ織鏈嶅姟.py` 鈫?`backend/services/log_service.py`
- `backend/services/绯荤粺鏈嶅姟.py` 鈫?`backend/services/system_service.py`
- `backend/services/瑙勫垯鏈嶅姟.py` 鈫?`backend/services/rule_service.py`
- `backend/services/鍞悗閰嶇疆鏈嶅姟.py` 鈫?`backend/services/after_sale_config_service.py`
- `backend/services/鍞悗闃熷垪鏈嶅姟.py` 鈫?`backend/services/after_sale_queue_service.py`
- `backend/services/鍞悗鍐崇瓥寮曟搸.py` 鈫?`backend/services/after_sale_decision_engine.py`
- `backend/services/瀹氭椂鎵ц鏈嶅姟.py` 鈫?`backend/services/scheduled_execute_service.py`
- `backend/services/蹇冭烦鏈嶅姟.py` 鈫?`backend/services/heartbeat_service.py`
- `backend/services/閭鏈嶅姟.py` 鈫?`backend/services/email_service.py`
- `backend/services/椋炰功鏈嶅姟.py` 鈫?`backend/services/feishu_service.py`

#### tasks/

- `tasks/celery搴旂敤.py` 鈫?`tasks/celery_app.py`
- `tasks/娉ㄥ唽琛?py` 鈫?`tasks/registry.py`
- `tasks/浠诲姟娉ㄥ唽琛?py` 鈫?`tasks/task_registry.py`
- `tasks/鍩虹浠诲姟.py` 鈫?`tasks/base_task.py`
- `tasks/鐧诲綍浠诲姟.py` 鈫?`tasks/login_task.py`
- `tasks/鍞悗浠诲姟.py` 鈫?`tasks/after_sale_task.py`
- `tasks/鎺ㄥ箍浠诲姟.py` 鈫?`tasks/promotion_task.py`
- `tasks/鎵ц浠诲姟.py` 鈫?`tasks/execute_task.py`
- `tasks/妗ユ帴浠诲姟.py` 鈫?`tasks/bridge_task.py`
- `tasks/瀹氭椂浠诲姟.py` 鈫?`tasks/scheduled_task.py`
- `tasks/闄愭椂闄愰噺浠诲姟.py` 鈫?`tasks/flash_sale_task.py`
- `tasks/鍙戝竷鎹㈠浘鍟嗗搧浠诲姟.py` 鈫?`tasks/publish_replace_image_task.py`
- `tasks/鍙戝竷鐩镐技鍟嗗搧浠诲姟.py` 鈫?`tasks/publish_similar_product_task.py`

#### browser/ / pages/ / selectors/

- `browser/浠诲姟鍥炶皟.py` 鈫?`browser/task_callback.py`
- `browser/绠＄悊鍣?py` 鈫?`browser/manager.py`
- `browser/鍙嶆娴?py` 鈫?`browser/anti_detection.py`
- `browser/婊戝潡楠岃瘉鐮?py` 鈫?`browser/slider_captcha.py`
- `browser/鐢ㄦ埛鐩綍宸ュ巶.py` 鈫?`browser/user_dir_factory.py`
- `browser/楠岃瘉鐮佽瘑鍒?py` 鈫?`browser/captcha_recognition.py`
- `pages/鍩虹椤?py` 鈫?`pages/base_page.py`
- `pages/鐧诲綍椤?py` 鈫?`pages/login_page.py`
- `pages/鍞悗椤?py` 鈫?`pages/after_sale_page.py`
- `pages/鍟嗗搧鍒楄〃椤?py` 鈫?`pages/product_list_page.py`
- `pages/鍙戝竷鍟嗗搧椤?py` 鈫?`pages/publish_product_page.py`
- `pages/鎺ㄥ箍椤?py` 鈫?`pages/promotion_page.py`
- `pages/寰俊椤?py` 鈫?`pages/wechat_page.py`
- `pages/妗岄潰鍩虹椤?py` 鈫?`pages/desktop_base_page.py`
- `pages/闄愭椂闄愰噺椤?py` 鈫?`pages/flash_sale_page.py`
- `selectors/閫夋嫨鍣ㄩ厤缃?py` 鈫?`selectors/selector_config.py`
- `selectors/鍩虹椤甸€夋嫨鍣?py` 鈫?`selectors/base_page_selector.py`
- `selectors/鐧诲綍椤甸€夋嫨鍣?py` 鈫?`selectors/login_page_selector.py`
- `selectors/鍞悗椤甸€夋嫨鍣?py` 鈫?`selectors/after_sale_page_selector.py`
- `selectors/鍟嗗搧鍒楄〃椤甸€夋嫨鍣?py` 鈫?`selectors/product_list_page_selector.py`
- `selectors/鍙戝竷鍟嗗搧椤甸€夋嫨鍣?py` 鈫?`selectors/publish_product_page_selector.py`
- `selectors/鎺ㄥ箍椤甸€夋嫨鍣?py` 鈫?`selectors/promotion_page_selector.py`
- `selectors/寰俊閫夋嫨鍣?py` 鈫?`selectors/wechat_selector.py`
- `selectors/妗岄潰閫夋嫨鍣ㄩ厤缃?py` 鈫?`selectors/desktop_selector_config.py`
- `selectors/闄愭椂闄愰噺椤甸€夋嫨鍣?py` 鈫?`selectors/flash_sale_page_selector.py`

#### tests/

- `tests/鍗曞厓娴嬭瘯/` 鐩綍 鈫?`tests/unit/`锛?8 涓祴璇曟枃浠讹紝`娴嬭瘯_*.py` 鈫?`test_*.py`锛?- `tests/test_鍞悗浠诲姟.py` 鈫?`tests/test_after_sale_task.py`
- `tests/test_鎺ㄥ箍浠诲姟.py` 鈫?`tests/test_promotion_task.py`
- `tests/test_鍙戝竷鎹㈠浘鍟嗗搧浠诲姟.py` 鈫?`tests/test_publish_replace_image_task.py`
- `tests/test_鍙戝竷鐩镐技鍟嗗搧浠诲姟.py` 鈫?`tests/test_publish_similar_product_task.py`
- `tests/test_鐧诲綍浠诲姟.py` 鈫?`tests/test_login_task.py`
- `tests/test_闄愭椂闄愰噺浠诲姟.py` 鈫?`tests/test_flash_sale_task.py`
- 鍏朵綑 `tests/test_*.py` 鍏?4 涓悓姝ラ噸鍛藉悕

#### 鍏朵粬鍏ュ彛涓庨厤缃枃浠?
- `entry_backend.py` 鈥?import 璺緞鏇存柊
- `entry_celery.py` 鈥?import 璺緞 + 鍙橀噺鍚嶆洿鏂?- `scripts/pyinstaller_celery_entry.py` 鈥?import 璺緞 + 鍙橀噺鍚嶆洿鏂?- `tasks/celery_app.py` 鈥?鍙橀噺鍚?`celery搴旂敤` 鈫?`celery_app`
- `tasks/registry.py` 鈥?`鎺掗櫎妯″潡` 闆嗗悎鐢变腑鏂囧悕鏇存柊涓鸿嫳鏂囧悕
- `tests/unit/test_production_env_check.py` 鈥?鏂█鏇存柊涓?PyInstaller 鏂规
- `tests/unit/test_system_set_machine_code.py` 鈥?閰嶇疆鏂囦欢璺緞鏇存柊涓?`backend/config.py`
- 鍏ㄤ粨搴?184 涓枃浠剁殑 import 璺緞鎵归噺鏇挎崲

## 鏀瑰姩璇存槑

### Part 1

- `electron/main.js`锛氬垹闄?`python-embed` 閫昏緫锛屾柊澧?`ensurePackagedFileExists` 鏍￠獙锛岀敓浜фā寮忕洿鎺?`spawn` PyInstaller 浜у嚭鐨?exe锛涘紑鍙戞ā寮?uvicorn 鍙傛暟鐢?`backend.鍚姩鍏ュ彛:app` 鏀逛负 `backend.main:app`锛宑elery 妯″潡璺緞鐢?`tasks.celery搴旂敤` 鏀逛负 `tasks.celery_app`
- `electron/package.json`锛歚extraResources` 鎭㈠涓?`{ "from": "../python-backend-dist", "to": "app/python-backend" }`

### Part 2

鍒嗗洓杞畬鎴?import 鏇挎崲锛?
1. **鍏ㄨ矾寰勬浛鎹?*锛坄backend.閰嶇疆` 鈫?`backend.config` 绛?147 鏉℃槧灏勶級锛岃鐩栨墍鏈?`import X.涓枃鍚峘 鍜?`from X.涓枃鍚?import Y` 鏍煎紡
2. **鍙橀噺鍚嶆浛鎹?*锛歚celery搴旂敤` 鈫?`celery_app`锛屼娇鐢ㄨ礋鍚戝墠鐬?`(?!妯″潡)` 淇濈暀娴嬭瘯鍒悕 `celery搴旂敤妯″潡`
3. **鐭悕瀛愭ā鍧楁浛鎹?*锛歚from backend.models import 鏁版嵁搴?as` 鈫?`from backend.models import database as` 绛夌簿纭瓧绗︿覆鏇挎崲锛?4 涓枃浠讹級
4. **Token 杈圭晫鏇挎崲**锛歚from backend.services import 绯荤粺鏈嶅姟` 绛夋ā寮忥紝浣跨敤姝ｅ垯鍓嶇灮 `(?=\s*(?:as\s|,|\n|#|\Z))` 纭繚涓嶈鏇挎崲锛?2 涓枃浠讹級

鍏抽敭淇锛歚tasks/registry.py` 鐨?`鎺掗櫎妯″潡` 闆嗗悎鐢辨棫涓枃鍚嶏紙`娉ㄥ唽琛╜銆乣浠诲姟娉ㄥ唽琛╜ 绛夛級鏇存柊涓鸿嫳鏂囧悕锛岄槻姝?`pkgutil.iter_modules` 鎵弿鏃跺皢 `registry` 鏈韩绾冲叆骞惰Е鍙戞ā鍧楅噸杞藉鑷存敞鍐岃〃琚竻绌恒€?
## 褰卞搷鑼冨洿

- 鍏ㄩ噺 Python 婧愭枃浠?import 璺緞鍙樻洿锛屾棤鍔熻兘閫昏緫淇敼
- Electron 涓昏繘绋嬫墦鍖呯瓥鐣ュ彉鏇达紙宓屽叆寮?鈫?PyInstaller exe锛?- 娴嬭瘯鐩綍缁撴瀯锛歚tests/鍗曞厓娴嬭瘯/` 鈫?`tests/unit/`

## 楠岃瘉缁撴灉

```
448 passed, 16 warnings in 61.78s
```
---

## 浠诲姟鎽樿

淇 PyInstaller 鎵撳寘鍚庣殑 `backend.exe` 鍚姩璺緞闂锛岃ˉ榻?`.env`/鏁版嵁搴撶洰褰曡В鏋愩€丒lectron 鎵撳寘 `cwd`锛屽苟璁?PyInstaller 6 onedir 浜х墿鎶?`.env` 鏀惧洖 exe 鍚岀骇锛屾渶缁堝畬鎴愮湡瀹炴墦鍖呭惎鍔ㄤ笌鍏ㄩ噺鍥炲綊楠岃瘉銆?
## 鏀瑰姩鏂囦欢鍒楄〃

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
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `scripts/pyinstaller_entry.py`锛氬喕缁撴ā寮忓惎鍔ㄥ墠鍒囨崲鍒?`sys.executable` 鎵€鍦ㄧ洰褰曪紱瀵煎叆澶辫触鏃跺皢閿欒銆乣cwd` 鍜?traceback 鍐欏叆 exe 鍚岀骇 `crash.log`锛屼究浜庣洿鎺ユ帓鏌ユ墦鍖呬骇鐗╁惎鍔ㄥけ璐ャ€?- `backend/config.py`锛氭柊澧炲喕缁撴ā寮?`.env` 瑙ｆ瀽绛栫暐锛屼紭鍏堣鍙?exe 鍚岀骇锛屽啀鍥為€€鍒?exe 涓婄骇鍜屽綋鍓嶅伐浣滅洰褰曪紝閬垮厤 Electron 鎴栧弻鍑诲惎鍔ㄦ椂鐩稿璺緞澶辨晥銆?- `backend/models/database.py`锛氬皢鍐荤粨妯″紡鏁版嵁搴撶洰褰曟敼涓?exe 鍚岀骇 `data/`锛屼繚璇佹墦鍖呭悗榛樿鍐欏叆 `python-backend-dist/backend/data/ecom.db`銆?- `electron/main.js`锛氭墦鍖呮ā寮忓惎鍔?`backend.exe` 涓?`celery-worker.exe` 鏃舵樉寮忚缃?`cwd: path.dirname(...)`锛屼繚璇佸悗绔笌 Worker 鐨勮繍琛岀洰褰曚竴鑷淬€?- `backend.spec`锛氳ˉ榻?`('.env', '.')`锛屽苟鍦?`EXE(...)` 涓缃?`contents_directory='.'`锛屽吋瀹?PyInstaller 6 onedir 甯冨眬锛岀‘淇?`.env` 瀹為檯澶嶅埗鍒?`backend.exe` 鍚岀骇鑰屼笉鏄?`_internal/`銆?- `tests/unit/test_pyinstaller_entry.py`锛氳ˉ鍏呭喕缁撴ā寮忓垏鎹?`cwd`銆佸鍏ュけ璐ュ啓 `crash.log` 鐨勫洖褰掞紝鍚屾椂淇娴嬭瘯鏈韩娈嬬暀 `cwd` 瀵艰嚧鍚庣画鐢ㄤ緥澶辫触鐨勯棶棰樸€?- `tests/unit/test_packaged_runtime_paths.py`锛氭柊澧炴墦鍖呰繍琛屾椂 `.env` 涓庢暟鎹簱鐩綍瑙ｆ瀽娴嬭瘯銆?- `tests/unit/test_electron_main.py`锛氳ˉ鍏呮墦鍖呮ā寮?`cwd` 蹇呴』浣跨敤 `path.dirname(exe)` 鐨勯潤鎬佹柇瑷€銆?- `tests/unit/test_pyinstaller_spec_files.py`锛氳ˉ鍏?`.env` 鏀堕泦涓?`contents_directory='.'` 鐨?spec 鏂█銆?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞敼閫犮€侀獙璇佸懡浠や笌楠屾敹缁撴灉銆?
## 褰卞搷鑼冨洿

- PyInstaller 鍚庣鍏ュ彛鍚姩閾捐矾
- 鎵撳寘鍚?`.env` 璇诲彇涓?SQLite 鏁版嵁鐩綍瀹氫綅
- Electron 鎵撳寘妯″紡涓嬪悗绔笌 Worker 瀛愯繘绋嬪惎鍔?- 鎵撳寘鐩稿叧鍗曞厓娴嬭瘯涓庨潤鎬佸洖褰?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`pyinstaller --noconfirm --distpath ./python-backend-dist backend.spec`锛屾瀯寤烘垚鍔熴€?- 宸茬洿鎺ヨ繍琛?`python-backend-dist/backend/backend.exe`锛屾帶鍒跺彴杈撳嚭 `Application startup complete`锛屽苟鑷姩鍒涘缓 `python-backend-dist/backend/data/ecom.db`銆?- 浜х墿鐩綍宸茬‘璁?`.env` 浣嶄簬 `python-backend-dist/backend/.env`锛宍crash.log` 鏈敓鎴愩€?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `479 passed, 16 warnings`銆?- 鏋勫缓闃舵浠嶆湁 `kombu.asynchronous.aws` 缂哄皯 `botocore` 鐨?PyInstaller 璀﹀憡锛屼絾涓嶅奖鍝嶆湰杞獙鏀躲€?---

## 浠诲姟鎽樿

淇 PyInstaller 鎵撳寘鍚庝腑鏂囨棩蹇椾贡鐮侊細鏂板 UTF-8 runtime hook锛岀粰 backend / celery 鍏ュ彛琛ュ弻淇濋櫓缂栫爜璁剧疆锛屽苟璁?Electron 瀛愯繘绋嬫棩蹇楃閬撴樉寮忔寜 `utf8` 瑙ｇ爜锛屽畬鎴愮湡瀹炴墦鍖呬骇鐗╂棩蹇楅獙鏀朵笌鍏ㄩ噺鍥炲綊銆?
## 鏀瑰姩鏂囦欢鍒楄〃

- `scripts/encoding_hook.py`
- `scripts/pyinstaller_entry.py`
- `scripts/pyinstaller_celery_entry.py`
- `backend.spec`
- `celery-worker.spec`
- `electron/main.js`
- `tests/unit/test_packaged_log_encoding.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `scripts/encoding_hook.py`锛氭柊澧?PyInstaller runtime hook锛岀粺涓€璁剧疆 `PYTHONUTF8=1` 涓?`PYTHONIOENCODING=utf-8`锛涗紭鍏堜娇鐢?`reconfigure()` 鍒囨崲鍒?UTF-8锛屼粎鍦ㄥ師鐢熸爣鍑嗘祦鍦烘櫙鍥為€€鍒?`TextIOWrapper`锛岄伩鍏嶇牬鍧?pytest 鎴栧紑鍙戞€佹崟鑾锋祦銆?- `scripts/pyinstaller_entry.py`锛氬喕缁撴ā寮忓叆鍙ｅ鍔?UTF-8 鍙屼繚闄╅€昏緫锛岀‘淇?backend.exe 鍗充娇鏈 runtime hook 鎺ョ锛屼篃浼氬湪鍚姩鏈€鏃╅樁娈靛垏鎹㈣緭鍑虹紪鐮併€?- `scripts/pyinstaller_celery_entry.py`锛氫负鎵撳寘 Worker 鍏ュ彛琛ュ悓鏍风殑 UTF-8 鍙屼繚闄╅€昏緫銆?- `backend.spec`锛氭敞鍐?`runtime_hooks=['scripts/encoding_hook.py']`锛屽苟灏?`('scripts/encoding_hook.py', 'scripts')` 绾冲叆鎵撳寘鏁版嵁銆?- `celery-worker.spec`锛氬悓鏍锋敞鍐?runtime hook锛屽苟灏?hook 鏂囦欢绾冲叆鎵撳寘鏁版嵁銆?- `electron/main.js`锛氫繚鐣?`PYTHONUTF8`銆乣PYTHONIOENCODING` 鐜鍙橀噺锛涘湪 `pipeLogs()` 涓 `child.stdout` / `child.stderr` 鏄惧紡璋冪敤 `setEncoding('utf8')`锛岄伩鍏?Node 榛樿鎸夋湰鍦颁唬鐮侀〉瑙ｇ爜瀛愯繘绋嬭緭鍑恒€?- `tests/unit/test_packaged_log_encoding.py`锛氭柊澧?runtime hook銆乥ackend/celery 鍏ュ彛缂栫爜鍒囨崲銆乻pec 娉ㄥ唽鍜?Electron 鏃ュ織绠￠亾鐨勫洖褰掓祴璇曘€?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞敼閫犮€佹墦鍖呴獙璇佸拰楠屾敹缁撴灉銆?
## 褰卞搷鑼冨洿

- PyInstaller backend / celery-worker 杩愯鏃惰緭鍑虹紪鐮?- Electron 涓昏繘绋嬪瀛愯繘绋嬫棩蹇楃殑瑙ｇ爜鏂瑰紡
- 鎵撳寘鐩稿叧 spec 閰嶇疆涓庣紪鐮佸洖褰掓祴璇?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`pyinstaller --noconfirm --distpath ./python-backend-dist backend.spec` 涓?`pyinstaller --noconfirm --distpath ./python-backend-dist celery-worker.spec`锛屾瀯寤烘垚鍔熴€?- 宸叉墽琛?`python-backend-dist/backend/backend.exe` 骞跺皢杈撳嚭閲嶅畾鍚戝埌 `startup-utf8.log`锛涙寜 UTF-8 璇诲彇鏃讹紝涓枃鏃ュ織姝ｅ父锛岃緭鍑哄寘鍚?`[浠诲姟娉ㄥ唽]`銆乣鉁?鍥炶皟鍦板潃宸茶缃甡銆乣鍚庣鍚姩瀹屾垚锛岀鍙? 8000`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `484 passed, 16 warnings`銆?- 宸插皾璇?`cd electron && npx electron .`锛屼絾褰撳墠鐜浠嶅洜 `platform_channel.cc(83): 鎷掔粷璁块棶 (0x5)` 鎻愬墠閫€鍑猴紝鏈畬鎴?GUI 渚ф渶缁堥獙鏀躲€?- PyInstaller 鏋勫缓闃舵浠嶆湁 `kombu.asynchronous.aws` 缂哄皯 `botocore` 鐨勮鍛婏紝浣嗕笉褰卞搷鏈疆缂栫爜淇缁撴灉銆?---

## 浠诲姟鎽樿

淇娴佺▼鎵ц鏃跺洜 `flow_params` 娈嬬暀璁板綍瀵艰嚧鍚屼竴搴楅摵閲嶅鎶曢€掗姝ヤ换鍔＄殑闂锛氳鍙栧瓨閲忓緟鎵ц璁板綍鍚庢寜搴楅摵鍘婚噸锛屼粎淇濈暀鏈€鏂颁竴鏉★紝鍏朵綑娈嬬暀璁板綍鏍囪涓?`skipped`銆?
## 鏀瑰姩鏂囦欢鍒楄〃

- `backend/services/execute_service.py`
- `tests/unit/test_execute_service.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `backend/services/execute_service.py`锛氭柊澧?`_娓呯悊搴楅摵娈嬬暀娴佺▼鍙傛暟璁板綍(...)`锛屽湪 `鍒涘缓鎵规()` 鐨勨€滆鍙栧凡鏈夊緟鎵ц flow_params鈥濆垎鏀腑锛屽姣忎釜搴楅摵鐨勫緟鎵ц璁板綍鎸?`id` 鍊掑簭鍘婚噸锛屼粎淇濈暀鏈€鏂颁竴鏉★紱鍏朵綑娈嬬暀璁板綍閫氳繃 `娴佺▼鍙傛暟鏈嶅姟瀹炰緥.鏇存柊(..., {"status": "skipped"})` 娓呯悊锛岄伩鍏嶅悓搴楅摵琚噸澶嶆姇閫掑涓姝ヤ换鍔°€?- `backend/services/execute_service.py`锛氫繚鎸佺┖涓婁笅鏂囨祦绋嬮€昏緫涓嶅彉锛沗input_set_id` 瑙﹀彂鐨勮緭鍏ラ泦鍏煎 `flow_params` 鍒涘缓鍒嗘敮涓嶈蛋鏈娈嬬暀娓呯悊锛岄伩鍏嶅奖鍝嶈緭鍏ラ泦涓€娆＄敓鎴愬鏉′笂涓嬫枃鐨勭幇鏈夎兘鍔涖€?- `tests/unit/test_execute_service.py`锛氳皟鏁?barrier 棣栨鍦烘櫙鐨勬棫棰勬湡锛屾敼涓烘柇瑷€娈嬬暀璁板綍鍙繚鐣欐渶鏂颁竴鏉★紱鏂板闈?barrier 棣栨鍦烘櫙鍥炲綊锛岃鐩栤€滃悓搴楅摵涓ゆ潯寰呮墽琛岃褰曟椂鍙姇閫掍竴娆￠姝ヤ换鍔★紝骞跺皢鏃ц褰曠疆涓?`skipped`鈥濄€?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞敼閫犲唴瀹逛笌楠岃瘉缁撴灉銆?
## 褰卞搷鑼冨洿

- 娴佺▼妯″紡涓?`鍒涘缓鎵规()` 璇诲彇瀛橀噺 `flow_params` 鐨勫惎鍔ㄨ矾寰?- 鍚屽簵閾洪姝ヤ换鍔℃姇閫掓暟閲忎笌鎵规蹇収涓殑 `task_ids`
- 娴佺▼鎵ц鐩稿叧鍗曞厓娴嬭瘯

## 娉ㄦ剰浜嬮」

- 鏈疆淇鍙綔鐢ㄤ簬鈥滅洿鎺ヨ鍙栨暟鎹簱涓凡鏈夊緟鎵ц `flow_params`鈥濈殑鍒嗘敮锛屼笉褰卞搷 `input_set_id` 杈撳叆闆嗙敓鎴愬吋瀹?`flow_params` 鐨勮矾寰勩€?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_execute_service.py -q` 涓?`python -m pytest -c tests/pytest.ini tests/unit/test_batch_execute_shop_name.py -q`锛屽潎閫氳繃銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `485 passed, 16 warnings`銆?## 浠诲姟鎽樿

瀹屾垚娴佺▼缂栨帓寮圭獥閲嶆瀯锛氬皢姝ラ缂栬緫鍖轰粠澶у崱鐗囨敼涓虹揣鍑戣〃鏍艰甯冨眬锛屾斁澶у脊绐楀苟琛ラ綈鎷栨嫿鎻掑叆绾裤€佹柊澧炶鑱氱劍涓庨潤鎬佸洖褰掓祴璇曘€?## 鏀瑰姩鏂囦欢鍒楄〃

- `frontend/src/views/FlowManage.vue`
- `tests/unit/test_flow_manage_editor_static.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/views/FlowManage.vue`锛氬皢娴佺▼缂栬緫寮圭獥瀹藉害璋冩暣涓?`min(80vw, 900px)`锛屽苟鎶婃楠ょ紪杈戝尯閲嶆瀯涓虹揣鍑戣〃鏍艰甯冨眬锛涗繚鐣欑幇鏈夋祦绋嬩繚瀛?payload锛屼笉鏀瑰姩 API 璋冪敤锛涙柊澧炲師鐢熸嫋鎷芥彃鍏ョ嚎銆佹楠ゆ柊澧炲悗浠诲姟涓嬫媺鑷姩鑱氱劍锛屼互鍙婁繚瀛樺墠鈥滆嚦灏戜竴涓楠?/ 姣忔蹇呴』閫夋嫨浠诲姟鈥濈殑鏍￠獙銆?- `tests/unit/test_flow_manage_editor_static.py`锛氭柊澧為潤鎬佸洖褰掞紝瑕嗙洊寮圭獥灏哄銆佽〃鏍煎垪缁撴瀯銆佹嫋鎷芥彃鍏ョ嚎銆佽嚜鍔ㄨ仛鐒﹀拰淇濆瓨鍓嶆牎楠屾枃妗堬紝闃叉鍥為€€鍒版棫鐨勫ぇ鍗＄墖甯冨眬銆?- `PLAN.md`锛氬悓姝ユ湰杞脊绐楁敼閫犻」銆侀獙璇佸懡浠ゅ拰褰撳墠鏋勫缓闄愬埗銆?- `鏀归€犺繘搴?md`锛氬悓姝ヨ褰曟湰杞墠绔敼閫犲唴瀹广€侀獙璇佺粨鏋滃拰娉ㄦ剰浜嬮」銆?- `.pipeline/progress.md`锛氳褰曟湰杞?Builder 鎵ц缁撴灉銆?
## 褰卞搷鑼冨洿

- 娴佺▼绠＄悊椤典腑鐨勬祦绋嬫柊寤?/ 缂栬緫寮圭獥
- 娴佺▼姝ラ鎷栨嫿鎺掑簭涓庢柊澧炴楠や氦浜?- 鍓嶇闈欐€佸洖褰掓祴璇曡鐩栬寖鍥?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_frontend_display_details.py tests/unit/test_flow_manage_editor_static.py -v`锛岀粨鏋滀负 `4 passed`銆?- 宸叉墽琛?`npx --prefix frontend vue-tsc -b frontend/tsconfig.json`锛岄€氳繃銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `487 passed, 16 warnings`銆?- `npm --prefix frontend run build` 鍦ㄥ綋鍓嶇幆澧冧粛鍥?`vite` 鍚姩 `esbuild` 瀛愯繘绋嬫椂鎶?`spawn EPERM` 澶辫触锛屽睘浜庣幇鏈夌幆澧冮檺鍒讹紝涓嶆槸鏈疆鏀瑰姩寮曞叆鐨勯棶棰樸€?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦版敼鍔紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

灏嗘祦绋嬬鐞嗛〉浠庘€滅粺璁″崱鐗?+ 娴佺▼鍗＄墖缃戞牸鈥濆帇缂╀负鈥滃崟琛岀粺璁?+ 绱у噾琛ㄦ牸鍒楄〃鈥濓紝鎻愬崌棣栧睆淇℃伅瀵嗗害骞朵繚鐣欏師鏈夌紪杈?鍒犻櫎鍏ュ彛銆?
## 鏀瑰姩鏂囦欢鍒楄〃

- `frontend/src/views/FlowManage.vue`
- `tests/unit/test_flow_manage_list_static.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/views/FlowManage.vue`锛氬垹闄ら《閮?`summary-grid` 缁熻鍗＄墖锛屾浛鎹负鍗曡 `inline-stats` 鏂囨锛涘垹闄?`flow-grid / flow-card` 鍗＄墖寮忔ā鏉垮垪琛紝鏀逛负 `flow-table` 绱у噾琛ㄦ牸锛涙柊澧?`getStepSummary(flow)` 鐢熸垚姝ラ鎽樿锛涙祦绋嬪悕绉版敼涓虹偣鍑诲嵆缂栬緫鐨勯摼鎺ワ紝姝ラ鏁版敼涓?`step-badge`锛屾搷浣滄寜閽缉涓?`btn-sm`锛屼互婊¤冻鈥?0 涓祦绋嬪敖閲忎竴灞忓彲瑙佲€濈殑鏂板瘑搴﹁姹傘€?- `tests/unit/test_flow_manage_list_static.py`锛氭柊澧為潤鎬佸洖褰掞紝瑕嗙洊鍗曡缁熻銆佽〃鏍煎垪缁撴瀯銆佹祦绋嬪悕绉伴摼鎺ユ墦寮€缂栬緫銆佹棫鍗＄墖绫诲悕绉婚櫎锛屼互鍙婅〃鏍肩揣鍑戞牱寮忓叧閿瓧锛岄槻姝㈠洖閫€銆?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞祦绋嬬鐞嗛〉鍒楄〃鍘嬬缉鏀归€犲拰楠岃瘉缁撴灉銆?
## 褰卞搷鑼冨洿

- 娴佺▼绠＄悊椤甸《閮ㄧ粺璁′俊鎭睍绀?- 娴佺▼妯℃澘鍒楄〃鐨勯灞忎俊鎭瘑搴︿笌浜や簰鍏ュ彛
- FlowManage 椤甸潰鐩稿叧闈欐€佸洖褰掕鐩栬寖鍥?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_frontend_display_details.py tests/unit/test_flow_manage_editor_static.py tests/unit/test_flow_manage_list_static.py -v`锛岀粨鏋滀负 `6 passed`銆?- 宸叉墽琛?`npx --prefix frontend vue-tsc -b frontend/tsconfig.json`锛岄€氳繃銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -q`锛岀粨鏋滀负 `489 passed, 16 warnings`銆?- 16 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery` 涓?`openpyxl` 鐨?`datetime.utcnow()` 寮冪敤鎻愮ず锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- 鏈疆鏈噸鏂版墽琛?`npm --prefix frontend run build`锛涘綋鍓嶇幆澧冩鍓嶅凡鐭ュ瓨鍦?`esbuild` 瀛愯繘绋?`spawn EPERM` 闄愬埗銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦版敼鍔紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

杩涗竴姝ュ帇缂╂祦绋嬬紪鎺掑脊绐楀唴鐨勬楠よ〃鏍艰楂樺害鍜屾帶浠跺昂瀵革紝璁?6 姝ユ祦绋嬫洿瀹规槗鍦ㄥ脊绐楀唴涓€灞忔樉绀恒€?
## 鏀瑰姩鏂囦欢鍒楄〃

- `frontend/src/views/FlowManage.vue`
- `tests/unit/test_flow_manage_editor_static.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/views/FlowManage.vue`锛氭寜浠诲姟缁欏畾鏁板€兼敹绱ф楠ゅ尯鏍峰紡锛屽皢 `.step-row` 璋冩暣涓?`min-height: 40px`銆乣padding: 2px 6px`銆乣border-radius: 8px`锛屽皢鐩搁偦姝ラ闂磋窛鍘嬪埌 `1px`锛涘皢 `.step-table-header` 鍘嬬缉涓?`36px` 楂樺害锛涘皢姝ラ鍖鸿緭鍏ユ鍜屼笅鎷夋楂樺害缁熶竴璋冧负 `32px` 涓斿渾瑙掍负 `6px`锛涘悓姝ョ缉灏忔嫋鎷芥墜鏌勫拰鍒犻櫎鎸夐挳灏哄锛屽噺灏戝脊绐楀唴鍨傜洿鍗犵敤锛屽悓鏃朵繚鐣欑幇鏈夋嫋鎷姐€佷笅鎷夈€乧heckbox 鍜屽垹闄や氦浜掗€昏緫涓嶅彉銆?- `tests/unit/test_flow_manage_editor_static.py`锛氭柊澧炴牱寮忓瘑搴﹂潤鎬佸洖褰掞紝瑕嗙洊姝ラ琛ㄥご楂樺害銆佹楠よ楂樺害銆佺浉閭昏闂磋窛銆佹楠ゅ尯鎺т欢楂樺害銆佹嫋鎷芥墜鏌勫昂瀵稿拰鍒犻櫎鎸夐挳灏哄锛岄槻姝㈡牱寮忓洖閫€銆?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞楠ゅ尯鍘嬬缉鏀归€犲拰楠岃瘉缁撴灉銆?
## 褰卞搷鑼冨洿

- 娴佺▼绠＄悊椤垫祦绋嬬紪杈戝脊绐楃殑姝ラ琛ㄦ牸鍖鸿瑙夊瘑搴?- 6 姝ュ強浠ヤ笂娴佺▼鍦ㄧ紪杈戝脊绐楀唴鐨勫彲瑙佹€?- FlowManage 椤甸潰鐩稿叧闈欐€佸洖褰掕鐩栬寖鍥?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_frontend_display_details.py tests/unit/test_flow_manage_editor_static.py tests/unit/test_flow_manage_list_static.py -v`锛岀粨鏋滀负 `7 passed`銆?- 宸叉墽琛?`npx --prefix frontend vue-tsc -b frontend/tsconfig.json`锛岄€氳繃銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -q`锛岀粨鏋滀负 `490 passed, 16 warnings`銆?- 16 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery` 涓?`openpyxl` 鐨?`datetime.utcnow()` 寮冪敤鎻愮ず锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- 鏈疆浠呰皟鏁村墠绔牱寮忓瘑搴︼紝鏈敼鍔ㄦ祦绋嬩繚瀛?payload銆佹嫋鎷芥帓搴忛€昏緫鎴栧悗绔?API銆?- 鏈疆鏈噸鏂版墽琛?`npm --prefix frontend run build`锛涘綋鍓嶇幆澧冩鍓嶅凡鐭ュ瓨鍦?`esbuild` 瀛愯繘绋?`spawn EPERM` 闄愬埗銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦版敼鍔紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

灏嗘壒閲忔墽琛岄〉鍜屽畾鏃朵换鍔￠〉缁熶竴鏀逛负绱у噾琛ㄦ牸甯冨眬锛氭壒閲忔墽琛岀姸鎬佸尯琛ㄦ牸鍖栧苟鏀寔璇︽儏灞曞紑锛屽畾鏃朵换鍔″垪琛ㄦ敼涓哄紑鍏?+ 琛ㄦ牸锛屽苟鎶婂脊绐楀昂瀵镐笌娴佺▼绠＄悊椤靛榻愩€?
## 鏀瑰姩鏂囦欢鍒楄〃

- `frontend/src/views/BatchExecute.vue`
- `frontend/src/views/ScheduleManage.vue`
- `tests/unit/test_batch_execute_schedule_static.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/views/BatchExecute.vue`锛氱Щ闄ら〉闈㈠ `BatchStatusPanel` 鐨勪緷璧栵紝鍦ㄩ〉闈㈠唴鐩存帴瀹炵幇鐘舵€佽〃鏍硷紱鏂板鎵规鍗曡姹囨€绘枃妗堛€佸簵閾烘墽琛岀姸鎬佸僵鑹叉爣绛俱€佽繘搴︽潯銆佽€楁椂鍒楀拰鈥滄煡鐪嬭鎯呪€濆睍寮€姝ラ鏄庣粏锛涗繚鐣欏乏渚ф墽琛岄厤缃潰鏉裤€佹壒閲忓惎鍔?鍋滄閫昏緫鍜?SSE 鐘舵€佹祦涓嶅彉銆?- `frontend/src/views/ScheduleManage.vue`锛氬垹闄?`schedule-grid / schedule-card` 鍗＄墖寮忓垪琛紝鏀逛负 `schedule-table`锛涙柊澧炲紑鍏冲垪鐢ㄤ簬鍚敤/绂佺敤璁″垝锛屼换鍔″悕绉版敮鎸佺偣鍑昏繘鍏ョ紪杈戯紝鐩爣搴楅摵鏁版敼涓虹揣鍑?badge锛涢《閮ㄧ粺璁″尯鍘嬫垚鍗曡 `inline-stats`锛涘皢鏂板缓/缂栬緫寮圭獥瀹藉害璋冩暣涓?`min(80vw, 900px)` 骞堕€氳繃 `:deep(.modal-container)` 闄愬埗鍒?`80vh`銆?- `tests/unit/test_batch_execute_schedule_static.py`锛氭柊澧為潤鎬佸洖褰掞紝瑕嗙洊鎵归噺鎵ц椤佃〃鏍肩粨鏋勩€佺姸鎬佹爣绛鹃鑹叉槧灏勩€佽繘搴︽潯鍜岃鎯呭叆鍙ｏ紝浠ュ強瀹氭椂浠诲姟椤佃〃鏍煎垪銆佸紑鍏虫帶浠躲€佸脊绐楀昂瀵稿拰鏃у崱鐗囩粨鏋勭Щ闄ゃ€?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞〉闈㈣〃鏍煎寲鏀归€犲拰楠岃瘉缁撴灉銆?
## 褰卞搷鑼冨洿

- 鎵归噺鎵ц椤电殑瀹炴椂鐘舵€佸睍绀轰笌姝ラ璇︽儏鏌ョ湅鍏ュ彛
- 瀹氭椂浠诲姟椤电殑鍒楄〃灞曠ず瀵嗗害銆佸惎鍋滀氦浜掑拰寮圭獥灏哄
- 鎵归噺鎵ц / 瀹氭椂浠诲姟鐩稿叧鍓嶇闈欐€佸洖褰掕鐩栬寖鍥?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_batch_execute_schedule_static.py tests/unit/test_frontend_management_page.py tests/unit/test_batch_execute_shop_name.py -v`锛岀粨鏋滀负 `13 passed`銆?- 宸叉墽琛?`npx --prefix frontend vue-tsc -b frontend/tsconfig.json`锛岄€氳繃銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -q`锛岀粨鏋滀负 `494 passed, 16 warnings`銆?- 棣栨鍏ㄩ噺鍥炲綊鏃讹紝`tests/unit/test_anti_detection.py::test_闅忔満寤惰繜鍦ㄨ寖鍥村唴` 鍑虹幇涓€娆¤皟搴︽姈鍔ㄥ鑷寸殑瓒呮椂锛涘崟娴嬪璺戦€氳繃锛岄殢鍚庡叏閲忓璺戦€氳繃锛屾湭鍙戠幇涓庢湰杞墠绔敼鍔ㄦ湁鍏崇殑绋冲畾澶辫触銆?- 16 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery` 涓?`openpyxl` 鐨?`datetime.utcnow()` 寮冪敤鎻愮ず锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- 鏈疆鏈墽琛?`npm --prefix frontend run build`锛涘綋鍓嶇幆澧冩鍓嶅凡鐭ュ瓨鍦?`esbuild` 瀛愯繘绋?`spawn EPERM` 闄愬埗銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦版敼鍔紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

缁?SPA 鍥為€€鍒?`index.html` 鐨勫搷搴斿鍔犵缂撳瓨澶达紝纭繚 Electron 閲嶅惎鍚庤兘鎷垮埌鏈€鏂板墠绔〉闈紝鑰屼笉褰卞搷 `/assets/` 鐨?hash 闈欐€佽祫婧愮紦瀛樸€?
## 鏀瑰姩鏂囦欢鍒楄〃

- `backend/main.py`
- `tests/unit/test_startup_entry.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `backend/main.py`锛氬湪 `鎸傝浇鍓嶇闈欐€佽祫婧?...)` 涓紝淇濇寔瀹為檯瀛樺湪鐨勯潤鎬佹枃浠跺拰 `/assets/` 璧勬簮缁х画鐩存帴杩斿洖鍘熷 `FileResponse`锛涗粎鍦ㄦ墍鏈夐潪 API 璺緞鍥為€€鍒?`index.html` 鏃讹紝涓哄搷搴旇拷鍔?`Cache-Control: no-cache, no-store, must-revalidate`銆乣Pragma: no-cache` 鍜?`Expires: 0`锛岄伩鍏?Electron 鎴栨祻瑙堝櫒澶嶇敤杩囨湡鐨?HTML 鍏ュ彛銆?- `tests/unit/test_startup_entry.py`锛氳ˉ鍏?SPA 棣栭〉鍥為€€鍝嶅簲澶存柇瑷€锛屽悓鏃剁‘璁?`/assets/app.js` 鏈鍐欏叆鍚屾牱鐨勭缂撳瓨澶达紝闃叉璇激鍙畨鍏ㄧ紦瀛樼殑 hash 闈欐€佽祫婧愩€?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞悗绔叆鍙ｇ紦瀛樺ご鏀归€犲拰楠岃瘉缁撴灉銆?
## 褰卞搷鑼冨洿

- FastAPI 鎸傝浇鍓嶇闈欐€佽祫婧愭椂鐨?SPA 鍥為€€璺緞
- Electron 閲嶅惎鍚庡墠绔?`index.html` 鐨勭紦瀛樼瓥鐣?- 鍚姩鍏ュ彛鐩稿叧鍥炲綊娴嬭瘯瑕嗙洊鑼冨洿

## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_startup_entry.py -v`锛岀粨鏋滀负 `4 passed`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -q`锛岀粨鏋滀负 `494 passed, 16 warnings`銆?- 16 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery` 涓?`openpyxl` 鐨?`datetime.utcnow()` 寮冪敤鎻愮ず锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- 鏈疆鍙敼鍚庣 `index.html` 鍥為€€鍝嶅簲澶达紝娌℃湁淇敼 `/assets/` 闈欐€佽祫婧愮紦瀛樼瓥鐣ワ紝涔熸病鏈夎皟鏁村墠绔瀯寤轰骇鐗╂湰韬€?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦版敼鍔紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

瀹屾垚 SPA 鍥為€€绂佺紦瀛樻敹鍙ｃ€丷edis 杩炴帴姹犲崟渚嬪鐢ㄥ拰 PyInstaller 鍐荤粨浠诲姟妯″潡娓呭崟鑷姩鐢熸垚锛屽苟琛ラ綈瀵瑰簲鍥炲綊娴嬭瘯銆?
## 鏀瑰姩鏂囦欢鍒楄〃

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
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `backend/main.py`锛氬湪 `鎸傝浇鍓嶇闈欐€佽祫婧?...)` 涓户缁繚鎸佺湡瀹為潤鎬佹枃浠跺拰 `/assets/` 璧勬簮鐩存帴杩斿洖鍘熷 `FileResponse`锛涗粎鍦ㄦ墍鏈夐潪 API 璺緞鍥為€€鍒?`index.html` 鏃讹紝鏄惧紡鎸囧畾 `media_type="text/html"`锛屽苟杩藉姞 `Cache-Control: no-cache, no-store, must-revalidate`銆乣Pragma: no-cache`銆乣Expires: 0`锛岄伩鍏?Electron 鎴栨祻瑙堝櫒澶嶇敤杩囨湡 HTML銆?- `backend/services/execute_service.py`锛氭柊澧炴ā鍧楃骇鍚屾 `redis.ConnectionPool` 涓庡紓姝?`redis.asyncio.ConnectionPool`锛沗鍚屾鑾峰彇Redis瀹㈡埛绔?)`銆佸彇娑堟爣璁扮浉鍏冲紓姝ュ嚱鏁板拰 `鎵ц鏈嶅姟` 鍐呴儴寮傛瀹㈡埛绔粺涓€鏀逛负澶嶇敤杩炴帴姹狅紱涓哄紓姝ヨ繛鎺ユ睜琛ュ厖鎸変簨浠跺惊鐜噸寤洪€昏緫锛岄伩鍏?pytest 澶?event loop 澶嶇敤鏃ф睜瀵艰嚧鐨勫け璐ワ紱寮傛瀹㈡埛绔叧闂粺涓€鏀逛负 `await 瀹㈡埛绔?aclose()`銆?- `tasks/registry.py`锛氬垹闄ょ‖缂栫爜 `_FROZEN_TASK_MODULES`锛沠rozen 妯″紡涓嬫敼涓轰粠 `tasks._frozen_modules` 璇诲彇 `MODULES` 鍒楄〃锛岀己澶辨椂璁板綍 warning 骞惰繑鍥炵┖鍒楄〃锛涢潪 frozen 妯″紡缁х画閫氳繃 `pkgutil` 鍔ㄦ€佹壂鎻忋€?- `backend.spec`锛氬湪鏋勫缓闃舵鑷姩鎵弿 `tasks/` 鐩綍鐢熸垚 `tasks/_frozen_modules.py`锛屽苟鎶?`tasks._frozen_modules` 鍔犲叆 `hiddenimports`锛屽噺灏戞柊澧?task 鍚庢墜鍔ㄧ淮鎶ゅ喕缁撴ā鍧楀垪琛ㄧ殑椋庨櫓銆?- `.gitignore`锛氭柊澧?`tasks/_frozen_modules.py` 蹇界暐瑙勫垯锛岄伩鍏嶆瀯寤洪樁娈电敓鎴愭枃浠惰鎻愪氦銆?- `tests/unit/test_startup_entry.py`锛氳ˉ鍏?SPA 鍥為€€鍝嶅簲 `text/html` 涓庣缂撳瓨澶存柇瑷€锛屽悓鏃剁‘璁?`/assets/app.js` 鏈璇姞鍚屾牱鐨勭缂撳瓨澶淬€?- `tests/unit/test_execute_service.py`锛氳ˉ鍏呭悓姝?/ 寮傛 Redis 杩炴帴姹犲鐢ㄦ柇瑷€锛屽苟瑕嗙洊绌烘壒娆?ID 蹇€熻繑鍥炲拰鍙栨秷鏍囪鐩稿叧寮傛瀹㈡埛绔叧闂矾寰勩€?- `tests/unit/test_task_registry.py`锛氳ˉ鍏?frozen 妯″紡璇诲彇 `tasks._frozen_modules.MODULES` 鐨勫洖褰掞紝浠ュ強鐢熸垚鏂囦欢缂哄け鏃?warning + 绌哄垪琛ㄥ垎鏀€?- `tests/unit/test_pyinstaller_spec_files.py`锛氳ˉ鍏?`backend.spec` 鑷姩鐢熸垚 `_frozen_modules.py` 閫昏緫涓?`.gitignore` 蹇界暐椤圭殑闈欐€佹柇瑷€銆?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞?Builder 鎵ц缁撴灉涓庨獙璇佹儏鍐点€?
## 褰卞搷鑼冨洿

- FastAPI 鎸傝浇鍓嶇闈欐€佽祫婧愭椂鐨?SPA 鍥為€€鍏ュ彛缂撳瓨绛栫暐
- 鎵规鎵ц銆佸彇娑堟爣璁板拰鎵ц鏈嶅姟鍐呴儴鐨?Redis 杩炴帴澶嶇敤鏂瑰紡
- PyInstaller 鍐荤粨妯″紡涓?task 鑷姩鍙戠幇涓?`backend.spec` 鏋勫缓娴佺▼
- 鍚姩鍏ュ彛銆佹墽琛屾湇鍔°€佷换鍔℃敞鍐屽拰 spec 鏂囦欢鐩稿叧鍥炲綊娴嬭瘯瑕嗙洊鑼冨洿

## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_startup_entry.py tests/unit/test_execute_service.py tests/unit/test_task_registry.py tests/unit/test_task_registry_extension.py tests/unit/test_pyinstaller_spec_files.py -v`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -q`锛岀粨鏋滀负 `500 passed, 18 warnings`銆?- 18 鏉?warning 涓紝16 鏉′粛鏉ヨ嚜鏃㈡湁绗笁鏂逛緷璧?`celery` 涓?`openpyxl` 鐨?`datetime.utcnow()` 寮冪敤鎻愮ず锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- 鍙﹀ 2 鏉?warning 涓?`PytestUnraisableExceptionWarning`锛屾潵鑷?`tests/unit/test_task_service.py` 涓?Redis asyncio `StreamWriter.__del__` 鍦ㄤ簨浠跺惊鐜叧闂悗鐨勬竻鐞嗘椂鏈猴紝褰撳墠涓嶅奖鍝嶆祴璇曢€氳繃锛屼絾鍊煎緱鍚庣画鍗曠嫭澶勭悊銆?- 鏈疆鎸変换鍔¤姹傚彧璋冩暣浜?`backend.spec`锛屾湭鎵╁睍淇敼 `celery-worker.spec`銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦版敼鍔紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

瀹屾垚 `platform` 瀛楁杩佺Щ銆佸骞冲彴娉ㄥ唽鍩虹妗嗘灦銆佸钩鍙板垪琛ㄦ帴鍙ｅ拰鍓嶇鍏ㄥ眬骞冲彴鍒囨崲鍣紝骞惰搴楅摵鍒楄〃涓庢柊寤哄簵閾虹粦瀹氬綋鍓嶅钩鍙般€?
## 鏀瑰姩鏂囦欢鍒楄〃

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
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `backend/models/shop_model.py`銆乣backend/models/flow_model.py`锛氫负 `shops / flows` 澧炲姞 `platform` 瀛楁鍜岄粯璁ゅ€?`pdd`锛岃鏂板缓鏁版嵁澶╃劧甯﹀钩鍙板綊灞炪€?- `backend/models/database.py`锛氫负 `task_logs` 寤鸿〃 SQL 澧炲姞 `platform`锛涘垵濮嬪寲鏁版嵁搴撴椂琛ラ綈鏃у簱 `shops / flows / task_logs` 鐨?`platform` 瀛楁锛屽苟鎶婂巻鍙茬┖鍊煎洖濉负 `pdd`锛屼繚璇侀噸澶嶆墽琛?migration 涓嶆姤閿欍€?- `backend/models/data_structure.py`锛氬簵閾哄垱寤鸿姹傘€佸簵閾哄搷搴斻€佹祦绋嬪搷搴斻€佷换鍔℃棩蹇楀搷搴旇ˉ榻?`platform` 瀛楁锛屼繚鎸佹帴鍙ｇ粨鏋勫畬鏁淬€?- `backend/services/shop_service.py`銆乣backend/api/shop_api.py`锛氬簵閾哄垪琛ㄦ敮鎸?`platform` 鏌ヨ鍙傛暟杩囨护锛屾柊寤哄簵閾烘椂鍐欏叆褰掍竴鍖栧悗鐨?`platform`銆?- `backend/services/flow_service.py`銆乣backend/api/flow_api.py`锛氭祦绋嬪垪琛ㄦ敮鎸?`platform` 杩囨护锛屾柊寤烘祦绋嬮粯璁ゅ啓鍏?`platform='pdd'`銆?- `backend/api/platform_api.py`銆乣backend/api/router.py`锛氭柊澧?`GET /api/platforms` 骞舵敞鍐岃矾鐢憋紝鎺ュ彛閫氳繃缁熶竴 `鎴愬姛()` 鍝嶅簲杩斿洖骞冲彴娉ㄥ唽琛ㄣ€?- `platforms/`锛氭柊澧炲骞冲彴鍩虹娉ㄥ唽妗嗘灦鍜?`PddPlatform`锛屾彁渚?`register_platform / get_platform / list_platforms`锛屼负绗簩涓钩鍙版帴鍏ラ鐣欑粺涓€鍏ュ彛銆?- `frontend/src/api/types.ts`銆乣frontend/src/api/shops.ts`銆乣frontend/src/api/platforms.ts`锛氳ˉ榻愬墠绔?`platform` 绫诲瀷涓庡钩鍙版帴鍙ｅ皝瑁咃紝搴楅摵鍒楄〃 API 鏀寔甯?`platform` 鏌ヨ鍙傛暟銆?- `frontend/src/stores/platform.ts`銆乣frontend/src/components/PlatformSelector.vue`銆乣frontend/src/App.vue`锛氭柊澧炲叏灞€骞冲彴 store 涓庡钩鍙伴€夋嫨鍣紝渚ц竟鏍忔寕杞藉垏鎹㈠叆鍙ｏ紝褰撳墠骞冲彴鎸佷箙鍖栧埌 `localStorage.selectedPlatform`銆?- `frontend/src/views/ShopManage.vue`锛氬簵閾哄垪琛ㄦ寜褰撳墠骞冲彴鑷姩鍔犺浇锛屽钩鍙板垏鎹㈠悗鑷姩鍒锋柊锛涙柊寤哄簵閾烘椂鑷姩缁戝畾褰撳墠骞冲彴锛屼笉澧炲姞棰濆琛ㄥ崟椤广€?- `frontend/src/components/ShopCard.vue`锛氭敼鐢ㄧ粺涓€ `Shop` 绫诲瀷锛屾秷闄ゆ柊澧?`platform` 瀛楁鍚庣殑绫诲瀷鍒嗗弶銆?- `tests/unit/test_platform_backend.py`锛氭柊澧炲悗绔洖褰掞紝瑕嗙洊 migration 鍥炲～銆佸簵閾?娴佺▼骞冲彴杩囨护銆佸钩鍙版帴鍙ｄ互鍙婃湭娉ㄥ唽骞冲彴寮傚父璺緞銆?- `tests/unit/test_platform_frontend_static.py`锛氭柊澧炲墠绔潤鎬佸洖褰掞紝瑕嗙洊骞冲彴 API銆丳inia store銆佸叏灞€閫夋嫨鍣ㄥ拰搴楅摵椤垫帴绾裤€?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞钩鍙版敼閫犱笌楠岃瘉缁撴灉銆?
## 褰卞搷鑼冨洿

- `shops / flows / task_logs` 鐨勬暟鎹粨鏋勪笌鏃у簱鍗囩骇閫昏緫
- 搴楅摵鍒楄〃銆佹祦绋嬪垪琛ㄧ殑鎸夊钩鍙拌繃婊よ兘鍔?- 骞冲彴鍒楄〃鎺ュ彛鍜屾湭鏉ュ骞冲彴娉ㄥ唽鎵╁睍鍏ュ彛
- 鍓嶇鍏ㄥ眬骞冲彴鍒囨崲鐘舵€併€佸簵閾虹鐞嗛〉鏌ヨ鍜屾柊寤哄簵閾虹殑榛樿褰掑睘
- 骞冲彴鐩稿叧鍚庣/鍓嶇鍥炲綊娴嬭瘯瑕嗙洊鑼冨洿

## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_platform_backend.py tests/unit/test_platform_frontend_static.py tests/unit/test_shop_and_flow_api.py tests/unit/test_database_model.py tests/unit/test_frontend_management_page.py -v`锛岀粨鏋滀负 `19 passed`銆?- 宸叉墽琛?`npx --prefix frontend vue-tsc -b frontend/tsconfig.json`锛岄€氳繃銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `505 passed, 18 warnings`銆?- 褰撳墠 `GET /api/platforms` 鍙繑鍥?`pdd`锛屽悗缁柊澧炲钩鍙版椂鍙渶瑕佽ˉ鍏呭钩鍙版敞鍐屽疄鐜帮紝涓嶉渶瑕侀噸鍐欐帴鍙ｇ粨鏋勩€?- 18 鏉?warning 涓紝16 鏉′粛鏉ヨ嚜鏃㈡湁绗笁鏂逛緷璧?`celery` 涓?`openpyxl` 鐨?`datetime.utcnow()` 寮冪敤鎻愮ず锛屽彟澶?2 鏉′负鏃㈡湁 `PytestUnraisableExceptionWarning`锛屽潎涓嶆槸鏈疆鏀瑰姩寮曞叆鐨勯棶棰樸€?- 鏈疆鏈墽琛?`npm --prefix frontend run build`锛涘綋鍓嶇幆澧冩鍓嶅凡鐭ュ瓨鍦?`esbuild` 瀛愯繘绋?`spawn EPERM` 闄愬埗銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦版敼鍔紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

鏂板鎶栭煶鍜屾窐瀹濆钩鍙版敞鍐岋紝缁欏簵閾哄脊绐楄ˉ鎵€灞炲钩鍙伴€夋嫨锛屽苟鎶婂脊绐楀拰搴楅摵琛ㄥ崟鏀规垚鐏拌壊鏆楄壊涓婚涓庢柊鐨勫瘑鐮佸崰浣嶆枃妗堛€?
## 鏀瑰姩鏂囦欢鍒楄〃

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
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `platforms/__init__.py`锛氭柊澧?`platforms.douyin` 鍜?`platforms.taobao` 鐨勫鍏ワ紝璁╁钩鍙版敞鍐岃〃鍦ㄥ惎鍔ㄦ椂涓€娆℃€у姞杞戒笁涓钩鍙般€?- `platforms/douyin/__init__.py`銆乣platforms/douyin/platform.py`锛氭柊澧炴姈闊冲钩鍙板寘鍜?`DouyinPlatform`锛屾敞鍐?`douyin`銆佸浘鏍?`馃幍`銆佺櫥褰曞湴鍧€ `https://fxg.jinritemai.com/login/common`锛屽綋鍓嶄换鍔″垪琛ㄥ厛涓虹┖銆?- `platforms/taobao/__init__.py`銆乣platforms/taobao/platform.py`锛氭柊澧炴窐瀹濆钩鍙板寘鍜?`TaoBaoPlatform`锛屾敞鍐?`taobao`銆佸浘鏍?`馃煣`銆佺櫥褰曞湴鍧€ `https://myseller.taobao.com/`锛屽綋鍓嶄换鍔″垪琛ㄥ厛涓虹┖銆?- `frontend/src/views/ShopManage.vue`锛氭柊澧?`formPlatform` 浣滀负寮圭獥鍐呮墍灞炲钩鍙板€硷紱鏂板搴楅摵鏃堕粯璁よ窡闅忓叏灞€骞冲彴锛岀紪杈戞椂鏄剧ず宸叉湁骞冲彴骞剁鐢ㄤ笅鎷夛紱鏂板缓搴楅摵鎻愪氦鏀逛负浣跨敤 `formPlatform.value`锛涘熀鏈俊鎭尯椤堕儴鏂板鎵€灞炲钩鍙伴€夋嫨锛涗袱涓瘑鐮佽緭鍏ユ鍗犱綅绗︽敼涓?`鈥⑩€⑩€⑩€⑩€⑩€⑩€⑩€?/ 鈥⑩€⑩€⑩€⑩€⑩€⑩€⑩€紙鐣欑┖鍒欎笉淇敼锛塦锛涜〃鍗曡緭鍏ヨ儗鏅€佽竟妗嗗拰娆℃寜閽粠钃濊壊璋冩敼涓虹伆鑹叉殫鑹茬郴锛岃仛鐒﹁壊鏀逛负绱壊銆?- `frontend/src/components/Modal.vue`锛氬脊绐楀鍣ㄣ€乭eader銆乥ody銆乫ooter 浠庣櫧搴曟敼涓烘繁鐏拌壊涓婚锛岃竟妗嗘敼涓虹伆鑹诧紝鍏抽棴鎸夐挳 hover 鏀逛负鐏拌壊楂樹寒锛岀粺涓€鍘绘帀鏄庢樉钃濊壊璋冦€?- `tests/unit/test_platform_backend.py`锛氭洿鏂板钩鍙版帴鍙ｄ笌骞冲彴娉ㄥ唽琛ㄥ洖褰掞紝鏂█骞冲彴鍒楄〃鐜板湪鍖呭惈鎷煎澶氥€佹姈闊炽€佹窐瀹濄€?- `tests/unit/test_platform_frontend_static.py`锛氭洿鏂伴潤鎬佹柇瑷€锛屽簵閾洪〉鏂板缓搴楅摵缁戝畾骞冲彴鏀逛负 `formPlatform.value`銆?- `tests/unit/test_shop_platform_modal_static.py`锛氭柊澧為潤鎬佸洖褰掞紝瑕嗙洊搴楅摵寮圭獥鎵€灞炲钩鍙颁笅鎷夈€佹柊瀵嗙爜鍗犱綅鏂囨鍜?Modal 鐏拌壊涓婚鏍峰紡銆?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞?Builder 鎵ц缁撴灉涓庨獙璇佹儏鍐点€?
## 褰卞搷鑼冨洿

- 骞冲彴娉ㄥ唽琛ㄤ笌 `GET /api/platforms` 杩斿洖缁撴灉
- 鍓嶇鍏ㄥ眬骞冲彴鍒囨崲鍣ㄧ殑鍙€夊钩鍙版暟閲?- 搴楅摵绠＄悊椤垫柊澧?缂栬緫寮圭獥鐨勫钩鍙伴€夋嫨銆佸瘑鐮佸崰浣嶅拰琛ㄥ崟瑙嗚鏍峰紡
- 骞冲彴鐩稿叧鍚庣鍥炲綊涓庡簵閾哄脊绐楅潤鎬佸洖褰掕鐩栬寖鍥?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_platform_backend.py tests/unit/test_platform_frontend_static.py tests/unit/test_shop_platform_modal_static.py tests/unit/test_shop_restore.py tests/unit/test_frontend_display_details.py -v`锛岀粨鏋滀负 `11 passed`銆?- 宸叉墽琛?`npx --prefix frontend vue-tsc -b frontend/tsconfig.json`锛岄€氳繃銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `507 passed, 18 warnings`銆?- `GET /api/platforms` 鐜板湪杩斿洖 3 涓钩鍙帮細`鎷煎澶?/ 鎶栭煶 / 娣樺疂`銆?- 鏈疆鏈墽琛?`npm --prefix frontend run build`锛涘綋鍓嶇幆澧冩鍓嶅凡鐭ュ瓨鍦?`esbuild` 瀛愯繘绋?`spawn EPERM` 闄愬埗銆?- 18 鏉?warning 涓紝16 鏉′粛鏉ヨ嚜鏃㈡湁绗笁鏂逛緷璧?`celery` 涓?`openpyxl` 鐨?`datetime.utcnow()` 寮冪敤鎻愮ず锛屽彟澶?2 鏉′负鏃㈡湁 `PytestUnraisableExceptionWarning`锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦版敼鍔紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

鎶婂钩鍙板垏鎹㈠叆鍙ｄ粠 `App.vue` 渚ц竟鏍忕Щ鍒板簵閾虹鐞嗛〉 header锛屽苟鎶婄浉鍏抽厤鑹茬粺涓€鏀跺彛涓烘繁鐏?+ 绱壊楂樹寒锛屽悓鏃惰ˉ榻愬墠绔潤鎬佸洖褰掋€?
## 鏀瑰姩鏂囦欢鍒楄〃

- `frontend/src/App.vue`
- `frontend/src/views/ShopManage.vue`
- `frontend/src/components/PlatformSelector.vue`
- `tests/unit/test_platform_frontend_static.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/App.vue`锛氱Щ闄?`PlatformSelector` 鐨?import 鍜屼晶杈规爮鎸傝浇锛涗晶杈规爮鑳屾櫙銆佽竟妗嗐€佸鑸?hover 涓庢縺娲绘€佸叏閮ㄥ幓钃濆寲锛岀粺涓€鏀逛负娣辩伆 + 绱壊楂樹寒銆?- `frontend/src/views/ShopManage.vue`锛氬湪 header 鏂板 `header-actions` 涓?`platform-tabs` 鑳跺泭鎸夐挳缁勶紝鎶婂钩鍙板垏鎹㈠拰鈥滄柊澧炲簵閾衡€濇寜閽斁鍒板悓涓€琛岋紱鐐瑰嚮鎸夐挳鐩存帴璋冪敤 `platformStore.setPlatform(p.id)`锛沗onMounted` 鏀逛负鍏?`platformStore.loadPlatforms()` 鍐?`loadShops()`锛岄伩鍏嶇Щ闄や晶杈规爮鍚庡钩鍙版暟鎹湭鍒濆鍖栵紱澶撮儴鎸夐挳銆佹鎸夐挳銆佺┖鐘舵€佸拰绉诲姩绔?header 甯冨眬鍚屾鏀跺彛涓虹伆绱厤鑹层€?- `frontend/src/components/PlatformSelector.vue`锛氱粍浠朵繚鐣欎负澶囩敤锛屼絾杈撳叆妗嗚儗鏅€佽竟妗嗗拰 focus 楂樹寒鏀逛负鐏扮传鑹茬郴锛岀Щ闄ゅ師鏈夎摑鑹茶皟銆?- `tests/unit/test_platform_frontend_static.py`锛氶潤鎬佸洖褰掓敼涓烘柇瑷€ `App.vue` 涓嶅啀鎸傝浇 `PlatformSelector`锛屽苟鏂板搴楅摵椤?header 骞冲彴鎸夐挳缁勩€佸钩鍙板垏鎹㈣皟鐢ㄥ拰鐏扮传涓婚鏍峰紡鏂█銆?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞墠绔敼閫犱笌楠岃瘉缁撴灉銆?
## 褰卞搷鑼冨洿

- 渚ц竟鏍忎笌搴楅摵绠＄悊椤电殑鍓嶇骞冲彴鍒囨崲鍏ュ彛浣嶇疆
- 搴楅摵绠＄悊椤甸娆″姞杞藉钩鍙版暟鎹笌鎸夊钩鍙板埛鏂板垪琛ㄧ殑鍓嶇鏃跺簭
- 骞冲彴鐩稿叧鐏扮传涓婚鏍峰紡涓庨潤鎬佸洖褰掕鐩栬寖鍥?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_platform_frontend_static.py tests/unit/test_shop_platform_modal_static.py tests/unit/test_shop_restore.py tests/unit/test_frontend_management_page.py tests/unit/test_frontend_display_details.py -v`銆?- 宸叉墽琛?`npx --prefix frontend vue-tsc -b frontend/tsconfig.json`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `508 passed, 18 warnings`銆?- `PlatformSelector.vue` 褰撳墠浠呬綔涓哄鐢ㄧ粍浠朵繚鐣欙紝涓嶅啀鍦?`App.vue` 涓娇鐢ㄣ€?- 18 鏉?warning 涓紝16 鏉′粛鏉ヨ嚜鏃㈡湁绗笁鏂逛緷璧?`celery` 涓?`openpyxl` 鐨?`datetime.utcnow()` 寮冪敤鎻愮ず锛屽彟澶?2 鏉′负鏃㈡湁 `PytestUnraisableExceptionWarning`锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦版敼鍔紝鏈疆鏈慨鏀广€?
---
## 浠诲姟鎽樿

瀹屾垚鍓嶇 Tailwind 鏍峰紡鍩哄缓鎺ュ叆锛岀Щ闄ゆ棫 CSS 鍙橀噺鍏ュ彛鍜?Vite 榛樿绀轰緥缁勪欢锛屽苟琛ラ綈瀵瑰簲闈欐€佸洖褰掓祴璇曘€?
## 鏀瑰姩鏂囦欢鍒楄〃

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vite.config.ts`
- `frontend/src/style.css`
- `frontend/src/main.ts`
- `frontend/src/styles/variables.css`
- `frontend/src/components/HelloWorld.vue`
- `tests/unit/test_frontend_tailwind_static.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/package.json`銆乣frontend/package-lock.json`锛氭柊澧?`tailwindcss`銆乣@tailwindcss/vite`銆乣@headlessui/vue` 渚濊禆锛屽苟鍚屾閿佸畾瀹夎缁撴灉銆?- `frontend/vite.config.ts`锛氫负 Vite 澧炲姞 `tailwindcss()` 鎻掍欢锛屽悓鏃朵繚鐣欏師鏈夊紑鍙戠鍙ｅ拰 `/api` 浠ｇ悊閰嶇疆銆?- `frontend/src/style.css`锛氭浛鎹负 Tailwind v4 鐨?`@import "tailwindcss";` 鍏ュ彛锛屽彧淇濈暀鍏ㄥ眬 `body` 瀛椾綋鍜屽瓧浣撳钩婊戝熀纭€鏍峰紡銆?- `frontend/src/main.ts`锛氬垹闄ゆ棫 `./styles/variables.css` 寮曞叆锛岃鍏ㄥ眬鏍峰紡鍙粠 Tailwind 鍏ュ彛鍔犺浇銆?- `frontend/src/styles/variables.css`銆乣frontend/src/components/HelloWorld.vue`锛氭寜浠诲姟瑕佹眰鍒犻櫎鏃?CSS 鍙橀噺鏂囦欢鍜?Vite 榛樿绀轰緥缁勪欢銆?- `tests/unit/test_frontend_tailwind_static.py`锛氭柊澧炲墠绔潤鎬佸洖褰掞紝瑕嗙洊 Tailwind 渚濊禆銆乂ite 鎻掍欢銆佸叏灞€鏍峰紡鍏ュ彛鍜屾棫鏂囦欢鍒犻櫎鐨勬甯?鍙嶅悜鏂█銆?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞换鍔″拰楠岃瘉缁撴灉銆?
## 褰卞搷鑼冨洿

- 鍓嶇 Vite 鏋勫缓閾捐矾涓庢牱寮忓叆鍙?- 鍏ㄥ眬 CSS reset 涓庨〉闈㈤粯璁ゅ瓧浣撳熀绾?- 鍚庣画 Headless UI 缁勪欢鎺ュ叆鐨勪緷璧栧墠缃潯浠?- 鍓嶇闈欐€佸洖褰掕鐩栬寖鍥?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_frontend_tailwind_static.py -v`锛岀粨鏋滀负 `2 passed`銆?- 宸叉墽琛?`cd frontend && npm run build`锛屾瀯寤洪€氳繃銆?- 宸插皾璇?`cd frontend && npm run dev -- --host 127.0.0.1`锛屽綋鍓嶇幆澧冧粛鍥?Node 瀛愯繘绋?`spawn EPERM` 鏃犳硶瀹屾垚 Vite dev server 鍚姩楠屾敹銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `510 passed, 18 warnings`銆?- 18 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery`銆乣openpyxl` 鐨勫純鐢ㄦ彁绀猴紝浠ュ強鏃㈡湁 `PytestUnraisableExceptionWarning`锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- 鏈疆鎸変换鍔¤姹傜Щ闄や簡鏃?CSS 鍙橀噺绯荤粺锛岀幇鏈夐〉闈腑澶ч噺渚濊禆 `var(--...)` 鐨勬牱寮忎細鏆傛椂澶辨晥锛岄〉闈㈠彉涓戝睘浜庨鏈熺幇璞°€?- 瀹夎渚濊禆鏃剁敱浜庡叏灞€ npm 缂撳瓨鐩綍鏉冮檺涓嶈冻锛屼娇鐢?`npm install ... --cache .npm-cache` 瀹屾垚锛屼复鏃剁紦瀛樼洰褰曞凡鍒犻櫎銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

鐢?Tailwind + Headless UI 瀹屾垚搴楅摵绠＄悊椤靛拰 6 涓腑绛夊鏉傚害椤甸潰鐨勭伆闃堕噸鍐欙紝绉婚櫎鐩稿叧 `<style>` 鍧楋紝骞跺悓姝ユ洿鏂伴潤鎬佸洖褰掓祴璇曘€?
## 鏀瑰姩鏂囦欢鍒楄〃

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
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/views/ShopManage.vue`锛氬皢椤甸潰 header 鏀跺彛涓烘爣棰樸€佸钩鍙拌兌鍥婃寜閽粍鍜屸€滄柊澧炲簵閾衡€濇寜閽悓鎺掑竷灞€锛涘簵閾哄垪琛ㄦ敼涓虹揣鍑戣鍒楄〃锛涘脊绐楄〃鍗曟敼鎴愮櫧搴曠伆闃惰緭鍏ユ牱寮忥紝骞舵妸鎵€灞炲钩鍙板垏鎹㈡垚 Headless UI `Listbox`锛屽悓鏃朵繚鎸佸師鏈?script 涓氬姟閫昏緫涓嶅彉銆?- `frontend/src/components/ShopCard.vue`锛氫粠澶у崱鐗囨敼鎴?Linear 椋庢牸琛岄」锛岀粺涓€灞曠ず搴楅摵鍚嶇О銆佽处鍙枫€佷唬鐞嗐€佺姸鎬佸拰鏂囨湰鍖栨搷浣滄寜閽紝鍑忓皯绾靛悜鍗犵敤銆?- `frontend/src/components/StatusBadge.vue`锛氭敹鍙ｄ负鏋佺畝 dot + text 褰㈠紡锛屽悓鏃跺吋瀹瑰簵閾虹姸鎬併€佷换鍔＄姸鎬佸拰鏃ュ織绾у埆锛屼笉鍐嶄繚鐣欐棫褰╄壊鍧楃姸鏍囩銆?- `frontend/src/components/PlatformSelector.vue`锛氭寜浠诲姟瑕佹眰鍒犻櫎锛屽钩鍙板垏鎹㈠叆鍙ｅ畬鍏ㄥ悎骞惰繘 `ShopManage.vue` 鐨?header銆?- `frontend/src/views/Settings.vue`锛氬垏鎴愮櫧搴曠伆杈规鍗＄墖甯冨眬锛岀粺涓€琛ㄥ崟銆佹寜閽拰鐘舵€佸潡鐨?Tailwind 椋庢牸銆?- `frontend/src/views/TaskMonitor.vue`锛氫换鍔＄瓫閫夊尯銆佺粺璁″尯鍜岃〃鏍煎叏閮ㄦ敼鎴愮伆闃跺崱鐗囦笌鏍囧噯琛ㄦ牸缁撴瀯锛屽幓鎺夋棫钃濊壊鏍峰紡鍜岄〉闈㈠唴 `<style>`銆?- `frontend/src/views/LogViewer.vue`锛氭棩蹇楃瓫閫夈€佸鍑哄叆鍙ｅ拰鏃ュ織琛ㄦ牸鏀逛负缁熶竴 Tailwind 缁撴瀯锛岃〃澶淬€佸窘鏍囧拰绌虹姸鎬佷笌鏂拌璁′繚鎸佷竴鑷淬€?- `frontend/src/views/TaskParamsManage.vue`锛氫粎閲嶅啓椤甸潰澹冲眰鍜屽垪琛ㄥ竷灞€锛屼繚鎸佸瓙 tab 涓氬姟閫昏緫涓庡瓙鏂囦欢涓嶅姩锛屾弧瓒虫湰杞换鍔¤寖鍥寸害鏉熴€?- `frontend/src/views/BatchExecute.vue`锛氬皢鎵规閰嶇疆鍜岀姸鎬佸尯鐩存帴鍐呰仈鍒伴〉闈腑锛岀粺涓€鎴愮伆闃跺崱鐗囥€佽〃鏍煎拰 badge 椋庢牸锛岄伩鍏嶇户缁緷璧栨棫鑹茬郴甯冨眬銆?- `frontend/src/views/BrowserManager.vue`锛氭祻瑙堝櫒閰嶇疆鍖恒€佸疄渚嬪垪琛ㄥ拰鐘舵€佸睍绀虹粺涓€鏀规垚 Tailwind 鍗＄墖涓庤〃鏍肩粨鏋勶紝绉婚櫎鏃?`<style>`銆?- `frontend/src/components/StatCard.vue`锛氭敼鎴愭瀬绠€鏁板瓧鍗＄墖锛屾爣棰樹娇鐢ㄦ祬鐏板皬瀛楋紝鎸囨爣浣跨敤 `font-mono` 澶у彿鏁板瓧銆?- `frontend/src/components/LogTable.vue`锛氭敼鎴愭爣鍑?Tailwind 鏃ュ織琛ㄦ牸锛屾椂闂村垪鍙冲榻愩€佺骇鍒垪浣跨敤娴呭簳 badge銆?- `frontend/src/components/BrowserStatus.vue`锛氭敼鎴愭瀬绠€ dot 鐘舵€佹寚绀哄櫒锛屽拰鍏朵粬鐘舵€佸睍绀虹粍浠朵繚鎸佷竴鑷淬€?- `tests/unit/test_platform_frontend_static.py`锛氭洿鏂板簵閾洪〉 header 骞冲彴鍒囨崲銆佽兌鍥婃寜閽粍鍜?Tailwind 缁撴瀯鏂█銆?- `tests/unit/test_shop_platform_modal_static.py`锛氭洿鏂板簵閾哄脊绐椼€佸钩鍙颁笅鎷夊拰鐧藉簳琛ㄥ崟鏍峰紡鐨勯潤鎬佹柇瑷€銆?- `tests/unit/test_shop_card_task_params_display.py`锛氭洿鏂板簵閾洪」鍜屼换鍔″弬鏁板睍绀虹殑绱у噾琛岀粨鏋勬柇瑷€銆?- `tests/unit/test_shop_restore.py`锛氭洿鏂板簵閾烘仮澶嶇浉鍏?UI 鍏ュ彛涓庢柊琛屽垪琛ㄧ粨鏋勬柇瑷€銆?- `tests/unit/test_task_params_page.py`锛氭洿鏂?`TaskParamsManage.vue` 鏂板崱鐗囧寲椤甸潰缁撴瀯鏂█銆?- `tests/unit/test_batch_execute_schedule_static.py`锛氭洿鏂?`BatchExecute.vue` 鍐呰仈閰嶇疆鍖恒€佺姸鎬佽〃鍜?Tailwind 缁撴瀯鏂█銆?- `tests/unit/test_frontend_tailwind_static.py`锛氳ˉ鍏呰繖鎵归〉闈㈠拰缁勪欢鈥滄棤 `<style>` 鍧椼€佷娇鐢?Tailwind class鈥?鐨勯潤鎬佺害鏉熴€?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞?Builder 鎵ц缁撴灉涓庨獙璇佹儏鍐点€?
## 褰卞搷鑼冨洿

- 搴楅摵绠＄悊椤电殑骞冲彴鍒囨崲銆佸垪琛ㄥ睍绀哄拰鏂板/缂栬緫搴楅摵寮圭獥
- 璁剧疆椤点€佷换鍔＄洃鎺ч〉銆佹棩蹇楁煡鐪嬮〉銆佷换鍔″弬鏁伴〉銆佹壒閲忔墽琛岄〉銆佹祻瑙堝櫒绠＄悊椤电殑缁熶竴鐏伴樁瑙嗚灞?- `ShopCard`銆乣StatusBadge`銆乣StatCard`銆乣LogTable`銆乣BrowserStatus` 绛夊墠绔叕鍏卞睍绀虹粍浠?- 鍓嶇闈欐€佸洖褰掍腑涓?Tailwind / Headless UI 缁撴瀯銆佲€滄棤钃濊壊鈥濅笌鈥滄棤 `<style>`鈥濈害鏉熺浉鍏崇殑鏂█

## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`cd frontend && npm run build`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `514 passed, 18 warnings`銆?- 18 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery`銆乣openpyxl` 鐨勫純鐢ㄦ彁绀猴紝浠ュ強鏃㈡湁 `PytestUnraisableExceptionWarning`锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- 鏈疆鏈噸鏂版墽琛?`cd frontend && npm run dev`锛涘綋鍓嶇幆澧冩鍓嶅凡鐭ュ瓨鍦?Vite `spawn EPERM` 闄愬埗銆?- `TaskParamsManage.vue` 鏈疆浠呰皟鏁撮〉闈㈠３灞傦紝瀛?tab 鏂囦欢鏈撼鍏ヤ慨鏀硅寖鍥淬€?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀广€?---

## 浠诲姟鎽樿

鐢?Tailwind + Headless UI 瀹屾垚 `FlowManage.vue`銆乣AftersaleConfig.vue`銆乣RuleManage.vue`銆乣ScheduleManage.vue` 4 涓鏉傞〉闈㈢殑閲嶅啓锛屽苟鍚屾鏇存柊瀵瑰簲闈欐€佸洖褰掓祴璇曘€?
## 鏀瑰姩鏂囦欢鍒楄〃

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
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/views/FlowManage.vue`锛氭妸娴佺▼鍒楄〃鍜岀紪杈戝脊绐楁敼涓?Tailwind 琛ㄦ牸缁撴瀯锛涗换鍔￠€夋嫨涓庡け璐ョ瓥鐣ユ敼鐢?Headless UI `Listbox`锛涗繚鐣欐柊澧炴楠よ仛鐒︺€佹嫋鎷芥帓搴忋€佸け璐ョ瓥鐣ラ噸璇曟鏁般€佸悓姝ュ睆闅滃拰鍚堝苟鎵ц閫昏緫锛涗负婊¤冻鈥滅Щ闄ゅ師鐢?select鈥濈害鏉燂紝灏嗚仛鐒﹀厹搴曟帶浠惰皟鏁翠负闅愯棌 `input`銆?- `frontend/src/views/AftersaleConfig.vue`锛氭妸搴楅摵鍒囨崲鏀逛负 `Listbox`锛涘皢鍞悗閰嶇疆琛ㄥ崟鎷嗕负澶氭 section锛涚櫧鍚嶅崟鏀逛负 `overflow-x-auto` 琛ㄦ牸锛涙爣绛惧綍鍏ョ粺涓€涓?Tailwind chip 缁撴瀯锛涘垹闄ゆ棫 `<style>`銆?- `frontend/src/views/RuleManage.vue`锛氱瓫閫夊櫒銆佽鍒欑紪杈戝櫒銆佸姩浣滅紪杈戝櫒鍜屾祴璇曞尮閰嶅叏閮ㄥ垏鍒?`Listbox`锛涘垪琛ㄦ敼涓?Tailwind 琛ㄦ牸锛涢〉闈㈢骇寮圭獥缁熶竴浣跨敤 Headless UI `Modal`锛涙寜浠诲姟瑕佹眰淇濈暀 `window.confirm` 鍒犻櫎纭锛屼笉鏀?script 涓氬姟閫昏緫銆?- `frontend/src/views/ScheduleManage.vue`锛氭妸鍒楄〃鍒囨垚琛ㄦ牸缁撴瀯锛涙祦绋嬨€佸苟鍙戞暟銆侀噸鍙犵瓥鐣ュ垏鍒?`Listbox`锛涜Е鍙戞ā寮忔敼鐢?Headless UI `TabGroup`锛涘簵閾哄閫変笌绌虹姸鎬佺粺涓€涓烘柊鐨?Tailwind 甯冨眬锛涘垹闄ゆ棫 `<style>`銆?- `tests/unit/test_flow_manage_editor_static.py`銆乣tests/unit/test_flow_manage_list_static.py`銆乣tests/unit/test_after_sale_config_page.py`銆乣tests/unit/test_rule_config_page.py`銆乣tests/unit/test_batch_execute_schedule_static.py`銆乣tests/unit/test_frontend_display_details.py`锛氭妸鏃?CSS / 鏃?modal 缁撴瀯鏂█鏇存柊涓烘柊鐨?Tailwind / Headless UI 缁撴瀯鏂█锛屽苟琛ュ厖鈥滄棤 `<style>` / 鏃犲師鐢?`<select>` / 浣跨敤 `Modal` / `Listbox` / `TabGroup`鈥濈瓑鍥炲綊鐐广€?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氬悓姝ヨ褰曟湰杞?Builder 鎵ц缁撴灉涓庨獙璇佹儏鍐点€?
## 褰卞搷鑼冨洿

- 娴佺▼妯℃澘绠＄悊椤电殑鍒楄〃銆佺紪杈戝脊绐楀拰鎷栨嫿姝ラ缂栨帓
- 鍞悗閰嶇疆椤电殑搴楅摵鍒囨崲銆佺櫧鍚嶅崟閰嶇疆鍜屽鍒嗘琛ㄥ崟甯冨眬
- 瑙勫垯閰嶇疆椤电殑绛涢€夊櫒銆佽鍒欑紪杈戙€佹祴璇曞尮閰嶅拰寮圭獥鎵胯浇鏂瑰紡
- 瀹氭椂浠诲姟椤电殑鍒楄〃銆佺紪杈戝脊绐椼€佽Е鍙戞ā寮忓垏鎹㈠拰搴楅摵澶氶€?- 鐩稿叧鍓嶇闈欐€佸洖褰掓祴璇曡鐩栬寖鍥?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_flow_manage_editor_static.py tests/unit/test_flow_manage_list_static.py tests/unit/test_after_sale_config_page.py tests/unit/test_rule_config_page.py tests/unit/test_batch_execute_schedule_static.py tests/unit/test_frontend_display_details.py -q`锛岀粨鏋滀负 `17 passed`銆?- 宸叉墽琛?`cd frontend && npm run build`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `514 passed, 18 warnings`銆?- 18 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery`銆乣openpyxl` 鍜屾棦鏈?`PytestUnraisableExceptionWarning`锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- 鏈疆鏈墽琛?`cd frontend && npm run dev`锛涘綋鍓嶇幆澧冩鍓嶅凡鐭ュ瓨鍦?Vite `spawn EPERM`銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀广€?---

## 浠诲姟鎽樿

瀹屾垚搴楅摵绠＄悊椤点€佷换鍔″弬鏁伴〉鍙婂叧鑱斾腑澶嶆潅椤甸潰鐨勫搧鐗岃壊缁熶竴锛屾竻鐞嗘棫 `task-params` CSS 娈嬬暀锛岃ˉ榻愬搴旈潤鎬佸洖褰掞紝骞剁ǔ瀹氬寲涓€涓嫭绔嬬殑瓒呯煭寤惰繜娴嬭瘯銆?
## 鏀瑰姩鏂囦欢鍒楄〃

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
- `frontend/src/components/ShopCard.vue`锛堝垹闄わ級
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
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/views/TaskParamsManage.vue` 涓?`frontend/src/views/task-params/*`
  - 缁熶竴绛涢€夊尯銆乼ab銆佸垎椤点€佽〃澶淬€佺┖鐘舵€佸拰 tooltip 鐨?`brand-*` 閰嶈壊
  - 琛ュ厖 `switch-slider`銆乣step-result-tag` 鍏煎鏍囪锛岄伩鍏嶉潤鎬佸洖褰掍笌鐜版湁缁撴瀯鑴辫妭
- `frontend/src/views/ShopManage.vue`
  - 淇濇寔骞冲彴涓嬫媺妗嗘柟妗堬紝浣跨敤 `table` 淇琛ㄥご涓庤鍐呭瀵归綈闂
  - 琛ㄥ崟杈撳叆銆佹爣绛俱€佹鎸夐挳鍜屽脊绐楁搷浣滃尯缁熶竴鍒板搧鐗岃壊浣撶郴
- `frontend/src/components/Modal.vue`銆乣ConfirmDialog.vue`銆乣StatusBadge.vue`銆乣LogTable.vue`銆乣BrowserStatus.vue`
  - 灏嗗脊绐椼€佹彁绀恒€佺姸鎬佸窘鏍囧拰琛ㄦ牸鏀拺缁勪欢鏀瑰埌鍚屼竴濂楃伆钃濆搧鐗岄鏍?- `frontend/src/views/FlowManage.vue`銆乣ScheduleManage.vue`銆乣Settings.vue`銆乣TaskMonitor.vue`銆乣LogViewer.vue`銆乣BatchExecute.vue`銆乣BrowserManager.vue`
  - 娓呮帀娈嬬暀鏃х伆鑹蹭氦浜掕壊锛岀粺涓€杈规銆乭over銆乥adge銆佽〃澶村拰绌虹姸鎬?- `frontend/src/components/ShopCard.vue`
  - 鐢变簬宸叉棤寮曠敤锛屾寜浠诲姟鍗曞厑璁哥殑鑼冨洿鐩存帴鍒犻櫎锛岄伩鍏嶆棫瀹炵幇缁х画骞叉壈
- `tests/unit/*.py`
  - 灏嗛潤鎬佹柇瑷€鍒囨崲鍒版柊鐨?`brand-*` 缁撴瀯
  - 璁╂祴璇曟樉寮忔牎楠屾棫 `task-params` CSS 鏂囦欢宸插垹闄?  - 灏?`tests/unit/test_anti_detection.py` 鏀逛负浣跨敤 `time.perf_counter()`锛屽苟鏀惧 Windows 涓?10~20ms sleep 鐨勮皟搴﹀宸?
## 褰卞搷鑼冨洿

- 搴楅摵绠＄悊椤电殑鍒楄〃灞曠ず銆佸钩鍙板垏鎹€佸脊绐楄〃鍗曞拰鐘舵€佹爣璇?- 浠诲姟鍙傛暟绠＄悊椤靛強鍏朵换鍔″垪琛?缁撴灉鍒楄〃/娴佺▼鍙傛暟瀛愮粍浠?- Flow / Schedule / Settings / TaskMonitor / LogViewer / BatchExecute / BrowserManager 鐨勮瑙夌粺涓€鎬?- 鍓嶇闈欐€佸洖褰掑鏂板搧鐗岃壊銆佹繁鑹蹭晶鏍忋€佽〃鏍肩洿鍑哄拰鏃?CSS 鍒犻櫎鐘舵€佺殑鏂█
- 涓€涓嫭绔嬬殑娴忚鍣ㄥ弽妫€娴嬪欢杩熸祴璇曠殑绋冲畾鎬?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`cd frontend && npm run build`
- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/ -v`锛岀粨鏋滀负 `514 passed, 18 warnings`
- 18 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery`銆乣openpyxl` 涓庢棦鏈?`PytestUnraisableExceptionWarning`
- 鏃?`frontend/src/views/task-params/*.css` 鏂囦欢鏈疆纭宸蹭笉瀛樺湪锛屾簮鐮佷腑涔熸棤娈嬬暀寮曠敤
- 褰撳墠鐜姝ゅ墠宸茬煡瀛樺湪 `npm run dev` 鐨?`spawn EPERM`锛屾湰杞湭鎵ц dev server 楠屾敹

---

## 浠诲姟鎽樿

瀹屾垚 CSV 瀵煎叆寮圭獥鐨?Tailwind 閲嶅啓锛屽苟鎶婂彈褰卞搷寮圭獥/琛ㄥ崟椤电殑鏍囩涓庤鏄庢枃瀛楀姞娣卞埌浠诲姟鍗曡姹傜殑鐏伴樁銆?
## 鏀瑰姩鏂囦欢鍒楄〃

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
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `frontend/src/views/task-params/ImportCsvModal.vue`锛氬垹闄ゆ棫 `<style scoped>`锛屾寜浠诲姟鍗曟敼涓虹函 Tailwind 缁撴瀯锛涚粦瀹氭柟寮忔寜閽垏鍒伴€変腑娣辫壊 / 鏈€変腑鐧藉簳鎻忚竟锛涗换鍔?娴佺▼涓嬫媺浣跨敤娓呮櫚鐨?`border-brand-300`锛涙ā鏉胯鏄庢銆佷笅杞芥ā鏉挎寜閽€佹枃浠朵笂浼犳寜閽拰 footer 鎿嶄綔鍖虹粺涓€鍒版柊鍝佺墝椋庢牸銆?- `frontend/src/components/Modal.vue`锛氬脊绐楁鏂囬粯璁ゆ枃瀛楁敼涓?`text-gray-700`锛岃璇存槑鏂囨姣斾箣鍓嶆洿娣变竴妗ｃ€?- `frontend/src/components/ConfirmDialog.vue`锛氱‘璁ゅ脊绐楁鏂囪鏄庢枃瀛楀悓姝ユ敼鍒?`text-gray-700`銆?- `frontend/src/views/AftersaleConfig.vue`銆乣frontend/src/views/RuleManage.vue`锛氬皢寮圭獥/琛ㄥ崟鏍囩鏂囧瓧浠?`text-gray-600` 鏀跺彛鍒?`text-gray-800`锛屼粎璋冩暣瑙嗚灞傦紝涓嶆敼涓氬姟閫昏緫銆?- `tests/unit/test_headless_ui_components_static.py`銆乣tests/unit/test_flow_params_import_static_page.py`銆乣tests/unit/test_task_params_dynamic_type.py`銆乣tests/unit/test_after_sale_config_page.py`銆乣tests/unit/test_rule_config_page.py`锛氬悓姝ユ洿鏂伴潤鎬佸洖褰掞紝瑕嗙洊鏂板鍏ュ脊绐楃粨鏋勩€佸幓闄?`<style>`銆佹枃浠朵笂浼犳寜閽牱寮忎互鍙婃爣绛剧伆闃跺彉鏇淬€?- `frontend/src/style.css`锛氬凡澶嶆牳褰撳墠鍐风伆钃?`brand-*` 鑹叉澘涓庝换鍔″崟涓€鑷达紝鏈疆鏈啀淇敼婧愮爜銆?
## 褰卞搷鑼冨洿

- 浠诲姟鍙傛暟绠＄悊椤电殑 CSV 瀵煎叆寮圭獥瑙嗚涓庡彲璇绘€?- 鍏叡寮圭獥姝ｆ枃榛樿璇存槑鏂囧瓧
- 鍞悗閰嶇疆椤典笌瑙勫垯閰嶇疆椤典腑鐨勮〃鍗?寮圭獥鏍囩灞?- 鍓嶇闈欐€佸洖褰掍腑涓庡鍏ュ脊绐楃粨鏋勩€佹爣绛剧伆闃跺拰姝ｆ枃棰滆壊鐩稿叧鐨勬柇瑷€

## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_headless_ui_components_static.py tests/unit/test_flow_params_import_static_page.py tests/unit/test_task_params_dynamic_type.py tests/unit/test_after_sale_config_page.py tests/unit/test_rule_config_page.py -q`锛岀粨鏋滀负 `13 passed`銆?- 宸叉墽琛?`cd frontend && npm run build`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini -q`锛岀粨鏋滀负 `514 passed, 18 warnings`銆?- 18 鏉?warning 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery`銆乣openpyxl` 涓庢棦鏈?`PytestUnraisableExceptionWarning`锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦版敼鍔紝鏈疆鏈慨鏀广€?- 褰撳墠鐜姝ゅ墠宸茬煡瀛樺湪 `npm run dev` 鐨?`spawn EPERM`锛屾湰杞湭鎵ц dev server 楠屾敹銆?
---

## 浠诲姟鎽樿

绉婚櫎浠撳簱涓殑澶氬钩鍙版娊璞″眰锛屽垹闄ゅ钩鍙版敞鍐屾帴鍙ｄ笌鍓嶇骞冲彴鍒囨崲閾捐矾锛岃椤圭洰鍥炲綊鍗曞钩鍙?PDD 妯″紡锛屽悓鏃惰ˉ榻愬搴旂殑鍚庣銆佸墠绔潤鎬佸拰鍥炲綊娴嬭瘯銆?
## 鏀瑰姩鏂囦欢鍒楄〃

- `backend/api/platform_api.py`锛堝垹闄わ級
- `backend/api/router.py`
- `backend/api/shop_api.py`
- `frontend/src/api/platforms.ts`锛堝垹闄わ級
- `frontend/src/stores/platform.ts`锛堝垹闄わ級
- `frontend/src/api/types.ts`
- `frontend/src/api/shops.ts`
- `frontend/src/views/ShopManage.vue`
- `platforms/__init__.py`锛堝垹闄わ級
- `platforms/base/__init__.py`锛堝垹闄わ級
- `platforms/base/base_platform.py`锛堝垹闄わ級
- `platforms/douyin/__init__.py`锛堝垹闄わ級
- `platforms/douyin/platform.py`锛堝垹闄わ級
- `platforms/pdd/__init__.py`锛堝垹闄わ級
- `platforms/pdd/platform.py`锛堝垹闄わ級
- `platforms/taobao/__init__.py`锛堝垹闄わ級
- `platforms/taobao/platform.py`锛堝垹闄わ級
- `tests/unit/test_platform_backend.py`
- `tests/unit/test_platform_frontend_static.py`
- `tests/unit/test_shop_platform_modal_static.py`
- `tests/unit/test_shop_card_task_params_display.py`
- `tests/unit/test_shop_restore.py`
- `PLAN.md`
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `backend/api/platform_api.py`锛氬垹闄ゅ钩鍙板垪琛ㄦ帴鍙ｏ紱`/api/platforms` 涓嶅啀浣滀负鍙敤 API 鏆撮湶銆?- `backend/api/router.py`锛氱Щ闄?`platform_api` 鐨勫鍏ヤ笌璺敱娉ㄥ唽锛屽悗绔矾鐢卞叆鍙ｅ洖鏀朵负鍗曞钩鍙扮粨鏋勩€?- `backend/api/shop_api.py`锛氬垱寤哄簵閾烘椂涓嶅啀淇′换澶栭儴浼犲叆鐨?`platform`锛岀粺涓€鍥哄畾鍐欏叆 `platform="pdd"`锛岄伩鍏嶅崟骞冲彴鍦烘櫙涓嬪嚭鐜拌剰鏁版嵁銆?- `frontend/src/api/platforms.ts`銆乣frontend/src/stores/platform.ts`锛氬垹闄ゅ墠绔钩鍙?API 涓庡钩鍙扮姸鎬佷粨搴擄紝鍓嶇涓嶅啀缁存姢骞冲彴鍒楄〃鍜屽綋鍓嶅钩鍙颁笂涓嬫枃銆?- `frontend/src/api/types.ts`锛氬垹闄?`Platform` 鎺ュ彛锛屽苟浠?`ShopPayload` 涓Щ闄?`platform?: string`锛岃鍓嶇琛ㄥ崟杈撳叆涓庡崟骞冲彴妯″瀷涓€鑷淬€?- `frontend/src/api/shops.ts`锛氬皢 `listShops()` 鏀跺彛涓烘棤鍙傜増鏈紝缁熶竴璇锋眰 `/api/shops`锛屼笉鍐嶆惡甯﹀钩鍙扮瓫閫夈€?- `frontend/src/views/ShopManage.vue`锛氱Щ闄ら〉澶村钩鍙板垏鎹€佸脊绐椻€滄墍灞炲钩鍙扳€濆瓧娈点€乣usePlatformStore` 鐩稿叧鐘舵€佷笌璁＄畻灞炴€э紱椤甸潰鏂囨銆佺┖鐘舵€佸拰琛ㄥ崟甯冨眬璋冩暣涓哄崟骞冲彴 PDD 鐗堟湰銆?- `platforms/` 鐩綍锛氬垹闄?`base_platform` 娉ㄥ唽鎶借薄鍜?`douyin`銆乣taobao`銆乣pdd` 骞冲彴澹冲眰瀹炵幇锛屽交搴曠Щ闄ゅ骞冲彴鍩虹璁炬柦銆?- `tests/unit/test_platform_backend.py`锛氭敼涓洪獙璇?`/api/platforms` 宸蹭笉瀛樺湪锛屼互鍙婂簵閾哄垱寤哄嵆浣夸紶鍏ュ叾浠栧钩鍙颁篃浼氳鍥哄畾淇濆瓨涓?`pdd`銆?- `tests/unit/test_platform_frontend_static.py`銆乣tests/unit/test_shop_platform_modal_static.py`锛氭敼涓烘牎楠屽墠绔凡鍒犻櫎骞冲彴 store銆佸钩鍙?API銆佸钩鍙扮被鍨嬨€佸簵閾洪〉澶村钩鍙板垏鎹㈠拰寮圭獥骞冲彴瀛楁銆?- `tests/unit/test_shop_card_task_params_display.py`銆乣tests/unit/test_shop_restore.py`锛氬悓姝ユ竻鐞嗕笌澶氬钩鍙?UI 鐩稿叧鐨勯潤鎬佹柇瑷€锛屼繚鎸佸簵閾虹鐞嗛〉鍥炲綊绋冲畾銆?- `PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`锛氳ˉ鍏呰褰曟湰杞崟骞冲彴鍥炴敹鏀归€犮€侀獙璇佺粨鏋滀笌鐜闄愬埗璇存槑銆?
## 褰卞搷鑼冨洿

- 鍚庣 API 璺敱娉ㄥ唽涓庡簵閾哄垱寤哄叆鍙?- 鍓嶇搴楅摵绠＄悊椤电殑鏁版嵁鍔犺浇鏂瑰紡銆侀〉闈㈢粨鏋勪笌琛ㄥ崟瀛楁
- 澶氬钩鍙版娊璞＄洰褰曚笌骞冲彴娉ㄥ唽閾捐矾
- 涓庡钩鍙板垏鎹€佸钩鍙板瓧娈点€佸钩鍙?API 鐩稿叧鐨勫崟鍏冩祴璇曞拰闈欐€佸洖褰掓祴璇?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -c "from backend.api.router import 娉ㄥ唽鎵€鏈夎矾鐢? print('ok')"`锛屽鍏ラ獙璇侀€氳繃銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini tests/unit/test_platform_backend.py tests/unit/test_platform_frontend_static.py tests/unit/test_shop_platform_modal_static.py tests/unit/test_shop_card_task_params_display.py tests/unit/test_shop_restore.py -q`锛岀粨鏋滀负 `10 passed`銆?- 宸叉墽琛?`cd frontend && npm run build`銆?- 宸叉墽琛?`python -m pytest -c tests/pytest.ini -q`锛岀粨鏋滀负 `512 passed, 18 warnings`銆?- 宸叉墽琛?`rg -n "platformStore|usePlatformStore|listPlatforms|platform\.ts|from platforms|import platforms|import platform_api|platform_api|get_platform|list_platforms|register_platform|BasePlatform" backend frontend/src -g "*.py" -g "*.ts" -g "*.vue"`锛屾棤鍖归厤缁撴灉銆?- 淇濈暀 `shops`銆乣flows` 绛夋暟鎹〃涓殑 `platform` 鍒楋紝涓嶅仛鏁版嵁搴撹縼绉伙紝鍗曞钩鍙板浐瀹氬€间负 `pdd`銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀广€?- `python -m backend.main` 鍦ㄥ綋鍓嶇幆澧冨彲杩涘叆 Uvicorn 鍚姩娴佺▼锛屼絾鍚庣画鍙?Windows 鏉冮檺闄愬埗瑙﹀彂 `PermissionError: [WinError 5]`锛屾湭鑳藉畬鎴愯繍琛屾€侀獙鏀躲€?- `cd frontend && npm run dev -- --host 127.0.0.1` 鍦ㄥ綋鍓嶇幆澧冧粛瑙﹀彂 `spawn EPERM`锛屾湭鑳藉畬鎴?dev server 杩愯鎬侀獙鏀躲€?
---

## 浠诲姟鎽樿

瀹屾垚鈥滅Щ闄?`.env`銆佹敼鐢ㄦ暟鎹簱 `settings` 绠＄悊閰嶇疆銆佸鍔犲墠绔郴缁熻缃〉銆佺粺涓€鎵撳寘鑴辨晱鈥濈殑鏁磋疆鏀归€狅紝骞惰ˉ榻?Redis 闄嶇骇銆丳yInstaller 鍏ュ彛鍏煎涓庣浉鍏冲洖褰掓祴璇曘€?
## 鏀瑰姩鏂囦欢鍒楄〃

- 鍚庣閰嶇疆涓庤缃摼璺細`backend/models/settings_model.py`銆乣backend/utils/__init__.py`銆乣backend/utils/crypto.py`銆乣backend/utils/settings.py`銆乣backend/config.py`銆乣backend/models/database.py`銆乣backend/api/settings_api.py`銆乣backend/api/router.py`銆乣backend/services/system_service.py`
- 杩愯鏃跺吋瀹逛笌鏈嶅姟淇锛歚backend/models/__init__.py`銆乣backend/logging_config.py`銆乣backend/services/shop_service.py`銆乣backend/services/execute_service.py`銆乣backend/services/scheduled_execute_service.py`銆乣browser/user_dir_factory.py`銆乣pages/product_list_page.py`銆乣tasks/celery_app.py`銆乣scripts/pyinstaller_celery_entry.py`
- 鍓嶇璁剧疆椤碉細`frontend/src/api/settings.ts`銆乣frontend/src/api/types.ts`銆乣frontend/src/views/SystemSettings.vue`銆乣frontend/src/router/index.ts`銆乣frontend/src/App.vue`
- 鎵撳寘涓庤剼鏈細`scripts/clean_for_dist.py`銆乣scripts/machine_worker.py`銆乣scripts/dispatch_test.py`銆乣electron/main.js`銆乣backend.spec`銆乣celery-worker.spec`銆乣requirements.txt`銆乣.gitignore`
- 娴嬭瘯锛歚tests/unit/test_settings_api.py`銆乣tests/unit/test_database_model.py`銆乣tests/unit/test_system_set_machine_code.py`銆乣tests/unit/test_frontend_management_page.py`銆乣tests/unit/test_frontend_tailwind_static.py`銆乣tests/unit/test_packaged_runtime_paths.py`銆乣tests/unit/test_pyinstaller_spec_files.py`銆乣tests/unit/test_machine_access_script.py`銆乣tests/unit/test_task_dispatch_script.py`銆乣tests/test_feishu_service.py`銆乣tests/unit/test_production_env_check.py`
- 鍒犻櫎鏂囦欢锛歚.env`
- 鍚屾鏂囨。锛歚PLAN.md`銆乣鏀归€犺繘搴?md`銆乣.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `settings` 涓婚摼璺細鏂板 `settings` 琛ㄦā鍨嬨€侀粯璁ら厤缃€佸悓姝ヨ鍐欏伐鍏峰拰 `/api/settings` 鎺ュ彛锛涙晱鎰熷瓧娈靛鍓嶇鍙繑鍥?`has_value`锛屼繚瀛樻椂缁熶竴鍔犲瘑鍏ュ簱銆?- 閰嶇疆璇诲彇锛歚backend/config.py` 涓嶅啀渚濊禆 `.env`锛屾敼涓烘暟鎹洰褰曞父閲?+ `閰嶇疆瀹炰緥` 鍔ㄦ€佷唬鐞嗭紝鍏煎鏃ц皟鐢ㄦ柟缁х画閫氳繃灞炴€ц鍙栭厤缃€?- 鏁版嵁鐩綍涓庡瘑閽ワ細缁熶竴杩愯鏃剁洰褰曞埌 `data/`锛屾晱鎰熼厤缃瘑閽ユ敼涓?`data/.secret_key`锛屽苟鏀寔娴嬭瘯涓垏鎹?`DATA_DIR` 鏃跺姩鎬佽В鏋愩€?- 鍏煎灞傦細淇濈暀鏃?`/api/system/config` 鎺ュ彛锛屽簳灞傚疄鐜版敼璧?`settings`锛屽噺灏戝鏃㈡湁椤甸潰鍜岃剼鏈殑鐮村潖闈€?- Redis 闄嶇骇锛歚execute_service.py` 涓?`scheduled_execute_service.py` 鍦?Redis 涓嶅彲鐢ㄦ椂鍥為€€鍒拌繘绋嬪唴缂撳瓨锛岄伩鍏嶅彇娑堟爣璁般€佹壒娆＄姸鎬併€佽鍒掓壒娆℃槧灏勫湪娴嬭瘯鎴栨棤 Redis 鐜鐩存帴鎶ラ敊銆?- 寰幆瀵煎叆淇锛歚backend.models` 涓?`backend.utils` 鏀逛负鎸夐渶瀵煎嚭锛屾媶鎺?`config -> settings -> database -> logging` 鐨勫垵濮嬪寲鐜€?- PyInstaller 鍏ュ彛锛歚scripts/pyinstaller_celery_entry.py` 鏀逛负寤惰繜瀵煎叆閰嶇疆锛岄伩鍏嶅紑鍙戞ā寮忎笅鍏堝鍏?`backend.config` 瀵艰嚧璺緞娉ㄥ叆娴嬭瘯澶辫触銆?- 鍓嶇绯荤粺璁剧疆椤碉細鏂板 `SystemSettings.vue` 涓?`settings.ts`锛屾寜鍒嗙被鍒嗙粍灞曠ず閰嶇疆锛涙晱鎰熼」浣跨敤瀵嗙爜妗嗗拰鈥滃凡璁剧疆鈥濆崰浣嶇锛屼繚瀛樻椂鎵归噺鎻愪氦銆?- 鎵撳寘涓庤劚鏁忥細鏂板 `scripts/clean_for_dist.py`锛屾洿鏂?spec銆乣.gitignore`銆佷緷璧栨竻鍗曞拰 Electron 鍏ュ彛锛屽交搴曠Щ闄?dotenv 鏂规銆?- 娴嬭瘯鍚屾锛氳ˉ鍏?`settings` API銆佹暟鎹簱鍒濆鍖栥€佹墦鍖呭叆鍙ｃ€佹満鍣ㄨ剼鏈笌鍓嶇闈欐€佸洖褰掞紝鏃у瘑閽ユ枃浠舵柇瑷€鍚屾鍒?`.secret_key`銆?
## 褰卞搷鑼冨洿

- 鍚庣鎵€鏈夐€氳繃 `閰嶇疆瀹炰緥` 璇诲彇杩愯閰嶇疆鐨勬ā鍧椼€?- FastAPI 閰嶇疆鎺ュ彛銆佹棫绯荤粺閰嶇疆鎺ュ彛鍜屽墠绔?`/settings` 椤甸潰銆?- Redis 渚濊禆鐨勬壒娆℃墽琛屻€佸彇娑堟爣璁般€佸畾鏃惰鍒掓壒娆℃槧灏勯€昏緫銆?- PyInstaller Celery Worker 鍚姩鍏ュ彛涓庢墦鍖呭墠娓呯悊娴佺▼銆?- Electron 鍚姩閾捐矾鍜屽墠绔鑸腑鐨勨€滅郴缁熻缃€濆叆鍙ｃ€?
## 娉ㄦ剰浜嬮」

- 宸叉墽琛?`python -m pytest -c tests/pytest.ini -q`锛岀粨鏋滀负 `516 passed, 16 warnings`銆?- 宸叉墽琛?`npm --prefix frontend run build`锛屽綋鍓嶇幆澧冧粛鍥?`esbuild` 瀛愯繘绋?`spawn EPERM` 澶辫触锛屽睘浜庣幆澧冮檺鍒讹紝鏈畬鎴愬墠绔瀯寤洪獙鏀躲€?- 鏃?`frontend/src/views/Settings.vue` 浠嶄繚鐣欏湪浠撳簱涓紝浣嗚矾鐢卞凡鍒囨崲鍒?`frontend/src/views/SystemSettings.vue`銆?- `.pipeline/task.md` 涓烘棦鏈夋湰鍦板彉鏇达紝鏈疆鏈慨鏀广€?
---

## 浠诲姟鎽樿

瀹屾垚 settings 杩佺Щ鍚庣殑璺熻繘琛ヤ竵锛欳elery 閰嶇疆鏀寔鍔ㄦ€佸埛鏂帮紝Redis URL 鑷姩褰掍竴鍖栵紝鏂板楠岃瘉鐮?椋炰功娴嬭瘯鎺ュ彛锛屽苟琛ラ綈瀵瑰簲鍗曞厓娴嬭瘯銆?
## 鏀瑰姩鏂囦欢鍒楄〃

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
- `鏀归€犺繘搴?md`
- `.pipeline/progress.md`

## 鏀瑰姩璇存槑

- `tasks/celery_app.py`锛氭柊澧?`鍒锋柊Celery閰嶇疆()`锛屼粠 `settings` 鍔ㄦ€佽鍙?broker / backend锛屽苟鍦ㄥ湴鍧€鍙樺寲鏃跺悓姝ユ竻鐞嗚繛鎺ユ睜銆乸roducer pool 鍜?backend 缂撳瓨銆?- `backend/services/system_service.py`锛氭棫 `/api/system/config` 鍏煎灞傚湪淇濆瓨 `redis_url` 鍓嶈嚜鍔ㄤ慨姝ｅ父瑙佹牸寮忛敊璇紝淇濆瓨鍚庢渶浣冲姫鍔涘埛鏂?Celery 閰嶇疆銆?- `backend/api/settings_api.py`锛氱粰鐪熷疄 `/settings` 椤甸潰浣跨敤鐨?`/api/settings`銆乣/api/settings/batch` 鍐欏叆閾捐矾琛ヤ笂 Redis URL 瑙勮寖鍖栦笌鎸夐渶鍒锋柊 Celery锛岄伩鍏嶅彧淇吋瀹规帴鍙ｄ笉淇幇鐢ㄥ叆鍙ｃ€?- `backend/models/data_structure.py`锛氭柊澧?`楠岃瘉鐮佹祴璇曡姹俙銆乣椋炰功Webhook娴嬭瘯璇锋眰`锛屽苟鍏煎鏃у弬鏁板埆鍚嶃€?- `backend/api/system_api.py`锛氭柊澧?`POST /api/system/test-captcha` 涓?`POST /api/system/test-feishu-webhook`锛屾敮鎸佽姹備綋瑕嗙洊绯荤粺閰嶇疆锛岄涔︽祴璇曟敮鎸佸彲閫夌鍚嶃€?- `tasks/execute_task.py`锛氬湪 `鍒濆鍖朩orker鐜()` 鍚庡鍔?`鍒锋柊Celery閰嶇疆()`锛岃 Worker 姣忔鎵ц浠诲姟鍓嶅厛鍚屾鏈€鏂伴厤缃€?- `tests/unit/test_celery_config_refresh.py`銆乣tests/unit/test_system_followup.py`銆乣tests/unit/test_system_api_followup.py`銆乣tests/unit/test_execute_task_refresh.py`銆乣tests/unit/test_settings_api_followup.py`锛氳ˉ榻愭湰杞柊澧炶涓虹殑鐙珛鍥炲綊娴嬭瘯銆?
## 褰卞搷鑼冨洿

- `/settings` 椤甸潰鍜屾棫 `/api/system/config` 鐨?Celery / Redis 璁剧疆鏇存柊閾捐矾
- `/api/system/test-redis`銆乣/api/system/test-captcha`銆乣/api/system/test-feishu-webhook`
- Celery 涓昏繘绋嬫淳鍙戜换鍔℃椂鐨勯厤缃鍙?- Worker 鎵ц浠诲姟鍓嶇殑閰嶇疆鍚屾

## 娉ㄦ剰浜嬮」

- 宸叉墽琛屾柊澧炲畾鍚戞祴璇曚笌鍙楀奖鍝嶅洖褰掞細
  - `python -m pytest tests/unit/test_celery_config_refresh.py tests/unit/test_system_followup.py tests/unit/test_system_api_followup.py tests/unit/test_execute_task_refresh.py tests/unit/test_settings_api_followup.py -q`
  - `python -m pytest tests/unit/test_system_api.py tests/unit/test_settings_api.py tests/unit/test_execute_task.py tests/unit/test_celery_bridge.py tests/unit/test_system_set_machine_code.py -q`
  - `python -m pytest tests/test_feishu_service.py -q`
- 宸叉墽琛屽叏閲忓洖褰掞細
  - `python -m pytest -c tests/pytest.ini -q`
  - 缁撴灉涓?`525 passed, 18 warnings`
- 18 鏉?warnings 浠嶆潵鑷棦鏈夌涓夋柟渚濊禆 `celery`銆乣openpyxl` 涓庢棦鏈?`PytestUnraisableExceptionWarning`锛屼笉鏄湰杞敼鍔ㄥ紩鍏ョ殑闂銆?- `frontend/src/views/Settings.vue` 浠嶄繚鐣欐棫鎺ュ彛璋冪敤锛屼絾姝ｅ紡璺敱椤典负 `frontend/src/views/SystemSettings.vue`锛涙湰杞凡纭繚褰撳墠 `/settings` 椤甸潰瀹為檯渚濊禆鐨?`/api/settings` 閾捐矾鍏峰 Celery 鍒锋柊鑳藉姏銆?- `.pipeline/task.md`銆乣backend.spec`銆乣build_all.bat`銆乣build_backend.bat` 绛変负鏃㈡湁鏈湴鍙樻洿锛屾湰杞湭淇敼鍏朵换鍔′箣澶栧唴瀹广€?

---

## 任务摘要

完成仓库结构审计与文档校准，识别单一职责、重复实现和屎山热点，并把当前真实架构、路由、配置和测试现状同步到规则文档。

## 改动文件列表

- `AGENTS.md`
- `docs/architecture.md`
- `docs/coding-style.md`
- `docs/frontend.md`
- `docs/testing.md`
- `docs/deployment.md`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `AGENTS.md`：补充 settings 配置来源、当前主路由容器结构、技术债提醒，以及禁止跨 service 调 `_私有方法`、禁止 API monkey patch、统一复用 `tasks/async_utils.py` 等红线。
- `docs/architecture.md`：按当前代码重写入口、分层职责、页面容器关系、关键调用链，并记录 `execute_service.py`、`task_service.py`、`flow_input_service.py`、`task_api.py`、`BatchExecute.vue` 等热点。
- `docs/coding-style.md`：明确 service 拆分方向、共享逻辑抽取原则、前端容器页拆分约束和运行时配置读取规则。
- `docs/frontend.md`：更新真实路由与容器页结构，补充 `SystemSettings.vue`、`BusinessManage.vue`、`MonitorManage.vue` 等当前主页面，以及 `batch-execute/*` 遗留片段说明。
- `docs/testing.md`：改成当前 `tests/unit` 为主、`tests/单元测试` 兼容保留的测试现状，去掉过期的固定通过数。
- `docs/deployment.md`：更新 settings 表配置模型、启动命令和运行时目录说明，移除过期的 `.env` 主配置描述。
- `PLAN.md`、`改造进度.md`、`.pipeline/progress.md`：同步记录本轮 Builder 审计、建议和验证结果。

## 影响范围

- 仓库协作规则与开发约束
- 架构、前端、测试、部署文档的准确性
- 后续执行链路拆分和遗留代码清理的改造方向

## 注意事项

- 本轮未修改业务代码，仅更新规则文档和改造建议。
- 审计确认当前未完全做到单一职责，问题集中在 `backend/services/execute_service.py`、`backend/services/task_service.py`、`backend/services/flow_input_service.py`、`backend/api/task_api.py` 与 `frontend/src/views/BatchExecute.vue`。
- 已执行 `python -m pytest -c tests/pytest.ini -q`，结果为 `525 passed, 18 warnings`。
- 18 条 warnings 仍来自既有第三方依赖 `celery`、`openpyxl` 与既有 `PytestUnraisableExceptionWarning`，不是本轮文档修改引入的问题。
