<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

import { del, get, post } from '../api'
import Modal from '../components/Modal.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { toast } from '../utils/toast'

interface Task {
  task_id: string
  shop_id: string
  task_name: string
  status: string
  started_at: string
  finished_at: string | null
  result: string | null
  error: string | null
}

interface Shop {
  id: string
  name: string
}

const props = withDefaults(defineProps<{ showTitle?: boolean }>(), {
  showTitle: true,
})

const tasks = ref<Task[]>([])
const shops = ref<Shop[]>([])
const showTriggerModal = ref(false)
const triggerForm = ref({
  shop_id: '',
  task_name: '登录',
})
const inputClass =
  'w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'
const secondaryButtonClass =
  'rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 transition hover:bg-gray-50'
const primaryButtonClass =
  'rounded-md bg-brand-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-brand-700'

let refreshTimer: number | null = null

const loadTasks = async () => {
  try {
    const result = await get<{ list: Task[]; total: number }>('/api/tasks/')
    tasks.value = result.list
  } catch (error: any) {
    console.error('加载任务列表失败:', error)
  }
}

const loadShops = async () => {
  try {
    const result = await get<{ list: Shop[]; total: number }>('/api/shops/')
    shops.value = result.list
  } catch (error: any) {
    console.error('加载店铺列表失败:', error)
  }
}

const openTriggerModal = () => {
  triggerForm.value = {
    shop_id: shops.value[0]?.id || '',
    task_name: '登录',
  }
  showTriggerModal.value = true
}

const handleTrigger = async () => {
  try {
    await post('/api/tasks/execute', triggerForm.value)
    showTriggerModal.value = false
    toast.success('任务已触发')
    await loadTasks()
  } catch (error: any) {
    toast.error(error.message || '触发任务失败')
  }
}

const handleCancel = async (taskId: string) => {
  try {
    await post(`/api/tasks/${taskId}/cancel`)
    toast.success('任务已取消')
    await loadTasks()
  } catch (error: any) {
    toast.error(error.message || '取消任务失败')
  }
}

const handleClearHistory = async () => {
  if (!confirm('确定要清空所有已完成和已失败的任务记录吗？')) {
    return
  }

  try {
    const result = await del('/api/tasks/history/clear')
    toast.success(result.msg || '历史记录已清空')
    await loadTasks()
  } catch (error: any) {
    toast.error(error.message || '清空历史失败')
  }
}

const canCancel = (status: string) => status === 'pending' || status === 'running'

const getShopName = (shopId: string) => {
  const shop = shops.value.find((item) => item.id === shopId)
  return shop?.name || shopId
}

const getResultDisplay = (task: Task) => {
  if (task.status === 'failed' && task.error) {
    return task.error
  }
  return task.result || '-'
}

const getResultClass = (task: Task) => {
  if (task.status === 'failed') return 'text-rose-700'
  if (task.status === 'completed') return 'text-emerald-700'
  return 'text-gray-500'
}

const startAutoRefresh = () => {
  refreshTimer = window.setInterval(() => {
    loadTasks()
  }, 5000)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  loadTasks()
  loadShops()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div v-if="props.showTitle" class="space-y-1">
        <h1 class="text-lg font-semibold text-gray-900">任务监控</h1>
        <p class="text-xs text-gray-500">自动轮询任务状态，支持手动触发和取消进行中的任务。</p>
      </div>

      <div class="flex flex-wrap gap-2">
        <button type="button" :class="secondaryButtonClass" @click="handleClearHistory">清空历史</button>
        <button type="button" :class="primaryButtonClass" @click="openTriggerModal">手动触发</button>
      </div>
    </div>

    <div class="overflow-hidden rounded-md border border-brand-200/50 bg-white shadow-sm">
      <div class="overflow-x-auto">
        <table class="min-w-full">
          <thead class="bg-brand-50 text-xs font-medium uppercase tracking-wider text-gray-500">
            <tr>
              <th class="px-4 py-3 text-left font-medium">任务 ID</th>
              <th class="px-4 py-3 text-left font-medium">店铺</th>
              <th class="px-4 py-3 text-left font-medium">任务类型</th>
              <th class="px-4 py-3 text-left font-medium">状态</th>
              <th class="px-4 py-3 text-left font-medium">开始时间</th>
              <th class="px-4 py-3 text-left font-medium">结果</th>
              <th class="px-4 py-3 text-right font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="tasks.length === 0">
              <td colspan="7" class="px-4 py-12 text-center text-sm text-gray-500">暂无任务记录</td>
            </tr>
            <tr v-for="task in tasks" :key="task.task_id" class="border-b border-gray-100 hover:bg-gray-50/50">
              <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ task.task_id.substring(0, 8) }}...</td>
              <td class="px-4 py-3 text-sm text-gray-900">{{ getShopName(task.shop_id) }}</td>
              <td class="px-4 py-3 text-sm text-gray-900">{{ task.task_name }}</td>
              <td class="px-4 py-3 text-sm text-gray-900">
                <StatusBadge :status="task.status" type="task" />
              </td>
              <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ task.started_at }}</td>
              <td :class="['px-4 py-3 text-sm font-medium', getResultClass(task)]">
                {{ getResultDisplay(task) }}
              </td>
              <td class="px-4 py-3 text-right">
                <button
                  v-if="canCancel(task.status)"
                  type="button"
                  class="rounded-md bg-rose-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-rose-700"
                  @click="handleCancel(task.task_id)"
                >
                  取消
                </button>
                <span v-else class="text-xs text-gray-400">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Modal :show="showTriggerModal" title="手动触发任务" width="520px" @close="showTriggerModal = false">
      <form class="space-y-4" @submit.prevent="handleTrigger">
        <div class="space-y-2">
          <label class="text-xs font-medium text-gray-600">选择店铺</label>
          <select v-model="triggerForm.shop_id" :class="inputClass" required>
            <option v-for="shop in shops" :key="shop.id" :value="shop.id">
              {{ shop.name }}
            </option>
          </select>
        </div>

        <div class="space-y-2">
          <label class="text-xs font-medium text-gray-600">任务类型</label>
          <select v-model="triggerForm.task_name" :class="inputClass" required>
            <option value="登录">登录</option>
          </select>
        </div>
      </form>

      <template #footer>
        <button type="button" :class="secondaryButtonClass" @click="showTriggerModal = false">取消</button>
        <button type="button" :class="primaryButtonClass" @click="handleTrigger">触发</button>
      </template>
    </Modal>
  </div>
</template>
