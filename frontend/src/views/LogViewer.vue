<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { get, del } from '../api'
import { toast } from '../utils/toast'
import LogTable from '../components/LogTable.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

interface Log {
  id: string
  timestamp: string
  level: string
  source: string
  message: string
  shop_id?: string
  shop_name?: string
}

const allLogs = ref<Log[]>([])
const filters = ref({
  shop: '',
  level: '',
  source: '',
  keyword: ''
})
const currentPage = ref(1)
const pageSize = ref(20)
const realtimeMode = ref(false)
const loading = ref(false)
const showClearConfirm = ref(false)
let realtimeInterval: number | null = null

const props = withDefaults(defineProps<{ showTitle?: boolean }>(), {
  showTitle: true,
})

// 获取所有店铺列表（用于筛选）
const shopList = computed(() => {
  const shops = new Set<string>()
  allLogs.value.forEach(log => {
    if (log.shop_name) {
      shops.add(log.shop_name)
    }
  })
  return Array.from(shops).sort()
})

const filteredLogs = computed(() => {
  let result = allLogs.value

  if (filters.value.shop) {
    result = result.filter(log => log.shop_name === filters.value.shop)
  }
  if (filters.value.level) {
    result = result.filter(log => log.level === filters.value.level)
  }
  if (filters.value.source) {
    result = result.filter(log => log.source === filters.value.source)
  }
  if (filters.value.keyword) {
    result = result.filter(log =>
      log.message.toLowerCase().includes(filters.value.keyword.toLowerCase())
    )
  }

  return result
})

const paginatedLogs = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredLogs.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredLogs.value.length / pageSize.value)
})

const loadLogs = async () => {
  loading.value = true
  try {
    const result = await get<{list: Log[], total: number}>('/api/logs/')
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
  } catch (e: any) {
    toast.error('清空失败: ' + (e.message || e))
  }
}

const handleExport = () => {
  const csv = [
    ['时间', '店铺', '级别', '来源', '内容'].join(','),
    ...filteredLogs.value.map(log =>
      [log.timestamp, log.shop_name || '', log.level, log.source, log.message].join(',')
    )
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
  } else {
    if (realtimeInterval) {
      clearInterval(realtimeInterval)
      realtimeInterval = null
    }
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
  <div class="log-viewer">
    <div class="header">
      <h1 v-if="props.showTitle">日志查看</h1>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="handleExport">📥 导出CSV</button>
        <button class="btn btn-danger" @click="showClearConfirm = true">🗑️ 清空日志</button>
        <button
          class="btn"
          :class="realtimeMode ? 'btn-danger' : 'btn-secondary'"
          @click="toggleRealtimeMode"
        >
          🔴 实时模式 {{ realtimeMode ? 'ON' : 'OFF' }}
        </button>
      </div>
    </div>

    <div class="filters">
      <select v-model="filters.shop" class="filter-select">
        <option value="">全部店铺</option>
        <option v-for="shop in shopList" :key="shop" :value="shop">{{ shop }}</option>
      </select>
      <select v-model="filters.level" class="filter-select">
        <option value="">全部级别</option>
        <option value="INFO">INFO</option>
        <option value="WARN">WARN</option>
        <option value="ERROR">ERROR</option>
      </select>
      <select v-model="filters.source" class="filter-select">
        <option value="">全部来源</option>
        <option value="task">任务</option>
        <option value="browser">浏览器</option>
        <option value="captcha">验证码</option>
        <option value="system">系统</option>
      </select>
      <input
        v-model="filters.keyword"
        type="text"
        placeholder="关键词搜索..."
        class="filter-input"
        @keyup.enter="handleSearch"
      />
      <button class="btn btn-primary" @click="handleSearch">搜索</button>
    </div>

    <LogTable :logs="paginatedLogs" :loading="loading" show-shop />

    <div class="pagination">
      <button
        class="btn-page"
        :disabled="currentPage === 1"
        @click="currentPage--"
      >
        上一页
      </button>
      <span class="page-info">
        第 {{ currentPage }} / {{ totalPages }} 页，共 {{ filteredLogs.length }} 条
      </span>
      <button
        class="btn-page"
        :disabled="currentPage === totalPages"
        @click="currentPage++"
      >
        下一页
      </button>
    </div>

    <ConfirmDialog
      :show="showClearConfirm"
      title="确认清空"
      message="确定要清空所有日志吗？此操作不可恢复。"
      type="danger"
      @confirm="handleClearLogs"
      @cancel="showClearConfirm = false"
    />
  </div>
</template>

<style scoped>
.log-viewer {
  color: #1a1a2e;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

h1 {
  font-size: 28px;
  margin: 0;
  color: #1a1a2e;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #f3f4f6;
  color: #1a1a2e;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-select,
.filter-input {
  padding: 10px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #1a1a2e;
  font-size: 14px;
}

.filter-select {
  min-width: 150px;
}

.filter-input {
  flex: 1;
  min-width: 200px;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.btn-page {
  padding: 8px 16px;
  background: #f3f4f6;
  border: none;
  border-radius: 6px;
  color: #1a1a2e;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-page:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #6b7280;
  font-size: 14px;
}
</style>
