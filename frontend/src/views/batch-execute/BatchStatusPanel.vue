<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { BatchShopState, BatchSnapshot, Flow, Shop } from '../../api/types'

interface ShopTimeline {
  startedAt?: number
  finishedAt?: number
}

const props = defineProps<{
  batchSnapshot: BatchSnapshot | null
  shops: Shop[]
  flows: Flow[]
}>()

const shopTimeline = ref<Record<string, ShopTimeline>>({})

const batchShops = computed(() => Object.values(props.batchSnapshot?.shops ?? {}))
const waitingShops = computed(() => batchShops.value.filter((shop) => shop.status === 'waiting'))
const runningShops = computed(() => batchShops.value.filter((shop) => shop.status === 'running'))
const completedShops = computed(() => batchShops.value.filter((shop) => ['completed', 'failed', 'stopped'].includes(shop.status)))

const progressPercent = computed(() => {
  if (!props.batchSnapshot || props.batchSnapshot.total === 0) {
    return 0
  }

  const finished = props.batchSnapshot.completed + props.batchSnapshot.failed
  return Math.min(100, Math.round((finished / props.batchSnapshot.total) * 100))
})

watch(
  () => props.batchSnapshot?.batch_id,
  () => {
    shopTimeline.value = {}
  },
)

watch(
  () => props.batchSnapshot,
  (snapshot) => {
    if (!snapshot) {
      shopTimeline.value = {}
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

function formatDuration(shopId: string) {
  const timeline = shopTimeline.value[shopId]
  if (!timeline?.startedAt) {
    return '--'
  }

  const finishedAt = timeline.finishedAt ?? Date.now()
  return formatSeconds(Math.round(Math.max(0, finishedAt - timeline.startedAt) / 1000))
}

function getShopName(shopId: string) {
  return props.shops.find((shop) => shop.id === shopId)?.name ?? shopId
}

function getBatchShopName(shop: BatchShopState) {
  return shop.shop_name || getShopName(shop.shop_id)
}

function getFlowName(flowId?: string | null) {
  if (!flowId) {
    return '--'
  }

  return props.flows.find((flow) => flow.id === flowId)?.name ?? flowId
}

function getTerminalStatusLabel(status: string) {
  if (status === 'completed') return '成功'
  if (status === 'failed') return '失败'
  if (status === 'stopped') return '已停止'
  return status
}

function getTerminalStatusClass(status: string) {
  if (status === 'completed') return 'success-pill'
  if (status === 'failed') return 'danger-pill'
  return 'neutral-pill'
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
</script>

<template>
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
            {{ batchSnapshot.mode === 'flow' ? getFlowName(batchSnapshot.flow_id) : batchSnapshot.task_name || '--' }}
          </span>
        </article>
        <article class="summary-card">
          <span class="summary-label">总进度</span>
          <strong>{{ progressPercent }}%</strong>
          <span class="summary-note">{{ batchSnapshot.completed + batchSnapshot.failed }} / {{ batchSnapshot.total }}</span>
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
</template>

<style scoped src="./BatchStatusPanel.css"></style>
