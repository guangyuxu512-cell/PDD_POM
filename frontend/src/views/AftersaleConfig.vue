<script setup lang="ts">
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
  <div class="aftersale-config">
    <div class="page-header">
      <div>
        <h1>售后配置</h1>
        <p class="page-tip">按店铺隔离管理自动售后参数，覆盖退货退款、仅退款、通知和执行策略。</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" :disabled="loading || saving" @click="resetToDefault">重置为默认</button>
        <button class="btn btn-primary" :disabled="loading || saving || !selectedShopId" @click="handleSave">
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>

    <div class="shop-bar">
      <label class="field">
        <span>店铺选择</span>
        <select v-model="selectedShopId">
          <option value="" disabled>请选择店铺</option>
          <option v-for="shop in shops" :key="shop.id" :value="shop.id">{{ shop.name }}</option>
        </select>
      </label>
      <p v-if="loading" class="loading-tip">配置加载中...</p>
      <p v-else-if="!shops.length" class="loading-tip">暂无店铺，请先创建店铺</p>
    </div>

    <div class="card-grid">
      <section class="config-card">
        <div class="card-header">
          <h2>全局设置</h2>
        </div>
        <label class="switch-row">
          <span>启用自动售后</span>
          <input v-model="form.autoEnabled" type="checkbox" />
        </label>
        <div class="field">
          <span>不支持自动处理类型</span>
          <div class="tag-list">
            <button
              v-for="option in unsupportedTypeOptions"
              :key="option"
              :class="['tag-btn', { active: form.unsupportedTypes.includes(option) }]"
              @click="toggleSelection(form.unsupportedTypes, option)"
            >
              {{ option }}
            </button>
          </div>
          <div class="tag-editor">
            <input
              v-model="form.unsupportedTypeInput"
              type="text"
              placeholder="自定义类型，回车添加"
              @keydown.enter.prevent="addUnsupportedType"
            />
            <button class="btn btn-light" @click="addUnsupportedType">添加</button>
          </div>
          <div class="tag-list selected">
            <span v-for="item in form.unsupportedTypes" :key="item" class="tag-chip">
              {{ item }}
              <button @click="removeTag(form.unsupportedTypes, item)">×</button>
            </span>
          </div>
        </div>
      </section>

      <section class="config-card config-card-wide">
        <div class="card-header">
          <h2>退货退款</h2>
          <button class="btn btn-light" @click="addWhitelistRow">+ 添加白名单</button>
        </div>
        <p class="section-tip">退货物流白名单</p>
        <div class="table-shell">
          <table class="config-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>快递公司</th>
                <th>地区关键词</th>
                <th>派件人</th>
                <th>启用</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="form.whitelist.length === 0">
                <td colspan="6" class="empty-cell">暂无白名单配置</td>
              </tr>
              <tr v-for="row in form.whitelist" :key="row.id">
                <td><input v-model="row.name" type="text" placeholder="杭州仓-韵达" /></td>
                <td><input v-model="row.courierCompany" type="text" placeholder="*" /></td>
                <td>
                  <div class="tag-list selected inline">
                    <span v-for="tag in row.areaKeywords" :key="tag" class="tag-chip">
                      {{ tag }}
                      <button @click="removeTag(row.areaKeywords, tag)">×</button>
                    </span>
                  </div>
                  <div class="tag-editor compact">
                    <input
                      v-model="row.areaKeywordInput"
                      type="text"
                      placeholder="回车添加"
                      @keydown.enter.prevent="addWhitelistTag(row, 'area')"
                    />
                  </div>
                </td>
                <td>
                  <div class="tag-list selected inline">
                    <span v-for="tag in row.deliveryPeople" :key="tag" class="tag-chip">
                      {{ tag }}
                      <button @click="removeTag(row.deliveryPeople, tag)">×</button>
                    </span>
                  </div>
                  <div class="tag-editor compact">
                    <input
                      v-model="row.deliveryPersonInput"
                      type="text"
                      placeholder="回车添加"
                      @keydown.enter.prevent="addWhitelistTag(row, 'delivery')"
                    />
                  </div>
                </td>
                <td><input v-model="row.enabled" type="checkbox" /></td>
                <td><button class="btn btn-danger" @click="removeWhitelistRow(row.id)">删除</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="inline-grid">
          <label class="field">
            <span>刚发出（天）</span>
            <input v-model.number="form.waitTimeJustSent" type="number" min="0" step="0.25" />
          </label>
          <label class="field">
            <span>中途运输（天）</span>
            <input v-model.number="form.waitTimeInTransit" type="number" min="0" step="0.25" />
          </label>
          <label class="field">
            <span>到达目的市（天）</span>
            <input v-model.number="form.waitTimeDestinationCity" type="number" min="0" step="0.25" />
          </label>
          <label class="field">
            <span>自动退款金额上限（元）</span>
            <input v-model.number="form.autoRefundLimit" type="number" min="0" step="0.5" />
          </label>
        </div>
        <label class="switch-row">
          <span>需要入库校验</span>
          <input v-model="form.requireInventoryCheck" type="checkbox" />
        </label>
      </section>

      <section class="config-card">
        <div class="card-header">
          <h2>仅退款</h2>
        </div>
        <label class="switch-row">
          <span>启用自动处理</span>
          <input v-model="form.refundOnlyEnabled" type="checkbox" />
        </label>
        <div class="inline-grid">
          <label class="field">
            <span>自动同意金额上限（元）</span>
            <input v-model.number="form.refundOnlyAutoApproveLimit" type="number" min="0" step="0.5" />
          </label>
          <label class="field">
            <span>最大拒绝次数</span>
            <input v-model.number="form.refundOnlyMaxRejectCount" type="number" min="0" />
          </label>
          <label class="field">
            <span>拒绝后等待（分钟）</span>
            <input v-model.number="form.refundOnlyRejectWaitMinutes" type="number" min="0" />
          </label>
        </div>
        <label class="switch-row">
          <span>启用拒绝策略</span>
          <input v-model="form.refundOnlyNeedReject" type="checkbox" />
        </label>
        <label class="switch-row">
          <span>有图片转人工</span>
          <input v-model="form.refundOnlyManualOnImages" type="checkbox" />
        </label>
        <label class="switch-row">
          <span>拒收退回自动同意</span>
          <input v-model="form.refundOnlyAutoApproveRejectedReturn" type="checkbox" />
        </label>
      </section>

      <section class="config-card">
        <div class="card-header">
          <h2>通知配置</h2>
        </div>
        <label class="switch-row">
          <span>飞书通知</span>
          <input v-model="form.feishuNotifyEnabled" type="checkbox" />
        </label>
        <label class="field">
          <span>飞书 Webhook</span>
          <input v-model="form.feishuNotifyWebhook" type="text" placeholder="https://open.feishu.cn/..." />
        </label>
        <label class="switch-row">
          <span>微信通知</span>
          <input v-model="form.wechatNotifyEnabled" type="checkbox" />
        </label>
        <label class="field">
          <span>微信群ID</span>
          <input v-model="form.wechatGroupId" type="text" placeholder="请输入微信群ID" />
        </label>
        <div class="field">
          <span>通知场景</span>
          <div class="tag-list">
            <button
              v-for="scene in notifySceneOptions"
              :key="scene"
              :class="['tag-btn', { active: form.notifyScenes.includes(scene) }]"
              @click="toggleSelection(form.notifyScenes, scene)"
            >
              {{ scene }}
            </button>
          </div>
        </div>
      </section>

      <section class="config-card">
        <div class="card-header">
          <h2>弹窗与备注</h2>
        </div>
        <label class="field">
          <span>弹窗输入内容</span>
          <input v-model="form.popupInputContent" type="text" placeholder="复杂弹窗默认输入内容" />
        </label>
        <label class="field">
          <span>弹窗下拉偏好</span>
          <input v-model="form.popupSelectPreference" type="text" placeholder="例如：顺丰" />
        </label>
        <div class="field">
          <span>弹窗选项偏好</span>
          <div class="tag-editor">
            <input
              v-model="form.popupOptionInput"
              type="text"
              placeholder="输入后回车添加"
              @keydown.enter.prevent="addPopupOptionPreference"
            />
            <button class="btn btn-light" @click="addPopupOptionPreference">添加</button>
          </div>
          <div class="tag-list selected">
            <span v-for="item in form.popupOptionPreferences" :key="item" class="tag-chip">
              {{ item }}
              <button @click="removeTag(form.popupOptionPreferences, item)">×</button>
            </span>
          </div>
        </div>
        <label class="field">
          <span>备注模板：退货匹配</span>
          <input v-model="form.remarkReturnMatch" type="text" />
        </label>
        <label class="field">
          <span>备注模板：人工</span>
          <input v-model="form.remarkManual" type="text" />
        </label>
        <label class="field">
          <span>备注模板：拒绝</span>
          <input v-model="form.remarkReject" type="text" />
        </label>
      </section>

      <section class="config-card">
        <div class="card-header">
          <h2>执行策略</h2>
        </div>
        <div class="inline-grid">
          <label class="field">
            <span>每批最大处理数</span>
            <input v-model.number="form.batchMaxProcess" type="number" min="1" />
          </label>
          <label class="field">
            <span>单条超时秒数</span>
            <input v-model.number="form.singleTimeoutSeconds" type="number" min="1" />
          </label>
          <label class="field">
            <span>失败重试次数</span>
            <input v-model.number="form.retryCount" type="number" min="0" />
          </label>
          <label class="field">
            <span>扫描间隔分钟</span>
            <input v-model.number="form.scanIntervalMinutes" type="number" min="1" />
          </label>
        </div>
        <div class="field">
          <span>优先处理类型</span>
          <div class="tag-list">
            <button
              v-for="type in priorityTypeOptions"
              :key="type"
              :class="['tag-btn', { active: form.priorityTypes.includes(type) }]"
              @click="toggleSelection(form.priorityTypes, type)"
            >
              {{ type }}
            </button>
          </div>
        </div>
      </section>

      <section class="config-card">
        <div class="card-header">
          <h2>飞书多维表</h2>
        </div>
        <label class="switch-row">
          <span>启用飞书多维表</span>
          <input v-model="form.bitableEnabled" type="checkbox" />
        </label>
        <label class="field">
          <span>App Token</span>
          <input v-model="form.bitableAppToken" type="text" />
        </label>
        <label class="field">
          <span>Table ID</span>
          <input v-model="form.bitableTableId" type="text" />
        </label>
        <div class="field">
          <span>写入场景</span>
          <div class="tag-list">
            <button
              v-for="scene in bitableSceneOptions"
              :key="scene"
              :class="['tag-btn', { active: form.bitableScenes.includes(scene) }]"
              @click="toggleSelection(form.bitableScenes, scene)"
            >
              {{ scene }}
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.aftersale-config {
  color: #1a1a2e;
}

.page-header,
.shop-bar,
.card-header,
.switch-row,
.tag-editor,
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-header,
.shop-bar {
  justify-content: space-between;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
}

.page-tip,
.loading-tip,
.section-tip {
  margin: 8px 0 0;
  color: #6b7280;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.config-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-card-wide {
  grid-column: 1 / -1;
}

.card-header {
  justify-content: space-between;
  flex-wrap: wrap;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.field span {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

input,
select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #ffffff;
  color: #1a1a2e;
  font-size: 14px;
  box-sizing: border-box;
}

input:focus,
select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.switch-row {
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.switch-row span {
  font-weight: 600;
}

.switch-row input {
  width: auto;
}

.inline-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.table-shell {
  overflow-x: auto;
}

.config-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 900px;
}

.config-table th,
.config-table td {
  padding: 10px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  vertical-align: top;
}

.empty-cell {
  text-align: center;
  color: #9ca3af;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-list.inline {
  margin-bottom: 8px;
}

.tag-list.selected {
  min-height: 24px;
}

.tag-btn,
.tag-chip,
.btn {
  border-radius: 999px;
  border: none;
}

.tag-btn {
  padding: 8px 12px;
  background: #e5e7eb;
  color: #374151;
  cursor: pointer;
}

.tag-btn.active {
  background: #2563eb;
  color: #ffffff;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: #eff6ff;
  color: #1d4ed8;
}

.tag-chip button {
  border: none;
  background: none;
  color: inherit;
  cursor: pointer;
}

.tag-editor input {
  flex: 1;
}

.tag-editor.compact {
  display: block;
}

.btn {
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #2563eb;
  color: #ffffff;
}

.btn-secondary {
  background: #e5e7eb;
  color: #111827;
}

.btn-light {
  background: #eff6ff;
  color: #1d4ed8;
}

.btn-danger {
  padding: 8px 14px;
  background: #ef4444;
  color: #ffffff;
}

@media (max-width: 1100px) {
  .card-grid,
  .inline-grid {
    grid-template-columns: 1fr;
  }

  .page-header,
  .shop-bar,
  .card-header,
  .header-actions,
  .tag-editor {
    align-items: stretch;
    flex-direction: column;
  }

  .header-actions .btn,
  .tag-editor .btn {
    width: 100%;
  }
}
</style>
