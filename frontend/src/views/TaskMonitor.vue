<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { get, post, del } from '../api'
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

const tasks = ref<Task[]>([])
const shops = ref<Shop[]>([])
const showTriggerModal = ref(false)
const triggerForm = ref({
  shop_id: '',
  task_name: '登录'
})

let refreshTimer: number | null = null

const loadTasks = async () => {
  try {
    const result = await get<{list: Task[], total: number}>('/api/tasks/')
    tasks.value = result.list
  } catch (error: any) {
    console.error('加载任务列表失败:', error)
  }
}

const loadShops = async () => {
  try {
    const result = await get<{list: Shop[], total: number}>('/api/shops/')
    shops.value = result.list
  } catch (error: any) {
    console.error('加载店铺列表失败:', error)
  }
}

const openTriggerModal = () => {
  triggerForm.value = {
    shop_id: shops.value[0]?.id || '',
    task_name: '登录'
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
    // 调用批量删除 API
    const result = await del('/api/tasks/history/clear')
    toast.success(result.msg || '历史记录已清空')
    await loadTasks()
  } catch (error: any) {
    toast.error(error.message || '清空历史失败')
  }
}

const canCancel = (status: string) => {
  return status === 'pending' || status === 'running'
}

const getShopName = (shopId: string) => {
  const shop = shops.value.find(s => s.id === shopId)
  return shop?.name || shopId
}

const getResultDisplay = (task: Task) => {
  if (task.status === 'failed' && task.error) {
    return task.error
  }
  return task.result || '-'
}

const getResultClass = (task: Task) => {
  if (task.status === 'failed') return 'result-error'
  if (task.status === 'completed') return 'result-success'
  return ''
}

// 启动自动刷新（每 5 秒）
const startAutoRefresh = () => {
  refreshTimer = window.setInterval(() => {
    loadTasks()
  }, 5000)
}

// 停止自动刷新
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
  <div class="task-monitor">
    <div class="header">
      <h1>任务监控</h1>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="handleClearHistory">清空历史</button>
        <button class="btn btn-primary" @click="openTriggerModal">手动触发</button>
      </div>
    </div>

    <div class="table-container">
      <table class="task-table">
        <thead>
          <tr>
            <th>任务ID</th>
            <th>店铺</th>
            <th>任务类型</th>
            <th>状态</th>
            <th>开始时间</th>
            <th>结果</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="tasks.length === 0">
            <td colspan="7" class="empty-state">暂无任务记录</td>
          </tr>
          <tr v-for="task in tasks" :key="task.task_id">
            <td class="task-id">{{ task.task_id.substring(0, 8) }}...</td>
            <td>{{ getShopName(task.shop_id) }}</td>
            <td>{{ task.task_name }}</td>
            <td>
              <StatusBadge :status="task.status" type="task" />
            </td>
            <td>{{ task.started_at }}</td>
            <td :class="getResultClass(task)">{{ getResultDisplay(task) }}</td>
            <td>
              <button
                v-if="canCancel(task.status)"
                class="btn-action"
                @click="handleCancel(task.task_id)"
              >
                取消
              </button>
              <span v-else class="disabled">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :show="showTriggerModal" title="手动触发任务" width="500px" @close="showTriggerModal = false">
      <form class="trigger-form" @submit.prevent="handleTrigger">
        <div class="form-group">
          <label>选择店铺</label>
          <select v-model="triggerForm.shop_id" required>
            <option v-for="shop in shops" :key="shop.id" :value="shop.id">
              {{ shop.name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>任务类型</label>
          <select v-model="triggerForm.task_name" required>
            <option value="登录">登录</option>
          </select>
        </div>
      </form>

      <template #footer>
        <button class="btn btn-secondary" @click="showTriggerModal = false">取消</button>
        <button class="btn btn-primary" @click="handleTrigger">触发</button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.task-monitor {
  color: #1a1a2e;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

h1 {
  font-size: 28px;
  margin: 0;
  color: #1a1a2e;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover {
  background: #4b5563;
}

.table-container {
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.task-table {
  width: 100%;
  border-collapse: collapse;
}

.task-table thead {
  background: #f3f4f6;
}

.task-table th {
  padding: 16px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  color: #374151;
}

.task-table tbody tr {
  border-bottom: 1px solid #e5e7eb;
  transition: background 0.2s;
}

.task-table tbody tr:nth-child(even) {
  background: #f9fafb;
}

.task-table tbody tr:hover {
  background: #f3f4f6;
}

.task-table td {
  padding: 16px;
  font-size: 14px;
  color: #1f2937;
}

.task-id {
  font-family: 'Courier New', monospace;
  color: #6b7280;
}

.empty-state {
  text-align: center;
  color: #9ca3af;
  padding: 40px !important;
}

.result-success {
  color: #059669;
  font-weight: 500;
}

.result-error {
  color: #dc2626;
  font-weight: 500;
}

.btn-action {
  padding: 6px 16px;
  background: #3b82f6;
  border: none;
  border-radius: 4px;
  color: white;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-action:hover {
  background: #2563eb;
}

.disabled {
  color: #9ca3af;
}

.trigger-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.form-group select {
  padding: 10px;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  color: #1f2937;
  font-size: 14px;
}

.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
