# 开发进度

## Prompt 150：执行链路拆分与批量执行遗留清理
- [x] 提取共享导入解析层
  - `backend/services/import_parser_service.py`
  - `backend/services/task_params_service.py` 与 `backend/services/flow_input_service.py` 改为复用共享解析服务
- [x] 拆分 `backend/services/task_service.py`
  - 新增 `backend/services/task_param_runtime_service.py`
  - 新增 `backend/services/task_execution_context_service.py`
  - 新增 `backend/services/task_flow_service.py`
  - `task_service.py` 收口为协调层，并保留原有兼容入口
- [x] 拆分 `backend/services/execute_service.py`
  - 新增 `backend/services/execute_state_store.py`
  - 新增 `backend/services/execute_flow_precheck_service.py`
  - `execute_service.py` 下沉状态存储与流程预检逻辑，并保留现有导出与 patch 点
- [x] 移除 `backend/api/task_api.py` 运行时 monkey patch
  - 内部执行改为显式 `flow_context` 适配，不再使用 `_准备任务参数 = _准备流程上下文`
- [x] 统一 Celery 异步桥接实现
  - `tasks/bridge_task.py` 与 `tasks/scheduled_task.py` 统一复用 `tasks/async_utils.py`
- [x] 清理批量执行遗留双实现
  - 删除 `frontend/src/views/batch-execute/ExecuteConfigPanel.vue`
  - 删除 `frontend/src/views/batch-execute/BatchStatusPanel.vue`
  - 删除 `frontend/src/views/batch-execute/BatchStatusPanel.css`
- [x] 更新受影响回归测试
  - `tests/unit/test_batch_execute_schedule_static.py`
  - `tests/unit/test_batch_execute_shop_name.py`
  - `tests/unit/test_celery_bridge.py`
- [x] 验证通过
  - `python -m pytest tests/unit/test_task_service.py tests/unit/test_task_service_browser_reuse.py tests/unit/test_execute_service.py tests/unit/test_task_api_internal_exec.py tests/unit/test_celery_bridge.py tests/unit/test_flow_input_service.py tests/unit/test_task_params_service.py tests/unit/test_batch_execute_schedule_static.py tests/unit/test_batch_execute_shop_name.py -q`
  - `64 passed, 3 warnings`
  - `python -m pytest -c tests/pytest.ini -q`
  - `525 passed, 18 warnings`

## Prompt 148：批量执行补齐输入集透传
- [x] `frontend/src/api/flowInputs.ts`
  - 新增流程输入集 API 封装，读取 `/api/flows/{flow_id}/input-sets`
- [x] `frontend/src/api/types.ts`
  - 新增 `FlowInputSet` 类型
  - 为 `BatchRequest` 补齐 `input_set_id`
- [x] `frontend/src/views/BatchExecute.vue`
  - 流程模式下新增输入集加载与选择
  - 启动批量执行时透传 `input_set_id`
  - 未选择输入集时继续沿用旧的 `flow_params` 执行链路
- [x] 更新静态回归测试
  - `tests/unit/test_batch_execute_schedule_static.py`
  - `tests/unit/test_frontend_management_page.py`
- [x] 验证通过
  - `python -m pytest tests/unit/test_batch_execute_schedule_static.py tests/unit/test_frontend_management_page.py tests/unit/test_execute_api.py -q`
  - `cd frontend && npm run build`
  - `python -m pytest -c tests/pytest.ini -q`

## Prompt 147锛氳缃〉 Celery 鍔ㄦ€佸埛鏂般€丷edis URL 褰掍竴鍖栦笌绯荤粺娴嬭瘯鎺ュ彛 鉁?
- [x] `tasks/celery_app.py`
  - 鏂板 `鍒锋柊Celery閰嶇疆()`锛屽姩鎬佸埛鏂?broker / backend锛屽苟娓呯悊杩炴帴姹犮€乸roducer pool銆乥ackend 缂撳瓨
- [x] `backend/services/system_service.py`
  - 鍏煎鏃?`/api/system/config` 鏇存柊閾捐矾
  - 鏇存柊 `redis_url` 鏃惰嚜鍔ㄤ慨姝?`redis://host/:port` 杩欑被鑴忔牸寮?  - 淇濆瓨鍚庡皾璇曞埛鏂?Celery 閰嶇疆
- [x] `backend/api/settings_api.py`
  - 涓哄綋鍓嶇湡瀹?`/settings` 椤甸潰浣跨敤鐨?`/api/settings`銆乣/api/settings/batch` 閾捐矾琛ヤ笂 Redis URL 瑙勮寖鍖?  - `celery_broker_url` / `celery_result_backend` 鏇存柊鍚庢寜闇€鍒锋柊 Celery 閰嶇疆
- [x] `backend/models/data_structure.py`
  - 鏂板 `楠岃瘉鐮佹祴璇曡姹俙銆乣椋炰功Webhook娴嬭瘯璇锋眰`
  - 鍏煎鏃у墠绔?`provider` / `api_key` 绛夊瓧娈靛埆鍚?- [x] `backend/api/system_api.py`
  - 鏂板 `POST /api/system/test-captcha`
  - 鏂板 `POST /api/system/test-feishu-webhook`
  - 璇锋眰浣撲紭鍏堬紝绯荤粺閰嶇疆鍥為€€锛涢涔︽祴璇曟敮鎸佸彲閫夌鍚?- [x] `tasks/execute_task.py`
  - 鍦?`鍒濆鍖朩orker鐜()` 鍚庤皟鐢?`鍒锋柊Celery閰嶇疆()`
- [x] 鏂板鍥炲綊娴嬭瘯
  - `tests/unit/test_celery_config_refresh.py`
  - `tests/unit/test_system_followup.py`
  - `tests/unit/test_system_api_followup.py`
  - `tests/unit/test_execute_task_refresh.py`
  - `tests/unit/test_settings_api_followup.py`
- [x] 鍙楀奖鍝嶅洖褰掗€氳繃
  - `python -m pytest tests/unit/test_system_api.py tests/unit/test_settings_api.py tests/unit/test_execute_task.py tests/unit/test_celery_bridge.py tests/unit/test_system_set_machine_code.py -q`
  - `python -m pytest tests/test_feishu_service.py -q`
- [x] 鍏ㄩ噺鍥炲綊閫氳繃
  - `python -m pytest -c tests/pytest.ini -q`
  - `525 passed, 18 warnings`

## 澶囨敞

- 褰撳墠姝ｅ紡璺敱椤典负 `frontend/src/views/SystemSettings.vue`锛屾湰杞凡鎶婂畠渚濊禆鐨?`/api/settings` 鍐欏叆閾捐矾琛ラ綈 Celery 鍒锋柊鑳藉姏銆?- 鏃?`frontend/src/views/Settings.vue` 浠嶄繚鐣欏湪浠撳簱涓紝浣嗕笉鍦ㄥ綋鍓嶈矾鐢遍摼璺笂銆?
## Prompt 149：结构审计与文档校准
- [x] 盘点单一职责、重复实现和屎山热点
  - `backend/services/execute_service.py`
  - `backend/services/task_service.py`
  - `backend/services/flow_input_service.py`
  - `backend/api/task_api.py`
  - `tasks/bridge_task.py`
  - `tasks/scheduled_task.py`
  - `frontend/src/views/BatchExecute.vue`
  - `frontend/src/views/batch-execute/ExecuteConfigPanel.vue`
  - `frontend/src/views/batch-execute/BatchStatusPanel.vue`
- [x] 更新仓库规则与专题文档
  - `AGENTS.md`
  - `docs/architecture.md`
  - `docs/coding-style.md`
  - `docs/frontend.md`
  - `docs/testing.md`
  - `docs/deployment.md`
- [x] 将修复与优化建议写入 `改造进度.md`
- [x] 全量回归验证
  - `python -m pytest -c tests/pytest.ini -q`
  - `525 passed, 18 warnings`
