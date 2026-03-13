<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import Modal from '../components/Modal.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { listShops } from '../api/shops'
import {
  batchDisableTaskParams,
  batchEnableTaskParams,
  batchResetTaskParams,
  clearTaskParams,
  deleteTaskParam,
  disableTaskParam,
  enableTaskParam,
  importTaskParamsCsv,
  listTaskParamBatchOptions,
  listTaskParams,
  resetTaskParam,
} from '../api/taskParams'
import type {
  Shop,
  TaskParam,
  TaskParamBatchOption,
  TaskParamBatchPayload,
  TaskParamFilters,
  TaskParamImportResult,
} from '../api/types'
import { toast } from '../utils/toast'

type BatchActionKey = '' | 'reset' | 'enable' | 'disable'
type TabKey = 'taskList' | 'resultList'
type JsonTooltipState = {
  visible: boolean
  content: string
  left: number
  top: number
  width: number
}

const taskOptions = ['发布相似商品', '发布换图商品']
const pageSize = 10
const tooltipMaxWidth = 500
const tooltipViewportPadding = 16
const tooltipGap = 10

const shops = ref<Shop[]>([])
const batchOptions = ref<TaskParamBatchOption[]>([])
const taskParams = ref<TaskParam[]>([])
const resultTaskParams = ref<TaskParam[]>([])
const taskParamTotal = ref(0)
const resultTotal = ref(0)
const taskListPage = ref(1)
const resultPage = ref(1)
const activeTab = ref<TabKey>('taskList')
const loading = ref(false)
const showImportModal = ref(false)
const showClearConfirm = ref(false)
const selectedFile = ref<File | null>(null)
const importTaskName = ref('发布相似商品')
const importing = ref(false)
const importSummary = ref<TaskParamImportResult | null>(null)
const rowActioningIds = ref<number[]>([])
const batchAction = ref<BatchActionKey>('')
const jsonTooltip = ref<JsonTooltipState>({
  visible: false,
  content: '-',
  left: 0,
  top: 0,
  width: tooltipMaxWidth,
})
let tooltipHideTimer: ReturnType<typeof setTimeout> | null = null

const taskListFilters = ref({
  task_name: '',
  status: '',
  shop_id: '',
  batch_id: '',
})

const resultFilters = ref({
  task_name: '',
  status: '',
  shop_id: '',
  batch_id: '',
  updated_from: '',
  updated_to: '',
})

const isTaskListTab = computed(() => activeTab.value === 'taskList')
const totalPages = computed(() => {
  const totalCount = isTaskListTab.value ? taskParamTotal.value : resultTotal.value
  return Math.max(1, Math.ceil(totalCount / pageSize))
})
const currentPage = computed(() => (isTaskListTab.value ? taskListPage.value : resultPage.value))
const currentTotal = computed(() => (isTaskListTab.value ? taskParamTotal.value : resultTotal.value))

const currentTemplateColumns = computed(() => {
  if (importTaskName.value === '发布换图商品') {
    return ['店铺ID', '父商品ID', '新标题', '发布次数', '图片路径']
  }
  return ['店铺ID', '父商品ID', '新标题', '发布次数']
})

const shopNameMap = computed<Record<string, string>>(() =>
  Object.fromEntries(shops.value.map((shop) => [shop.id, shop.name])),
)

function buildTaskListFilters(page = taskListPage.value): TaskParamFilters {
  return {
    page,
    page_size: pageSize,
    shop_id: taskListFilters.value.shop_id || undefined,
    task_name: taskListFilters.value.task_name || undefined,
    status: taskListFilters.value.status || undefined,
    batch_id: taskListFilters.value.batch_id || undefined,
    sort_by: 'created_at',
    sort_order: 'desc',
  }
}

function buildResultFilters(page = resultPage.value): TaskParamFilters {
  return {
    page,
    page_size: pageSize,
    shop_id: resultFilters.value.shop_id || undefined,
    task_name: resultFilters.value.task_name || undefined,
    status: resultFilters.value.status || 'success,failed',
    batch_id: resultFilters.value.batch_id || undefined,
    updated_from: resultFilters.value.updated_from || undefined,
    updated_to: resultFilters.value.updated_to || undefined,
    sort_by: 'updated_at',
    sort_order: 'desc',
  }
}

function buildBatchPayload(): TaskParamBatchPayload {
  return {
    shop_id: taskListFilters.value.shop_id || undefined,
    task_name: taskListFilters.value.task_name || undefined,
    status: taskListFilters.value.status || undefined,
    batch_id: taskListFilters.value.batch_id || undefined,
  }
}

function buildBatchOptionFilters(): TaskParamFilters {
  if (activeTab.value === 'taskList') {
    return {
      shop_id: taskListFilters.value.shop_id || undefined,
      task_name: taskListFilters.value.task_name || undefined,
      status: taskListFilters.value.status || undefined,
    }
  }

  return {
    shop_id: resultFilters.value.shop_id || undefined,
    task_name: resultFilters.value.task_name || undefined,
    status: resultFilters.value.status || 'success,failed',
  }
}

function hasExplicitBatchFilter() {
  return Boolean(
    taskListFilters.value.shop_id
      || taskListFilters.value.task_name
      || taskListFilters.value.status
      || taskListFilters.value.batch_id,
  )
}

function isRowActioning(id: number) {
  return rowActioningIds.value.includes(id)
}

function setRowActioning(id: number, actioning: boolean) {
  if (actioning) {
    if (!rowActioningIds.value.includes(id)) {
      rowActioningIds.value = [...rowActioningIds.value, id]
    }
    return
  }

  rowActioningIds.value = rowActioningIds.value.filter((itemId) => itemId !== id)
}

function normalizeJson(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>
  }

  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>
      }
    } catch {
      return {}
    }
  }

  return {}
}

function pickValue(source: unknown, keys: string[]) {
  const record = normalizeJson(source)
  for (const key of keys) {
    const value = record[key]
    if (value === undefined || value === null) {
      continue
    }

    const text = String(value).trim()
    if (text) {
      return text
    }
  }

  return ''
}

function formatJsonTooltip(source: unknown) {
  const record = normalizeJson(source)
  if (!Object.keys(record).length) {
    return '-'
  }
  return JSON.stringify(record, null, 2)
}

function formatParamSummary(params: unknown) {
  const 字段列表: Array<[string, string]> = [
    ['父商品ID', pickValue(params, ['父商品ID', 'parent_product_id'])],
    ['新标题', pickValue(params, ['新标题', 'new_title'])],
    ['折扣', pickValue(params, ['折扣', 'discount'])],
    ['投产比', pickValue(params, ['投产比', 'roi'])],
    ['发布次数', pickValue(params, ['发布次数', 'publish_count'])],
  ]

  const 有效字段 = 字段列表
    .filter(([, 值]) => Boolean(值))
    .map(([标签, 值]) => `${标签}: ${值}`)

  return 有效字段.length ? 有效字段.join(' / ') : '-'
}

function formatResultSummary(result: unknown) {
  const message = pickValue(result, ['message', 'msg'])
  if (message) {
    return message
  }

  const goodsId = pickValue(result, ['goods_id'])
  if (goodsId) {
    return `商品ID: ${goodsId}`
  }

  const newProductId = pickValue(result, ['新商品ID', 'new_product_id'])
  if (newProductId) {
    return `新商品ID: ${newProductId}`
  }

  return '-'
}

function formatExecutionResult(result: unknown) {
  const newProductId = pickValue(result, ['新商品ID', 'new_product_id'])
  return newProductId ? `新ID: ${newProductId}` : '-'
}

function formatFieldValue(source: unknown, keys: string[]) {
  return pickValue(source, keys) || '-'
}

function parseDateTime(value?: string | null) {
  if (!value) {
    return null
  }

  const date = new Date(value.replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) {
    return null
  }

  return date
}

function formatDateTime(value?: string | null) {
  const date = parseDateTime(value)
  if (!date) {
    return '--'
  }

  return date.toLocaleString('zh-CN', {
    hour12: false,
  })
}

function formatBatchOptionLabel(option: TaskParamBatchOption) {
  const latestDate = option.latest_updated_at ? option.latest_updated_at.slice(0, 10) : '--'
  return `批次 ${option.batch_id} (${latestDate}, ${option.record_count}条)`
}

function formatShopLabel(taskParam: TaskParam) {
  const shopName = shopNameMap.value[taskParam.shop_id] || taskParam.shop_name
  if (!shopName) {
    return `#${taskParam.shop_id}`
  }
  return `${shopName}（#${taskParam.shop_id}）`
}

function clearTooltipHideTimer() {
  if (tooltipHideTimer) {
    clearTimeout(tooltipHideTimer)
    tooltipHideTimer = null
  }
}

function showJsonTooltip(event: MouseEvent, source: unknown) {
  clearTooltipHideTimer()
  const currentTarget = event.currentTarget
  if (!(currentTarget instanceof HTMLElement)) {
    return
  }

  const rect = currentTarget.getBoundingClientRect()
  const tooltipWidth = Math.min(
    tooltipMaxWidth,
    Math.max(240, window.innerWidth - tooltipViewportPadding * 2),
  )
  const maxLeft = Math.max(
    tooltipViewportPadding,
    window.innerWidth - tooltipWidth - tooltipViewportPadding,
  )
  const maxTop = Math.max(
    tooltipViewportPadding,
    window.innerHeight - tooltipViewportPadding - 160,
  )

  jsonTooltip.value = {
    visible: true,
    content: formatJsonTooltip(source),
    left: Math.min(Math.max(rect.left, tooltipViewportPadding), maxLeft),
    top: Math.min(rect.bottom + tooltipGap, maxTop),
    width: tooltipWidth,
  }
}

function scheduleHideJsonTooltip() {
  clearTooltipHideTimer()
  tooltipHideTimer = window.setTimeout(() => {
    jsonTooltip.value.visible = false
    tooltipHideTimer = null
  }, 120)
}

function keepJsonTooltipOpen() {
  clearTooltipHideTimer()
}

function hideJsonTooltip() {
  clearTooltipHideTimer()
  jsonTooltip.value.visible = false
}

function replaceTaskParam(updatedTaskParam: TaskParam) {
  taskParams.value = taskParams.value.map((taskParam) =>
    taskParam.id === updatedTaskParam.id ? updatedTaskParam : taskParam,
  )
  resultTaskParams.value = resultTaskParams.value.map((taskParam) =>
    taskParam.id === updatedTaskParam.id ? updatedTaskParam : taskParam,
  )
}

async function loadShops() {
  try {
    const result = await listShops()
    shops.value = result.list
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载店铺列表失败'
    toast.error(message)
  }
}

async function loadBatchOptions() {
  try {
    batchOptions.value = await listTaskParamBatchOptions(buildBatchOptionFilters())
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载批次列表失败'
    toast.error(message)
  }
}

async function loadTaskParams(page = taskListPage.value) {
  loading.value = true
  try {
    const result = await listTaskParams(buildTaskListFilters(page))
    taskListPage.value = page
    taskParams.value = result.list
    taskParamTotal.value = result.total
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载任务参数失败'
    toast.error(message)
  } finally {
    loading.value = false
  }
}

async function loadResultTaskParams(page = resultPage.value) {
  if (
    resultFilters.value.updated_from
    && resultFilters.value.updated_to
    && resultFilters.value.updated_from > resultFilters.value.updated_to
  ) {
    resultTaskParams.value = []
    resultTotal.value = 0
    toast.warning('开始日期不能晚于结束日期')
    return
  }

  loading.value = true
  try {
    const result = await listTaskParams(buildResultFilters(page))
    resultPage.value = page
    resultTaskParams.value = result.list
    resultTotal.value = result.total
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载执行结果失败'
    toast.error(message)
  } finally {
    loading.value = false
  }
}

function handleTaskListSearch() {
  void loadBatchOptions()
  void loadTaskParams(1)
}

function handleResultSearch() {
  void loadBatchOptions()
  void loadResultTaskParams(1)
}

function handleTabChange(tab: TabKey) {
  if (activeTab.value === tab) {
    return
  }

  activeTab.value = tab
  void loadBatchOptions()

  if (tab === 'taskList') {
    void loadTaskParams(1)
    return
  }

  void loadResultTaskParams(1)
}

function handlePageChange(page: number) {
  if (page < 1 || page > totalPages.value) {
    return
  }

  if (activeTab.value === 'taskList') {
    void loadTaskParams(page)
    return
  }

  void loadResultTaskParams(page)
}

function openImportModal() {
  importTaskName.value = taskListFilters.value.task_name || '发布相似商品'
  selectedFile.value = null
  importSummary.value = null
  showImportModal.value = true
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
}

async function handleImport() {
  if (!selectedFile.value) {
    toast.warning('请选择 CSV 文件')
    return
  }

  importing.value = true
  try {
    const result = await importTaskParamsCsv(importTaskName.value, selectedFile.value)
    importSummary.value = result
    toast.success(`导入完成：成功 ${result.success_count} 条，跳过 ${result.failed_count} 条`)
    await loadTaskParams(1)
    await loadBatchOptions()
  } catch (error) {
    const message = error instanceof Error ? error.message : '导入 CSV 失败'
    toast.error(message)
  } finally {
    importing.value = false
  }
}

async function handleToggleEnabled(taskParam: TaskParam) {
  setRowActioning(taskParam.id, true)
  try {
    const updatedTaskParam = taskParam.enabled
      ? await disableTaskParam(taskParam.id)
      : await enableTaskParam(taskParam.id)
    replaceTaskParam(updatedTaskParam)
    toast.success(taskParam.enabled ? '记录已禁用' : '记录已启用')
  } catch (error) {
    const message = error instanceof Error ? error.message : '切换启用状态失败'
    toast.error(message)
    await loadTaskParams(taskListPage.value)
  } finally {
    setRowActioning(taskParam.id, false)
  }
}

async function handleResetTaskParam(taskParam: TaskParam) {
  setRowActioning(taskParam.id, true)
  try {
    const updatedTaskParam = await resetTaskParam(taskParam.id)
    replaceTaskParam(updatedTaskParam)
    toast.success('记录已重置为待执行')
  } catch (error) {
    const message = error instanceof Error ? error.message : '重置记录失败'
    toast.error(message)
  } finally {
    setRowActioning(taskParam.id, false)
  }
}

async function handleDelete(id: number) {
  setRowActioning(id, true)
  try {
    await deleteTaskParam(id)
    toast.success('记录已删除')
    if (taskParams.value.length === 1 && taskListPage.value > 1) {
      await loadTaskParams(taskListPage.value - 1)
    } else {
      await loadTaskParams(taskListPage.value)
    }
    await loadBatchOptions()
  } catch (error) {
    const message = error instanceof Error ? error.message : '删除记录失败'
    toast.error(message)
  } finally {
    setRowActioning(id, false)
  }
}

async function handleClear() {
  try {
    const result = await clearTaskParams(buildTaskListFilters())
    toast.success(`已清空 ${result.deleted_count} 条记录`)
    showClearConfirm.value = false
    await loadTaskParams(1)
    await loadBatchOptions()
  } catch (error) {
    const message = error instanceof Error ? error.message : '清空记录失败'
    toast.error(message)
  }
}

async function runBatchAction(action: Exclude<BatchActionKey, ''>) {
  if (action !== 'reset' && !hasExplicitBatchFilter()) {
    toast.warning('批量启用或批量禁用前，请至少选择一个筛选条件')
    return
  }

  batchAction.value = action
  const payload = buildBatchPayload()

  try {
    if (action === 'reset') {
      const result = await batchResetTaskParams(payload)
      toast.success(`已重置 ${result.updated_count} 条记录`)
    }

    if (action === 'enable') {
      const result = await batchEnableTaskParams(payload)
      toast.success(`已启用 ${result.updated_count} 条记录`)
    }

    if (action === 'disable') {
      const result = await batchDisableTaskParams(payload)
      toast.success(`已禁用 ${result.updated_count} 条记录`)
    }

    await loadTaskParams(1)
    await loadBatchOptions()
  } catch (error) {
    const actionLabel = action === 'reset' ? '批量重置' : action === 'enable' ? '批量启用' : '批量禁用'
    const message = error instanceof Error ? error.message : `${actionLabel}失败`
    toast.error(message)
  } finally {
    batchAction.value = ''
  }
}

function downloadTemplate() {
  const rows = [
    currentTemplateColumns.value.join(','),
    importTaskName.value === '发布换图商品'
      ? '示例店铺名称,123456,示例标题,3,E:/images/demo.png'
      : '示例店铺名称,123456,示例标题,3',
  ]
  const blob = new Blob([`\uFEFF${rows.join('\n')}`], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${importTaskName.value}_模板.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

onMounted(() => {
  void loadShops()
  void loadBatchOptions()
  void loadTaskParams()
})

onBeforeUnmount(() => {
  clearTooltipHideTimer()
})
</script>

<template>
  <div class="task-params-manage">
    <div class="header">
      <div>
        <h1>任务参数管理</h1>
        <p class="header-tip">导入后的记录会长期保留，可按需禁用、重置或查看执行结果。</p>
      </div>
      <div v-if="isTaskListTab" class="header-actions">
        <button class="btn btn-secondary" @click="showClearConfirm = true">清空</button>
        <button class="btn btn-primary" @click="openImportModal">导入CSV</button>
      </div>
    </div>

    <div class="tabs">
      <button
        class="tab-button"
        :class="{ 'is-active': activeTab === 'taskList' }"
        @click="handleTabChange('taskList')"
      >
        任务列表
      </button>
      <button
        class="tab-button"
        :class="{ 'is-active': activeTab === 'resultList' }"
        @click="handleTabChange('resultList')"
      >
        执行结果
      </button>
    </div>

    <div v-if="isTaskListTab" class="filters">
      <select v-model="taskListFilters.task_name" class="filter-select" @change="handleTaskListSearch">
        <option value="">全部任务类型</option>
        <option v-for="task in taskOptions" :key="task" :value="task">{{ task }}</option>
      </select>

      <select v-model="taskListFilters.status" class="filter-select" @change="handleTaskListSearch">
        <option value="">全部状态</option>
        <option value="pending">待执行</option>
        <option value="running">执行中</option>
        <option value="success">成功</option>
        <option value="failed">失败</option>
        <option value="skipped">跳过</option>
      </select>

      <select v-model="taskListFilters.shop_id" class="filter-select" @change="handleTaskListSearch">
        <option value="">全部店铺</option>
        <option v-for="shop in shops" :key="shop.id" :value="shop.id">{{ shop.name }}（#{{ shop.id }}）</option>
      </select>

      <select v-model="taskListFilters.batch_id" class="filter-select" @change="handleTaskListSearch">
        <option value="">全部批次</option>
        <option v-for="option in batchOptions" :key="option.batch_id" :value="option.batch_id">
          {{ formatBatchOptionLabel(option) }}
        </option>
      </select>

      <button class="btn btn-light" @click="handleTaskListSearch">刷新</button>
    </div>

    <div v-else class="filters">
      <select v-model="resultFilters.task_name" class="filter-select" @change="handleResultSearch">
        <option value="">全部任务类型</option>
        <option v-for="task in taskOptions" :key="task" :value="task">{{ task }}</option>
      </select>

      <select v-model="resultFilters.status" class="filter-select" @change="handleResultSearch">
        <option value="">全部执行状态</option>
        <option value="success">成功</option>
        <option value="failed">失败</option>
      </select>

      <select v-model="resultFilters.shop_id" class="filter-select" @change="handleResultSearch">
        <option value="">全部店铺</option>
        <option v-for="shop in shops" :key="shop.id" :value="shop.id">{{ shop.name }}（#{{ shop.id }}）</option>
      </select>

      <select v-model="resultFilters.batch_id" class="filter-select" @change="handleResultSearch">
        <option value="">全部批次</option>
        <option v-for="option in batchOptions" :key="option.batch_id" :value="option.batch_id">
          {{ formatBatchOptionLabel(option) }}
        </option>
      </select>

      <input
        v-model="resultFilters.updated_from"
        class="filter-date"
        type="date"
        @change="handleResultSearch"
      />
      <input
        v-model="resultFilters.updated_to"
        class="filter-date"
        type="date"
        @change="handleResultSearch"
      />

      <button class="btn btn-light" @click="handleResultSearch">刷新</button>
    </div>

    <div v-if="isTaskListTab" class="toolbar">
      <div class="toolbar-actions">
        <button
          class="btn btn-light"
          :disabled="batchAction !== ''"
          @click="runBatchAction('reset')"
        >
          {{ batchAction === 'reset' ? '批量重置中...' : '批量重置' }}
        </button>
        <button
          class="btn btn-light"
          :disabled="batchAction !== ''"
          @click="runBatchAction('enable')"
        >
          {{ batchAction === 'enable' ? '批量启用中...' : '批量启用' }}
        </button>
        <button
          class="btn btn-light"
          :disabled="batchAction !== ''"
          @click="runBatchAction('disable')"
        >
          {{ batchAction === 'disable' ? '批量禁用中...' : '批量禁用' }}
        </button>
      </div>
      <p class="toolbar-tip">批量启用、批量禁用需要至少选择一个筛选条件；批量重置默认处理成功和失败记录。</p>
    </div>

    <div class="table-container">
      <table v-if="isTaskListTab" class="task-param-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>店铺</th>
            <th>任务类型</th>
            <th>启用</th>
            <th>参数</th>
            <th>状态</th>
            <th>已执行次数</th>
            <th>结果</th>
            <th>执行结果</th>
            <th>错误信息</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="12" class="empty-state">加载中...</td>
          </tr>
          <tr v-else-if="taskParams.length === 0">
            <td colspan="12" class="empty-state">暂无任务参数记录</td>
          </tr>
          <template v-else>
            <tr
              v-for="taskParam in taskParams"
              :key="taskParam.id"
              :class="{ 'is-disabled': !taskParam.enabled }"
            >
              <td>{{ taskParam.id }}</td>
              <td class="cell-wrap">{{ formatShopLabel(taskParam) }}</td>
              <td>{{ taskParam.task_name }}</td>
              <td>
                <label class="switch">
                  <input
                    type="checkbox"
                    :checked="taskParam.enabled"
                    :disabled="isRowActioning(taskParam.id)"
                    @change="handleToggleEnabled(taskParam)"
                  />
                  <span class="switch-slider" />
                  <span class="switch-label">{{ taskParam.enabled ? '启用' : '禁用' }}</span>
                </label>
              </td>
              <td class="cell-wide">
                <span
                  class="tooltip-trigger cell-ellipsis cell-wide"
                  @mouseenter="showJsonTooltip($event, taskParam.params)"
                  @mouseleave="scheduleHideJsonTooltip"
                >
                  {{ formatParamSummary(taskParam.params) }}
                </span>
              </td>
              <td>
                <StatusBadge :status="taskParam.status" type="task" />
              </td>
              <td>{{ taskParam.run_count }}</td>
              <td class="cell-ellipsis" :title="formatJsonTooltip(taskParam.result)">
                {{ formatResultSummary(taskParam.result) }}
              </td>
              <td>
                <span
                  class="tooltip-trigger cell-ellipsis"
                  @mouseenter="showJsonTooltip($event, taskParam.result)"
                  @mouseleave="scheduleHideJsonTooltip"
                >
                  {{ formatExecutionResult(taskParam.result) }}
                </span>
              </td>
              <td class="cell-ellipsis error-text" :title="taskParam.error || '-'">
                {{ taskParam.error || '-' }}
              </td>
              <td>{{ formatDateTime(taskParam.created_at) }}</td>
              <td>
                <div class="action-group">
                  <button
                    v-if="taskParam.status !== 'pending'"
                    class="btn-action btn-reset"
                    :disabled="isRowActioning(taskParam.id)"
                    @click="handleResetTaskParam(taskParam)"
                  >
                    重置
                  </button>
                  <button
                    class="btn-action btn-delete"
                    :disabled="isRowActioning(taskParam.id)"
                    @click="handleDelete(taskParam.id)"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>

      <table v-else class="task-param-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>店铺</th>
            <th>任务类型</th>
            <th>父商品ID</th>
            <th>新商品ID</th>
            <th>折扣</th>
            <th>投产比</th>
            <th>状态</th>
            <th>错误信息</th>
            <th>执行时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="10" class="empty-state">加载中...</td>
          </tr>
          <tr v-else-if="resultTaskParams.length === 0">
            <td colspan="10" class="empty-state">暂无执行结果记录</td>
          </tr>
          <template v-else>
            <tr v-for="taskParam in resultTaskParams" :key="taskParam.id">
              <td>{{ taskParam.id }}</td>
              <td class="cell-wrap">{{ formatShopLabel(taskParam) }}</td>
              <td>{{ taskParam.task_name }}</td>
              <td class="cell-ellipsis" :title="formatJsonTooltip(taskParam.params)">
                {{ formatFieldValue(taskParam.params, ['父商品ID', 'parent_product_id']) }}
              </td>
              <td class="cell-ellipsis" :title="formatJsonTooltip(taskParam.result)">
                {{ formatFieldValue(taskParam.result, ['新商品ID', 'new_product_id']) }}
              </td>
              <td>{{ formatFieldValue(taskParam.params, ['折扣', 'discount']) }}</td>
              <td>{{ formatFieldValue(taskParam.params, ['投产比', 'roi']) }}</td>
              <td>
                <StatusBadge :status="taskParam.status" type="task" />
              </td>
              <td class="cell-ellipsis error-text" :title="taskParam.error || '-'">
                {{ taskParam.error || '-' }}
              </td>
              <td>{{ formatDateTime(taskParam.updated_at) }}</td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <div class="pagination">
      <button class="btn-page" :disabled="currentPage <= 1" @click="handlePageChange(currentPage - 1)">
        上一页
      </button>
      <span class="page-info">
        第 {{ currentPage }} / {{ totalPages }} 页，共 {{ currentTotal }} 条
      </span>
      <button class="btn-page" :disabled="currentPage >= totalPages" @click="handlePageChange(currentPage + 1)">
        下一页
      </button>
    </div>

    <Modal :show="showImportModal" title="CSV导入" width="720px" @close="showImportModal = false">
      <div class="import-form">
        <div class="form-group">
          <label>任务类型</label>
          <select v-model="importTaskName">
            <option v-for="task in taskOptions" :key="task" :value="task">{{ task }}</option>
          </select>
        </div>

        <div class="template-box">
          <div class="template-header">
            <h4>CSV 模板说明</h4>
            <button class="btn btn-light" @click="downloadTemplate">下载模板</button>
          </div>
          <p>列名：{{ currentTemplateColumns.join('、') }}</p>
          <p>“店铺ID”列支持填写店铺ID或店铺名称，导入时会自动匹配。</p>
          <p>“发布次数”列可选，留空默认导入 1 条，填写 3 会自动展开 3 条 pending 记录。</p>
          <p>多次展开后的记录会自动写入批次序号，便于区分同一批次内的重复发布任务。</p>
          <p v-if="importTaskName === '发布换图商品'">示例：店铺ID、父商品ID、新标题、发布次数、图片路径（本地绝对路径）</p>
          <p v-else>示例：店铺ID、父商品ID、新标题、发布次数</p>
        </div>

        <div class="form-group">
          <label>上传 CSV 文件</label>
          <input type="file" accept=".csv,text/csv" @change="handleFileChange" />
          <span class="file-name">{{ selectedFile?.name || '未选择文件' }}</span>
        </div>

        <div v-if="importSummary" class="import-result">
          <strong>导入结果</strong>
          <p>成功 {{ importSummary.success_count }} 条 / 跳过 {{ importSummary.failed_count }} 条</p>
          <p v-if="importSummary.errors.length > 0" class="error-text">
            {{ importSummary.errors.slice(0, 3).join('；') }}
          </p>
        </div>
      </div>

      <template #footer>
        <button class="btn btn-secondary" @click="showImportModal = false">关闭</button>
        <button class="btn btn-primary" :disabled="importing" @click="handleImport">
          {{ importing ? '导入中...' : '开始导入' }}
        </button>
      </template>
    </Modal>

    <ConfirmDialog
      :show="showClearConfirm"
      title="确认清空"
      message="确定要按当前筛选条件清空任务参数记录吗？"
      type="danger"
      @confirm="handleClear"
      @cancel="showClearConfirm = false"
    />

    <Teleport to="body">
      <div
        v-if="jsonTooltip.visible"
        class="json-tooltip-panel"
        :style="{
          left: `${jsonTooltip.left}px`,
          top: `${jsonTooltip.top}px`,
          width: `${jsonTooltip.width}px`,
        }"
        @mouseenter="keepJsonTooltipOpen"
        @mouseleave="hideJsonTooltip"
      >
        <pre>{{ jsonTooltip.content }}</pre>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.task-params-manage {
  color: #1a1a2e;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

.header-tip {
  margin: 8px 0 0;
  color: #6b7280;
  line-height: 1.5;
}

.tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.tab-button {
  border: 1px solid #dbeafe;
  background: #eff6ff;
  color: #1d4ed8;
  border-radius: 999px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-button.is-active {
  background: #1d4ed8;
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(29, 78, 216, 0.18);
}

.header-actions,
.toolbar-actions,
.action-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

h1 {
  margin: 0;
  font-size: 28px;
}

.filters,
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
  justify-content: space-between;
}

.toolbar {
  padding: 14px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
}

.toolbar-tip {
  margin: 0;
  color: #6b7280;
  font-size: 13px;
  line-height: 1.5;
}

.filter-select,
.filter-date {
  min-width: 180px;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #ffffff;
  color: #1a1a2e;
}

.filter-date {
  min-width: 170px;
}

.table-container {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow-x: auto;
}

.task-param-table {
  width: 100%;
  border-collapse: collapse;
}

.task-param-table thead {
  background: #f3f4f6;
}

.task-param-table th,
.task-param-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
  vertical-align: top;
}

.task-param-table tbody tr:nth-child(even) {
  background: #f9fafb;
}

.task-param-table tbody tr.is-disabled {
  opacity: 0.55;
}

.task-param-table tbody tr.is-disabled td {
  background: rgba(229, 231, 235, 0.25);
}

.cell-wrap {
  max-width: 240px;
  white-space: normal;
  word-break: break-word;
}

.cell-ellipsis {
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cell-wide {
  max-width: 320px;
}

.tooltip-trigger {
  display: block;
  width: 100%;
  cursor: help;
}

.json-tooltip-panel {
  position: fixed;
  z-index: 3000;
  max-width: 500px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.96);
  color: #e5eefc;
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.28);
}

.json-tooltip-panel pre {
  margin: 0;
  max-height: min(60vh, 420px);
  overflow: auto;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.empty-state {
  text-align: center;
  color: #9ca3af;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.page-info {
  color: #6b7280;
  font-size: 14px;
}

.btn,
.btn-action,
.btn-page {
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn {
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 500;
}

.btn-primary {
  background: #3b82f6;
  color: #ffffff;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #6b7280;
  color: #ffffff;
}

.btn-secondary:hover {
  background: #4b5563;
}

.btn-light {
  background: #f3f4f6;
  color: #1a1a2e;
}

.btn-light:hover {
  background: #e5e7eb;
}

.btn-action {
  padding: 6px 14px;
  color: #ffffff;
  font-size: 12px;
}

.btn-reset {
  background: #0ea5e9;
}

.btn-reset:hover {
  background: #0284c7;
}

.btn-delete {
  background: #ef4444;
}

.btn-delete:hover {
  background: #dc2626;
}

.btn-page {
  padding: 8px 16px;
  background: #f3f4f6;
  color: #1a1a2e;
}

.btn:disabled,
.btn-action:disabled,
.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.switch {
  display: inline-flex;
  align-items: center;
  gap: 10px;
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

.switch-label {
  color: #374151;
  font-size: 13px;
}

.import-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label,
.template-box h4 {
  margin: 0;
  font-size: 14px;
  color: #374151;
}

.form-group select,
.form-group input[type="file"] {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #ffffff;
  color: #1a1a2e;
}

.template-box,
.import-result {
  padding: 16px;
  border-radius: 8px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.template-box p,
.import-result p {
  margin: 6px 0 0;
  color: #4b5563;
  line-height: 1.5;
}

.file-name,
.error-text {
  color: #dc2626;
}

@media (max-width: 900px) {
  .header,
  .toolbar,
  .template-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions,
  .toolbar-actions {
    width: 100%;
  }

  .header-actions .btn,
  .toolbar-actions .btn {
    flex: 1;
  }

  .filters {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-select,
  .filter-date {
    width: 100%;
  }
}
</style>
