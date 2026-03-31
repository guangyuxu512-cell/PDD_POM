<script setup lang="ts">
import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
} from '@headlessui/vue'
import { onMounted, ref, watch } from 'vue'

import { getAftersaleConfig, updateAftersaleConfig } from '../api/aftersaleConfig'
import { listShops } from '../api/shops'
import type { Shop } from '../api/types'
import { toast } from '../utils/toast'

type WhitelistRow = {
  id: string
  name: string
  courierCompany: string
  areaKeywords: string[]
  areaKeywordInput: string
  deliveryPeople: string[]
  deliveryPersonInput: string
  enabled: boolean
}

type AftersaleConfigForm = {
  autoEnabled: boolean
  unsupportedTypes: string[]
  unsupportedTypeInput: string
  whitelist: WhitelistRow[]
  waitTimeJustSent: number
  waitTimeInTransit: number
  waitTimeDestinationCity: number
  requireInventoryCheck: boolean
  autoRefundLimit: number
  refundOnlyEnabled: boolean
  refundOnlyAutoApproveLimit: number
  refundOnlyNeedReject: boolean
  refundOnlyMaxRejectCount: number
  refundOnlyRejectWaitMinutes: number
  refundOnlyManualOnImages: boolean
  refundOnlyAutoApproveRejectedReturn: boolean
  rejectRefundEnabled: boolean
  rejectRefundNeedLogisticsCheck: boolean
  feishuNotifyEnabled: boolean
  feishuNotifyWebhook: string
  wechatNotifyEnabled: boolean
  wechatGroupId: string
  notifyScenes: string[]
  popupInputContent: string
  popupSelectPreference: string
  popupOptionPreferences: string[]
  popupOptionInput: string
  remarkReturnMatch: string
  remarkManual: string
  remarkReject: string
  batchMaxProcess: number
  singleTimeoutSeconds: number
  retryCount: number
  scanIntervalMinutes: number
  priorityTypes: string[]
  bitableEnabled: boolean
  bitableAppToken: string
  bitableTableId: string
  bitableScenes: string[]
}

const unsupportedTypeOptions = ['补寄', '维修', '换货']
const notifySceneOptions = ['人工审核', '金额超限', '派件人不匹配', '入库校验']
const priorityTypeOptions = ['退货退款', '仅退款', '拒收退款']
const bitableSceneOptions = ['已签收', '入库校验']

const shops = ref<Shop[]>([])
const selectedShopId = ref('')
const loading = ref(false)
const saving = ref(false)
const form = ref<AftersaleConfigForm>(createDefaultForm())
const originalPayload = ref<Record<string, any>>({})

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`
}

function createEmptyWhitelistRow(): WhitelistRow {
  return {
    id: createId('whitelist'),
    name: '',
    courierCompany: '*',
    areaKeywords: [],
    areaKeywordInput: '',
    deliveryPeople: [],
    deliveryPersonInput: '',
    enabled: true,
  }
}

function createDefaultForm(): AftersaleConfigForm {
  return {
    autoEnabled: true,
    unsupportedTypes: ['补寄', '维修', '换货'],
    unsupportedTypeInput: '',
    whitelist: [],
    waitTimeJustSent: 3,
    waitTimeInTransit: 1,
    waitTimeDestinationCity: 0.25,
    requireInventoryCheck: false,
    autoRefundLimit: 50,
    refundOnlyEnabled: false,
    refundOnlyAutoApproveLimit: 10,
    refundOnlyNeedReject: false,
    refundOnlyMaxRejectCount: 3,
    refundOnlyRejectWaitMinutes: 30,
    refundOnlyManualOnImages: true,
    refundOnlyAutoApproveRejectedReturn: true,
    rejectRefundEnabled: true,
    rejectRefundNeedLogisticsCheck: true,
    feishuNotifyEnabled: true,
    feishuNotifyWebhook: '',
    wechatNotifyEnabled: false,
    wechatGroupId: '',
    notifyScenes: ['人工审核', '金额超限', '派件人不匹配', '入库校验'],
    popupInputContent: '',
    popupSelectPreference: '',
    popupOptionPreferences: [],
    popupOptionInput: '',
    remarkReturnMatch: '退回物流匹配，自动退款',
    remarkManual: '转人工处理',
    remarkReject: '系统拒绝第{n}次',
    batchMaxProcess: 50,
    singleTimeoutSeconds: 60,
    retryCount: 3,
    scanIntervalMinutes: 30,
    priorityTypes: ['退货退款', '仅退款'],
    bitableEnabled: false,
    bitableAppToken: '',
    bitableTableId: '',
    bitableScenes: ['已签收', '入库校验'],
  }
}

function normalizeStringArray(value: unknown, fallback: string[]) {
  return Array.isArray(value)
    ? value.map((item) => String(item).trim()).filter(Boolean)
    : [...fallback]
}

function normalizeWhitelistRow(value: Record<string, any>): WhitelistRow {
  return {
    id: createId('whitelist'),
    name: String(value['名称'] || '').trim(),
    courierCompany: String(value['快递公司'] || '*').trim() || '*',
    areaKeywords: normalizeStringArray(value['地区关键词'], []),
    areaKeywordInput: '',
    deliveryPeople: normalizeStringArray(value['派件人'], []),
    deliveryPersonInput: '',
    enabled: Boolean(value['启用'] ?? true),
  }
}

function formFromConfig(config: Record<string, any>): AftersaleConfigForm {
  const defaultForm = createDefaultForm()
  const waitTime = config['退货等待时间'] || {}
  const popupPreference = config['弹窗偏好'] || {}
  const remarkTemplates = config['备注模板'] || {}

  return {
    autoEnabled: Boolean(config['启用自动售后'] ?? defaultForm.autoEnabled),
    unsupportedTypes: normalizeStringArray(config['不支持自动处理类型'], defaultForm.unsupportedTypes),
    unsupportedTypeInput: '',
    whitelist: Array.isArray(config['退货物流白名单'])
      ? config['退货物流白名单'].map((item) => normalizeWhitelistRow(item))
      : [],
    waitTimeJustSent: Number(waitTime['刚发出'] ?? defaultForm.waitTimeJustSent),
    waitTimeInTransit: Number(waitTime['中途运输'] ?? defaultForm.waitTimeInTransit),
    waitTimeDestinationCity: Number(waitTime['到达目的市'] ?? defaultForm.waitTimeDestinationCity),
    requireInventoryCheck: Boolean(config['需要入库校验'] ?? defaultForm.requireInventoryCheck),
    autoRefundLimit: Number(config['自动退款金额上限'] ?? defaultForm.autoRefundLimit),
    refundOnlyEnabled: Boolean(config['仅退款_启用'] ?? defaultForm.refundOnlyEnabled),
    refundOnlyAutoApproveLimit: Number(
      config['仅退款_自动同意金额上限'] ?? defaultForm.refundOnlyAutoApproveLimit,
    ),
    refundOnlyNeedReject: Boolean(config['仅退款_需要拒绝'] ?? defaultForm.refundOnlyNeedReject),
    refundOnlyMaxRejectCount: Number(
      config['仅退款_最大拒绝次数'] ?? defaultForm.refundOnlyMaxRejectCount,
    ),
    refundOnlyRejectWaitMinutes: Number(
      config['仅退款_拒绝后等待分钟'] ?? defaultForm.refundOnlyRejectWaitMinutes,
    ),
    refundOnlyManualOnImages: Boolean(
      config['仅退款_有图片转人工'] ?? defaultForm.refundOnlyManualOnImages,
    ),
    refundOnlyAutoApproveRejectedReturn: Boolean(
      config['仅退款_拒收退回自动同意'] ?? defaultForm.refundOnlyAutoApproveRejectedReturn,
    ),
    rejectRefundEnabled: Boolean(config['拒收退款_启用'] ?? defaultForm.rejectRefundEnabled),
    rejectRefundNeedLogisticsCheck: Boolean(
      config['拒收退款_需要检查物流'] ?? defaultForm.rejectRefundNeedLogisticsCheck,
    ),
    feishuNotifyEnabled: Boolean(config['飞书通知_启用'] ?? defaultForm.feishuNotifyEnabled),
    feishuNotifyWebhook: String(config['飞书通知_webhook'] || ''),
    wechatNotifyEnabled: Boolean(config['微信通知_启用'] ?? defaultForm.wechatNotifyEnabled),
    wechatGroupId: String(config['微信通知_群ID'] || ''),
    notifyScenes: normalizeStringArray(config['通知场景'], defaultForm.notifyScenes),
    popupInputContent: String(popupPreference['输入内容'] || ''),
    popupSelectPreference: String(popupPreference['下拉偏好'] || ''),
    popupOptionPreferences: normalizeStringArray(
      popupPreference['选项偏好'],
      defaultForm.popupOptionPreferences,
    ),
    popupOptionInput: '',
    remarkReturnMatch: String(remarkTemplates['退货匹配'] || defaultForm.remarkReturnMatch),
    remarkManual: String(remarkTemplates['人工'] || defaultForm.remarkManual),
    remarkReject: String(remarkTemplates['拒绝'] || defaultForm.remarkReject),
    batchMaxProcess: Number(config['每批最大处理数'] ?? defaultForm.batchMaxProcess),
    singleTimeoutSeconds: Number(config['单条超时秒数'] ?? defaultForm.singleTimeoutSeconds),
    retryCount: Number(config['失败重试次数'] ?? defaultForm.retryCount),
    scanIntervalMinutes: Number(config['扫描间隔分钟'] ?? defaultForm.scanIntervalMinutes),
    priorityTypes: normalizeStringArray(config['优先处理类型'], defaultForm.priorityTypes),
    bitableEnabled: Boolean(config['飞书多维表_启用'] ?? defaultForm.bitableEnabled),
    bitableAppToken: String(config['飞书多维表_app_token'] || ''),
    bitableTableId: String(config['飞书多维表_table_id'] || ''),
    bitableScenes: normalizeStringArray(config['飞书多维表_写入场景'], defaultForm.bitableScenes),
  }
}

function buildPayload(currentForm: AftersaleConfigForm) {
  return {
    启用自动售后: currentForm.autoEnabled,
    不支持自动处理类型: currentForm.unsupportedTypes,
    退货物流白名单: currentForm.whitelist.map((row) => ({
      名称: row.name.trim(),
      快递公司: row.courierCompany.trim() || '*',
      地区关键词: row.areaKeywords,
      派件人: row.deliveryPeople,
      启用: row.enabled,
    })),
    退货等待时间: {
      刚发出: currentForm.waitTimeJustSent,
      中途运输: currentForm.waitTimeInTransit,
      到达目的市: currentForm.waitTimeDestinationCity,
    },
    需要入库校验: currentForm.requireInventoryCheck,
    自动退款金额上限: currentForm.autoRefundLimit,
    仅退款_启用: currentForm.refundOnlyEnabled,
    仅退款_自动同意金额上限: currentForm.refundOnlyAutoApproveLimit,
    仅退款_需要拒绝: currentForm.refundOnlyNeedReject,
    仅退款_最大拒绝次数: currentForm.refundOnlyMaxRejectCount,
    仅退款_拒绝后等待分钟: currentForm.refundOnlyRejectWaitMinutes,
    仅退款_有图片转人工: currentForm.refundOnlyManualOnImages,
    仅退款_拒收退回自动同意: currentForm.refundOnlyAutoApproveRejectedReturn,
    拒收退款_启用: currentForm.rejectRefundEnabled,
    拒收退款_需要检查物流: currentForm.rejectRefundNeedLogisticsCheck,
    飞书通知_启用: currentForm.feishuNotifyEnabled,
    飞书通知_webhook: currentForm.feishuNotifyWebhook.trim(),
    微信通知_启用: currentForm.wechatNotifyEnabled,
    微信通知_群ID: currentForm.wechatGroupId.trim(),
    通知场景: currentForm.notifyScenes,
    弹窗偏好: {
      输入内容: currentForm.popupInputContent.trim(),
      下拉偏好: currentForm.popupSelectPreference.trim(),
      选项偏好: currentForm.popupOptionPreferences,
    },
    备注模板: {
      退货匹配: currentForm.remarkReturnMatch.trim(),
      人工: currentForm.remarkManual.trim(),
      拒绝: currentForm.remarkReject.trim(),
    },
    每批最大处理数: currentForm.batchMaxProcess,
    单条超时秒数: currentForm.singleTimeoutSeconds,
    失败重试次数: currentForm.retryCount,
    扫描间隔分钟: currentForm.scanIntervalMinutes,
    优先处理类型: currentForm.priorityTypes,
    飞书多维表_启用: currentForm.bitableEnabled,
    飞书多维表_app_token: currentForm.bitableAppToken.trim(),
    飞书多维表_table_id: currentForm.bitableTableId.trim(),
    飞书多维表_写入场景: currentForm.bitableScenes,
  }
}

async function loadShopsData() {
  try {
    const result = await listShops()
    shops.value = result.list || []
    const firstShop = shops.value[0]
    if (!selectedShopId.value && firstShop) {
      selectedShopId.value = firstShop.id
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载店铺失败'
    toast.error(message)
  }
}

async function loadConfig(shopId: string) {
  if (!shopId) {
    return
  }

  loading.value = true
  try {
    const config = await getAftersaleConfig(shopId)
    form.value = formFromConfig(config)
    originalPayload.value = buildPayload(form.value)
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载售后配置失败'
    toast.error(message)
  } finally {
    loading.value = false
  }
}

function addTag(target: string[], rawValue: string) {
  const value = rawValue.trim()
  if (!value || target.includes(value)) {
    return
  }
  target.push(value)
}

function removeTag(target: string[], value: string) {
  const index = target.indexOf(value)
  if (index >= 0) {
    target.splice(index, 1)
  }
}

function addUnsupportedType() {
  addTag(form.value.unsupportedTypes, form.value.unsupportedTypeInput)
  form.value.unsupportedTypeInput = ''
}

function addPopupOptionPreference() {
  addTag(form.value.popupOptionPreferences, form.value.popupOptionInput)
  form.value.popupOptionInput = ''
}

function addWhitelistRow() {
  form.value.whitelist.push(createEmptyWhitelistRow())
}

function removeWhitelistRow(id: string) {
  form.value.whitelist = form.value.whitelist.filter((row) => row.id !== id)
}

function addWhitelistTag(row: WhitelistRow, field: 'area' | 'delivery') {
  if (field === 'area') {
    addTag(row.areaKeywords, row.areaKeywordInput)
    row.areaKeywordInput = ''
    return
  }
  addTag(row.deliveryPeople, row.deliveryPersonInput)
  row.deliveryPersonInput = ''
}

function toggleSelection(target: string[], value: string) {
  if (target.includes(value)) {
    removeTag(target, value)
    return
  }
  target.push(value)
}

function resetToDefault() {
  form.value = createDefaultForm()
  toast.info('已恢复为默认表单值，点击保存后生效')
}

async function handleSave() {
  if (!selectedShopId.value) {
    toast.warning('请先选择店铺')
    return
  }

  const payload = buildPayload(form.value)
  const changedPayload: Record<string, any> = {}
  Object.entries(payload).forEach(([key, value]) => {
    if (JSON.stringify(value) !== JSON.stringify(originalPayload.value[key])) {
      changedPayload[key] = value
    }
  })

  if (!Object.keys(changedPayload).length) {
    toast.info('没有需要保存的变更')
    return
  }

  saving.value = true
  try {
    const updated = await updateAftersaleConfig(selectedShopId.value, changedPayload)
    form.value = formFromConfig(updated)
    originalPayload.value = buildPayload(form.value)
    toast.success('售后配置已保存')
  } catch (error) {
    const message = error instanceof Error ? error.message : '保存售后配置失败'
    toast.error(message)
  } finally {
    saving.value = false
  }
}

watch(selectedShopId, (value) => {
  if (value) {
    void loadConfig(value)
  }
})

onMounted(() => {
  void loadShopsData()
})
</script>
<template>
  <div class="space-y-6">
    <header class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div class="space-y-2">
        <h1 class="text-lg font-semibold text-gray-900">售后配置</h1>
        <p class="max-w-3xl text-sm text-brand-500">按店铺隔离管理自动售后参数，覆盖退货退款、仅退款、通知和执行策略。</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-brand-100/50 disabled:opacity-50" :disabled="loading || saving" @click="resetToDefault">重置为默认</button>
        <button class="rounded-md bg-brand-900 px-3 py-1.5 text-sm text-white hover:bg-brand-700 disabled:opacity-60" :disabled="loading || saving || !selectedShopId" @click="handleSave">{{ saving ? '保存中...' : '保存配置' }}</button>
      </div>
    </header>

    <section class="rounded-md border border-brand-300/50 bg-white p-5 shadow-sm">
      <div class="grid gap-4 lg:grid-cols-[320px_1fr] lg:items-end">
        <div class="space-y-2">
          <span class="text-xs font-medium text-gray-800">店铺选择</span>
          <Listbox v-model="selectedShopId">
            <div class="relative">
              <ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">{{ shops.find((shop) => shop.id === selectedShopId)?.name || '请选择店铺' }}</ListboxButton>
              <ListboxOptions class="absolute z-20 mt-2 max-h-72 w-full overflow-auto rounded-md border border-brand-300/50 bg-white py-1 shadow-lg">
                <ListboxOption v-for="shop in shops" :key="shop.id" :value="shop.id" v-slot="{ active, selected }">
                  <li :class="['cursor-pointer px-3 py-2 text-sm', active ? 'bg-brand-100 text-gray-900' : 'text-gray-700', selected ? 'font-medium text-gray-900' : '']">{{ shop.name }}</li>
                </ListboxOption>
              </ListboxOptions>
            </div>
          </Listbox>
        </div>
        <div class="rounded-md border border-brand-300/50 bg-brand-100 px-4 py-3 text-sm text-brand-500">
          <p v-if="loading">配置加载中...</p>
          <p v-else-if="!shops.length">暂无店铺，请先创建店铺</p>
          <p v-else>当前配置按店铺独立保存，切换店铺后会自动拉取对应参数。</p>
        </div>
      </div>
    </section>

    <div v-if="!shops.length && !loading" class="rounded-md border border-brand-300/50 bg-white px-6 py-12 text-center text-sm text-gray-400 shadow-sm">🏪 暂无店铺，请先创建店铺</div>

    <section v-else class="space-y-4 rounded-md border border-brand-300/50 bg-white p-5 shadow-sm">
      <section class="space-y-4">
        <div class="space-y-1">
          <h2 class="text-sm font-medium text-gray-900">全局设置</h2>
          <p class="text-xs text-brand-500">启用自动售后与默认排除类型统一在此维护。</p>
        </div>
        <label class="flex items-center justify-between rounded-md border border-brand-300/50 bg-brand-100 px-4 py-3">
          <span class="text-sm text-gray-700">启用自动售后</span>
          <input v-model="form.autoEnabled" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500" />
        </label>
        <div class="space-y-3">
          <span class="text-xs font-medium text-gray-800">不支持自动处理类型</span>
          <div class="flex flex-wrap gap-2">
            <button v-for="option in unsupportedTypeOptions" :key="option" type="button" class="rounded-full px-3 py-1 text-xs font-medium" :class="form.unsupportedTypes.includes(option) ? 'bg-brand-900 text-white' : 'bg-brand-100 text-gray-600 hover:bg-gray-200'" @click="toggleSelection(form.unsupportedTypes, option)">{{ option }}</button>
          </div>
          <div class="flex gap-2">
            <input v-model="form.unsupportedTypeInput" type="text" placeholder="自定义类型，回车添加" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" @keydown.enter.prevent="addUnsupportedType" />
            <button type="button" class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-brand-100/50" @click="addUnsupportedType">添加</button>
          </div>
          <div class="tag-list selected flex flex-wrap gap-2">
            <span v-for="item in form.unsupportedTypes" :key="item" class="tag-chip inline-flex items-center gap-2 rounded-full bg-brand-100 px-3 py-1 text-xs text-gray-700">{{ item }}<button type="button" class="text-gray-400 hover:text-gray-700" @click="removeTag(form.unsupportedTypes, item)">×</button></span>
          </div>
        </div>
      </section>

      <section class="space-y-4 border-t border-brand-300/30 pt-4">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div class="space-y-1">
            <h2 class="text-sm font-medium text-gray-900">退货退款</h2>
            <p class="text-xs text-brand-500">退货物流白名单、等待时长和退款阈值。</p>
          </div>
          <button type="button" class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-brand-100/50" @click="addWhitelistRow">+ 添加白名单</button>
        </div>
        <div class="whitelist overflow-x-auto rounded-md border border-brand-300/50">
          <table class="config-table min-w-[920px] w-full divide-y divide-brand-300/30 text-sm">
            <thead class="bg-brand-100 text-xs font-medium uppercase tracking-wider text-brand-500">
              <tr><th class="px-4 py-3 text-left">名称</th><th class="px-4 py-3 text-left">快递公司</th><th class="px-4 py-3 text-left">地区关键词</th><th class="px-4 py-3 text-left">派件人</th><th class="px-4 py-3 text-center">启用</th><th class="px-4 py-3 text-center">操作</th></tr>
            </thead>
            <tbody class="divide-y divide-brand-300/20">
              <tr v-if="form.whitelist.length === 0"><td colspan="6" class="px-4 py-8 text-center text-sm text-gray-400">📭 暂无白名单配置</td></tr>
              <tr v-for="row in form.whitelist" :key="row.id" class="align-top">
                <td class="px-4 py-3"><input v-model="row.name" type="text" placeholder="杭州仓-韵达" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></td>
                <td class="px-4 py-3"><input v-model="row.courierCompany" type="text" placeholder="*" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></td>
                <td class="space-y-2 px-4 py-3"><div class="tag-list selected flex flex-wrap gap-2"><span v-for="tag in row.areaKeywords" :key="tag" class="tag-chip inline-flex items-center gap-2 rounded-full bg-brand-100 px-3 py-1 text-xs text-gray-700">{{ tag }}<button type="button" class="text-gray-400 hover:text-gray-700" @click="removeTag(row.areaKeywords, tag)">×</button></span></div><input v-model="row.areaKeywordInput" type="text" placeholder="回车添加" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" @keydown.enter.prevent="addWhitelistTag(row, 'area')" /></td>
                <td class="space-y-2 px-4 py-3"><div class="tag-list selected flex flex-wrap gap-2"><span v-for="tag in row.deliveryPeople" :key="tag" class="tag-chip inline-flex items-center gap-2 rounded-full bg-brand-100 px-3 py-1 text-xs text-gray-700">{{ tag }}<button type="button" class="text-gray-400 hover:text-gray-700" @click="removeTag(row.deliveryPeople, tag)">×</button></span></div><input v-model="row.deliveryPersonInput" type="text" placeholder="回车添加" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" @keydown.enter.prevent="addWhitelistTag(row, 'delivery')" /></td>
                <td class="px-4 py-3 text-center"><input v-model="row.enabled" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500" /></td>
                <td class="px-4 py-3 text-center"><button type="button" class="rounded-md bg-rose-50 px-3 py-1.5 text-xs text-rose-600 hover:bg-rose-100" @click="removeWhitelistRow(row.id)">删除</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">刚发出（天）</span><input v-model.number="form.waitTimeJustSent" type="number" min="0" step="0.25" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">中途运输（天）</span><input v-model.number="form.waitTimeInTransit" type="number" min="0" step="0.25" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">到达目的市（天）</span><input v-model.number="form.waitTimeDestinationCity" type="number" min="0" step="0.25" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">自动退款金额上限（元）</span><input v-model.number="form.autoRefundLimit" type="number" min="0" step="0.5" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
        </div>
        <label class="flex items-center justify-between rounded-md border border-brand-300/50 bg-brand-100 px-4 py-3"><span class="text-sm text-gray-700">需要入库校验</span><input v-model="form.requireInventoryCheck" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500" /></label>
      </section>

      <section class="grid gap-4 border-t border-brand-300/30 pt-4 xl:grid-cols-2">
        <div class="space-y-4">
          <div class="space-y-1"><h2 class="text-sm font-medium text-gray-900">仅退款</h2><p class="text-xs text-brand-500">自动同意、拒绝策略和图片转人工。</p></div>
          <label class="flex items-center justify-between rounded-md border border-brand-300/50 bg-brand-100 px-4 py-3"><span class="text-sm text-gray-700">启用自动处理</span><input v-model="form.refundOnlyEnabled" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500" /></label>
          <div class="grid gap-4 md:grid-cols-3">
            <label class="space-y-2"><span class="text-xs font-medium text-gray-800">自动同意金额上限（元）</span><input v-model.number="form.refundOnlyAutoApproveLimit" type="number" min="0" step="0.5" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
            <label class="space-y-2"><span class="text-xs font-medium text-gray-800">最大拒绝次数</span><input v-model.number="form.refundOnlyMaxRejectCount" type="number" min="0" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
            <label class="space-y-2"><span class="text-xs font-medium text-gray-800">拒绝后等待（分钟）</span><input v-model.number="form.refundOnlyRejectWaitMinutes" type="number" min="0" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <label class="flex items-center justify-between rounded-md border border-brand-300/50 bg-brand-100 px-4 py-3"><span class="text-sm text-gray-700">启用拒绝策略</span><input v-model="form.refundOnlyNeedReject" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500" /></label>
            <label class="flex items-center justify-between rounded-md border border-brand-300/50 bg-brand-100 px-4 py-3"><span class="text-sm text-gray-700">有图片转人工</span><input v-model="form.refundOnlyManualOnImages" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500" /></label>
            <label class="flex items-center justify-between rounded-md border border-brand-300/50 bg-brand-100 px-4 py-3 sm:col-span-2"><span class="text-sm text-gray-700">拒收退回自动同意</span><input v-model="form.refundOnlyAutoApproveRejectedReturn" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500" /></label>
          </div>
        </div>

        <div class="space-y-4">
          <div class="space-y-1"><h2 class="text-sm font-medium text-gray-900">通知配置</h2><p class="text-xs text-brand-500">飞书、微信和通知场景。</p></div>
          <div class="grid gap-3 sm:grid-cols-2">
            <label class="flex items-center justify-between rounded-md border border-brand-300/50 bg-brand-100 px-4 py-3"><span class="text-sm text-gray-700">飞书通知</span><input v-model="form.feishuNotifyEnabled" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500" /></label>
            <label class="flex items-center justify-between rounded-md border border-brand-300/50 bg-brand-100 px-4 py-3"><span class="text-sm text-gray-700">微信通知</span><input v-model="form.wechatNotifyEnabled" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500" /></label>
          </div>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">飞书 Webhook</span><input v-model="form.feishuNotifyWebhook" type="text" placeholder="https://open.feishu.cn/..." class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">微信群ID</span><input v-model="form.wechatGroupId" type="text" placeholder="请输入微信群ID" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <div class="space-y-3"><span class="text-xs font-medium text-gray-800">通知场景</span><div class="flex flex-wrap gap-2"><button v-for="scene in notifySceneOptions" :key="scene" type="button" class="rounded-full px-3 py-1 text-xs font-medium" :class="form.notifyScenes.includes(scene) ? 'bg-brand-900 text-white' : 'bg-brand-100 text-gray-600 hover:bg-gray-200'" @click="toggleSelection(form.notifyScenes, scene)">{{ scene }}</button></div></div>
        </div>
      </section>
      <section class="grid gap-4 border-t border-brand-300/30 pt-4 xl:grid-cols-2">
        <div class="space-y-4">
          <div class="space-y-1"><h2 class="text-sm font-medium text-gray-900">弹窗与备注</h2><p class="text-xs text-brand-500">弹窗输入、下拉偏好与备注模板。</p></div>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">弹窗输入内容</span><input v-model="form.popupInputContent" type="text" placeholder="复杂弹窗默认输入内容" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">弹窗下拉偏好</span><input v-model="form.popupSelectPreference" type="text" placeholder="例如：顺丰" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <div class="space-y-3">
            <span class="text-xs font-medium text-gray-800">弹窗选项偏好</span>
            <div class="flex gap-2"><input v-model="form.popupOptionInput" type="text" placeholder="输入后回车添加" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" @keydown.enter.prevent="addPopupOptionPreference" /><button type="button" class="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-brand-100/50" @click="addPopupOptionPreference">添加</button></div>
            <div class="tag-list selected flex flex-wrap gap-2"><span v-for="item in form.popupOptionPreferences" :key="item" class="tag-chip inline-flex items-center gap-2 rounded-full bg-brand-100 px-3 py-1 text-xs text-gray-700">{{ item }}<button type="button" class="text-gray-400 hover:text-gray-700" @click="removeTag(form.popupOptionPreferences, item)">×</button></span></div>
          </div>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">备注模板：退货匹配</span><input v-model="form.remarkReturnMatch" type="text" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">备注模板：人工</span><input v-model="form.remarkManual" type="text" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">备注模板：拒绝</span><input v-model="form.remarkReject" type="text" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
        </div>
        <div class="space-y-4">
          <div class="space-y-1"><h2 class="text-sm font-medium text-gray-900">执行策略</h2><p class="text-xs text-brand-500">批次、超时、重试与优先处理。</p></div>
          <div class="grid gap-4 md:grid-cols-2">
            <label class="space-y-2"><span class="text-xs font-medium text-gray-800">每批最大处理数</span><input v-model.number="form.batchMaxProcess" type="number" min="1" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
            <label class="space-y-2"><span class="text-xs font-medium text-gray-800">单条超时秒数</span><input v-model.number="form.singleTimeoutSeconds" type="number" min="1" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
            <label class="space-y-2"><span class="text-xs font-medium text-gray-800">失败重试次数</span><input v-model.number="form.retryCount" type="number" min="0" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
            <label class="space-y-2"><span class="text-xs font-medium text-gray-800">扫描间隔分钟</span><input v-model.number="form.scanIntervalMinutes" type="number" min="1" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          </div>
          <div class="space-y-3"><span class="text-xs font-medium text-gray-800">优先处理类型</span><div class="flex flex-wrap gap-2"><button v-for="type in priorityTypeOptions" :key="type" type="button" class="rounded-full px-3 py-1 text-xs font-medium" :class="form.priorityTypes.includes(type) ? 'bg-brand-900 text-white' : 'bg-brand-100 text-gray-600 hover:bg-gray-200'" @click="toggleSelection(form.priorityTypes, type)">{{ type }}</button></div></div>
          <div class="space-y-1 pt-2"><h2 class="text-sm font-medium text-gray-900">飞书多维表</h2><p class="text-xs text-brand-500">App Token、Table ID 与写入场景。</p></div>
          <label class="flex items-center justify-between rounded-md border border-brand-300/50 bg-brand-100 px-4 py-3"><span class="text-sm text-gray-700">启用飞书多维表</span><input v-model="form.bitableEnabled" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500" /></label>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">App Token</span><input v-model="form.bitableAppToken" type="text" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <label class="space-y-2"><span class="text-xs font-medium text-gray-800">Table ID</span><input v-model="form.bitableTableId" type="text" class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" /></label>
          <div class="space-y-3"><span class="text-xs font-medium text-gray-800">写入场景</span><div class="flex flex-wrap gap-2"><button v-for="scene in bitableSceneOptions" :key="scene" type="button" class="rounded-full px-3 py-1 text-xs font-medium" :class="form.bitableScenes.includes(scene) ? 'bg-brand-900 text-white' : 'bg-brand-100 text-gray-600 hover:bg-gray-200'" @click="toggleSelection(form.bitableScenes, scene)">{{ scene }}</button></div></div>
        </div>
      </section>
    </section>
  </div>
</template>
