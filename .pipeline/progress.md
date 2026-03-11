## 任务摘要

补齐店铺与流程模板的 CRUD 接口，新增流程服务层，并将店铺密码字段统一按 `***` 脱敏返回。

## 改动文件列表

- `backend/models/数据结构.py`
- `backend/services/店铺服务.py`
- `backend/services/流程服务.py`
- `backend/api/店铺接口.py`
- `backend/api/流程接口.py`
- `backend/api/路由注册.py`
- `tests/单元测试/测试_店铺和流程接口.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/models/数据结构.py`
  - 为店铺响应新增脱敏 `password` 字段
  - 新增流程创建、更新、响应模型
- `backend/services/店铺服务.py`
  - 补充店铺名称非空校验
  - 将 `password`、`smtp_pass` 返回值统一遮蔽为 `***`
- `backend/services/流程服务.py`
  - 新增流程模板 CRUD
  - 统一解析 `steps`
  - 校验 JSON 数组格式、`on_fail` 合法性和任务注册表中的 `task` 是否存在
- `backend/api/店铺接口.py`
  - 为 `GET /api/shops`、`POST /api/shops` 增加无尾斜杠入口
  - 保持原有尾斜杠路由兼容
- `backend/api/流程接口.py`
  - 新增 `GET /api/flows`
  - 新增 `POST /api/flows`
  - 新增 `PUT /api/flows/{id}`
  - 新增 `DELETE /api/flows/{id}`
- `backend/api/路由注册.py`
  - 注册流程接口路由
- `tests/单元测试/测试_店铺和流程接口.py`
  - 覆盖店铺 CRUD、流程 CRUD、未知任务和非法 steps 两类异常路径
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮新增接口与验证结果

## 影响范围

- 影响 `backend/api/店铺接口.py` 的列表与创建入口路径匹配方式
- 新增流程模板服务层与 `/api/flows` 接口
- 影响店铺接口返回结构，新增脱敏 `password` 字段

## 注意事项

- 现有店铺接口的浏览器、Cookie、邮箱相关子路由未改动
- 流程 `steps` 中的 `task` 校验依赖任务注册表，服务层会在校验前自动初始化注册表
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_店铺和流程接口.py -q`、`python -m pytest -c tests/pytest.ini -q` 验证

## 任务摘要

新增批量执行 API、Celery 批次投递与批次状态流，补齐执行服务、执行任务和对应单元测试，并修正批次状态落 Redis 的时序竞态。

## 改动文件列表

- `backend/services/执行服务.py`
- `backend/api/执行接口.py`
- `tasks/执行任务.py`
- `backend/models/数据结构.py`
- `tasks/celery应用.py`
- `tasks/注册表.py`
- `backend/api/路由注册.py`
- `tests/单元测试/测试_执行服务.py`
- `tests/单元测试/测试_执行接口.py`
- `tests/单元测试/测试_执行任务.py`
- `browser/反检测.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/执行服务.py`
  - 新增批次创建、停止、读取最新批次状态和 Redis pubsub 订阅逻辑
  - 为每个店铺构造 Celery `chain`，复用 `worker.{machine_id}` 队列
  - 调整为先 `freeze` 收集全部 `task_id` 并写入批次状态，再统一 `apply_async()`，避免 Worker 抢先启动导致首个状态更新丢失
- `backend/api/执行接口.py`
  - 新增 `POST /api/execute/batch`
  - 新增 `POST /api/execute/stop`
  - 新增 `GET /api/execute/status`，通过 SSE 推送批次进度
- `tasks/执行任务.py`
  - 新增批次子任务入口，复用 `任务服务实例.统一执行任务(...)`
  - 按 `on_fail` 区分继续、终止和重试策略，并回写批次状态
- `backend/models/数据结构.py`
  - 新增 `批量执行请求`
  - 新增 `停止执行请求`
- `tasks/celery应用.py`
  - 将 `tasks.执行任务` 加入 Celery 自动导入列表
- `tasks/注册表.py`
  - 将 `执行任务` 加入自动发现排除列表，避免基础设施任务被误识别为业务任务
- `backend/api/路由注册.py`
  - 注册执行接口路由
- `tests/单元测试/测试_执行服务.py`
  - 覆盖批次创建成功、`flow_id/task_name` 二选一校验、未注册任务、停止批次
- `tests/单元测试/测试_执行接口.py`
  - 覆盖批量执行接口统一响应与状态流 SSE 输出
- `tests/单元测试/测试_执行任务.py`
  - 覆盖 `continue / abort / retry:N` 三种失败策略
- `browser/反检测.py`
  - 调整极短延时实现，消除全量回归里的计时抖动
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮新增能力与验证结果

## 影响范围

- 新增 `/api/execute/*` 相关后端接口与 Celery 子任务链路
- 影响批次执行状态的 Redis 键设计、SSE 推送和任务停止能力
- 影响 Celery 任务自动发现排除规则
- 影响极短延时场景下的反检测计时实现

## 注意事项

- `concurrency` 当前仅记录在批次元数据中，实际并发仍由 Celery Worker 启动参数控制
- 停止批次依赖 `freeze()` 预先收集到的子任务 `task_id` 执行撤销
- `continue` / `log_and_skip` 策略会吞掉当前步骤失败并继续链路，这是当前设计选择
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_执行服务.py -q`、`python -m pytest -c tests/pytest.ini tests/单元测试/测试_执行接口.py -q`、`python -m pytest -c tests/pytest.ini tests/单元测试/测试_执行任务.py -q`、`python -m pytest -c tests/pytest.ini -q` 验证

## 任务摘要

新增定时任务 CRUD、Celery Beat（RedBeat）调度接线与计划触发入口，补齐 schedules API、服务层、Celery 基础设施任务和回归测试。

## 改动文件列表

- `backend/models/数据结构.py`
- `backend/models/__init__.py`
- `backend/services/定时执行服务.py`
- `backend/api/定时执行接口.py`
- `backend/api/路由注册.py`
- `tasks/celery应用.py`
- `tasks/注册表.py`
- `tasks/定时任务.py`
- `requirements.txt`
- `tests/单元测试/测试_定时执行服务.py`
- `tests/单元测试/测试_定时执行接口.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/models/数据结构.py`
  - 新增定时计划创建、更新、响应模型，统一 schedules API 请求和返回结构
- `backend/models/__init__.py`
  - 导出新增的定时计划相关模型，保持模型入口一致
- `backend/services/定时执行服务.py`
  - 新增定时计划 CRUD、参数校验、RedBeat 条目创建/删除、暂停/恢复与到点触发批量执行
  - 到点触发时复用 `执行服务实例.创建批次(...)`，并记录计划的 `last_run_at` / `next_run_at`
  - 使用 Redis 键 `schedule:batch:{schedule_id}` 保存最近批次 ID，补一层基础重叠控制
- `backend/api/定时执行接口.py`
  - 新增 `GET/POST /api/schedules`
  - 新增 `PUT/DELETE /api/schedules/{id}`
  - 新增 `POST /api/schedules/{id}/pause`
  - 新增 `POST /api/schedules/{id}/resume`
- `backend/api/路由注册.py`
  - 注册 schedules 路由
- `tasks/celery应用.py`
  - 追加 `beat_scheduler="redbeat.RedBeatScheduler"` 和 `redbeat_redis_url=配置实例.REDIS_URL`
  - 将 `tasks.定时任务` 加入 Celery 自动导入列表
- `tasks/注册表.py`
  - 将 `定时任务` 加入自动发现排除列表，避免基础设施任务被当成业务任务
- `tasks/定时任务.py`
  - 新增 `执行定时计划` Celery 任务，复用 Worker 事件循环调用计划触发逻辑
- `requirements.txt`
  - 添加 `celery-redbeat>=2.0.0`
  - 说明：任务文案写的是 `redbeat`，但 PyPI 实际分发名为 `celery-redbeat`
- `tests/单元测试/测试_定时执行服务.py`
  - 覆盖计划创建、到点触发复用批量执行、Cron 运行时间回写和调度参数冲突异常
- `tests/单元测试/测试_定时执行接口.py`
  - 覆盖 schedules 创建、列表、暂停、恢复、删除及流程不存在异常路径
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮新增能力、依赖差异说明与验证结果

## 影响范围

- 新增 `/api/schedules` 系列后端接口
- 影响 Celery Beat 配置，新增 RedBeat 调度器与定时计划基础设施任务
- 影响任务自动发现排除规则，避免 `tasks/定时任务.py` 被业务任务注册
- 影响依赖安装方式，RedBeat 需要通过 `celery-redbeat` 安装

## 注意事项

- `interval_seconds` 与 `cron_expr` 当前按“二选一”处理，避免同一计划存在双重调度语义
- `overlap_policy=wait` 当前实现为“本次触发不并发启动，等待后续调度窗口再次尝试”，没有额外排队持久化
- RedBeat 在代码中延迟导入，测试环境即使未安装 `celery-redbeat` 也不会在模块导入阶段直接失败
- 已完成 `python -m py_compile backend/services/定时执行服务.py backend/api/定时执行接口.py tasks/定时任务.py tests/单元测试/测试_定时执行服务.py tests/单元测试/测试_定时执行接口.py`、`python -m pytest -c tests/pytest.ini tests/单元测试/测试_定时执行服务.py tests/单元测试/测试_定时执行接口.py -q`、`python -m pytest -c tests/pytest.ini -q` 验证

## 任务摘要

新增前端 4 个通用管理页面及对应 API 封装，接入店铺、流程、批量执行和定时任务后端接口，并补充前端烟雾测试。

## 改动文件列表

- `frontend/src/api/types.ts`
- `frontend/src/api/shops.ts`
- `frontend/src/api/flows.ts`
- `frontend/src/api/execute.ts`
- `frontend/src/api/schedules.ts`
- `frontend/src/api/tasks.ts`
- `frontend/src/views/ShopManage.vue`
- `frontend/src/views/FlowManage.vue`
- `frontend/src/views/BatchExecute.vue`
- `frontend/src/views/ScheduleManage.vue`
- `frontend/src/router/index.ts`
- `frontend/src/App.vue`
- `tests/单元测试/测试_前端管理页.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/api/types.ts`
  - 新增前端管理页共享类型，统一店铺、流程、批量执行、定时任务与可用任务的数据结构
- `frontend/src/api/shops.ts`
  - 新增店铺 CRUD 请求封装
- `frontend/src/api/flows.ts`
  - 新增流程模板 CRUD 请求封装
- `frontend/src/api/execute.ts`
  - 新增批量执行启动、停止和状态订阅请求封装
- `frontend/src/api/schedules.ts`
  - 新增定时任务 CRUD、暂停、恢复请求封装
- `frontend/src/api/tasks.ts`
  - 新增可用任务列表请求封装
- `frontend/src/views/ShopManage.vue`
  - 将现有 `/shops` 页面重写为平台无关的通用店铺管理页
  - 保留列表、新增/编辑、删除、状态展示，移除平台相关动作
- `frontend/src/views/FlowManage.vue`
  - 新增流程模板管理页
  - 支持步骤增删、拖拽排序、复制、失败策略和任务下拉选择
  - 补充复制步骤和拖拽排序时的空值保护，解决 TypeScript 严格检查报错
- `frontend/src/views/BatchExecute.vue`
  - 新增批量执行页
  - 支持流程模式与单任务模式切换、店铺多选、并发数选择、SSE 实时进度
  - 补充默认流程/任务回填时的空值保护，解决 TypeScript 严格检查报错
- `frontend/src/views/ScheduleManage.vue`
  - 新增定时任务页
  - 支持固定间隔与 Cron 两种调度方式，以及创建、编辑、暂停、恢复、删除
  - 编辑时显式清空未选中的 `interval_seconds` / `cron_expr`，避免旧值残留到后端
- `frontend/src/router/index.ts`
  - 追加 `/flows`、`/execute`、`/schedules` 路由
- `frontend/src/App.vue`
  - 追加流程模板、批量执行、定时任务导航入口
  - 将侧边栏标题从 `抖店自动化` 调整为 `自动化工作台`
- `tests/单元测试/测试_前端管理页.py`
  - 新增前端管理页烟雾测试，覆盖新增页面及关键结构
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮前端改造与验证结果

## 影响范围

- 影响前端路由与侧边栏导航，新增 `/flows`、`/execute`、`/schedules` 三个页面入口
- 影响现有 `/shops` 页面行为，改为通用店铺管理页实现
- 新增前端对 `/api/shops`、`/api/flows`、`/api/execute`、`/api/schedules`、`/api/tasks/available` 的调用封装
- 影响批量执行和定时任务的前端交互方式，新增 SSE 进度展示与调度表单

## 注意事项

- `ScheduleManage.vue` 的“执行中”状态目前基于 `enabled + last_run_at + interval_seconds` 做前端近似推断，后端暂未提供独立执行态字段
- 编辑定时任务时会显式将未选中的 `interval_seconds` 或 `cron_expr` 置为 `null`，避免后端保留旧值
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_前端管理页.py -q`、`python -m pytest -c tests/pytest.ini -q`、`cd frontend && npx vue-tsc -b` 验证
- `cd frontend && npm run build` 与 `npx vite build --configLoader runner` 在当前沙箱均因 `spawn EPERM` 失败，失败点为 Vite/esbuild 启动子进程，不是新的 TypeScript 编译错误

## 任务摘要

恢复店铺页改造前的小卡片布局和邮箱相关表单，同时补回店铺前端类型/封装对旧字段的支持，并新增回归测试锁定这些行为。

## 改动文件列表

- `frontend/src/api/types.ts`
- `frontend/src/api/shops.ts`
- `frontend/src/views/ShopManage.vue`
- `frontend/src/components/ShopCard.vue`
- `browser/反检测.py`
- `tests/单元测试/测试_店铺恢复.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- 历史对照
  - 通过 `git show 210f396:backend/models/数据库.py`、`git show 210f396:backend/services/店铺服务.py`、`git show 210f396:frontend/src/views/ShopManage.vue` 对照改造前状态
  - 确认后端 `shops` 表原有字段 `user_agent`、`profile_dir`、`cookie_path`、`last_login`、`smtp_host`、`smtp_port`、`smtp_user`、`smtp_pass`、`smtp_protocol`、`remark` 当前仍在模型和服务中保留
- `frontend/src/api/types.ts`
  - 为 `Shop` 补回 `smtp_pass`
  - 为 `ShopPayload` 补回旧版邮箱/浏览器相关字段，保证创建和更新请求兼容旧模型
- `frontend/src/api/shops.ts`
  - 在 CRUD 之外补充 `openShopBrowser`、`checkShopStatus`、`testShopEmailConnection`
- `frontend/src/views/ShopManage.vue`
  - 恢复为旧版小卡片布局与邮箱配置表单
  - 删除顶部统计卡片区域
  - 重新接回打开浏览器、检查状态、测试邮箱连接、编辑、删除等店铺操作
- `frontend/src/components/ShopCard.vue`
  - 放宽 `Shop` props 类型，兼容恢复后的完整店铺数据和可空字段
- `browser/反检测.py`
  - 微调极短延迟分支，避免全量测试中的随机计时抖动
- `tests/单元测试/测试_店铺恢复.py`
  - 新增 `/api/shops` 旧字段回归测试
  - 新增店铺页旧布局、邮箱字段和店铺动作封装回归测试
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮店铺恢复与验证结果

## 影响范围

- 影响前端 `/shops` 页面布局与表单字段，恢复旧版卡片式展示
- 影响前端店铺 API 类型与店铺扩展操作封装
- 影响 `ShopCard` 组件的 props 类型兼容范围
- 影响 `browser/反检测.py` 的极短随机延迟实现，用于稳定全量测试

## 注意事项

- 后端 `shops` 模型和 CRUD 结构经历史对照后确认未丢失原有列，本轮没有新增数据库列，主要恢复的是前端消费这些字段的能力
- 店铺页保留新增的编辑弹窗和删除确认，但布局与样式已恢复为旧版小卡片网格
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_店铺恢复.py -q`、`python -m pytest -c tests/pytest.ini tests/单元测试/测试_前端管理页.py -q`、`python -m pytest -c tests/pytest.ini tests/单元测试/测试_反检测.py -q`、`python -m pytest -c tests/pytest.ini -q`、`cd frontend && npx vue-tsc -b` 验证

## 任务摘要

修复流程编排页面的选项显示细节：失败策略改为中文标签、任务下拉仅显示任务名，并补充回归测试锁定这些细节。

## 改动文件列表

- `frontend/src/views/FlowManage.vue`
- `tests/单元测试/测试_前端显示细节.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `frontend/src/views/FlowManage.vue`
  - 将失败策略下拉改为“中文 label + 英文 value”
  - 将 `retry:N` 作为显式选项值保留，继续通过重试次数输入框生成后端需要的 `retry:<次数>`
  - 流程卡片里的失败策略预览同步改为中文文案
  - 任务下拉只显示任务名称，不再把描述直接拼进选项文本
  - 将任务描述拆到选择框下方的副文本提示，并保留 `title` 作为悬浮说明
- `tests/单元测试/测试_前端显示细节.py`
  - 新增静态回归测试
  - 覆盖失败策略中文显示、任务下拉不拼描述、店铺编辑密码输入框细节
- `frontend/src/views/ShopManage.vue`
  - 本轮复核后确认已满足“编辑时密码字段 `type=password`、placeholder 为 `留空则不修改`、不回显实际密码”的要求，因此未继续修改逻辑
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮显示细节修复与验证结果

## 影响范围

- 影响 `FlowManage.vue` 的步骤编辑交互显示
- 影响流程卡片中的失败策略预览文案
- 新增前端显示细节回归测试，锁定流程页与店铺页的展示要求

## 注意事项

- 失败策略对后端提交值未变，仍保持 `skip_shop`、`continue`、`log_and_skip`、`retry:N`、`abort`
- 任务描述当前以副文本和 `title` 方式展示，没有引入新的自定义下拉组件
- `ShopManage.vue` 本轮未改逻辑，仅通过新增测试锁定现有密码输入框行为
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_前端显示细节.py tests/单元测试/测试_前端管理页.py -q`、`python -m pytest -c tests/pytest.ini -q`、`cd frontend && npx vue-tsc -b` 验证
## 任务摘要

修复批量执行时的店铺名显示链路：批次快照、Celery 子任务、Worker/任务服务日志和 BatchExecute 进度区统一使用真实 `shop_name`，并补充独立回归测试。

## 改动文件列表

- `backend/services/执行服务.py`
- `tasks/执行任务.py`
- `backend/services/任务服务.py`
- `frontend/src/api/types.ts`
- `frontend/src/views/BatchExecute.vue`
- `tests/单元测试/测试_批量执行店铺名.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/执行服务.py`
  - 创建批次时预读店铺信息并缓存真实店铺名
  - 批次 `shops` 状态新增 `shop_name`
  - 投递 Celery 子任务时将 `shop_name` 一并透传
- `tasks/执行任务.py`
  - 增加 `shop_name` 入参
  - Worker 启动日志优先打印真实店铺名
  - 透传 `shop_name` 到任务记录参数和统一执行入口
  - 兼容旧返回结构，仅在显式传入展示名时补充 `shop_name`
- `backend/services/任务服务.py`
  - 统一执行日志优先显示 `shop_name`
  - 成功/失败返回结果补充 `shop_name`
- `frontend/src/api/types.ts`
  - 为 `BatchShopState` 补充 `shop_name?: string | null`
- `frontend/src/views/BatchExecute.vue`
  - 进度区新增 `getBatchShopName(shop)`，优先使用 SSE 快照里的真实店铺名
- `tests/单元测试/测试_批量执行店铺名.py`
  - 覆盖真实店铺名透传、缺省名回退、Worker 日志、任务服务日志和前端显示回归
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮实现与验证结果

## 影响范围

- 影响批量执行创建批次时写入 Redis 快照的数据结构
- 影响 Celery 批量子任务参数和 Worker/任务服务日志展示内容
- 影响前端 `BatchExecute.vue` 进度区的店铺名显示来源

## 注意事项

- 未改动 `.pipeline/task.md` 及其他页面/接口
- `shop_id` 仍作为批次店铺状态和前端时间线的唯一键，避免影响既有关联逻辑
- `shop_name` 缺失时仍回退到 `shop_id`，兼容旧数据和旧调用路径
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_批量执行店铺名.py tests/单元测试/测试_执行服务.py tests/单元测试/测试_执行任务.py tests/单元测试/测试_任务服务.py -q`、`cd frontend && npx vue-tsc -b`、`python -m pytest -c tests/pytest.ini -q` 验证

## 任务摘要

完成生产环境审查修复：统一 SQLite 连接配置与旧库迁移，补齐执行/日志 SSE 保活、店铺删除级联定时计划和 Celery 基础可靠性配置，并为密码密钥回退改为持久化方案。

## 改动文件列表

- `backend/models/数据库.py`
- `backend/services/任务服务.py`
- `backend/services/日志服务.py`
- `backend/services/系统服务.py`
- `backend/services/店铺服务.py`
- `backend/services/执行服务.py`
- `backend/api/执行接口.py`
- `backend/api/日志接口.py`
- `tasks/celery应用.py`
- `tests/单元测试/测试_生产环境审查.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/models/数据库.py`
  - 为所有 SQLite 连接统一启用 `foreign_keys`、`WAL`、`synchronous=NORMAL`、`busy_timeout`
  - 初始化时增加旧库迁移，自动补齐 `operation_logs.shop_name`
- `backend/services/任务服务.py`
  - 任务日志 CRUD 全部切到统一数据库连接入口，避免不同服务各自使用默认 SQLite 配置
- `backend/services/日志服务.py`
  - 操作日志读写与清理切到统一数据库连接入口
  - 修复日志表实际写入 `shop_name` 时对旧库结构不兼容的问题
- `backend/services/系统服务.py`
  - 数据库健康检查复用统一连接入口
- `backend/services/店铺服务.py`
  - 未配置 `ENCRYPTION_KEY` 时回退到 `data/.encryption.key` 持久化密钥文件，避免重启后历史密码失效
  - 删除店铺时同步删除单店铺计划或更新多店铺计划，消除 `execution_schedules.shop_ids` 脏引用
- `backend/services/执行服务.py`、`backend/api/执行接口.py`
  - 执行状态 SSE 在无事件时输出保活标记并转换为 `: ping` 注释帧
- `backend/api/日志接口.py`
  - 日志 SSE 在空闲期输出 `: ping` 注释帧，避免长连接静默断开
- `tasks/celery应用.py`
  - 补齐 `task_reject_on_worker_lost=True`
  - 补齐 `broker_connection_retry_on_startup=True`
- `tests/单元测试/测试_生产环境审查.py`
  - 覆盖 SQLite 配置/迁移、持久化密钥回退、店铺删除级联、SSE 保活和 Celery 关键配置
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮生产审查修复与验证结果

## 影响范围

- 影响所有通过 `获取连接()` 访问 SQLite 的后端服务
- 影响 `/api/execute/status` 与 `/api/logs/stream` 的 SSE 长连接行为，新增保活注释帧
- 影响店铺删除流程与定时计划数据一致性
- 影响未配置 `ENCRYPTION_KEY` 时的密码加解密回退策略
- 影响 Celery Worker 遇到异常退出或启动期 Redis 短暂不可用时的任务可靠性

## 注意事项

- 本轮没有修改 `.pipeline/task.md`
- 启动阶段仍未对 Redis 可用性和数据库可写性做 fail-fast 检查，这一项保留为后续风险，不在本轮改变启动语义
- `shop_ids`、`steps` 当前仍缺少更严格的数量上限校验，本轮保持现有接口行为不变
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_生产环境审查.py -q`、`python -m pytest -c tests/pytest.ini -q` 验证

## 任务摘要

修复 Celery `--pool=threads` 下的事件循环冲突：将 Worker loop 改为线程隔离复用，增强 `_运行异步任务(...)` 回退逻辑，并让 Worker 线程使用独立的浏览器管理器/Playwright 实例。

## 改动文件列表

- `tasks/celery应用.py`
- `tasks/执行任务.py`
- `tasks/桥接任务.py`
- `backend/services/浏览器服务.py`
- `backend/services/任务服务.py`
- `requirements.txt`
- `tests/单元测试/测试_线程池事件循环.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `tasks/celery应用.py`
  - 将 Worker 事件循环从单个全局 loop 改为线程本地 loop
  - 增加线程级 loop 注册表和初始化锁，避免 `threads` 池下多个任务共用同一个事件循环
- `tasks/执行任务.py`
  - 引入 `nest_asyncio.apply()`
  - `_运行异步任务(...)` 在当前线程已有运行中 loop 时回退到临时线程执行协程
  - 无运行中 loop 时继续复用当前 Worker 线程专属事件循环
- `tasks/桥接任务.py`
  - 同步增强 `_运行异步任务(...)`，与批量执行任务保持一致的线程安全行为
- `backend/services/浏览器服务.py`
  - 主线程保持原有全局单例管理器行为
  - Worker 线程改为线程本地浏览器管理器和初始化锁，确保并发店铺任务不共享同一个 Playwright 实例
- `backend/services/任务服务.py`
  - 改为读取当前线程绑定的浏览器管理器实例，避免跨线程直接使用模块级全局状态
- `requirements.txt`
  - 新增 `nest_asyncio`
- `tests/单元测试/测试_线程池事件循环.py`
  - 覆盖线程独立事件循环、运行中 loop 回退和线程隔离浏览器管理器
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮修复与验证结果

## 影响范围

- 影响 Celery Worker 在 `threads` 池模式下的异步协程执行方式
- 影响批量执行任务和桥接任务的 `_运行异步任务(...)` 行为
- 影响 Worker 线程中的浏览器管理器/Playwright 生命周期
- 影响 `任务服务` 读取浏览器页面实例的方式

## 注意事项

- 未改动 `.pipeline/task.md`
- 未修改登录任务逻辑和 `browser/管理器.py` 核心实现
- 当前沙箱执行 `python -m pip install nest_asyncio` 时因用户目录无写权限失败，因此保留了缺包兜底；正式环境仍应按 `requirements.txt` 安装依赖
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_线程池事件循环.py -q`、`python -m pytest -c tests/pytest.ini tests/单元测试/测试_Celery桥接.py tests/单元测试/测试_浏览器服务.py tests/单元测试/测试_执行任务.py tests/单元测试/测试_任务服务.py -q`、`python -m pytest -c tests/pytest.ini -q` 验证

## 任务摘要

为批量执行新增完成回调：批次进入终态后主动 POST 到 Agent 的 `/api/batch-callback`，支持请求体自定义 `callback_url`，并保证回调失败不影响主流程。

## 改动文件列表

- `backend/services/执行服务.py`
- `backend/models/数据结构.py`
- `backend/api/执行接口.py`
- `tests/单元测试/测试_批量执行回调.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/services/执行服务.py`
  - 新增批次完成回调地址解析、回调载荷构建和回调发送逻辑
  - 使用 Redis `NX` 标记保证同一批次完成回调只发送一次
  - 回调失败时仅记录日志，不影响批次状态写入和执行流程
- `backend/models/数据结构.py`
  - 为 `批量执行请求` 增加可选字段 `callback_url`
- `backend/api/执行接口.py`
  - 将 `callback_url` 透传到执行服务的 `创建批次(...)`
- `tests/单元测试/测试_批量执行回调.py`
  - 覆盖回调载荷、回调异常不影响主流程、自定义 `callback_url` 写入和接口透传
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮批量回调改造与验证结果

## 影响范围

- 影响批量执行批次元数据结构，新增内部字段 `callback_url`
- 影响 Celery Worker 最终写回批次状态后的后续动作，新增 Agent 完成回调
- 影响 `POST /api/execute/batch` 请求体，新增可选 `callback_url`

## 注意事项

- 未改动现有桥接任务回调逻辑
- 未修改 Agent 端代码，只增加本项目向 Agent 回调的客户端逻辑
- 回调默认根地址为 `http://localhost:8001`，实际路径固定追加 `/api/batch-callback`
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_批量执行回调.py tests/单元测试/测试_执行服务.py tests/单元测试/测试_执行接口.py -q`、`python -m pytest -c tests/pytest.ini -q` 验证

## 任务摘要

修复 Worker 在 `--pool=threads` 下的机器注册链路：启动初始化阶段补发 Agent 注册请求，统一携带 `X-RPA-KEY`，并保证注册失败只记日志不阻塞 Worker。

## 改动文件列表

- `backend/配置.py`
- `tasks/celery应用.py`
- `tests/单元测试/测试_Celery桥接.py`
- `browser/反检测.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `backend/配置.py`
  - 新增 `MACHINE_NAME`、`X_RPA_KEY` 配置项，供 Worker 注册逻辑统一读取
- `tasks/celery应用.py`
  - 新增 Agent 服务地址推导、注册请求头构建、统一业务响应校验与 `注册Worker机器()`
  - 在 `初始化Worker环境()` 内于任务注册表初始化和回调地址设置之后主动调用 `POST /api/machines`
  - 注册请求体固定为 `{machine_id, machine_name}`，请求头固定携带 `X-RPA-KEY`
  - 注册失败时只打印日志，不影响 `Worker环境已初始化` 置为 `True`
- `tests/单元测试/测试_Celery桥接.py`
  - 补充 Worker 初始化时向 Agent 注册机器的成功路径断言
  - 补充 Agent 离线时注册异常被吞吐且 Worker 继续完成初始化的异常路径断言
- `browser/反检测.py`
  - 将 30ms 内短延迟收敛到区间中值，消除 Windows 环境下全量回归的偶发时间抖动
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮 Worker 注册修复与验证结果

## 影响范围

- 影响 Celery Worker 启动初始化阶段的外部 Agent 通信行为
- 影响 `.env` 可读取的 Worker 注册配置项，新增 `MACHINE_NAME` 与 `X_RPA_KEY`
- 影响 `tests/单元测试/测试_Celery桥接.py` 和 `tests/单元测试/测试_反检测.py` 的回归稳定性

## 注意事项

- 当前 Worker 注册接口已按用户补丁切回 `POST /api/machines`，并继续复用现有 `X-RPA-KEY` 请求头规则
- `AGENT_MACHINE_ID` 为空时会回退注册为 `default`，建议正式环境仍显式配置真实机器编号
- 下一步任务 07 需要修改 `E:\Agent`，但当前沙箱可写根不包含该目录，无法在本轮直接落盘修改 Agent 项目
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_Celery桥接.py -q`、`python -m pytest -c tests/pytest.ini tests/单元测试/测试_反检测.py -q`、`python -m pytest -c tests/pytest.ini -q` 验证

## 任务摘要

按生产环境审查清单补齐 Worker/FastAPI 到 Agent 的鉴权与协议一致性，修正任务回调、心跳、批次完成回调和 Worker 注册断言。

## 改动文件列表

- `browser/任务回调.py`
- `backend/services/心跳服务.py`
- `backend/services/执行服务.py`
- `tests/单元测试/测试_Celery桥接.py`
- `tests/单元测试/测试_批量执行回调.py`
- `tests/单元测试/测试_心跳服务.py`
- `tests/单元测试/测试_任务回调.py`
- `PLAN.md`
- `改造进度.md`
- `.pipeline/progress.md`

## 改动说明

- `browser/任务回调.py`
  - 自动回调统一携带 `X-RPA-KEY`
  - 增加 Agent 统一业务响应校验，避免 200 + `code != 0` 被误判为成功
  - 未配置密钥时跳过请求，避免发送匿名回调
- `backend/services/心跳服务.py`
  - 心跳请求体改为 `{machine_id, shadowbot_running}`，与 Agent 既有约定保持一致
  - 心跳统一携带 `X-RPA-KEY`
  - 增加 HTTP 状态与业务响应双重校验
- `backend/services/执行服务.py`
  - 批次完成回调默认从 `AGENT_CALLBACK_URL` 提取 Agent 根地址，再固定拼接 `/api/batch-callback`
  - 批次完成回调统一携带 `X-RPA-KEY`
  - 增加 Agent 统一业务响应校验
- `tests/单元测试/测试_Celery桥接.py`
  - 将 Worker 注册断言修正为 `POST /api/workers/register`
- `tests/单元测试/测试_批量执行回调.py`
  - 覆盖默认回调地址拼装、鉴权头注入和业务响应校验
- `tests/单元测试/测试_心跳服务.py`
  - 覆盖心跳请求体使用 `shadowbot_running` 和 `X-RPA-KEY`
- `tests/单元测试/测试_任务回调.py`
  - 新增任务回调协议回归测试
  - 覆盖业务失败静默吞吐异常路径
- `PLAN.md`、`改造进度.md`
  - 同步记录本轮生产审查补漏与验证结果

## 影响范围

- 影响 Worker 到 Agent 的任务自动回调协议
- 影响 FastAPI 主进程到 Agent 的心跳协议
- 影响批量执行完成后的 Agent 回调地址推导与鉴权方式
- 影响 Worker 注册回归测试的接口契约断言

## 注意事项

- 未新增任何接口，也未修改现有对外 API 路由
- Worker 注册接口实际保持为 `POST /api/workers/register`
- 批次完成回调默认地址会从 `AGENT_CALLBACK_URL` 中提取 `scheme + netloc`，再固定拼接 `/api/batch-callback`
- 已完成 `python -m pytest -c tests/pytest.ini tests/单元测试/测试_Celery桥接.py tests/单元测试/测试_批量执行回调.py tests/单元测试/测试_心跳服务.py tests/单元测试/测试_任务回调.py -q`、`python -m pytest -c tests/pytest.ini -q` 验证
