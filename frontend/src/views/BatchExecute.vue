<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { createBatch, createBatchStatusEventSource, stopBatch } from '../api/execute'
import { listFlows } from '../api/flows'
import { listShops } from '../api/shops'
import { listAvailableTasks } from '../api/tasks'
import type { AvailableTask, BatchSnapshot, Flow, Shop } from '../api/types'
import { toast } from '../utils/toast'
import BatchStatusPanel from './batch-execute/BatchStatusPanel.vue'
import ExecuteConfigPanel from './batch-execute/ExecuteConfigPanel.vue'

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

let statusSource: EventSource | null = null

const hasActiveBatch = computed(() => batchSnapshot.value?.status === 'running')

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
      <BatchStatusPanel :batch-snapshot="batchSnapshot" :shops="shops" :flows="flows" />
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

.layout-grid {
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  gap: var(--spacing-md);
}

@media (max-width: 1180px) {
  .layout-grid {
    grid-template-columns: 1fr;
  }
}
</style>
