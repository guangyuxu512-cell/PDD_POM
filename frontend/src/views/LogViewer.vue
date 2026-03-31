<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { del, get } from '../api'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import LogTable from '../components/LogTable.vue'
import { toast } from '../utils/toast'

interface Log {
  id: string
  timestamp: string
  level: string
  source: string
  message: string
  shop_id?: string
  shop_name?: string
}

const props = withDefaults(defineProps<{ showTitle?: boolean }>(), {
  showTitle: true,
})

const allLogs = ref<Log[]>([])
const filters = ref({
  shop: '',
  level: '',
  source: '',
  keyword: '',
})
const currentPage = ref(1)
const pageSize = ref(20)
const realtimeMode = ref(false)
const loading = ref(false)
const showClearConfirm = ref(false)
const inputClass =
  'rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'
const secondaryButtonClass =
  'rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 transition hover:bg-gray-50'
const dangerButtonClass =
  'rounded-md bg-rose-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-rose-700'

let realtimeInterval: number | null = null

const shopList = computed(() => {
  const shops = new Set<string>()
  allLogs.value.forEach((log) => {
    if (log.shop_name) {
      shops.add(log.shop_name)
    }
  })
  return Array.from(shops).sort()
})

const filteredLogs = computed(() => {
  let result = allLogs.value

  if (filters.value.shop) {
    result = result.filter((log) => log.shop_name === filters.value.shop)
  }
  if (filters.value.level) {
    result = result.filter((log) => log.level === filters.value.level)
  }
  if (filters.value.source) {
    result = result.filter((log) => log.source === filters.value.source)
  }
  if (filters.value.keyword) {
    result = result.filter((log) => log.message.toLowerCase().includes(filters.value.keyword.toLowerCase()))
  }

  return result
})

const paginatedLogs = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredLogs.value.slice(start, end)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredLogs.value.length / pageSize.value)))

const loadLogs = async () => {
  loading.value = true
  try {
    const result = await get<{ list: Log[]; total: number }>('/api/logs/')
    allLogs.value = result.list
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleClearLogs = async () => {
  try {
    await del('/api/logs/')
    showClearConfirm.value = false
    toast.success('日志已清空')
    await loadLogs()
  } catch (error: any) {
    toast.error('清空失败: ' + (error.message || error))
  }
}

const handleExport = () => {
  const csv = [
    ['时间', '店铺', '级别', '来源', '内容'].join(','),
    ...filteredLogs.value.map((log) => [log.timestamp, log.shop_name || '', log.level, log.source, log.message].join(',')),
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `logs_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
}

const toggleRealtimeMode = () => {
  realtimeMode.value = !realtimeMode.value

  if (realtimeMode.value) {
    realtimeInterval = window.setInterval(() => {
      loadLogs()
    }, 3000)
  } else if (realtimeInterval) {
    clearInterval(realtimeInterval)
    realtimeInterval = null
  }
}

onMounted(loadLogs)

onUnmounted(() => {
  if (realtimeInterval) {
    clearInterval(realtimeInterval)
  }
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
      <div v-if="props.showTitle" class="space-y-1">
        <h1 class="text-lg font-semibold text-gray-900">日志查看</h1>
        <p class="text-xs text-gray-500">支持按店铺、级别、来源和关键词筛选，并可切换实时刷新。</p>
      </div>

      <div class="flex flex-wrap gap-2">
        <button type="button" :class="secondaryButtonClass" @click="handleExport">导出 CSV</button>
        <button type="button" :class="dangerButtonClass" @click="showClearConfirm = true">清空日志</button>
        <button
          type="button"
          :class="realtimeMode ? dangerButtonClass : secondaryButtonClass"
          @click="toggleRealtimeMode"
        >
          实时模式 {{ realtimeMode ? 'ON' : 'OFF' }}
        </button>
      </div>
    </div>

    <div class="grid gap-3 rounded-md border border-brand-200/50 bg-white p-4 shadow-sm lg:grid-cols-[repeat(3,minmax(0,1fr))_minmax(0,1.4fr)_auto]">
      <select v-model="filters.shop" :class="inputClass">
        <option value="">全部店铺</option>
        <option v-for="shop in shopList" :key="shop" :value="shop">{{ shop }}</option>
      </select>
      <select v-model="filters.level" :class="inputClass">
        <option value="">全部级别</option>
        <option value="INFO">INFO</option>
        <option value="WARN">WARN</option>
        <option value="ERROR">ERROR</option>
      </select>
      <select v-model="filters.source" :class="inputClass">
        <option value="">全部来源</option>
        <option value="task">任务</option>
        <option value="browser">浏览器</option>
        <option value="captcha">验证码</option>
        <option value="system">系统</option>
      </select>
      <input
        v-model="filters.keyword"
        :class="inputClass"
        type="text"
        placeholder="关键词搜索..."
        @keyup.enter="handleSearch"
      />
      <button type="button" class="rounded-md bg-brand-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-brand-700" @click="handleSearch">
        搜索
      </button>
    </div>

    <LogTable :logs="paginatedLogs" :loading="loading" show-shop />

    <div class="flex flex-col gap-3 rounded-md border border-brand-200/50 bg-white px-4 py-3 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <span class="text-xs text-gray-500">第 {{ currentPage }} / {{ totalPages }} 页，共 {{ filteredLogs.length }} 条</span>
      <div class="flex gap-2">
        <button type="button" :class="secondaryButtonClass" :disabled="currentPage === 1" @click="currentPage--">上一页</button>
        <button type="button" :class="secondaryButtonClass" :disabled="currentPage >= totalPages" @click="currentPage++">下一页</button>
      </div>
    </div>

    <ConfirmDialog
      :show="showClearConfirm"
      title="清空日志"
      message="确定要清空所有日志吗？此操作不可恢复。"
      type="danger"
      @confirm="handleClearLogs"
      @cancel="showClearConfirm = false"
    />
  </div>
</template>
