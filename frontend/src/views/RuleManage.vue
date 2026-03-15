<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { del, get, post, put } from '../api/index'
import { listShops } from '../api/shops'
import type { PaginatedList, Shop } from '../api/types'
import { toast } from '../utils/toast'

type PlatformOption = 'pdd' | 'taobao' | 'jd'
type BusinessOption = '售后' | '推广' | '限时限量'
type LogicOperator = 'and' | 'or'
type CompareOperator = '==' | '!=' | '>' | '<' | '>=' | '<=' | 'in' | 'not_in' | 'contains'
type ActionType = '页面操作' | '微信通知' | '飞书通知' | '标记'

interface ConditionRule {
  field: string
  op: CompareOperator
  value: string | number
}

interface ConditionGroup {
  operator: LogicOperator
  rules: ConditionRule[]
}

interface Action {
  type: string
  action: string
  template?: string
}

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

interface RuleListResponse {
  list: Rule[]
  total: number
}

interface ConditionDraft extends ConditionRule {
  id: string
}

interface ActionDraft {
  id: string
  type: ActionType
  action: string
  template: string
}

interface RuleForm {
  name: string
  platform: string
  business: string
  shop_id: string
  priority: number
  conditions: {
    operator: LogicOperator
    rules: ConditionDraft[]
  }
  actions: ActionDraft[]
}

interface MatchResult {
  rule_name: string
  rule_id: number | null
  actions: Action[]
}

const props = withDefaults(defineProps<{ showTitle?: boolean }>(), {
  showTitle: true,
})

const platformOptions: PlatformOption[] = ['pdd', 'taobao', 'jd']
const businessOptions: BusinessOption[] = ['售后', '推广', '限时限量']
const logicOptions: LogicOperator[] = ['and', 'or']
const operatorOptions: CompareOperator[] = ['==', '!=', '>', '<', '>=', '<=', 'in', 'not_in', 'contains']
const conditionFieldOptions = ['售后类型', '退款金额', '商品名称', '退款原因', '发货状态', '订单号']
const actionTypeOptions: ActionType[] = ['页面操作', '微信通知', '飞书通知', '标记']
const actionOptionsMap: Record<ActionType, string[]> = {
  页面操作: ['同意退款', '同意退货', '拒绝'],
  微信通知: ['发消息'],
  飞书通知: ['发工单', '通知'],
  标记: ['人工审核', '跳过'],
}

const rules = ref<Rule[]>([])
const shops = ref<Shop[]>([])
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const showEditor = ref(false)
const showTestMatch = ref(false)
const editingRuleId = ref<number | null>(null)
const matchResult = ref<MatchResult | null>(null)

const filter = ref({
  platform: '',
  business: '',
  shop_id: '',
})

const testForm = ref({
  platform: 'pdd',
  business: '售后',
  shop_id: '*',
  dataText: '{\n  "售后类型": "仅退款",\n  "退款金额": 8\n}',
})

const form = ref<RuleForm>(createEmptyForm())

const sortedRules = computed(() =>
  [...rules.value].sort((left, right) => {
    if (right.priority !== left.priority) {
      return right.priority - left.priority
    }
    return right.id - left.id
  }),
)

const editorTitle = computed(() => (editingRuleId.value ? '编辑规则' : '新建规则'))
const matchActionSummary = computed(() =>
  (matchResult.value?.actions || []).map((action) => action.action).join(' / ') || '-',
)

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`
}

function createEmptyCondition(): ConditionDraft {
  return {
    id: createId('condition'),
    field: '售后类型',
    op: '==',
    value: '',
  }
}

function getActionOptions(type: ActionType) {
  return actionOptionsMap[type] || []
}

function createEmptyAction(type: ActionType = '页面操作'): ActionDraft {
  return {
    id: createId('action'),
    type,
    action: getActionOptions(type)[0] || '',
    template: type === '微信通知' ? '亲，您的退款 {退款金额} 元已处理~' : '',
  }
}

function createEmptyForm(): RuleForm {
  return {
    name: '',
    platform: 'pdd',
    business: '售后',
    shop_id: '*',
    priority: 100,
    conditions: {
      operator: 'and',
      rules: [createEmptyCondition()],
    },
    actions: [createEmptyAction()],
  }
}

function normalizeConditionRule(rule?: Partial<ConditionRule>): ConditionDraft {
  return {
    id: createId('condition'),
    field: String(rule?.field || '').trim(),
    op: (rule?.op as CompareOperator) || '==',
    value: rule?.value ?? '',
  }
}

function normalizeActionDraft(action?: Partial<Action>): ActionDraft {
  const type = actionTypeOptions.includes(action?.type as ActionType)
    ? (action?.type as ActionType)
    : '页面操作'
  const options = getActionOptions(type)
  const normalizedAction = String(action?.action || '').trim()

  return {
    id: createId('action'),
    type,
    action: options.includes(normalizedAction) ? normalizedAction : options[0] || '',
    template: String(action?.template || (type === '微信通知' ? '亲，您的退款 {退款金额} 元已处理~' : '')).trim(),
  }
}

function toRuleForm(rule: Rule): RuleForm {
  const rulesFromConditionGroup = Array.isArray(rule.conditions?.rules) ? rule.conditions.rules : []
  const normalizedConditions = rulesFromConditionGroup
    .filter((item): item is ConditionRule => Boolean(item && typeof item === 'object' && 'field' in item))
    .map((item) => normalizeConditionRule(item))

  const normalizedActions = Array.isArray(rule.actions) ? rule.actions.map((action) => normalizeActionDraft(action)) : []

  return {
    name: rule.name,
    platform: rule.platform || 'pdd',
    business: rule.business || '售后',
    shop_id: rule.shop_id || '*',
    priority: Number(rule.priority || 0),
    conditions: {
      operator: rule.conditions?.operator === 'or' ? 'or' : 'and',
      rules: normalizedConditions.length ? normalizedConditions : [createEmptyCondition()],
    },
    actions: normalizedActions.length ? normalizedActions : [createEmptyAction()],
  }
}

function buildRuleUrl() {
  const params = new URLSearchParams()
  if (filter.value.platform) {
    params.append('platform', filter.value.platform)
  }
  if (filter.value.business) {
    params.append('business', filter.value.business)
  }
  if (filter.value.shop_id) {
    params.append('shop_id', filter.value.shop_id)
  }

  const query = params.toString()
  return query ? `/api/rules?${query}` : '/api/rules'
}

async function loadRules() {
  loading.value = true
  try {
    const result = await get<RuleListResponse | Rule[]>(buildRuleUrl())
    rules.value = Array.isArray(result) ? result : result.list || []
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载规则列表失败'
    toast.error(message)
  } finally {
    loading.value = false
  }
}

async function loadShopsData() {
  try {
    const result = await listShops()
    shops.value = (result as PaginatedList<Shop>).list || []
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载店铺列表失败'
    toast.error(message)
  }
}

async function loadInitialData() {
  await Promise.all([loadShopsData(), loadRules()])
}

function openCreateDialog() {
  editingRuleId.value = null
  form.value = createEmptyForm()
  showEditor.value = true
}

function openEditDialog(rule: Rule) {
  editingRuleId.value = rule.id
  form.value = toRuleForm(rule)
  showEditor.value = true
}

function closeEditor() {
  showEditor.value = false
}

function openTestMatchDialog() {
  matchResult.value = null
  showTestMatch.value = true
}

function closeTestMatchDialog() {
  showTestMatch.value = false
}

function addCondition() {
  form.value.conditions.rules.push(createEmptyCondition())
}

function removeCondition(id: string) {
  form.value.conditions.rules = form.value.conditions.rules.filter((rule) => rule.id !== id)
}

function addAction() {
  form.value.actions.push(createEmptyAction())
}

function removeAction(id: string) {
  form.value.actions = form.value.actions.filter((action) => action.id !== id)
}

function handleActionTypeChange(action: ActionDraft) {
  const options = getActionOptions(action.type)
  action.action = options[0] || ''
  action.template = action.type === '微信通知' ? (action.template || '亲，您的退款 {退款金额} 元已处理~') : ''
}

function normalizeConditionValue(operator: CompareOperator, rawValue: string | number) {
  const text = String(rawValue).trim()
  if (!text) {
    return ''
  }
  if (['>', '<', '>=', '<='].includes(operator) && !Number.isNaN(Number(text))) {
    return Number(text)
  }
  return text
}

function buildPayload() {
  return {
    name: form.value.name.trim(),
    platform: form.value.platform,
    business: form.value.business,
    shop_id: form.value.shop_id || '*',
    priority: Number(form.value.priority || 0),
    conditions: {
      operator: form.value.conditions.operator,
      rules: form.value.conditions.rules.map((rule) => ({
        field: rule.field.trim(),
        op: rule.op,
        value: normalizeConditionValue(rule.op, rule.value),
      })),
    },
    actions: form.value.actions.map((action) => {
      const payload: Action = {
        type: action.type,
        action: action.action,
      }
      if (action.type === '微信通知' && action.template.trim()) {
        payload.template = action.template.trim()
      }
      return payload
    }),
  }
}

function validateForm() {
  if (!form.value.name.trim()) {
    toast.warning('名称不能为空')
    return false
  }

  if (!form.value.conditions.rules.length) {
    toast.warning('至少一条条件')
    return false
  }

  if (!form.value.actions.length) {
    toast.warning('至少一个动作')
    return false
  }

  const hasInvalidCondition = form.value.conditions.rules.some(
    (rule) => !rule.field.trim() || String(rule.value).trim() === '',
  )
  if (hasInvalidCondition) {
    toast.warning('请完整填写条件')
    return false
  }

  const hasInvalidAction = form.value.actions.some((action) => !action.type || !action.action)
  if (hasInvalidAction) {
    toast.warning('请完整填写动作')
    return false
  }

  return true
}

async function handleSave() {
  if (!validateForm()) {
    return
  }

  saving.value = true
  try {
    const payload = buildPayload()
    if (editingRuleId.value) {
      await put(`/api/rules/${editingRuleId.value}`, payload)
      toast.success('规则已更新')
    } else {
      await post('/api/rules', payload)
      toast.success('规则已创建')
    }
    closeEditor()
    await loadRules()
  } catch (error) {
    const message = error instanceof Error ? error.message : '保存规则失败'
    toast.error(message)
  } finally {
    saving.value = false
  }
}

async function handleDelete(rule: Rule) {
  if (!window.confirm(`确定删除规则 ${rule.name}？`)) {
    return
  }

  try {
    await del(`/api/rules/${rule.id}`)
    toast.success('规则已删除')
    await loadRules()
  } catch (error) {
    const message = error instanceof Error ? error.message : '删除规则失败'
    toast.error(message)
  }
}

async function handleToggle(rule: Rule, event: Event) {
  const target = event.target as HTMLInputElement | null
  const enabled = Boolean(target?.checked)

  try {
    await put(`/api/rules/${rule.id}/toggle`, { enabled })
    toast.success(enabled ? '规则已启用' : '规则已禁用')
  } catch (error) {
    const message = error instanceof Error ? error.message : '切换规则状态失败'
    toast.error(message)
  } finally {
    await loadRules()
  }
}

async function handleTestMatch() {
  let parsedData: Record<string, unknown>

  try {
    parsedData = JSON.parse(testForm.value.dataText)
  } catch {
    toast.error('请输入有效的 JSON')
    return
  }

  testing.value = true
  try {
    matchResult.value = await post<MatchResult>('/api/rules/match', {
      platform: testForm.value.platform,
      business: testForm.value.business,
      shop_id: testForm.value.shop_id || '*',
      data: parsedData,
    })
    toast.success('匹配测试完成')
  } catch (error) {
    const message = error instanceof Error ? error.message : '测试匹配失败'
    toast.error(message)
  } finally {
    testing.value = false
  }
}

function formatShopName(shopId: string) {
  if (!shopId || shopId === '*') {
    return '*'
  }
  return shops.value.find((shop) => shop.id === shopId)?.name || shopId
}

onMounted(() => {
  void loadInitialData()
})
</script>

<template>
  <div class="rule-manage">
    <div class="header">
      <div>
        <h1 v-if="props.showTitle">规则配置</h1>
        <h2 v-else>规则配置</h2>
        <p class="header-tip">配置条件-动作规则，用于售后、推广和限时限量等自动决策。</p>
      </div>

      <div class="header-actions">
        <button class="btn btn-primary" @click="openCreateDialog">+ 新建规则</button>
        <button class="btn btn-secondary" @click="openTestMatchDialog">测试匹配</button>
      </div>
    </div>

    <div class="filters">
      <span class="filter-label">筛选:</span>
      <select v-model="filter.platform" class="filter-select">
        <option value="">全部平台</option>
        <option v-for="platform in platformOptions" :key="platform" :value="platform">{{ platform }}</option>
      </select>
      <select v-model="filter.business" class="filter-select">
        <option value="">全部业务</option>
        <option v-for="business in businessOptions" :key="business" :value="business">{{ business }}</option>
      </select>
      <select v-model="filter.shop_id" class="filter-select">
        <option value="">全部店铺</option>
        <option v-for="shop in shops" :key="shop.id" :value="shop.id">{{ shop.name }}</option>
      </select>
      <button class="btn btn-primary" @click="loadRules">查询</button>
    </div>

    <div class="table-card">
      <table class="rule-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>平台</th>
            <th>业务</th>
            <th>店铺</th>
            <th>优先级</th>
            <th>启用</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="empty-state">加载中...</td>
          </tr>
          <tr v-else-if="sortedRules.length === 0">
            <td colspan="7" class="empty-state">暂无规则，点击上方"新建规则"添加</td>
          </tr>
          <tr v-for="rule in sortedRules" v-else :key="rule.id">
            <td>{{ rule.name }}</td>
            <td>{{ rule.platform }}</td>
            <td>{{ rule.business }}</td>
            <td>{{ formatShopName(rule.shop_id) }}</td>
            <td>{{ rule.priority }}</td>
            <td>
              <label class="switch">
                <input type="checkbox" :checked="rule.enabled" @change="handleToggle(rule, $event)" />
                <span class="switch-slider" />
              </label>
            </td>
            <td>
              <div class="action-group">
                <button class="btn-action btn-edit" @click="openEditDialog(rule)">编辑</button>
                <button class="btn-action btn-delete" @click="handleDelete(rule)">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showEditor" class="modal-overlay" @click.self="closeEditor">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>{{ editorTitle }}</h3>
          <button class="modal-close" @click="closeEditor">×</button>
        </div>

        <div class="modal-body">
          <div class="form-grid">
            <label class="form-item">
              <span>规则名称</span>
              <input v-model="form.name" type="text" placeholder="请输入规则名称" />
            </label>

            <label class="form-item">
              <span>平台</span>
              <select v-model="form.platform">
                <option v-for="platform in platformOptions" :key="platform" :value="platform">{{ platform }}</option>
              </select>
            </label>

            <label class="form-item">
              <span>业务类型</span>
              <select v-model="form.business">
                <option v-for="business in businessOptions" :key="business" :value="business">{{ business }}</option>
              </select>
            </label>

            <label class="form-item">
              <span>店铺</span>
              <select v-model="form.shop_id">
                <option value="*">全部</option>
                <option v-for="shop in shops" :key="shop.id" :value="shop.id">{{ shop.name }}</option>
              </select>
            </label>

            <label class="form-item form-item-small">
              <span>优先级</span>
              <input v-model.number="form.priority" type="number" min="0" />
            </label>
          </div>

          <section class="editor-section">
            <div class="section-header">
              <h4>条件</h4>
              <label class="inline-field">
                <span>逻辑关系</span>
                <select v-model="form.conditions.operator">
                  <option v-for="logic in logicOptions" :key="logic" :value="logic">{{ logic.toUpperCase() }}</option>
                </select>
              </label>
            </div>

            <div class="editor-list">
              <div v-for="condition in form.conditions.rules" :key="condition.id" class="editor-row">
                <input
                  v-model="condition.field"
                  list="rule-field-options"
                  class="field-input"
                  placeholder="字段名"
                />
                <select v-model="condition.op" class="operator-select">
                  <option v-for="operator in operatorOptions" :key="operator" :value="operator">{{ operator }}</option>
                </select>
                <input v-model="condition.value" type="text" class="value-input" placeholder="条件值" />
                <button class="btn-action btn-delete" @click="removeCondition(condition.id)">删除</button>
              </div>

              <button class="btn btn-light section-action" @click="addCondition">+ 添加条件</button>
            </div>
          </section>

          <section class="editor-section">
            <div class="section-header">
              <h4>动作</h4>
            </div>

            <div class="editor-list">
              <div v-for="action in form.actions" :key="action.id" class="editor-row editor-row-action">
                <select v-model="action.type" class="type-select" @change="handleActionTypeChange(action)">
                  <option v-for="type in actionTypeOptions" :key="type" :value="type">{{ type }}</option>
                </select>
                <select v-model="action.action" class="action-select">
                  <option v-for="option in getActionOptions(action.type)" :key="option" :value="option">{{ option }}</option>
                </select>
                <input
                  v-if="action.type === '微信通知'"
                  v-model="action.template"
                  type="text"
                  class="template-input"
                  placeholder="亲，您的退款 {退款金额} 元已处理~"
                />
                <button class="btn-action btn-delete" @click="removeAction(action.id)">删除</button>
              </div>

              <button class="btn btn-light section-action" @click="addAction">+ 添加动作</button>
            </div>
          </section>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeEditor">取消</button>
          <button class="btn btn-primary" :disabled="saving" @click="handleSave">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showTestMatch" class="modal-overlay" @click.self="closeTestMatchDialog">
      <div class="modal-content">
        <div class="modal-header">
          <h3>测试规则匹配</h3>
          <button class="modal-close" @click="closeTestMatchDialog">×</button>
        </div>

        <div class="modal-body">
          <div class="form-grid">
            <label class="form-item">
              <span>平台</span>
              <select v-model="testForm.platform">
                <option v-for="platform in platformOptions" :key="platform" :value="platform">{{ platform }}</option>
              </select>
            </label>

            <label class="form-item">
              <span>业务</span>
              <select v-model="testForm.business">
                <option v-for="business in businessOptions" :key="business" :value="business">{{ business }}</option>
              </select>
            </label>

            <label class="form-item">
              <span>店铺</span>
              <select v-model="testForm.shop_id">
                <option value="*">全部</option>
                <option v-for="shop in shops" :key="shop.id" :value="shop.id">{{ shop.name }}</option>
              </select>
            </label>
          </div>

          <label class="form-item form-item-block">
            <span>测试数据（JSON）</span>
            <textarea v-model="testForm.dataText" rows="8" />
          </label>

          <div class="match-result">
            <button class="btn btn-primary" :disabled="testing" @click="handleTestMatch">
              {{ testing ? '匹配中...' : '匹配测试' }}
            </button>

            <div v-if="matchResult" class="match-result-card">
              <p>✅ 命中规则: {{ matchResult.rule_name }}</p>
              <p>动作: {{ matchActionSummary }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <datalist id="rule-field-options">
      <option v-for="field in conditionFieldOptions" :key="field" :value="field" />
    </datalist>
  </div>
</template>

<style scoped>
.rule-manage {
  color: #1a1a2e;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.header h1,
.header h2 {
  margin: 0;
  color: #1a1a2e;
}

.header h1 {
  font-size: 28px;
}

.header h2 {
  font-size: 22px;
}

.header-tip {
  margin: 8px 0 0;
  color: #6b7280;
  line-height: 1.5;
}

.header-actions,
.action-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filters {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding: 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.filter-label {
  color: #4b5563;
  font-weight: 600;
}

.filter-select,
.form-item input,
.form-item select,
.form-item textarea,
.field-input,
.operator-select,
.value-input,
.type-select,
.action-select,
.template-input {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #ffffff;
  color: #1a1a2e;
  font-size: 14px;
}

.filter-select {
  min-width: 160px;
}

.table-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow-x: auto;
}

.rule-table {
  width: 100%;
  border-collapse: collapse;
}

.rule-table thead {
  background: #f3f4f6;
}

.rule-table th,
.rule-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  font-size: 14px;
}

.rule-table tbody tr:nth-child(even) {
  background: #f9fafb;
}

.empty-state {
  text-align: center;
  color: #9ca3af;
  padding: 48px 16px;
}

.btn,
.btn-action,
.modal-close {
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn {
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 600;
}

.btn-primary {
  background: #2563eb;
  color: #ffffff;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #e5e7eb;
  color: #111827;
}

.btn-secondary:hover {
  background: #d1d5db;
}

.btn-light {
  background: #eff6ff;
  color: #1d4ed8;
}

.btn-light:hover {
  background: #dbeafe;
}

.btn-action {
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  color: #ffffff;
}

.btn-edit {
  background: #0ea5e9;
}

.btn-edit:hover {
  background: #0284c7;
}

.btn-delete {
  background: #ef4444;
}

.btn-delete:hover {
  background: #dc2626;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.switch {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}

.switch input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.switch-slider {
  position: relative;
  width: 42px;
  height: 24px;
  border-radius: 999px;
  background: #cbd5e1;
  transition: background 0.2s ease;
}

.switch-slider::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ffffff;
  transition: transform 0.2s ease;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.2);
}

.switch input:checked + .switch-slider {
  background: #10b981;
}

.switch input:checked + .switch-slider::after {
  transform: translateX(18px);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 2000;
}

.modal-content {
  width: min(760px, 100%);
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.24);
  border: 1px solid #e5e7eb;
  max-height: calc(100vh - 48px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-large {
  width: min(980px, 100%);
}

.modal-header,
.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-footer {
  border-bottom: none;
  border-top: 1px solid #e5e7eb;
  justify-content: flex-end;
}

.modal-header h3 {
  margin: 0;
  color: #111827;
}

.modal-close {
  width: 36px;
  height: 36px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 22px;
  line-height: 1;
}

.modal-close:hover {
  background: #e5e7eb;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item span {
  color: #374151;
  font-size: 14px;
  font-weight: 600;
}

.form-item-small {
  max-width: 180px;
}

.form-item-block {
  width: 100%;
}

.form-item textarea {
  min-height: 180px;
  resize: vertical;
  font-family: 'Consolas', 'Courier New', monospace;
}

.editor-section {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #f9fafb;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.section-header h4 {
  margin: 0;
  color: #111827;
}

.inline-field {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #4b5563;
  font-size: 14px;
}

.editor-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.editor-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.editor-row-action {
  align-items: flex-start;
}

.field-input {
  flex: 1 1 180px;
}

.operator-select {
  width: 110px;
}

.value-input {
  flex: 1 1 180px;
}

.type-select,
.action-select {
  width: 160px;
}

.template-input {
  flex: 1 1 320px;
}

.section-action {
  align-self: flex-start;
}

.match-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.match-result-card {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #dbeafe;
  background: #eff6ff;
  color: #1d4ed8;
}

.match-result-card p {
  margin: 0;
}

@media (max-width: 900px) {
  .header,
  .filters,
  .modal-header,
  .modal-footer,
  .section-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions,
  .action-group {
    width: 100%;
  }

  .header-actions .btn,
  .action-group .btn-action {
    flex: 1;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-item-small {
    max-width: none;
  }
}
</style>
