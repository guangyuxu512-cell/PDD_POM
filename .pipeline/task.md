**Task 31：流程级参数体系 — 新建 flow_params 表 + CSV 导入绑定流程 + 步骤间共享参数与结果传递**

---

**一、做什么**

把当前"参数绑定单个任务"的设计，改为"参数绑定流程"。新建 `flow_params` 表，CSV 导入时绑定到流程，所有步骤共享同一个参数池，步骤执行结果自动回写供下一步读取。删除硬编码的 `任务链映射`。

---

**二、涉及文件**

1. `backend/models/数据库.py` — 新增 `flow_params` 建表 SQL
2. `backend/models/数据结构.py` — 新增 `流程参数创建请求`、`流程参数导入请求` 等 Pydantic 模型
3. `backend/services/流程参数服务.py` — **新建文件**，流程参数 CRUD + CSV 导入 + 步骤结果回写
4. `backend/api/流程参数接口.py` — **新建文件**，流程参数 REST API
5. `backend/api/路由注册.py` — 注册新路由
6. `backend/services/任务服务.py` — 删除 `任务链映射`，执行任务时支持从 `flow_context` 读参数
7. `backend/services/执行服务.py` — `创建批次()` 时查询 `flow_params` 待执行记录，把 `flow_param_id` 传入每个 Celery step
8. `tasks/执行任务.py` — 接收 `flow_param_id`，执行前读 flow_params，执行后回写 step_results
9. `backend/services/任务参数服务.py` — `创建后续任务()` 方法保留但不再从 `任务链映射` 触发，仅供兼容
10. `frontend/src/api/types.ts` — 新增 `FlowParam`、`FlowParamImportResult` 类型
11. `frontend/src/api/flowParams.ts` — **新建文件**，流程参数 API 调用
12. `frontend/src/views/TaskParamsManage.vue` — CSV 导入增加"绑定流程"选项（下拉选择已有流程）

---

**三、流程**

**第1步：建表**

在 `backend/models/数据库.py` 的建表列表中新增 `flow_params` 表：

```
flow_params 表字段：
- id INTEGER PRIMARY KEY AUTOINCREMENT
- shop_id TEXT NOT NULL（关联 shops.id）
- flow_id TEXT NOT NULL（关联 flows.id）
- params TEXT DEFAULT '{}'（共享参数 JSON，CSV 导入的所有列都写这里）
- step_results TEXT DEFAULT '{}'（每步执行完回写，格式: {"任务名": {结果字典}}）
- current_step INTEGER DEFAULT 0（当前执行到第几步，0=未开始）
- status TEXT DEFAULT 'pending'（pending/running/success/failed）
- error TEXT（最后一个错误信息）
- batch_id TEXT（执行批次ID）
- enabled INTEGER DEFAULT 1
- run_count INTEGER DEFAULT 0
- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**第2步：流程参数服务（新建 `backend/services/流程参数服务.py`）**

核心方法：

- `批量导入(文件内容, flow_id, file_name)` — 解析 CSV/XLSX，每行生成一条 flow_params 记录。CSV 列中 `店铺ID` 和 `发布次数` 为保留列，其余全部写入 params JSON。复用 `任务参数服务` 中已有的 `_解码CSV文本`、`_解析CSV内容`、`_解析XLSX内容`、`_修复科学计数法`、`_预处理CSV行`、`_解析店铺标识`、`_解析发布次数` 方法（建议提取为公共工具类或直接调用）
- `获取待执行列表(shop_id, flow_id)` — 返回 status='pending' 且 enabled=1 的记录，按 id ASC
- `获取步骤上下文(flow_param_id, 当前任务名)` — 读取该记录的 params + step_results，合并为一个 dict 返回给任务。合并逻辑：先放 params 的所有键值，再按流程步骤顺序依次覆盖 step_results 里每步的结果
- `回写步骤结果(flow_param_id, 任务名, 结果字典, step_index)` — 把执行结果写入 step_results[任务名]，更新 current_step
- `更新执行状态(flow_param_id, 状态, 错误信息)` — 更新 status/error/run_count/updated_at
- `分页查询(...)` — 同 task_params 的分页查询模式，支持 shop_id/flow_id/status/batch_id 筛选
- CRUD：`创建`、`根据ID获取`、`更新`、`删除`、`按条件清空`、`批量重置`、`批量启用`、`批量禁用`

**第3步：流程参数 API（新建 `backend/api/流程参数接口.py`）**

路由前缀：`/api/flow-params`

- `GET /` — 分页查询
- `POST /` — 创建单条
- `POST /import` — CSV/XLSX 导入（接收 flow_id + 文件）
- `GET /{id}` — 获取单条
- `PUT /{id}` — 更新单条
- `DELETE /{id}` — 删除单条
- `POST /batch-reset` — 批量重置
- `POST /batch-enable` — 批量启用
- `POST /batch-disable` — 批量禁用
- `DELETE /batch-clear` — 按条件清空

在 `backend/api/路由注册.py` 中注册路由。

**第4步：修改执行链路 — [执行服务.py](http://执行服务.py)**

`创建批次()` 方法改造：

- 当 mode="flow" 时（有 flow_id），查 `flow_params` 获取每个 shop_id 的待执行记录
- 构建 Celery chain 时，每个 step 的 `.si()` 参数新增 `flow_param_id`
- 如果 flow_params 中没有该 shop_id 的待执行记录，跳过该店铺（不报错）

**第5步：修改执行链路 — [执行任务.py](http://执行任务.py)（Celery task）**

`执行任务()` 函数签名新增可选参数 `flow_param_id: Optional[int] = None`

执行前：

- 如果有 flow_param_id，从 flow_params 读取 params + step_results，合并为 flow_context
- 更新 flow_params 状态为 running，current_step = step_index
- 把 flow_context 注入到 `任务参数`（传给 `统一执行任务`）

执行后：

- 成功：调用 `回写步骤结果(flow_param_id, task_name, 执行结果数据, step_index)`
- 如果是最后一步且成功：更新 flow_params status = success
- 失败：根据 on_fail 策略决定是否更新 flow_params status = failed

**第6步：[修改任务服务.py](http://修改任务服务.py)**

- 删除 `任务链映射 = {"发布相似商品": "限时限量"}`
- 删除 `执行任务()` 方法末尾的 `任务链映射` 相关代码（`下一步任务名 = 任务链映射.get(task_name)` 那段）
- `_准备任务参数()` 方法增加逻辑：如果 `店铺配置` 中已有 `flow_context`，直接用 flow_context 作为 task_param，不再查 task_params 表
- `任务参数任务集合` 保留，用于单任务执行的兼容

**第7步：前端改造**

`frontend/src/api/types.ts` 新增：

```
FlowParam: { id, shop_id, shop_name, flow_id, params, step_results, current_step, status, error, batch_id, enabled, run_count, created_at, updated_at }
FlowParamImportResult: { success_count, failed_count, errors }
```

`frontend/src/api/flowParams.ts` 新建，包含：

- `listFlowParams(filters)` — GET /api/flow-params
- `importFlowParams(flowId, file)` — POST /api/flow-params/import
- 其他 CRUD 方法

`frontend/src/views/TaskParamsManage.vue` 修改：

- 导入弹窗增加一个 Tab 或 Radio："绑定任务" / "绑定流程"
- 选择"绑定流程"时，下拉框显示已有流程列表（调用 listFlows）
- 导入时调用 flowParams.importFlowParams 而非 taskParams.import

---

**四、关键元素**

- 新表名：`flow_params`
- 新服务：`流程参数服务` / `流程参数服务实例`
- 新接口路由前缀：`/api/flow-params`
- `step_results` JSON 格式：`{"发布相似商品": {"新商品ID": "918522845367"}, "限时限量": {"活动ID": "xxx"}}`
- `获取步骤上下文` 合并顺序：params（基础）→ step_results 按步骤顺序依次覆盖
- Celery task 新参数：`flow_param_id: Optional[int] = None`

---

**五、约束**

1. **不删除 task_params 表和相关服务** — 保留兼容，单任务执行仍走 task_params
2. **不修改 flows 表结构** — 流程模板保持不变
3. **flow_params 与 task_params 互不干扰** — 流程执行读 flow_params，单任务执行读 task_params
4. **CSV 列名映射复用现有逻辑** — `参数键名映射`、`保持字符串字段`、`_规范参数键名`、`_转换参数值` 这些逻辑直接复用或提取为公共函数
5. **严格按流程步骤执行，不要自行添加步骤**
6. **不要硬编码任务链路** — 所有步骤顺序从 flows 表读取
7. **每个任务的 `执行()` 方法签名不变** — 任务仍然从 `店铺配置` 字典中取参数，只是注入方式从 task_params 变成了 flow_context
8. **后端 Python 中文命名，前端英文命名**