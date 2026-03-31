<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

import { get, post } from '../api'
import BrowserStatus from '../components/BrowserStatus.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { toast } from '../utils/toast'

interface BrowserInstance {
  id: string
  shop_id: string
  shop_name: string
  status: string
  created_at: string
  memory_usage: string
  cpu_usage: string
}

interface SystemConfig {
  max_browser_instances: number
  chrome_path?: string
  default_proxy?: string
}

const instances = ref<BrowserInstance[]>([])
const config = ref<SystemConfig>({
  max_browser_instances: 5,
  chrome_path: '',
  default_proxy: '',
})
const showCloseAllConfirm = ref(false)
const inputClass =
  'w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400'
const primaryButtonClass =
  'rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-gray-800'
const dangerButtonClass =
  'rounded-md bg-rose-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-rose-700'

let pollTimer: number | null = null

const loadInstances = async () => {
  try {
    instances.value = await get<BrowserInstance[]>('/api/browser/instances')
  } catch (error) {
    console.error('加载实例列表失败:', error)
  }
}

const loadConfig = async () => {
  try {
    const data = await get<any>('/api/system/config')
    config.value = {
      max_browser_instances: data.max_browser_instances || 5,
      chrome_path: data.chrome_path || '',
      default_proxy: data.default_proxy || '',
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

const handleInit = async () => {
  try {
    await post('/api/browser/init', config.value)
    toast.success('浏览器初始化成功')
    await loadInstances()
  } catch (error: any) {
    toast.error('初始化失败: ' + (error.message || error))
  }
}

const handleCloseInstance = async (shopId: string) => {
  try {
    await post(`/api/browser/${shopId}/close`)
    toast.success('浏览器已关闭')
    await loadInstances()
  } catch (error: any) {
    toast.error('关闭失败: ' + (error.message || error))
  }
}

const handleCloseAll = async () => {
  try {
    await post('/api/browser/close-all')
    showCloseAllConfirm.value = false
    toast.success('已关闭所有浏览器')
    await loadInstances()
  } catch (error: any) {
    toast.error('关闭失败: ' + (error.message || error))
  }
}

const startPolling = () => {
  pollTimer = window.setInterval(loadInstances, 5000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(() => {
  loadInstances()
  loadConfig()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="space-y-6">
    <div class="space-y-1">
      <h1 class="text-lg font-semibold text-gray-900">浏览器管理</h1>
      <p class="text-xs text-gray-500">统一查看运行中的浏览器实例，支持重新初始化与批量关闭。</p>
    </div>

    <section class="rounded-md border border-gray-200 bg-white p-5 shadow-sm">
      <div class="space-y-1">
        <h2 class="text-lg font-semibold text-gray-900">初始化配置</h2>
        <p class="text-xs text-gray-500">用于控制浏览器初始化时的实例上限、Chrome 路径和默认代理。</p>
      </div>

      <div class="mt-5 grid gap-4 md:grid-cols-3">
        <div class="space-y-2">
          <label class="text-xs font-medium text-gray-600">最大实例数</label>
          <input v-model.number="config.max_browser_instances" :class="inputClass" type="number" min="1" max="10" />
        </div>

        <div class="space-y-2">
          <label class="text-xs font-medium text-gray-600">Chrome 路径</label>
          <input v-model="config.chrome_path" :class="inputClass" type="text" placeholder="留空使用系统默认" />
        </div>

        <div class="space-y-2">
          <label class="text-xs font-medium text-gray-600">默认代理</label>
          <input v-model="config.default_proxy" :class="inputClass" type="text" placeholder="127.0.0.1:7890" />
        </div>
      </div>

      <div class="mt-4">
        <button type="button" :class="primaryButtonClass" @click="handleInit">初始化</button>
      </div>
    </section>

    <section class="rounded-md border border-gray-200 bg-white p-5 shadow-sm">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div class="space-y-1">
          <h2 class="text-lg font-semibold text-gray-900">运行中实例</h2>
          <p class="text-xs text-gray-500">当前共 {{ instances.length }} 个实例，列表会自动轮询刷新。</p>
        </div>

        <button v-if="instances.length > 0" type="button" :class="dangerButtonClass" @click="showCloseAllConfirm = true">
          关闭全部
        </button>
      </div>

      <div v-if="instances.length === 0" class="mt-5 rounded-md border border-dashed border-gray-200 bg-gray-50 px-6 py-12 text-center text-sm text-gray-500">
        暂无数据
      </div>
      <div v-else class="mt-5 grid gap-4 lg:grid-cols-2">
        <BrowserStatus
          v-for="instance in instances"
          :key="instance.id"
          :instance="instance"
          @close="handleCloseInstance"
        />
      </div>
    </section>

    <ConfirmDialog
      :show="showCloseAllConfirm"
      title="关闭全部浏览器"
      message="确定要关闭所有浏览器实例吗？"
      type="danger"
      @confirm="handleCloseAll"
      @cancel="showCloseAllConfirm = false"
    />
  </div>
</template>
