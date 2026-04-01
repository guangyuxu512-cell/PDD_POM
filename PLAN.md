# 开发进度

## Prompt 147：设置页 Celery 动态刷新、Redis URL 归一化与系统测试接口 ✅

- [x] `tasks/celery_app.py`
  - 新增 `刷新Celery配置()`，动态刷新 broker / backend，并清理连接池、producer pool、backend 缓存
- [x] `backend/services/system_service.py`
  - 兼容旧 `/api/system/config` 更新链路
  - 更新 `redis_url` 时自动修正 `redis://host/:port` 这类脏格式
  - 保存后尝试刷新 Celery 配置
- [x] `backend/api/settings_api.py`
  - 为当前真实 `/settings` 页面使用的 `/api/settings`、`/api/settings/batch` 链路补上 Redis URL 规范化
  - `celery_broker_url` / `celery_result_backend` 更新后按需刷新 Celery 配置
- [x] `backend/models/data_structure.py`
  - 新增 `验证码测试请求`、`飞书Webhook测试请求`
  - 兼容旧前端 `provider` / `api_key` 等字段别名
- [x] `backend/api/system_api.py`
  - 新增 `POST /api/system/test-captcha`
  - 新增 `POST /api/system/test-feishu-webhook`
  - 请求体优先，系统配置回退；飞书测试支持可选签名
- [x] `tasks/execute_task.py`
  - 在 `初始化Worker环境()` 后调用 `刷新Celery配置()`
- [x] 新增回归测试
  - `tests/unit/test_celery_config_refresh.py`
  - `tests/unit/test_system_followup.py`
  - `tests/unit/test_system_api_followup.py`
  - `tests/unit/test_execute_task_refresh.py`
  - `tests/unit/test_settings_api_followup.py`
- [x] 受影响回归通过
  - `python -m pytest tests/unit/test_system_api.py tests/unit/test_settings_api.py tests/unit/test_execute_task.py tests/unit/test_celery_bridge.py tests/unit/test_system_set_machine_code.py -q`
  - `python -m pytest tests/test_feishu_service.py -q`
- [x] 全量回归通过
  - `python -m pytest -c tests/pytest.ini -q`
  - `525 passed, 18 warnings`

## 备注

- 当前正式路由页为 `frontend/src/views/SystemSettings.vue`，本轮已把它依赖的 `/api/settings` 写入链路补齐 Celery 刷新能力。
- 旧 `frontend/src/views/Settings.vue` 仍保留在仓库中，但不在当前路由链路上。
