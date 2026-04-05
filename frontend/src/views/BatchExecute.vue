<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import { createBatch, createBatchStatusEventSource, stopBatch } from '../api/execute'
import { listFlowInputSets } from '../api/flowInputs'
import { listFlows } from '../api/flows'
import { listShops } from '../api/shops'
import { listAvailableTasks } from '../api/tasks'
import type { AvailableTask, BatchRequest, BatchShopState, BatchSnapshot, Flow, FlowInputSet, Shop } from '../api/types'
import { toast } from '../utils/toast'

interface ShopTimeline {
  startedAt?: number
  finishedAt?: number
}

type ExecuteMode = 'flow' | 'task'

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
const mode = ref<ExecuteMode>('flow')
const selectedFlowId = ref('')
const inputSets = ref<FlowInputSet[]>([])
const isLoadingInputSets = ref(false)
const selectedInputSetId = ref('')
const selectedTaskName = ref('')
const selectedShopIds = ref<string[]>([])
const concurrency = ref(1)
const inputClass =
  'w-full rounded-md border border-brand-300/50 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'
const secondaryButtonClass =
  'rounded-md border border-brand-300/50 bg-white px-3 py-1.5 text-sm text-brand-700 transition hover:bg-brand-100/50 hover:text-brand-900 disabled:cursor-not-allowed disabled:opacity-60'
const primaryButtonClass =
  'rounded-md bg-brand-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-gray-400'
const dangerButtonClass =
  'rounded-md bg-rose-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:bg-rose-300'

let statusSource: EventSource | null = null

const hasActiveBatch = computed(() => batchSnapshot.value?.status === 'running')
const totalShops = computed(() => shops.value.length)
const isAllSelected = computed(
  () => totalShops.value > 0 && selectedShopIds.value.length === totalShops.value,
)
const batchShops = computed(() => Object.values(batchSnapshot.value?.shops ?? {}))
const batchInlineStats = computed(() => {
  if (!batchSnapshot.value) return ''
  return `批次 ${batchSnapshot.value.batch_id} · 总计 ${batchSnapshot.value.total} · 完成 ${batchSnapshot.value.completed} · 运行 ${batchSnapshot.value.running} · 失败 ${batchSnapshot.value.failed}`
})

watch(
  () => flows.value,
  (items) => {
    if (!selectedFlowId.value && items[0]) {
      selectedFlowId.value = items[0].id
    }
  },
  { immediate: true },
)

watch(
  () => selectedFlowId.value,
  (flowId) => {
    void loadFlowInputSets(flowId)
  },
  { immediate: true },
)

watch(
  () => tasks.value,
  (items) => {
    if (!selectedTaskName.value && items[0]) {
      selectedTaskName.value = items[0].name
    }
  },
  { immediate: true },
)

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedShopIds.value = []
    return
  }

  selectedShopIds.value = shops.value.map((shop) => shop.id)
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
  if (!value) return null
  const date = new Date(value.replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return null
  return date
}

function formatDateTime(value?: string | null) {
  const date = parseDateTime(value)
  if (!date) return '--'
  return date.toLocaleString('zh-CN', { hour12: false })
}

function formatSeconds(value: number) {
  if (value < 60) return `${value}s`
  const minutes = Math.floor(value / 60)
  const seconds = value % 60
  return `${minutes}m ${seconds}s`
}

function syncTimeline(snapshot: BatchSnapshot) {
  const batchStartedAt = parseDateTime(snapshot.created_at)?.getTime() ?? Date.now()
  const batchUpdatedAt = parseDateTime(snapshot.updated_at)?.getTime() ?? Date.now()

  for (const shop of Object.values(snapshot.shops)) {
    const timeline = shopTimeline.value[shop.shop_id] ?? (shopTimeline.value[shop.shop_id] = {})
    if (!timeline.startedAt) timeline.startedAt = batchStartedAt
    if (['completed', 'failed', 'stopped'].includes(shop.status) && !timeline.finishedAt) {
      timeline.finishedAt = batchUpdatedAt
    }
  }
}

function formatDuration(shopId: string) {
  const timeline = shopTimeline.value[shopId]
  if (!timeline?.startedAt) return '--'
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
  if (shop.status === 'waiting') return '等待开始'
  if (shop.status === 'running') {
    if (!shop.current_task) return '等待任务进入执行'
    return `${shop.current_task}（${shop.current_step}/${shop.total_steps}）`
  }
  if (shop.status === 'completed') return '已完成'
  if (shop.status === 'failed') return '执行失败'
  if (shop.status === 'stopped') return '已停止'
  return '--'
}

function getProgressPercent(shop: BatchShopState) {
  if (shop.total_steps <= 0) return 0
  if (['completed', 'failed', 'stopped'].includes(shop.status)) return 100
  if (shop.status === 'waiting') return 0
  return Math.min(100, Math.round((shop.current_step / shop.total_steps) * 100))
}

function getProgressText(shop: BatchShopState) {
  if (shop.total_steps <= 0) return '--'
  if (['completed', 'failed', 'stopped'].includes(shop.status)) return `${shop.total_steps}/${shop.total_steps}`
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
  if (status === 'waiting' || status === 'pending') return 'bg-brand-100 text-brand-700'
  if (status === 'running') return 'bg-amber-100 text-amber-700'
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'failed') return 'bg-rose-100 text-rose-700'
  if (status === 'stopped') return 'bg-brand-300/40 text-brand-700'
  return 'bg-brand-100 text-brand-700'
}

function getProgressBarClass(status: string) {
  if (status === 'running') return 'bg-amber-500'
  if (status === 'completed') return 'bg-emerald-500'
  if (status === 'failed') return 'bg-rose-500'
  if (status === 'stopped') return 'bg-brand-300'
  return 'bg-brand-300'
}

function getDetailSummary(shop: BatchShopState) {
  if (shop.status === 'failed') return shop.last_error || '执行失败'
  if (shop.status === 'stopped') return '人工停止'
  if (shop.status === 'completed') return shop.last_result || '执行完成'
  if (shop.current_task) return `当前任务：${shop.current_task}`
  return '等待进入队列'
}

function getStepResultText(shop: BatchShopState, index: number) {
  const step = shop.steps[index]
  if (!step) return '--'
  if (step.status === 'failed') return step.error || '执行失败'
  if (step.status === 'completed') return step.result || '执行完成'
  if (step.status === 'running') return '执行中'
  if (step.status === 'stopped') return '已停止'
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

async function loadFlowInputSets(flowId: string) {
  const normalizedFlowId = flowId.trim()
  if (!normalizedFlowId) {
    isLoadingInputSets.value = false
    inputSets.value = []
    selectedInputSetId.value = ''
    return
  }

  isLoadingInputSets.value = true
  try {
    const result = await listFlowInputSets(normalizedFlowId)
    if (selectedFlowId.value !== normalizedFlowId) return

    const enabledInputSets = result.list.filter((item) => item.enabled)
    inputSets.value = enabledInputSets

    if (enabledInputSets.some((item) => item.id === selectedInputSetId.value)) {
      return
    }

    const defaultInputSet = enabledInputSets.length === 1 ? enabledInputSets[0] : null
    selectedInputSetId.value = defaultInputSet ? defaultInputSet.id : ''
  } catch (error) {
    if (selectedFlowId.value === normalizedFlowId) {
      inputSets.value = []
      selectedInputSetId.value = ''
    }
    toast.error(error instanceof Error ? error.message : '加载流程输入集失败')
  } finally {
    if (selectedFlowId.value === normalizedFlowId) {
      isLoadingInputSets.value = false
    }
  }
}

async function startExecution(payload: BatchRequest) {
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

function submitStart() {
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

  void startExecution({
    flow_id: mode.value === 'flow' ? selectedFlowId.value : undefined,
    task_name: mode.value === 'task' ? selectedTaskName.value : undefined,
    shop_ids: selectedShopIds.value,
    concurrency: concurrency.value,
    input_set_id: mode.value === 'flow' ? selectedInputSetId.value || undefined : undefined,
  })
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
  <div class="space-y-6">
    <header v-if="props.showTitle" class="space-y-1">
      <h1 class="text-lg font-semibold text-gray-900">批量执行</h1>
      <p class="text-xs text-brand-500">配置流程或任务与目标店铺，并实时查看每个店铺的执行进度。</p>
    </header>

    <div class="grid gap-6 xl:grid-cols-[minmax(320px,380px)_minmax(0,1fr)]">
      <section class="rounded-md border border-brand-300/50 bg-white p-5 shadow-sm">
        <div class="space-y-1">
          <h2 class="text-lg font-semibold text-gray-900">执行配置</h2>
          <p class="text-xs text-brand-500">流程和任务选项会自动读取后端当前可用的数据。</p>
        </div>

        <div v-if="isLoading" class="flex min-h-[220px] items-center justify-center text-sm text-brand-500">
          正在加载执行配置...
        </div>

        <div v-else class="mt-5 space-y-5">
          <div class="flex gap-1 rounded-md bg-brand-100 p-0.5">
            <button
              type="button"
              :class="['flex-1 rounded-md px-3 py-2 text-sm transition', mode === 'flow' ? 'bg-white font-medium text-brand-900 shadow-sm' : 'text-brand-500 hover:text-brand-900']"
              @click="mode = 'flow'"
            >
              流程模式
            </button>
            <button
              type="button"
              :class="['flex-1 rounded-md px-3 py-2 text-sm transition', mode === 'task' ? 'bg-white font-medium text-brand-900 shadow-sm' : 'text-brand-500 hover:text-brand-900']"
              @click="mode = 'task'"
            >
              单任务模式
            </button>
          </div>

          <div v-if="mode === 'flow'" class="space-y-2">
            <label class="text-xs font-medium text-brand-700">流程模板</label>
            <select v-model="selectedFlowId" :class="inputClass" :disabled="hasActiveBatch || isStarting">
              <option disabled value="">请选择流程模板</option>
              <option v-for="flow in flows" :key="flow.id" :value="flow.id">{{ flow.name }} · {{ flow.steps.length }} 步</option>
            </select>
          </div>

          <div v-if="mode === 'flow'" class="space-y-2">
            <div class="flex items-center justify-between gap-3">
              <label class="text-xs font-medium text-brand-700">流程输入集</label>
              <span v-if="isLoadingInputSets" class="text-xs text-brand-500">加载中...</span>
            </div>
            <select
              v-model="selectedInputSetId"
              :class="inputClass"
              :disabled="hasActiveBatch || isStarting || isLoadingInputSets"
            >
              <option value="">不使用输入集，沿用 flow_params</option>
              <option v-for="inputSet in inputSets" :key="inputSet.id" :value="inputSet.id">
                {{ inputSet.name }} · {{ inputSet.source_type }}
              </option>
            </select>
            <p class="text-xs text-brand-500">
              {{
                inputSets.length === 0
                  ? '当前流程没有可用输入集，执行时会读取已有 flow_params。'
                  : selectedInputSetId
                    ? '已选择输入集，执行时会先把输入行映射为兼容 flow_params。'
                    : '未选择输入集时，执行会继续读取已有 flow_params。'
              }}
            </p>
          </div>

          <div v-else class="space-y-2">
            <label class="text-xs font-medium text-brand-700">单个任务</label>
            <select v-model="selectedTaskName" :class="inputClass" :disabled="hasActiveBatch || isStarting">
              <option disabled value="">请选择任务</option>
              <option v-for="task in tasks" :key="task.name" :value="task.name">{{ task.name }} · {{ task.description }}</option>
            </select>
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">并发数量</label>
            <select v-model.number="concurrency" :class="inputClass" :disabled="hasActiveBatch || isStarting">
              <option :value="1">1</option>
              <option :value="2">2</option>
              <option :value="3">3</option>
              <option :value="5">5</option>
              <option :value="10">10</option>
            </select>
          </div>

          <section class="rounded-md border border-brand-300/50 bg-brand-100/70 p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div class="space-y-1">
                <h3 class="text-sm font-medium text-gray-900">目标店铺</h3>
                <p class="text-xs text-brand-500">已选择 {{ selectedShopIds.length }} / {{ totalShops }}</p>
              </div>
              <button type="button" :class="secondaryButtonClass" :disabled="shops.length === 0" @click="toggleSelectAll">
                {{ isAllSelected ? '取消全选' : '全选' }}
              </button>
            </div>

            <div v-if="shops.length === 0" class="mt-4 text-center text-sm text-brand-500">暂无可执行店铺</div>
            <div v-else class="mt-4 max-h-[320px] space-y-2 overflow-auto pr-1">
              <label
                v-for="shop in shops"
                :key="shop.id"
                class="flex items-start gap-3 rounded-md border border-brand-300/50 bg-white px-3 py-3 transition hover:bg-brand-100/50"
              >
                <input
                  v-model="selectedShopIds"
                  type="checkbox"
                  :value="shop.id"
                  :disabled="hasActiveBatch || isStarting"
                  class="mt-0.5 h-4 w-4 rounded border-brand-300/50 text-brand-500 focus:ring-brand-500"
                />
                <div class="min-w-0">
                  <p class="truncate text-sm font-medium text-gray-900">{{ shop.name }}</p>
                  <p class="truncate font-mono text-xs text-brand-500">{{ shop.username || shop.id }}</p>
                </div>
              </label>
            </div>
          </section>

          <div class="flex gap-2">
            <button type="button" :class="primaryButtonClass" :disabled="isStarting || hasActiveBatch" @click="submitStart">
              {{ isStarting ? '启动中...' : '开始执行' }}
            </button>
            <button type="button" :class="dangerButtonClass" :disabled="!hasActiveBatch || isStopping" @click="stopExecution">
              {{ isStopping ? '停止中...' : '全部停止' }}
            </button>
          </div>
        </div>
      </section>

      <section class="rounded-md border border-brand-300/50 bg-white p-5 shadow-sm">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div class="space-y-1">
            <h2 class="text-lg font-semibold text-gray-900">执行状态</h2>
            <p class="text-xs text-brand-500">基于 `/api/execute/status` 的 SSE 推送，按店铺实时更新执行进度。</p>
          </div>
          <p v-if="batchSnapshot" class="rounded-full bg-brand-100 px-3 py-1 text-xs text-brand-700">{{ batchInlineStats }}</p>
        </div>

        <div v-if="!batchSnapshot" class="flex min-h-[280px] flex-col items-center justify-center gap-3 text-center text-sm text-brand-500">
          <p>尚未收到批次状态。</p>
          <span>启动批量执行后，这里会显示表格化进度和步骤详情。</span>
        </div>

        <template v-else>
          <div class="mt-5 overflow-hidden rounded-md border border-brand-300/50">
            <div class="overflow-x-auto">
              <table class="min-w-full">
                <thead class="bg-brand-700/10 text-xs font-medium uppercase tracking-wider text-brand-700">
                  <tr>
                    <th class="px-4 py-3 text-left font-medium">店铺名称</th>
                    <th class="px-4 py-3 text-left font-medium">当前步骤</th>
                    <th class="px-4 py-3 text-left font-medium">进度</th>
                    <th class="px-4 py-3 text-center font-medium">状态</th>
                    <th class="px-4 py-3 text-center font-medium">耗时</th>
                    <th class="px-4 py-3 text-right font-medium">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="shop in batchShops" :key="shop.shop_id">
                    <tr class="border-b border-brand-300/30 hover:bg-brand-100/50">
                      <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ getBatchShopName(shop) }}</td>
                      <td class="px-4 py-3 text-sm text-gray-900">{{ getCurrentStepLabel(shop) }}</td>
                      <td class="px-4 py-3">
                        <div class="flex items-center gap-3">
                          <div class="h-2 min-w-[120px] flex-1 rounded-full bg-brand-100">
                            <div :class="['h-2 rounded-full transition-[width]', getProgressBarClass(shop.status)]" :style="{ width: `${getProgressPercent(shop)}%` }" />
                          </div>
                          <span class="min-w-[40px] text-right font-mono text-xs text-brand-500">{{ getProgressText(shop) }}</span>
                        </div>
                      </td>
                      <td class="px-4 py-3 text-center">
                        <span :class="['inline-flex rounded-full px-2.5 py-1 text-xs font-medium', getStatusClass(shop.status)]">{{ getStatusLabel(shop.status) }}</span>
                      </td>
                      <td class="px-4 py-3 text-center font-mono text-xs text-brand-500">{{ formatDuration(shop.shop_id) }}</td>
                      <td class="px-4 py-3 text-right">
                        <button type="button" :class="secondaryButtonClass" @click="toggleShopDetail(shop.shop_id)">
                          {{ isShopDetailOpen(shop.shop_id) ? '收起详情' : '查看详情' }}
                        </button>
                      </td>
                    </tr>
                    <tr v-if="isShopDetailOpen(shop.shop_id)" class="border-b border-brand-300/30 bg-brand-100">
                      <td colspan="6" class="px-4 py-4">
                        <div class="space-y-4">
                          <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                            <strong class="text-sm text-gray-900">{{ getBatchShopName(shop) }}</strong>
                            <span class="text-xs text-brand-500">{{ getDetailSummary(shop) }}</span>
                          </div>

                          <div class="overflow-hidden rounded-md border border-brand-300/50 bg-white">
                            <div class="overflow-x-auto">
                              <table class="min-w-full">
                                <thead class="bg-brand-700/10 text-xs font-medium uppercase tracking-wider text-brand-700">
                                  <tr>
                                    <th class="w-14 px-4 py-3 text-center font-medium">#</th>
                                    <th class="px-4 py-3 text-left font-medium">步骤</th>
                                    <th class="w-28 px-4 py-3 text-center font-medium">状态</th>
                                    <th class="px-4 py-3 text-left font-medium">结果</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  <tr v-for="(step, index) in shop.steps" :key="`${shop.shop_id}-${step.task}-${index}`" class="border-b border-brand-300/30 hover:bg-brand-100/50">
                                    <td class="px-4 py-3 text-center font-mono text-xs text-brand-500">{{ index + 1 }}</td>
                                    <td class="px-4 py-3 text-sm text-gray-900">{{ step.task }}</td>
                                    <td class="px-4 py-3 text-center">
                                      <span :class="['inline-flex rounded-full px-2.5 py-1 text-xs font-medium', getStatusClass(step.status)]">{{ getStepStatusLabel(step.status) }}</span>
                                    </td>
                                    <td class="px-4 py-3 text-sm text-brand-500">{{ getStepResultText(shop, index) }}</td>
                                  </tr>
                                  <tr v-if="shop.steps.length === 0">
                                    <td colspan="4" class="px-4 py-8 text-center text-sm text-brand-500">暂无步骤明细</td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>
          </div>

          <p class="mt-3 text-right font-mono text-xs text-brand-500">最近更新：{{ formatDateTime(batchSnapshot.updated_at) }}</p>
        </template>
      </section>
    </div>
  </div>
</template>
