## 任务摘要

在任务服务执行链路中接入 `task_params` 读取与回填，让发布相似商品/发布换图商品任务自动消费待执行参数。

## 改动文件列表

- `backend/services/任务服务.py`
- `tests/单元测试/测试_任务服务.py`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `backend/services/任务服务.py`
  - 新增发布类任务的 `task_params` 对接逻辑，仅对“发布相似商品”“发布换图商品”生效
  - 通过 `任务参数服务实例.获取待执行列表(...)` 读取当前店铺与任务名下首条 `pending` 记录，并把 `params` 注入到 `店铺配置["task_param"]`
  - 注入时补上 `task_param_id`，并在执行前将该记录回填为 `running`
  - 任务返回 `成功` 时回填 `success + 任务实例._执行结果`；返回失败结果或抛异常时回填 `failed + error`
  - 无待执行参数时调用 `上报("没有待执行的任务参数", shop_id)` 并返回 `跳过`，不再实例化具体任务
- `tests/单元测试/测试_任务服务.py`
  - 新增发布相似商品自动注入首条待执行参数并回填成功的用例
  - 新增发布换图商品无待执行参数时跳过的用例
  - 新增发布任务返回失败时回填 `failed` 和错误信息的用例
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮 `task_params` 执行链路对接与验证结果

## 影响范围

- 发布相似商品/发布换图商品任务现在可以直接消费 CSV 导入到 `task_params` 的待执行记录
- 同一店铺存在多条 `pending` 记录时，每次执行只消费一条，支持按顺序逐条执行
- `task_params` 的 `status/result/error` 会与任务执行结果同步，便于前端和批量流程追踪

## 注意事项

- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务服务.py`，结果 `4 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q`，结果 `161 passed, 6 warnings`
- `任务参数服务` 现有“店铺名称 → shop_id”映射仍返回 `shops` 表的实际 UUID，本轮未改动该逻辑
- 全量测试中的 6 条 Celery `datetime.utcnow()` 弃用警告为现有存量问题，非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db` 等非本轮源码改动外的既有本地变更

---

## 任务摘要

完成 Task 15：为 `task_params` 增加启用/禁用/重置、批量启用/禁用/重置、CSV“发布次数”展开和执行次数统计，并同步补齐前后端交互与回归测试。

## 改动文件列表

- `backend/models/数据库.py`
- `backend/models/数据结构.py`
- `backend/services/任务参数服务.py`
- `backend/api/任务参数接口.py`
- `frontend/src/api/types.ts`
- `frontend/src/api/taskParams.ts`
- `frontend/src/views/TaskParamsManage.vue`
- `tests/单元测试/测试_任务参数启用重置服务.py`
- `tests/单元测试/测试_任务参数启用重置接口.py`
- `tests/单元测试/测试_任务参数启用重置管理页.py`
- `PLAN.md`
- `改造进度.md`

## 改动说明

- `backend/models/数据库.py`
  - 为 `task_params` 新增 `enabled`、`run_count` 字段
  - 在数据库初始化阶段通过 `ALTER TABLE` 自动补齐旧库字段，兼容已有数据
- `backend/models/数据结构.py`
  - 扩展任务参数创建/更新/响应模型
  - 新增批量操作请求模型，统一承接批量启用、禁用、重置接口
- `backend/services/任务参数服务.py`
  - 创建、查询、记录转换逻辑接入 `enabled/run_count`
  - 待执行查询只读取 `enabled=1` 的 `pending` 记录，并按 `id ASC` 顺序返回
  - 新增单条启用、禁用、重置与批量启用、禁用、重置逻辑
  - `更新执行结果(...)` 在 `success/failed` 时自动累加 `run_count`
  - CSV 导入新增“发布次数”解析与展开，并为展开记录写入 `batch_index`
- `backend/api/任务参数接口.py`
  - 新增单条启用、禁用、重置接口
  - 新增批量启用、禁用、重置接口，并保持统一响应格式
- `frontend/src/api/types.ts` / `frontend/src/api/taskParams.ts`
  - 补齐任务参数启用态、执行次数与批量操作类型
  - 新增单条和批量任务参数操作的 API 封装
- `frontend/src/views/TaskParamsManage.vue`
  - 新增“启用”开关列与“已执行次数”列
  - 新增单条“重置”按钮、顶部批量重置/启用/禁用按钮
  - 新增禁用态整行置灰效果与“发布次数”模板说明
- `tests/单元测试/测试_任务参数启用重置服务.py`
  - 覆盖旧库迁移、新字段行为、单条与批量操作、发布次数展开和异常输入
- `tests/单元测试/测试_任务参数启用重置接口.py`
  - 覆盖单条启用/禁用/重置接口、批量接口筛选约束和发布次数导入链路
- `tests/单元测试/测试_任务参数启用重置管理页.py`
  - 覆盖前端 API wrapper 与页面批量操作/开关/执行次数静态回归
- `PLAN.md` / `改造进度.md`
  - 同步记录本轮 `task_params` 管理增强与验证结果

## 影响范围

- `task_params` 记录现在支持长期复用，可按需启用、禁用、重置后再次执行
- 发布类任务执行完成后会累计执行次数，前端可直接查看运行统计
- CSV 导入新增“发布次数”后，可从一行配置展开出多条待执行记录
- 前端任务参数管理页现在可以直接执行单条和批量运维操作

## 注意事项

- 批量启用、批量禁用必须至少带一个筛选条件，后端会拒绝无条件全表操作
- 批量重置未传 `status` 时默认处理 `success/failed` 记录，不会改动 `params`、`enabled` 和 `run_count`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数启用重置服务.py tests/单元测试/测试_任务参数启用重置接口.py tests/单元测试/测试_任务参数启用重置管理页.py`，结果 `9 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q tests/单元测试/测试_任务参数服务.py tests/单元测试/测试_任务参数接口.py tests/单元测试/测试_任务服务.py`，结果 `17 passed`
- 已执行 `python -m pytest -c tests/pytest.ini -q`，结果 `170 passed, 6 warnings`
- 已执行 `cd frontend && npx vue-tsc -b`，结果通过
- 全量测试中的 6 条 Celery `datetime.utcnow()` 弃用警告为现有存量问题，非本轮引入
- 工作区仍存在 `.pipeline/task.md`、`data/ecom.db` 等非本轮源码改动外的既有本地变更
