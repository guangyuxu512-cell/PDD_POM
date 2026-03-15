ask 40：前端系统设置增加机器码 + 流程执行结果显示修复
一、做什么
前端系统设置页增加"机器码"输入框，保存后更新 .env 和运行时配置
修复流程执行结果不在前端"执行结果"Tab显示的问题
二、涉及文件
frontend/src/views/Settings.vue — 增加机器码输入框
backend/services/系统服务.py — 白名单增加 agent_machine_id
backend/配置.py — 确认 AGENT_MACHINE_ID 字段存在
frontend/src/views/TaskParamsManage.vue — 修复执行结果Tab查询逻辑
backend/api/任务参数接口.py — 确认执行结果查询接口支持 flow_params 数据
测试同步更新
三、机器码设置
3.1 系统服务.py
_配置白名单 字典中新增：
"agent_machine_id": "AGENT_MACHINE_ID",
​
3.2 Settings.vue
SystemConfig 接口增加字段：
agent_machine_id?: string
​
config 初始值增加：
agent_machine_id: ''
​
loadConfig 中增加：
agent_machine_id: data.agent_machine_id || ''
​
模板中"基础配置"区域，在"Redis 地址"之前或之后，新增一个表单项：
<div class="form-group">
  <label>机器码</label>
  <input v-model="config.agent_machine_id" type="text" placeholder="例如: office-pc-001" />
  <span class="hint">用于标识当前机器的 Celery Worker 队列名称，修改后需重启 Worker 生效</span>
</div>
​
3.3 系统服务.py 获取配置
获取配置() 方法返回字典中增加：
"agent_machine_id": 配置实例.AGENT_MACHINE_ID or "",
​
四、流程执行结果显示修复
当前问题：前端"执行结果"Tab 查询的是 task_params 表（旧的单任务参数表），但流程模式的执行结果写在 flow_params 表里。
4.1 排查要点
检查 TaskParamsManage.vue 中"执行结果"Tab 的数据来源 API 路径。如果它调用的是 /api/task-params/results 或类似接口，需要确认：
该接口是否也查询 flow_params 表
如果只查 task_params，需要改为同时查 flow_params 或者优先查 flow_params
4.2 修复方向
方案A（推荐）：执行结果Tab 改为查询 flow_params 表
后端接口查询 flow_params 表，按 status 过滤（success/failed/running）
返回字段映射：id, shop_id, task_type（取 flow 最后执行的 task_name）, params（含父商品ID、新商品ID、折扣、投产比等）, status, error, executed_at
从 step_results JSON 字段中提取各步骤的结果数据（新商品ID、折扣等）
方案B：在流程执行完成后，自动往 task_params 表插入一条执行结果记录
方案A 更干净，不需要冗余写入。
4.3 具体实现
后端 任务参数接口.py 中"执行结果"相关的查询接口，修改查询 SQL：
查询 flow_params 表
筛选条件：status IN ('success', 'failed', 'running', 'cancelled')
支持按店铺、任务类型、状态、批次、日期范围筛选
从 params JSON 提取：父商品ID、新商品ID
从 step_results JSON 提取各步骤的结果：折扣、投产比等
按 updated_at DESC 排序
前端 TaskParamsManage.vue 执行结果Tab：
确认调用的是正确的 API 接口
列映射与后端返回字段对齐
五、约束
机器码修改后，提示用户需要重启 Worker 才能生效
机器码为空时使用默认值 default（与现有逻辑一致）
执行结果查询必须支持分页
不要删除 task_params 表的旧数据和旧接口，保持兼容
测试同步更新，确保 pytest 通过