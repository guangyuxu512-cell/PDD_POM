文件：frontend/src/views/BatchExecute.vue

目标：将批量执行页面改为紧凑表格布局。

因为这个文件较大（需完整查看现有结构），给 Codex 的核心指令：

1. 执行状态区域：不管现在用的是什么布局（卡片/列表），全部改为 <table> 表格：
   列定义：店铺名称 | 当前步骤 | 进度 | 状态 | 耗时 | 操作

2. 状态列用彩色标签（Tag）：
   - waiting → 灰色背景 "等待中"
   - running → 蓝色背景 "执行中"
   - completed → 绿色背景 "已完成"
   - failed → 红色背景 "失败"
   - stopped → 黄色背景 "已停止"

3. 进度列用一个简单的 CSS 进度条：
   <div class="progress-bar"><div class="progress-fill" :style="{width: percent + '%'}"></div></div>

4. 表格上方用一行汇总文字（类似 FlowManage 的 inline-stats）：
   "批次 {id} · 总计 {n} · ✅ {completed} · 🔄 {running} · ❌ {failed}"

5. 表格每行高度不超过 44px。

样式参考 FlowManage.vue 中 .flow-table 的风格保持一致。

验收：
- 10 个店铺执行时表格流畅更新
- 状态标签颜色正确
- 点击"查看详情"可看步骤明细

文件：frontend/src/views/ScheduleManage.vue

目标：统一改为表格风格。

1. 定时任务列表改为 <table>：
   列定义：开关(Switch) | 任务名称 | 执行流程 | 执行周期 | 上次执行 | 下次执行 | 目标店铺数 | 操作

2. 表格行高不超过 44px。

3. 删除所有大卡片相关的 HTML 和 CSS（如 .task-card、.schedule-card 等）。

4. 新增/编辑弹窗保持与 FlowManage 编辑弹窗一致的风格：
   width="min(80vw, 900px)", max-height: 80vh

5. 样式参考 FlowManage.vue 的 .flow-table 风格。

验收：
- 5+ 个定时任务在一屏内显示
- 开关可切换启用/禁用
- 视觉风格与流程管理页一致