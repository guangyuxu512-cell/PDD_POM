# Task 15：task_params 记录支持启用/禁用/重置 + 发布次数展开

## 目标
1. 每条 task_params 记录可以自由启用、禁用、重置
2. CSV 导入支持"发布次数"列，自动展开成 N 条记录
3. 记录导入后长期存在，每天可以重复使用，不用每天重新导入

## 改动范围
- backend/models/数据库.py（task_params 表加字段）
- backend/services/任务参数服务.py（新增启用/禁用/重置/批量重置接口逻辑，CSV 展开逻辑）
- backend/api/任务参数接口.py（新增 API）
- 前端 任务参数管理页（加按钮和操作列）

## 一、数据库改动

task_params 表新增字段：
- enabled INTEGER DEFAULT 1  — 1=启用 0=禁用
- run_count INTEGER DEFAULT 0  — 已执行次数（每次执行完 +1，方便统计）

用 ALTER TABLE 补字段，兼容已有数据。

## 二、后端逻辑改动

### 1) 任务服务取记录的逻辑改为：
WHERE shop_id=? AND task_name=? AND status='pending' AND enabled=1
ORDER BY id ASC LIMIT 1

只取 enabled=1 的记录。disabled 的跳过不执行。

### 2) 执行完成后：
- status 改为 success/failed
- run_count += 1

### 3) 新增 API

| 方法 | 路径 | 作用 |
|---|---|---|
| PUT | /api/task-params/{id}/enable | 启用单条记录（enabled=1） |
| PUT | /api/task-params/{id}/disable | 禁用单条记录（enabled=0） |
| PUT | /api/task-params/{id}/reset | 重置单条记录（status='pending'，error=null，result='{}'） |
| PUT | /api/task-params/batch-reset | 批量重置：按筛选条件（task_name、shop_id、status）把匹配的记录全部重置为 pending |
| PUT | /api/task-params/batch-enable | 批量启用 |
| PUT | /api/task-params/batch-disable | 批量禁用 |

### 4) CSV 导入展开逻辑

CSV 新增可选列"发布次数"：
- 如果有这列且值 > 1，把这一行展开成 N 条 pending 记录
- 如果没有这列或值为空，默认 1 条
- 每条展开的记录 params JSON 里加一个 "batch_index": 1/2/3... 方便区分

CSV 示例：
  店铺ID,父商品ID,新标题,发布次数
  QinLin生活馆,916453776556,夏季新款连衣裙,3
  QinLin生活馆,916453776557,,1

导入后 task_params 表会有 4 条记录（第一行展开 3 条 + 第二行 1 条）。

## 三、前端改动

### 1) 表格新增列
- "启用"列：显示开关（Switch 组件），点击切换 enabled 状态
- "已执行次数"列：显示 run_count

### 2) 操作列新增按钮
- "重置"按钮（status 不是 pending 时显示）→ 调用 PUT /api/task-params/{id}/reset
- 点击后该记录 status 变回 pending，可以再次执行

### 3) 顶部操作栏新增
- "批量重置"按钮 → 按当前筛选条件把所有 failed/success 记录重置为 pending
- "批量启用"/"批量禁用"按钮

### 4) 状态颜色更新
- pending 灰色
- running 蓝色
- success 绿色
- failed 红色
- disabled 的行整行变淡/半透明，视觉上区分

## 四、日常使用场景

### 每天重复执行
1. 第一次导入 CSV，记录入库，状态 pending
2. 执行任务，状态变 success/failed
3. 第二天想再跑 → 前端点"批量重置" → 所有记录变回 pending → 再执行
4. 某些记录今天不想跑 → 点禁用开关 → 该记录被跳过
5. 明天又想跑 → 点启用开关 → 下次执行时会被读取

### 新增商品
直接在前端手动添加一条记录，或者导入新的 CSV（会追加，不会覆盖已有记录）。

### 某条记录永久不用了
删除即可（已有删除功能）。

## 架构红线
- 后端中文命名
- 前端英文命名
- 重置只改 status/error/result，不动 params 和 enabled
- 批量操作要带筛选条件，不能无条件全表操作

## 验收标准
- 单条启用/禁用/重置正常
- 批量重置/启用/禁用正常
- 禁用的记录执行时被跳过
- 重置后的记录可以再次被执行
- CSV "发布次数"列正确展开成多条记录
- run_count 每次执行后 +1
- 前端 Switch 开关切换即时生效
- python -m pytest -c tests/pytest.ini -q 全部通过
- npx vue-tsc -b 通过