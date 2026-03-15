Task 45：规则配置前端页面
一、做什么
将数据管理页"规则配置"Tab 的"开发中"占位替换为完整的规则 CRUD 界面：规则列表 + 筛选 + 新建/编辑弹窗（含可视化条件编辑器和动作编辑器）+ 启用/禁用 + 删除 + 测试匹配。
二、涉及文件
frontend/src/views/RuleManage.vue — 新建，规则配置完整页面
frontend/src/views/DataManage.vue — 修改，用 RuleManage 组件替换占位
frontend/src/api/index.ts — 确认已有 get/post/put/del 方法可用（已有则不改）
三、DataManage.vue 修改
把"规则配置"Tab 的占位替换为组件引用：
<!-- 原来的占位 -->
<div v-if="activeTab === 'rules'" class="placeholder">
  <p>📋 规则配置功能开发中...</p>
</div>

<!-- 替换为 -->
<RuleManage v-if="activeTab === 'rules'" :showTitle="false" />
​
script 中添加：
import RuleManage from './RuleManage.vue'
​
四、RuleManage.vue 页面结构
4.1 整体布局
┌─────────────────────────────────────────────────────┐
│ 规则配置                            [+ 新建规则] [测试匹配] │
├─────────────────────────────────────────────────────┤
│ 筛选: 平台 [全部▾]  业务 [全部▾]  店铺 [全部▾]  [查询]    │
├─────────────────────────────────────────────────────┤
│ 名称        平台   业务   店铺   优先级  启用  操作         │
│ ─────────────────────────────────────────────────── │
│ 小额自动退   pdd   售后    *     100    ✅   编辑 删除    │
│ 中额退款通知 pdd   售后    *      90    ✅   编辑 删除    │
│ 大额人工审核 pdd   售后    *      80    ✅   编辑 删除    │
│ ...                                                  │
└─────────────────────────────────────────────────────┘
​
4.2 数据模型
interface Rule {
  id: number
  name: string
  platform: string
  business: string
  shop_id: string
  priority: number
  conditions: ConditionGroup
  actions: Action[]
  enabled: boolean
  created_at: string
  updated_at: string
}

interface ConditionGroup {
  operator: 'and' | 'or'
  rules: (ConditionRule | ConditionGroup)[]
}

interface ConditionRule {
  field: string
  op: string
  value: string | number
}

interface Action {
  type: string       // "页面操作" | "微信通知" | "飞书通知" | "标记"
  action: string     // "同意退款" | "同意退货" | "拒绝" | "发消息" | "发工单" | "人工审核"
  template?: string  // 微信消息模板（可选）
}
​
4.3 API 调用
// 规则列表
const loadRules = async () => {
  const params = new URLSearchParams()
  if (filter.platform) params.append('platform', filter.platform)
  if (filter.business) params.append('business', filter.business)
  if (filter.shop_id) params.append('shop_id', filter.shop_id)
  rules.value = await get<Rule[]>(`/api/rules?${params}`)
}

// 创建
const createRule = async (data: Partial<Rule>) => {
  await post('/api/rules', data)
}

// 更新
const updateRule = async (id: number, data: Partial<Rule>) => {
  await put(`/api/rules/${id}`, data)
}

// 删除
const deleteRule = async (id: number) => {
  await del(`/api/rules/${id}`)
}

// 切换启用
const toggleRule = async (id: number, enabled: boolean) => {
  await put(`/api/rules/${id}/toggle`, { enabled })
}

// 测试匹配
const testMatch = async (data: object) => {
  return await post<any>('/api/rules/match', data)
}
​
4.4 列表功能
表格展示所有规则，列：名称、平台、业务、店铺、优先级、启用（开关）、操作（编辑/删除）
顶部筛选栏：平台下拉（全部/pdd/taobao/jd）、业务下拉（全部/售后/推广/限时限量）、店铺下拉（全部 + 从 /api/shops 加载店铺列表）
启用列用 <input type="checkbox"> 样式的开关，点击直接调 toggle API
删除前弹 confirm("确定删除规则 xxx？")
列表按 priority 降序排列
五、新建/编辑弹窗
点击"新建规则"或"编辑"时弹出模态框：
┌───────────────────────────────────────────┐
│ 新建规则 / 编辑规则                    [X]  │
├───────────────────────────────────────────┤
│ 规则名称  [________________]               │
│ 平台     [pdd ▾]                          │
│ 业务类型  [售后 ▾]                         │
│ 店铺     [全部 ▾]                          │
│ 优先级   [100]                             │
│                                            │
│ ── 条件 ──                                 │
│ 逻辑关系: [AND ▾]                          │
│ ┌─────────────────────────────────────┐   │
│ │ 字段 [售后类型▾] 操作 [== ▾] 值 [仅退款]  │   │
│ │                              [- 删除]  │   │
│ │ 字段 [退款金额▾] 操作 [<= ▾] 值 [10   ]  │   │
│ │                              [- 删除]  │   │
│ │                      [+ 添加条件]       │   │
│ └─────────────────────────────────────┘   │
│                                            │
│ ── 动作 ──                                 │
│ ┌─────────────────────────────────────┐   │
│ │ 类型 [页面操作▾] 动作 [同意退款▾]        │   │
│ │                              [- 删除]  │   │
│ │ 类型 [微信通知▾] 动作 [发消息 ▾]         │   │
│ │ 模板 [亲，您的退款已处理~_________]      │   │
│ │                              [- 删除]  │   │
│ │                      [+ 添加动作]       │   │
│ └─────────────────────────────────────┘   │
│                                            │
│              [取消]  [保存]                  │
└───────────────────────────────────────────┘
​
5.1 条件编辑器
逻辑关系下拉：and / or
每行条件：字段下拉 + 操作符下拉 + 值输入框 + 删除按钮
字段下拉选项：售后类型、退款金额、商品名称、退款原因、发货状态、订单号（也允许手动输入自定义字段名）
操作符下拉：==、!=、>、<、>=、<=、in、not_in、contains
"+ 添加条件"按钮追加一行
暂不支持嵌套条件组（界面太复杂），只支持一层 and/or + 多条规则
5.2 动作编辑器
每行动作：类型下拉 + 动作下拉 + 可选模板输入 + 删除按钮
类型下拉：页面操作、微信通知、飞书通知、标记
动作下拉根据类型联动：
页面操作：同意退款、同意退货、拒绝
微信通知：发消息
飞书通知：发工单、通知
标记：人工审核、跳过
当类型为"微信通知"时，显示模板输入框（placeholder: 亲，您的退款 {退款金额} 元已处理~）
"+ 添加动作"按钮追加一行
5.3 保存逻辑
点击"保存"时：
校验：名称不能为空、至少一条条件、至少一个动作
组装 JSON：conditions 为 { operator, rules: [...] }，actions 为 [{ type, action, template? }]
调用 POST（新建）或 PUT（编辑）
成功后关闭弹窗、刷新列表、toast 提示
六、测试匹配功能
点击顶部"测试匹配"按钮弹出小弹窗：
┌─────────────────────────────────┐
│ 测试规则匹配                 [X] │
├─────────────────────────────────┤
│ 平台    [pdd ▾]                 │
│ 业务    [售后 ▾]                │
│ 店铺    [全部 ▾]                │
│ 测试数据（JSON）:               │
│ ┌─────────────────────────┐    │
│ │ {                       │    │
│ │   "售后类型": "仅退款",   │    │
│ │   "退款金额": 8          │    │
│ │ }                       │    │
│ └─────────────────────────┘    │
│               [匹配测试]        │
│                                 │
│ 匹配结果:                       │
│ ✅ 命中规则: 小额自动退款        │
│ 动作: [同意退款]                │
└─────────────────────────────────┘
​
调用 POST /api/rules/match，展示命中的规则名称和动作列表。
七、样式
与现有页面风格一致：
表格用 <table> + 现有的白底卡片 + 灰色边框样式
弹窗用自定义 modal（.modal-overlay + .modal-content），与现有弹窗风格一致
按钮用现有的 .btn、.btn-primary、.btn-secondary class
开关用 checkbox + 自定义样式（圆角滑块）
条件/动作编辑器每行用 flex 布局，gap: 8px
八、约束
只新建 RuleManage.vue，修改 DataManage.vue 一行引用
不使用任何第三方 UI 组件库（Element UI、Ant Design 等），保持现有手写风格
API 前缀 /api/rules，对应后端已有的规则接口
条件编辑器暂不支持嵌套（只支持一层 and/or），后续需要再加
字段下拉允许手动输入自定义字段名（用 <input list="..."> + <datalist> 实现）
删除确认用原生 confirm()
表格为空时显示"暂无规则，点击上方"新建规则"添加"
前端类型校验确保 conditions 和 actions 格式正确再提交
cd frontend && npx vue-tsc -b 类型检查通过