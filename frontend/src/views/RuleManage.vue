<script setup lang="ts">
import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
} from '@headlessui/vue'
import { computed, onMounted, ref } from 'vue'

import Modal from '../components/Modal.vue'
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
  <div class="space-y-6">
    <header class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="space-y-2">
        <h1 v-if="props.showTitle" class="text-lg font-semibold text-gray-900">规则配置</h1>
        <h2 v-else class="text-lg font-semibold text-gray-900">规则配置</h2>
        <p class="max-w-3xl text-sm text-gray-500">配置条件-动作规则，用于售后、推广和限时限量等自动决策。</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button class="rounded-md bg-gray-900 px-3 py-1.5 text-sm text-white hover:bg-gray-800" @click="openCreateDialog">+ 新建规则</button>
        <button class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50" @click="openTestMatchDialog">测试匹配</button>
      </div>
    </header>

    <section class="rounded-md border border-gray-200 bg-white p-5 shadow-sm">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-end">
        <div class="flex flex-1 flex-col gap-4 md:grid md:grid-cols-3">
          <div class="space-y-2"><span class="text-xs font-medium text-gray-600">筛选:</span>
            <Listbox v-model="filter.platform"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ filter.platform || '全部平台' }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption value="" v-slot="{ active }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700']">全部平台</li></ListboxOption><ListboxOption v-for="platform in platformOptions" :key="platform" :value="platform" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ platform }}</li></ListboxOption></ListboxOptions></div></Listbox>
          </div>
          <div class="space-y-2"><span class="text-xs font-medium text-gray-600">业务</span>
            <Listbox v-model="filter.business"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ filter.business || '全部业务' }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption value="" v-slot="{ active }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700']">全部业务</li></ListboxOption><ListboxOption v-for="business in businessOptions" :key="business" :value="business" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ business }}</li></ListboxOption></ListboxOptions></div></Listbox>
          </div>
          <div class="space-y-2"><span class="text-xs font-medium text-gray-600">店铺</span>
            <Listbox v-model="filter.shop_id"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ filter.shop_id ? formatShopName(filter.shop_id) : '全部店铺' }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 max-h-72 w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption value="" v-slot="{ active }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700']">全部店铺</li></ListboxOption><ListboxOption v-for="shop in shops" :key="shop.id" :value="shop.id" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ shop.name }}</li></ListboxOption></ListboxOptions></div></Listbox>
          </div>
        </div>
        <button class="rounded-md bg-gray-900 px-3 py-2 text-sm text-white hover:bg-gray-800" @click="loadRules">查询</button>
      </div>
    </section>

    <section class="rounded-md border border-gray-200 bg-white shadow-sm">
      <div class="flex items-center justify-between border-b border-gray-100 px-5 py-4"><div class="space-y-1"><h2 class="text-sm font-medium text-gray-900">规则列表</h2><p class="text-xs text-gray-500">按平台、业务和店铺过滤后统一查看规则优先级与状态。</p></div></div>
      <div v-if="loading" class="px-6 py-12 text-center text-sm text-gray-400">⏳ 加载中...</div>
      <div v-else-if="sortedRules.length === 0" class="px-6 py-12 text-center text-sm text-gray-400">🧾 暂无规则，点击上方&quot;新建规则&quot;添加</div>
      <div v-else class="overflow-x-auto">
        <table class="w-full min-w-[960px] table-fixed divide-y divide-gray-200">
          <thead class="bg-gray-50/60 text-xs font-medium uppercase tracking-wider text-gray-500"><tr><th class="px-4 py-3 text-left">名称</th><th class="px-4 py-3 text-left">平台</th><th class="px-4 py-3 text-left">业务</th><th class="px-4 py-3 text-left">店铺</th><th class="px-4 py-3 text-right">优先级</th><th class="px-4 py-3 text-center">启用</th><th class="px-4 py-3 text-center">操作</th></tr></thead>
          <tbody class="divide-y divide-gray-100 text-sm text-gray-900">
            <tr v-for="rule in sortedRules" :key="rule.id" class="border-b border-gray-100 hover:bg-gray-50/50">
              <td class="px-4 py-3 font-medium text-gray-900">{{ rule.name }}</td>
              <td class="px-4 py-3"><span class="rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-700">{{ rule.platform }}</span></td>
              <td class="px-4 py-3 text-xs text-gray-500">{{ rule.business }}</td>
              <td class="px-4 py-3 text-xs text-gray-500">{{ formatShopName(rule.shop_id) }}</td>
              <td class="px-4 py-3 text-right font-mono text-xs text-gray-500">{{ rule.priority }}</td>
              <td class="px-4 py-3 text-center"><label class="inline-flex cursor-pointer items-center"><input type="checkbox" class="peer sr-only" :checked="rule.enabled" @change="handleToggle(rule, $event)" /><span class="relative h-6 w-11 rounded-full bg-gray-200 transition after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:shadow-sm after:transition-all peer-checked:bg-gray-900 peer-checked:after:translate-x-5" /></label></td>
              <td class="px-4 py-3 text-center"><button class="text-xs text-gray-500 hover:text-gray-700" @click="openEditDialog(rule)">编辑</button><button class="ml-3 text-xs text-rose-600 hover:text-rose-700" @click="handleDelete(rule)">删除</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <Modal :show="showEditor" :title="editorTitle" width="min(88vw, 1100px)" @close="closeEditor">
      <form class="space-y-4" @submit.prevent="handleSave">
        <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <label class="space-y-2 xl:col-span-2"><span class="text-xs font-medium text-gray-600">规则名称</span><input v-model="form.name" type="text" placeholder="请输入规则名称" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400" /></label>
          <div class="space-y-2"><span class="text-xs font-medium text-gray-600">平台</span><Listbox v-model="form.platform"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ form.platform }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 w-full rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption v-for="platform in platformOptions" :key="platform" :value="platform" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ platform }}</li></ListboxOption></ListboxOptions></div></Listbox></div>
          <div class="space-y-2"><span class="text-xs font-medium text-gray-600">业务类型</span><Listbox v-model="form.business"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ form.business }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 w-full rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption v-for="business in businessOptions" :key="business" :value="business" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ business }}</li></ListboxOption></ListboxOptions></div></Listbox></div>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-600">优先级</span><input v-model.number="form.priority" type="number" min="0" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400" /></label>
        </section>
        <section class="border-t border-gray-100 pt-4">
          <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
            <div class="space-y-2"><span class="text-xs font-medium text-gray-600">店铺</span><Listbox v-model="form.shop_id"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ form.shop_id === '*' ? '全部' : formatShopName(form.shop_id) }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 max-h-72 w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption value="*" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">全部</li></ListboxOption><ListboxOption v-for="shop in shops" :key="shop.id" :value="shop.id" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ shop.name }}</li></ListboxOption></ListboxOptions></div></Listbox></div>
            <div class="space-y-2"><span class="text-xs font-medium text-gray-600">逻辑关系</span><Listbox v-model="form.conditions.operator"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ form.conditions.operator.toUpperCase() }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 w-full rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption v-for="logic in logicOptions" :key="logic" :value="logic" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ logic.toUpperCase() }}</li></ListboxOption></ListboxOptions></div></Listbox></div>
          </div>
        </section>
        <section class="border-t border-gray-100 pt-4">
          <div class="mb-4 flex items-center justify-between"><div><h3 class="text-sm font-medium text-gray-900">条件</h3><p class="text-xs text-gray-500">字段名可从 datalist 中直接选择。</p></div><button type="button" class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50" @click="addCondition">+ 添加条件</button></div>
          <div class="space-y-3">
            <div v-for="condition in form.conditions.rules" :key="condition.id" class="grid gap-3 rounded-md border border-gray-200 bg-gray-50 p-3 md:grid-cols-[minmax(0,1fr)_180px_minmax(0,1fr)_84px]">
              <input v-model="condition.field" list="rule-field-options" class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400" placeholder="字段名" />
              <Listbox v-model="condition.op"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ condition.op }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 w-full rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption v-for="operator in operatorOptions" :key="operator" :value="operator" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ operator }}</li></ListboxOption></ListboxOptions></div></Listbox>
              <input v-model="condition.value" type="text" class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400" placeholder="条件值" />
              <button type="button" class="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-600 hover:bg-rose-100" @click="removeCondition(condition.id)">删除</button>
            </div>
          </div>
        </section>
        <section class="border-t border-gray-100 pt-4">
          <div class="mb-4 flex items-center justify-between"><div><h3 class="text-sm font-medium text-gray-900">动作</h3><p class="text-xs text-gray-500">不同动作类型会自动切换可用动作集合。</p></div><button type="button" class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50" @click="addAction">+ 添加动作</button></div>
          <div class="space-y-3">
            <div v-for="action in form.actions" :key="action.id" class="grid gap-3 rounded-md border border-gray-200 bg-gray-50 p-3 md:grid-cols-[180px_180px_minmax(0,1fr)_84px]">
              <Listbox :modelValue="action.type" @update:modelValue="action.type = $event; handleActionTypeChange(action)"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ action.type }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 w-full rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption v-for="type in actionTypeOptions" :key="type" :value="type" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ type }}</li></ListboxOption></ListboxOptions></div></Listbox>
              <Listbox v-model="action.action"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ action.action }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 w-full rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption v-for="option in getActionOptions(action.type)" :key="option" :value="option" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ option }}</li></ListboxOption></ListboxOptions></div></Listbox>
              <input v-if="action.type === '微信通知'" v-model="action.template" type="text" class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400" placeholder="亲，您的退款 {退款金额} 元已处理~" />
              <div v-else class="rounded-md border border-dashed border-gray-300 bg-white px-3 py-2 text-sm text-gray-400">{{ action.action }}</div>
              <button type="button" class="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-600 hover:bg-rose-100" @click="removeAction(action.id)">删除</button>
            </div>
          </div>
        </section>
      </form>
      <template #footer><button class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50" @click="closeEditor">取消</button><button class="rounded-md bg-gray-900 px-3 py-1.5 text-sm text-white hover:bg-gray-800 disabled:opacity-60" :disabled="saving" @click="handleSave">{{ saving ? '保存中...' : '保存' }}</button></template>
    </Modal>
    <Modal :show="showTestMatch" title="测试规则匹配" width="min(72vw, 840px)" @close="closeTestMatchDialog">
      <div class="space-y-4">
        <div class="grid gap-4 md:grid-cols-3">
          <div class="space-y-2"><span class="text-xs font-medium text-gray-600">平台</span><Listbox v-model="testForm.platform"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ testForm.platform }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 w-full rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption v-for="platform in platformOptions" :key="platform" :value="platform" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ platform }}</li></ListboxOption></ListboxOptions></div></Listbox></div>
          <div class="space-y-2"><span class="text-xs font-medium text-gray-600">业务</span><Listbox v-model="testForm.business"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ testForm.business }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 w-full rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption v-for="business in businessOptions" :key="business" :value="business" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ business }}</li></ListboxOption></ListboxOptions></div></Listbox></div>
          <div class="space-y-2"><span class="text-xs font-medium text-gray-600">店铺</span><Listbox v-model="testForm.shop_id"><div class="relative"><ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900">{{ testForm.shop_id === '*' ? '全部' : formatShopName(testForm.shop_id) }}</ListboxButton><ListboxOptions class="absolute z-20 mt-2 max-h-72 w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 shadow-lg"><ListboxOption value="*" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">全部</li></ListboxOption><ListboxOption v-for="shop in shops" :key="shop.id" :value="shop.id" v-slot="{ active, selected }"><li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-gray-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ shop.name }}</li></ListboxOption></ListboxOptions></div></Listbox></div>
        </div>
        <label class="block space-y-2"><span class="text-xs font-medium text-gray-600">测试数据（JSON）</span><textarea v-model="testForm.dataText" rows="8" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400"></textarea></label>
        <div class="rounded-md border border-gray-200 bg-gray-50 p-4">
          <button class="rounded-md bg-gray-900 px-3 py-1.5 text-sm text-white hover:bg-gray-800 disabled:opacity-60" :disabled="testing" @click="handleTestMatch">{{ testing ? '匹配中...' : '匹配测试' }}</button>
          <div v-if="matchResult" class="mt-4 space-y-2 rounded-md border border-gray-200 bg-white p-4 text-sm text-gray-700">
            <p>✅ 命中规则: {{ matchResult.rule_name }}</p>
            <p>动作: {{ matchActionSummary }}</p>
          </div>
        </div>
      </div>
      <template #footer><button class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50" @click="closeTestMatchDialog">关闭</button></template>
    </Modal>

    <datalist id="rule-field-options">
      <option v-for="field in conditionFieldOptions" :key="field" :value="field" />
    </datalist>
  </div>
</template>
