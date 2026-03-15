<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { createBatch, createBatchStatusEventSource, stopBatch } from '../api/execute'
import { listFlows } from '../api/flows'
import { listShops } from '../api/shops'
import { listAvailableTasks } from '../api/tasks'
import type {
  AvailableTask,
  BatchShopState,
  BatchSnapshot,
  Flow,
  Shop,
} from '../api/types'
import { toast } from '../utils/toast'

type ExecuteMode = 'flow' | 'task'

interface ShopTimeline {
  startedAt?: number
  finishedAt?: number
}

const flows = ref<Flow[]>([])
const tasks = ref<AvailableTask[]>([])
const shops = ref<Shop[]>([])

const mode = ref<ExecuteMode>('flow')
const selectedFlowId = ref('')
const selectedTaskName = ref('')
const selectedShopIds = ref<string[]>([])
const concurrency = ref(1)

const isLoading = ref(false)
const isStarting = ref(false)
const isStopping = ref(false)
const batchSnapshot = ref<BatchSnapshot | null>(null)
const currentBatchId = ref('')
const shopTimeline = ref<Record<string, ShopTimeline>>({})

const props = withDefaults(defineProps<{ showTitle?: boolean }>(), {
  showTitle: true,
})

let statusSource: EventSource | null = null

const totalShops = computed(() => shops.value.length)
const isAllSelected = computed(
  () => totalShops.value > 0 && selectedShopIds.value.length === totalShops.value
)

const batchShops = computed(() => Object.values(batchSnapshot.value?.shops ?? {}))
const waitingShops = computed(() =>
  batchShops.value.filter((shop) => shop.status === 'waiting')
)
const runningShops = computed(() =>
  batchShops.value.filter((shop) => shop.status === 'running')
)
const completedShops = computed(() =>
  batchShops.value.filter((shop) =>
    ['completed', 'failed', 'stopped'].includes(shop.status)
  )
)

const progressPercent = computed(() => {
  if (!batchSnapshot.value || batchSnapshot.value.total === 0) {
    return 0
  }

  const finished = batchSnapshot.value.completed + batchSnapshot.value.failed
  return Math.min(100, Math.round((finished / batchSnapshot.value.total) * 100))
})

const hasActiveBatch = computed(() => batchSnapshot.value?.status === 'running')

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

function formatSeconds(value: number) {
  if (value < 60) {
    return `${value}s`
  }

  const minutes = Math.floor(value / 60)
  const seconds = value % 60
  return `${minutes}m ${seconds}s`
}

function formatDuration(shopId: string) {
  const timeline = shopTimeline.value[shopId]
  if (!timeline?.startedAt) {
    return '--'
  }

  const finishedAt = timeline.finishedAt ?? Date.now()
  const durationMs = Math.max(0, finishedAt - timeline.startedAt)
  return formatSeconds(Math.round(durationMs / 1000))
}

function getShopName(shopId: string) {
  return shops.value.find((shop) => shop.id === shopId)?.name ?? shopId
}

function getBatchShopName(shop: BatchShopState) {
  return shop.shop_name || getShopName(shop.shop_id)
}

function getFlowName(flowId?: string | null) {
  if (!flowId) {
    return '--'
  }

  return flows.value.find((flow) => flow.id === flowId)?.name ?? flowId
}

function getTerminalStatusLabel(status: string) {
  if (status === 'completed') {
    return '成功'
  }

  if (status === 'failed') {
    return '失败'
  }

  if (status === 'stopped') {
    return '已停止'
  }

  return status
}

function getTerminalStatusClass(status: string) {
  if (status === 'completed') {
    return 'success-pill'
  }

  if (status === 'failed') {
    return 'danger-pill'
  }

  return 'neutral-pill'
}

function resetTimeline() {
  shopTimeline.value = {}
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
    syncTimeline(snapshot)

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

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedShopIds.value = []
    return
  }

  selectedShopIds.value = shops.value.map((shop) => shop.id)
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

    const firstFlow = flows.value[0]
    if (!selectedFlowId.value && firstFlow) {
      selectedFlowId.value = firstFlow.id
    }

    const firstTask = tasks.value[0]
    if (!selectedTaskName.value && firstTask) {
      selectedTaskName.value = firstTask.name
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载执行配置失败'
    toast.error(message)
  } finally {
    isLoading.value = false
  }
}

async function startExecution() {
  if (selectedShopIds.value.length === 0) {
    toast.warning('请至少选择一个店铺')
    return
  }

  if (mode.value === 'flow' && !selectedFlowId.value) {
    toast.warning('请选择流程模板')
    return
  }

  if (mode.value === 'task' && !selectedTaskName.value) {
    toast.warning('请选择单个任务')
    return
  }

  isStarting.value = true

  try {
    resetTimeline()
    batchSnapshot.value = null

    const result = await createBatch({
      flow_id: mode.value === 'flow' ? selectedFlowId.value : undefined,
      task_name: mode.value === 'task' ? selectedTaskName.value : undefined,
      shop_ids: selectedShopIds.value,
      concurrency: concurrency.value,
    })

    currentBatchId.value = result.batch_id
    openStatusStream(result.batch_id)
    toast.success('批量执行已启动')
  } catch (error) {
    const message = error instanceof Error ? error.message : '启动批量执行失败'
    toast.error(message)
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
    const message = error instanceof Error ? error.message : '停止执行失败'
    toast.error(message)
  } finally {
    isStopping.value = false
  }
}

function getRunningDescription(shop: BatchShopState) {
  if (!shop.current_task) {
    return '等待任务进入执行'
  }

  return `当前步骤：${shop.current_task}（${shop.current_step}/${shop.total_steps}）`
}

function getCompletedDescription(shop: BatchShopState) {
  if (shop.status === 'failed') {
    return shop.last_error || '执行失败'
  }

  if (shop.status === 'stopped') {
    return '人工停止'
  }

  return shop.last_result || '执行完成'
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
    <header class="page-header">
      <div v-if="props.showTitle">
        <p class="eyebrow">Execution Console</p>
        <h1>批量执行</h1>
        <p class="page-description">在流程模板和单任务模式之间切换，并通过 SSE 实时查看批次进度。</p>
      </div>
    </header>

    <div class="layout-grid">
      <section class="panel setup-panel">
        <div class="panel-header">
          <div>
            <h2>执行配置</h2>
            <p>流程和任务选项都会自动读取后端当前可用的数据。</p>
          </div>
        </div>

        <div v-if="isLoading" class="empty-state">正在加载执行配置...</div>
        <div v-else class="setup-form">
          <div class="mode-switch">
            <button
              class="mode-button"
              :class="{ active: mode === 'flow' }"
              @click="mode = 'flow'"
            >
              流程模式
            </button>
            <button
              class="mode-button"
              :class="{ active: mode === 'task' }"
              @click="mode = 'task'"
            >
              单任务模式
            </button>
          </div>

          <label v-if="mode === 'flow'" class="field">
            <span>流程模板</span>
            <select v-model="selectedFlowId">
              <option disabled value="">请选择流程模板</option>
              <option v-for="flow in flows" :key="flow.id" :value="flow.id">
                {{ flow.name }} · {{ flow.steps.length }} 步
              </option>
            </select>
          </label>

          <label v-else class="field">
            <span>单个任务</span>
            <select v-model="selectedTaskName">
              <option disabled value="">请选择任务</option>
              <option v-for="task in tasks" :key="task.name" :value="task.name">
                {{ task.name }} · {{ task.description }}
              </option>
            </select>
          </label>

          <label class="field">
            <span>并发数量</span>
            <select v-model.number="concurrency">
              <option :value="1">1</option>
              <option :value="2">2</option>
              <option :value="3">3</option>
              <option :value="5">5</option>
              <option :value="10">10</option>
            </select>
          </label>

          <section class="shop-selector">
            <div class="shop-selector-header">
              <div>
                <h3>目标店铺</h3>
                <p>已选择 {{ selectedShopIds.length }} / {{ totalShops }}</p>
              </div>
              <button class="secondary-button" @click="toggleSelectAll">
                {{ isAllSelected ? '取消全选' : '全选' }}
              </button>
            </div>

            <div v-if="shops.length === 0" class="shop-empty">暂无可执行店铺</div>
            <div v-else class="shop-option-grid">
              <label v-for="shop in shops" :key="shop.id" class="shop-option">
                <input v-model="selectedShopIds" type="checkbox" :value="shop.id" />
                <div>
                  <strong>{{ shop.name }}</strong>
                  <span>{{ shop.username || shop.id }}</span>
                </div>
              </label>
            </div>
          </section>

          <div class="action-row">
            <button class="primary-button" :disabled="isStarting" @click="startExecution">
              {{ isStarting ? '启动中...' : '开始执行' }}
            </button>
            <button class="danger-button" :disabled="!hasActiveBatch || isStopping" @click="stopExecution">
              {{ isStopping ? '停止中...' : '全部停止' }}
            </button>
          </div>
        </div>
      </section>

      <section class="panel status-panel">
        <div class="panel-header">
          <div>
            <h2>实时进度</h2>
            <p>基于 `/api/execute/status` 的 SSE 推送。</p>
          </div>
        </div>

        <div v-if="!batchSnapshot" class="empty-state">
          <p>尚未收到批次状态。</p>
          <span>启动批量执行后，这里会实时显示进度和店铺执行情况。</span>
        </div>
        <template v-else>
          <div class="status-summary">
            <article class="summary-card">
              <span class="summary-label">批次 ID</span>
              <strong>{{ batchSnapshot.batch_id }}</strong>
              <span class="summary-note">{{ batchSnapshot.status }}</span>
            </article>
            <article class="summary-card">
              <span class="summary-label">执行模式</span>
              <strong>{{ batchSnapshot.mode === 'flow' ? '流程' : '单任务' }}</strong>
              <span class="summary-note">
                {{
                  batchSnapshot.mode === 'flow'
                    ? getFlowName(batchSnapshot.flow_id)
                    : batchSnapshot.task_name || '--'
                }}
              </span>
            </article>
            <article class="summary-card">
              <span class="summary-label">总进度</span>
              <strong>{{ progressPercent }}%</strong>
              <span class="summary-note">
                {{ batchSnapshot.completed + batchSnapshot.failed }} / {{ batchSnapshot.total }}
              </span>
            </article>
          </div>

          <div class="progress-block">
            <div class="progress-meta">
              <span>等待 {{ batchSnapshot.waiting }}</span>
              <span>运行 {{ batchSnapshot.running }}</span>
              <span>完成 {{ batchSnapshot.completed }}</span>
              <span>失败 {{ batchSnapshot.failed }}</span>
            </div>
            <div class="progress-track">
              <div class="progress-bar" :style="{ width: `${progressPercent}%` }" />
            </div>
            <p class="progress-time">最近更新：{{ formatDateTime(batchSnapshot.updated_at) }}</p>
          </div>

          <div class="status-columns">
            <section class="status-column">
              <div class="status-column-header">
                <h3>等待中</h3>
                <span>{{ waitingShops.length }}</span>
              </div>
              <div v-if="waitingShops.length === 0" class="column-empty">没有等待中的店铺</div>
              <ul v-else class="status-list">
                <li v-for="shop in waitingShops" :key="shop.shop_id" class="status-item">
                  <strong>{{ getBatchShopName(shop) }}</strong>
                  <span>等待进入队列</span>
                </li>
              </ul>
            </section>

            <section class="status-column">
              <div class="status-column-header">
                <h3>正在执行</h3>
                <span>{{ runningShops.length }}</span>
              </div>
              <div v-if="runningShops.length === 0" class="column-empty">当前没有执行中的店铺</div>
              <ul v-else class="status-list">
                <li v-for="shop in runningShops" :key="shop.shop_id" class="status-item active-item">
                  <strong>{{ getBatchShopName(shop) }}</strong>
                  <span>{{ getRunningDescription(shop) }}</span>
                  <small>已运行 {{ formatDuration(shop.shop_id) }}</small>
                </li>
              </ul>
            </section>

            <section class="status-column">
              <div class="status-column-header">
                <h3>已完成</h3>
                <span>{{ completedShops.length }}</span>
              </div>
              <div v-if="completedShops.length === 0" class="column-empty">尚无完成记录</div>
              <ul v-else class="status-list">
                <li v-for="shop in completedShops" :key="shop.shop_id" class="status-item">
                  <div class="status-line">
                    <strong>{{ getBatchShopName(shop) }}</strong>
                    <span class="status-pill" :class="getTerminalStatusClass(shop.status)">
                      {{ getTerminalStatusLabel(shop.status) }}
                    </span>
                  </div>
                  <span>{{ getCompletedDescription(shop) }}</span>
                  <small>耗时 {{ formatDuration(shop.shop_id) }}</small>
                </li>
              </ul>
            </section>
          </div>
        </template>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  color: #1a1a2e;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
}

.eyebrow {
  margin-bottom: 10px;
  color: #7c3aed;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 700;
}

h1 {
  margin: 0;
  font-size: 32px;
  line-height: 1.1;
}

.page-description {
  margin-top: 10px;
  color: #64748b;
  max-width: 760px;
  line-height: 1.6;
}

.layout-grid {
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  gap: 20px;
}

.panel,
.summary-card,
.status-column {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
}

.panel {
  padding: 24px;
}

.panel-header {
  margin-bottom: 18px;
}

.panel-header h2,
.status-column-header h3 {
  margin: 0;
  font-size: 22px;
}

.panel-header p {
  margin-top: 8px;
  color: #64748b;
  line-height: 1.5;
}

.setup-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.mode-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.mode-button {
  border: 1px solid #cbd5e1;
  border-radius: 14px;
  padding: 12px 14px;
  background: #f8fafc;
  color: #334155;
  font-weight: 700;
  cursor: pointer;
}

.mode-button.active {
  border-color: transparent;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(168, 85, 247, 0.25);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field span {
  color: #475569;
  font-size: 14px;
  font-weight: 600;
}

.field select {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: #ffffff;
  color: #0f172a;
  font-size: 14px;
}

.field select:focus {
  outline: none;
  border-color: #7c3aed;
  box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.12);
}

.shop-selector {
  padding: 18px;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.shop-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 14px;
}

.shop-selector-header h3 {
  margin: 0;
  font-size: 18px;
}

.shop-selector-header p {
  margin-top: 6px;
  color: #64748b;
}

.shop-option-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  max-height: 280px;
  overflow: auto;
}

.shop-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
}

.shop-option input {
  margin-top: 2px;
}

.shop-option strong {
  display: block;
}

.shop-option span {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.shop-empty {
  color: #64748b;
  text-align: center;
  padding: 18px 0 6px;
}

.action-row {
  display: flex;
  gap: 12px;
}

.status-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.summary-card {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-label {
  color: #64748b;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary-card strong {
  font-size: 22px;
  word-break: break-all;
}

.summary-note {
  color: #94a3b8;
  font-size: 13px;
}

.progress-block {
  margin-top: 18px;
  padding: 18px;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.progress-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #475569;
  font-size: 13px;
  font-weight: 600;
}

.progress-track {
  margin-top: 12px;
  height: 12px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  transition: width 0.3s ease;
}

.progress-time {
  margin-top: 10px;
  color: #64748b;
  font-size: 13px;
}

.status-columns {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.status-column {
  padding: 18px;
}

.status-column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.status-column-header span {
  min-width: 28px;
  height: 28px;
  border-radius: 999px;
  background: #ede9fe;
  color: #7c3aed;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.status-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  padding: 14px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-item strong {
  color: #0f172a;
}

.status-item span,
.status-item small {
  color: #64748b;
  line-height: 1.5;
}

.active-item {
  background: rgba(168, 85, 247, 0.08);
  border-color: rgba(168, 85, 247, 0.18);
}

.status-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.status-pill {
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.success-pill {
  color: #047857;
  background: rgba(16, 185, 129, 0.15);
}

.danger-pill {
  color: #b91c1c;
  background: rgba(248, 113, 113, 0.15);
}

.neutral-pill {
  color: #475569;
  background: rgba(148, 163, 184, 0.2);
}

.column-empty,
.empty-state {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #64748b;
  text-align: center;
}

.primary-button,
.secondary-button,
.danger-button {
  border: none;
  border-radius: 12px;
  padding: 11px 16px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.primary-button {
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(168, 85, 247, 0.2);
}

.secondary-button {
  background: #e2e8f0;
  color: #0f172a;
}

.danger-button {
  background: #fee2e2;
  color: #b91c1c;
}

.primary-button:hover,
.secondary-button:hover,
.danger-button:hover {
  transform: translateY(-1px);
}

.primary-button:disabled,
.danger-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
  transform: none;
}

@media (max-width: 1180px) {
  .layout-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .status-summary,
  .status-columns {
    grid-template-columns: 1fr;
  }

  .page-header,
  .shop-selector-header {
    flex-direction: column;
  }

  .action-row {
    flex-direction: column;
  }
}
</style>
