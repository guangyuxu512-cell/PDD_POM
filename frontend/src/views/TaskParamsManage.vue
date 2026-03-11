<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

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
  listTaskParams,
  resetTaskParam,
} from '../api/taskParams'
import type {
  Shop,
  TaskParam,
  TaskParamBatchPayload,
  TaskParamFilters,
  TaskParamImportResult,
} from '../api/types'
import { toast } from '../utils/toast'

type BatchActionKey = '' | 'reset' | 'enable' | 'disable'

const taskOptions = ['发布相似商品', '发布换图商品']
const pageSize = 10

const shops = ref<Shop[]>([])
const taskParams = ref<TaskParam[]>([])
const total = ref(0)
const currentPage = ref(1)
const loading = ref(false)
const showImportModal = ref(false)
const showClearConfirm = ref(false)
const selectedFile = ref<File | null>(null)
const importTaskName = ref('发布相似商品')
const importing = ref(false)
const importSummary = ref<TaskParamImportResult | null>(null)
const rowActioningIds = ref<number[]>([])
const batchAction = ref<BatchActionKey>('')

const filters = ref({
  task_name: '',
  status: '',
  shop_id: '',
})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const currentTemplateColumns = computed(() => {
  if (importTaskName.value === '发布换图商品') {
    return ['店铺ID', '父商品ID', '新标题', '发布次数', '图片路径']
  }
  return ['店铺ID', '父商品ID', '新标题', '发布次数']
})

function buildFilters(page = currentPage.value): TaskParamFilters {
  return {
    page,
    page_size: pageSize,
    shop_id: filters.value.shop_id || undefined,
    task_name: filters.value.task_name || undefined,
    status: filters.value.status || undefined,
  }
}

function buildBatchPayload(): TaskParamBatchPayload {
  return {
    shop_id: filters.value.shop_id || undefined,
    task_name: filters.value.task_name || undefined,
    status: filters.value.status || undefined,
  }
}

function hasExplicitBatchFilter() {
  return Boolean(filters.value.shop_id || filters.value.task_name || filters.value.status)
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

function replaceTaskParam(updatedTaskParam: TaskParam) {
  taskParams.value = taskParams.value.map((taskParam) =>
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

async function loadTaskParams(page = currentPage.value) {
  loading.value = true
  try {
    const result = await listTaskParams(buildFilters(page))
    currentPage.value = page
    taskParams.value = result.list
    total.value = result.total
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载任务参数失败'
    toast.error(message)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  void loadTaskParams(1)
}

function openImportModal() {
  importTaskName.value = filters.value.task_name || '发布相似商品'
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
    await loadTaskParams(currentPage.value)
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
    if (taskParams.value.length === 1 && currentPage.value > 1) {
      await loadTaskParams(currentPage.value - 1)
      return
    }
    await loadTaskParams()
  } catch (error) {
    const message = error instanceof Error ? error.message : '删除记录失败'
    toast.error(message)
  } finally {
    setRowActioning(id, false)
  }
}

async function handleClear() {
  try {
    const result = await clearTaskParams(buildFilters())
    toast.success(`已清空 ${result.deleted_count} 条记录`)
    showClearConfirm.value = false
    await loadTaskParams(1)
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
  } catch (error) {
    const actionLabel = action === 'reset' ? '批量重置' : action === 'enable' ? '批量启用' : '批量禁用'
    const message = error instanceof Error ? error.message : `${actionLabel}失败`
    toast.error(message)
  } finally {
    batchAction.value = ''
  }
}

function formatParams(params: Record<string, any>) {
  const parts: string[] = []
  if (params.parent_product_id) parts.push(`父商品ID：${params.parent_product_id}`)
  if (params.new_title) parts.push(`新标题：${params.new_title}`)
  if (params.image_path) parts.push(`图片路径：${params.image_path}`)
  if (params.batch_index) parts.push(`批次序号：${params.batch_index}`)
  return parts.length ? parts.join(' / ') : '-'
}

function formatResult(result: Record<string, any>) {
  const parts: string[] = []
  if (result.new_product_id) parts.push(`新商品ID：${result.new_product_id}`)
  if (result.goods_id) parts.push(`商品ID：${result.goods_id}`)
  if (result.message) parts.push(String(result.message))
  return parts.length ? parts.join(' / ') : '-'
}

const shopNameMap = computed<Record<string, string>>(() =>
  Object.fromEntries(shops.value.map((shop) => [shop.id, shop.name])),
)

function formatShopLabel(taskParam: TaskParam) {
  const shopName = shopNameMap.value[taskParam.shop_id] || taskParam.shop_name
  if (!shopName) {
    return `#${taskParam.shop_id}`
  }
  return `${shopName}（#${taskParam.shop_id}）`
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
  void loadTaskParams()
})
</script>

<template>
  <div class="task-params-manage">
    <div class="header">
      <div>
        <h1>任务参数管理</h1>
        <p class="header-tip">导入后的记录会长期保留，可按需禁用、重置或再次执行。</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="showClearConfirm = true">清空</button>
        <button class="btn btn-primary" @click="openImportModal">导入CSV</button>
      </div>
    </div>

    <div class="filters">
      <select v-model="filters.task_name" class="filter-select" @change="handleSearch">
        <option value="">全部任务类型</option>
        <option v-for="task in taskOptions" :key="task" :value="task">{{ task }}</option>
      </select>

      <select v-model="filters.status" class="filter-select" @change="handleSearch">
        <option value="">全部状态</option>
        <option value="pending">待执行</option>
        <option value="running">执行中</option>
        <option value="success">成功</option>
        <option value="failed">失败</option>
        <option value="skipped">跳过</option>
      </select>

      <select v-model="filters.shop_id" class="filter-select" @change="handleSearch">
        <option value="">全部店铺</option>
        <option v-for="shop in shops" :key="shop.id" :value="shop.id">{{ shop.name }}（#{{ shop.id }}）</option>
      </select>

      <button class="btn btn-light" @click="handleSearch">刷新</button>
    </div>

    <div class="toolbar">
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
      <table class="task-param-table">
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
            <th>错误信息</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="11" class="empty-state">加载中...</td>
          </tr>
          <tr v-else-if="taskParams.length === 0">
            <td colspan="11" class="empty-state">暂无任务参数记录</td>
          </tr>
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
            <td class="cell-wrap">{{ formatParams(taskParam.params) }}</td>
            <td>
              <StatusBadge :status="taskParam.status" type="task" />
            </td>
            <td>{{ taskParam.run_count }}</td>
            <td class="cell-wrap">{{ formatResult(taskParam.result) }}</td>
            <td class="cell-wrap error-text">{{ taskParam.error || '-' }}</td>
            <td>{{ taskParam.created_at || '-' }}</td>
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
        </tbody>
      </table>
    </div>

    <div class="pagination">
      <button class="btn-page" :disabled="currentPage <= 1" @click="loadTaskParams(currentPage - 1)">
        上一页
      </button>
      <span class="page-info">
        第 {{ currentPage }} / {{ totalPages }} 页，共 {{ total }} 条
      </span>
      <button class="btn-page" :disabled="currentPage >= totalPages" @click="loadTaskParams(currentPage + 1)">
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

.filter-select {
  min-width: 180px;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #ffffff;
  color: #1a1a2e;
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
  max-width: 260px;
  white-space: normal;
  word-break: break-all;
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
  }

  .filter-select {
    width: 100%;
  }
}
</style>
