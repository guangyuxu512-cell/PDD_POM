<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import { createBatch, createBatchStatusEventSource, stopBatch } from '../api/execute'
import { listFlows } from '../api/flows'
import { listShops } from '../api/shops'
import { listAvailableTasks } from '../api/tasks'
import type { AvailableTask, BatchShopState, BatchSnapshot, Flow, Shop } from '../api/types'
import { toast } from '../utils/toast'
import ExecuteConfigPanel from './batch-execute/ExecuteConfigPanel.vue'

interface ShopTimeline {
  startedAt?: number
  finishedAt?: number
}

const props = withDefaults(defineProps<{ showTitle?: boolean }>(), {
  showTitle: true,
})

const flows = ref<Flow[]>([])
const tasks = ref<AvailableTask[]>([])
const shops = ref<Shop[]>([])
const isLoading = ref(false)
const isStarting = ref(false)
const isStopping = ref(false)
const batchSnapshot = ref<BatchSnapshot | null>(null)
const currentBatchId = ref('')
const expandedShopId = ref<string | null>(null)
const shopTimeline = ref<Record<string, ShopTimeline>>({})

let statusSource: EventSource | null = null

const hasActiveBatch = computed(() => batchSnapshot.value?.status === 'running')
const batchShops = computed(() => Object.values(batchSnapshot.value?.shops ?? {}))
const batchInlineStats = computed(() => {
  if (!batchSnapshot.value) {
    return ''
  }

  return `批次 ${batchSnapshot.value.batch_id} · 总计 ${batchSnapshot.value.total} · ✅ ${batchSnapshot.value.completed} · 🔄 ${batchSnapshot.value.running} · ❌ ${batchSnapshot.value.failed}`
})

function closeStatusStream() {
  if (statusSource) {
    statusSource.close()
    statusSource = null
  }
}

function openStatusStream(batchId?: string) {
  closeStatusStream()

  statusSource = createBatchStatusEventSource(batchId)
  statusSource.onmessage = (event) => {
    const snapshot = JSON.parse(event.data) as BatchSnapshot
    currentBatchId.value = snapshot.batch_id
    batchSnapshot.value = snapshot
    if (['completed', 'failed', 'stopped'].includes(snapshot.status)) {
      closeStatusStream()
    }
  }

  statusSource.onerror = () => {
    if (!batchSnapshot.value || batchSnapshot.value.status === 'running') {
      return
    }
    closeStatusStream()
  }
}

watch(
  () => batchSnapshot.value?.batch_id,
  () => {
    shopTimeline.value = {}
    expandedShopId.value = null
  },
)

watch(
  batchSnapshot,
  (snapshot) => {
    if (!snapshot) {
      shopTimeline.value = {}
      expandedShopId.value = null
      return
    }

    syncTimeline(snapshot)
  },
  { immediate: true },
)

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

  return date.toLocaleString('zh-CN', { hour12: false })
}

function formatSeconds(value: number) {
  if (value < 60) {
    return `${value}s`
  }

  const minutes = Math.floor(value / 60)
  const seconds = value % 60
  return `${minutes}m ${seconds}s`
}

function syncTimeline(snapshot: BatchSnapshot) {
  const batchStartedAt = parseDateTime(snapshot.created_at)?.getTime() ?? Date.now()
  const batchUpdatedAt = parseDateTime(snapshot.updated_at)?.getTime() ?? Date.now()

  for (const shop of Object.values(snapshot.shops)) {
    const timeline = shopTimeline.value[shop.shop_id] ?? (shopTimeline.value[shop.shop_id] = {})
    if (!timeline.startedAt) {
      timeline.startedAt = batchStartedAt
    }
    if (['completed', 'failed', 'stopped'].includes(shop.status) && !timeline.finishedAt) {
      timeline.finishedAt = batchUpdatedAt
    }
  }
}

function formatDuration(shopId: string) {
  const timeline = shopTimeline.value[shopId]
  if (!timeline?.startedAt) {
    return '--'
  }

  const finishedAt = timeline.finishedAt ?? Date.now()
  return formatSeconds(Math.round(Math.max(0, finishedAt - timeline.startedAt) / 1000))
}

function getShopName(shopId: string) {
  return shops.value.find((shop) => shop.id === shopId)?.name ?? shopId
}

function getBatchShopName(shop: BatchShopState) {
  return shop.shop_name || getShopName(shop.shop_id)
}

function getCurrentStepLabel(shop: BatchShopState) {
  if (shop.status === 'waiting') {
    return '等待开始'
  }

  if (shop.status === 'running') {
    if (!shop.current_task) {
      return '等待任务进入执行'
    }
    return `${shop.current_task}（${shop.current_step}/${shop.total_steps}）`
  }

  if (shop.status === 'completed') {
    return '已完成'
  }

  if (shop.status === 'failed') {
    return '执行失败'
  }

  if (shop.status === 'stopped') {
    return '已停止'
  }

  return '--'
}

function getProgressPercent(shop: BatchShopState) {
  if (shop.total_steps <= 0) {
    return 0
  }

  if (['completed', 'failed', 'stopped'].includes(shop.status)) {
    return 100
  }

  if (shop.status === 'waiting') {
    return 0
  }

  return Math.min(100, Math.round((shop.current_step / shop.total_steps) * 100))
}

function getProgressText(shop: BatchShopState) {
  if (shop.total_steps <= 0) {
    return '--'
  }

  if (['completed', 'failed', 'stopped'].includes(shop.status)) {
    return `${shop.total_steps}/${shop.total_steps}`
  }

  return `${shop.current_step}/${shop.total_steps}`
}

function getStatusLabel(status: string) {
  if (status === 'waiting') return '等待中'
  if (status === 'running') return '执行中'
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  if (status === 'stopped') return '已停止'
  return status
}

function getStepStatusLabel(status: string) {
  if (status === 'pending') return '等待中'
  return getStatusLabel(status)
}

function getStatusClass(status: string) {
  if (status === 'waiting' || status === 'pending') return 'is-waiting'
  if (status === 'running') return 'is-running'
  if (status === 'completed') return 'is-completed'
  if (status === 'failed') return 'is-failed'
  if (status === 'stopped') return 'is-stopped'
  return 'is-waiting'
}

function getDetailSummary(shop: BatchShopState) {
  if (shop.status === 'failed') {
    return shop.last_error || '执行失败'
  }

  if (shop.status === 'stopped') {
    return '人工停止'
  }

  if (shop.status === 'completed') {
    return shop.last_result || '执行完成'
  }

  if (shop.current_task) {
    return `当前任务：${shop.current_task}`
  }

  return '等待进入队列'
}

function getStepResultText(shop: BatchShopState, index: number) {
  const step = shop.steps[index]
  if (!step) {
    return '--'
  }

  if (step.status === 'failed') {
    return step.error || '执行失败'
  }

  if (step.status === 'completed') {
    return step.result || '执行完成'
  }

  if (step.status === 'running') {
    return '执行中'
  }

  if (step.status === 'stopped') {
    return '已停止'
  }

  return '--'
}

function toggleShopDetail(shopId: string) {
  expandedShopId.value = expandedShopId.value === shopId ? null : shopId
}

function isShopDetailOpen(shopId: string) {
  return expandedShopId.value === shopId
}

async function loadReferenceData() {
  isLoading.value = true
  try {
    const [flowResponse, shopResponse, availableTasks] = await Promise.all([
      listFlows(),
      listShops(),
      listAvailableTasks(),
    ])

    flows.value = flowResponse.list
    shops.value = shopResponse.list
    tasks.value = availableTasks
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '加载执行配置失败')
  } finally {
    isLoading.value = false
  }
}

async function startExecution(payload: { flow_id?: string; task_name?: string; shop_ids: string[]; concurrency: number }) {
  isStarting.value = true
  try {
    batchSnapshot.value = null
    const result = await createBatch(payload)
    currentBatchId.value = result.batch_id
    openStatusStream(result.batch_id)
    toast.success('批量执行已启动')
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '启动批量执行失败')
  } finally {
    isStarting.value = false
  }
}

async function stopExecution() {
  isStopping.value = true
  try {
    await stopBatch(currentBatchId.value || undefined)
    toast.success('已请求停止当前批次')
  } catch (error) {
    toast.error(error instanceof Error ? error.message : '停止执行失败')
  } finally {
    isStopping.value = false
  }
}

onMounted(() => {
  void loadReferenceData()
  openStatusStream()
})

onUnmounted(() => {
  closeStatusStream()
})
</script>

<template>
  <div class="page">
    <header v-if="props.showTitle" class="page-header">
      <div>
        <h1>批量执行</h1>
      </div>
    </header>

    <div class="layout-grid">
      <ExecuteConfigPanel
        :flows="flows"
        :tasks="tasks"
        :shops="shops"
        :is-loading="isLoading"
        :has-active-batch="hasActiveBatch"
        :is-starting="isStarting"
        :is-stopping="isStopping"
        @start="startExecution"
        @stop="stopExecution"
      />

      <section class="panel status-panel">
        <div class="panel-header">
          <div>
            <h2>执行状态</h2>
            <p>基于 `/api/execute/status` 的 SSE 推送，按店铺实时更新执行进度。</p>
          </div>
        </div>

        <div v-if="!batchSnapshot" class="empty-state">
          <p>尚未收到批次状态。</p>
          <span>启动批量执行后，这里会显示表格化进度和步骤详情。</span>
        </div>

        <template v-else>
          <p class="inline-stats">{{ batchInlineStats }}</p>

          <div class="table-shell">
            <table class="status-table">
              <thead>
                <tr>
                  <th>店铺名称</th>
                  <th>当前步骤</th>
                  <th>进度</th>
                  <th style="width: 90px">状态</th>
                  <th style="width: 96px">耗时</th>
                  <th style="width: 108px">操作</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="shop in batchShops" :key="shop.shop_id">
                  <tr>
                    <td class="cell-shop" :title="getBatchShopName(shop)">
                      {{ getBatchShopName(shop) }}
                    </td>
                    <td class="cell-step" :title="getCurrentStepLabel(shop)">
                      {{ getCurrentStepLabel(shop) }}
                    </td>
                    <td class="cell-progress">
                      <div class="progress-cell">
                        <div class="progress-bar">
                          <div
                            class="progress-fill"
                            :style="{ width: `${getProgressPercent(shop)}%` }"
                          />
                        </div>
                        <span class="progress-text">{{ getProgressText(shop) }}</span>
                      </div>
                    </td>
                    <td class="cell-center">
                      <span class="status-tag" :class="getStatusClass(shop.status)">
                        {{ getStatusLabel(shop.status) }}
                      </span>
                    </td>
                    <td class="cell-center">{{ formatDuration(shop.shop_id) }}</td>
                    <td class="cell-center">
                      <button class="ghost-button btn-sm" @click="toggleShopDetail(shop.shop_id)">
                        {{ isShopDetailOpen(shop.shop_id) ? '收起详情' : '查看详情' }}
                      </button>
                    </td>
                  </tr>
                  <tr v-if="isShopDetailOpen(shop.shop_id)" class="detail-row">
                    <td colspan="6" class="detail-cell">
                      <div class="detail-header">
                        <strong>{{ getBatchShopName(shop) }}</strong>
                        <span>{{ getDetailSummary(shop) }}</span>
                      </div>
                      <table class="detail-table">
                        <thead>
                          <tr>
                            <th style="width: 56px">#</th>
                            <th>步骤</th>
                            <th style="width: 90px">状态</th>
                            <th>结果</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(step, index) in shop.steps" :key="`${shop.shop_id}-${step.task}-${index}`">
                            <td class="cell-center">{{ index + 1 }}</td>
                            <td>{{ step.task }}</td>
                            <td class="cell-center">
                              <span class="status-tag" :class="getStatusClass(step.status)">
                                {{ getStepStatusLabel(step.status) }}
                              </span>
                            </td>
                            <td class="detail-result" :title="getStepResultText(shop, index)">
                              {{ getStepResultText(shop, index) }}
                            </td>
                          </tr>
                          <tr v-if="shop.steps.length === 0">
                            <td colspan="4" class="detail-empty">暂无步骤明细</td>
                          </tr>
                        </tbody>
                      </table>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>

          <p class="update-tip">最近更新：{{ formatDateTime(batchSnapshot.updated_at) }}</p>
        </template>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  color: var(--color-text);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-lg);
}

h1 {
  margin: 0;
  font-size: var(--font-size-h1);
  line-height: 1.4;
}

.panel {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: var(--spacing-lg);
}

.panel-header {
  margin-bottom: var(--spacing-md);
}

.panel-header h2 {
  margin: 0;
  font-size: var(--font-size-h2);
}

.panel-header p {
  margin-top: 8px;
  color: #64748b;
  line-height: 1.5;
}

.layout-grid {
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  gap: var(--spacing-md);
}

.inline-stats {
  margin: 0 0 12px;
  color: #64748b;
  font-size: 14px;
}

.table-shell {
  overflow-x: auto;
}

.status-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 14px;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 14px;
}

.status-table th {
  padding: 10px 12px;
  border-bottom: 2px solid #e2e8f0;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-align: left;
  text-transform: uppercase;
  white-space: nowrap;
}

.detail-table th {
  padding: 10px 12px;
  border-bottom: 2px solid #e2e8f0;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-align: left;
  text-transform: uppercase;
  white-space: nowrap;
}

.status-table td {
  height: 44px;
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  line-height: 1.4;
  vertical-align: middle;
}

.detail-table td {
  height: 44px;
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  line-height: 1.4;
  vertical-align: middle;
}

.status-table tbody tr:hover {
  background: #f8fafc;
}

.cell-center {
  text-align: center;
}

.cell-shop,
.cell-step,
.detail-result {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-step,
.detail-result,
.update-tip {
  color: #64748b;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-bar {
  height: 10px;
  flex: 1;
  min-width: 120px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
  transition: width 0.3s ease;
}

.progress-text {
  min-width: 38px;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
  text-align: right;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.status-tag.is-waiting {
  color: #475569;
  background: rgba(148, 163, 184, 0.2);
}

.status-tag.is-running {
  color: #1d4ed8;
  background: rgba(59, 130, 246, 0.16);
}

.status-tag.is-completed {
  color: #047857;
  background: rgba(16, 185, 129, 0.16);
}

.status-tag.is-failed {
  color: #b91c1c;
  background: rgba(248, 113, 113, 0.16);
}

.status-tag.is-stopped {
  color: #b45309;
  background: rgba(245, 158, 11, 0.18);
}

.ghost-button {
  border: none;
  border-radius: var(--radius-md);
  background: #eff6ff;
  color: #1d4ed8;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}

.ghost-button:hover {
  transform: translateY(-1px);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.detail-row:hover {
  background: transparent;
}

.detail-cell {
  padding: 0;
  background: #f8fafc;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #e2e8f0;
  color: #64748b;
  font-size: 13px;
}

.detail-header strong {
  color: #1e293b;
}

.detail-table th,
.detail-table td {
  background: transparent;
}

.detail-empty {
  color: #94a3b8;
  text-align: center;
}

.update-tip {
  margin: 12px 0 0;
  font-size: 13px;
}

.empty-state {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
  text-align: center;
}

@media (max-width: 1180px) {
  .layout-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .detail-header {
    flex-direction: column;
  }
}
</style>
