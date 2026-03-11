<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { get, post } from '../api'
import { toast } from '../utils/toast'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import BrowserStatus from '../components/BrowserStatus.vue'

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
  default_proxy: ''
})
const showCloseAllConfirm = ref(false)
let pollTimer: number | null = null

const loadInstances = async () => {
  try {
    instances.value = await get<BrowserInstance[]>('/api/browser/instances')
  } catch (e) {
    console.error('加载实例列表失败:', e)
  }
}

const loadConfig = async () => {
  try {
    const data = await get<any>('/api/system/config')
    config.value = {
      max_browser_instances: data.max_browser_instances || 5,
      chrome_path: data.chrome_path || '',
      default_proxy: data.default_proxy || ''
    }
  } catch (e) {
    console.error('加载配置失败:', e)
  }
}

const handleInit = async () => {
  try {
    await post('/api/browser/init', config.value)
    toast.success('浏览器初始化成功')
    await loadInstances()
  } catch (e: any) {
    toast.error('初始化失败: ' + (e.message || e))
  }
}

const handleCloseInstance = async (shopId: string) => {
  try {
    await post(`/api/browser/${shopId}/close`)
    toast.success('浏览器已关闭')
    await loadInstances()
  } catch (e: any) {
    toast.error('关闭失败: ' + (e.message || e))
  }
}

const handleCloseAll = async () => {
  try {
    await post('/api/browser/close-all')
    showCloseAllConfirm.value = false
    toast.success('已关闭所有浏览器')
    await loadInstances()
  } catch (e: any) {
    toast.error('关闭失败: ' + (e.message || e))
  }
}

// 启动轮询
const startPolling = () => {
  pollTimer = window.setInterval(loadInstances, 5000)
}

// 停止轮询
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
  <div class="browser-manager">
    <h1>浏览器管理</h1>

    <div class="config-section">
      <h3>初始化配置</h3>
      <div class="config-form">
        <div class="form-row">
          <div class="form-group">
            <label>最大实例数</label>
            <input v-model.number="config.max_browser_instances" type="number" min="1" max="10" />
          </div>
          <div class="form-group">
            <label>Chrome 路径</label>
            <input v-model="config.chrome_path" type="text" placeholder="留空使用系统默认" />
          </div>
          <div class="form-group">
            <label>默认代理</label>
            <input v-model="config.default_proxy" type="text" placeholder="127.0.0.1:7890" />
          </div>
          <button class="btn btn-primary" @click="handleInit">初始化</button>
        </div>
      </div>
    </div>

    <div class="instances-section">
      <h3>运行中实例 ({{ instances.length }})</h3>
      <div v-if="instances.length === 0" class="empty-state">
        暂无数据
      </div>
      <div v-else class="instances-grid">
        <BrowserStatus
          v-for="instance in instances"
          :key="instance.id"
          :instance="instance"
          @close="handleCloseInstance"
        />
      </div>
    </div>

    <div v-if="instances.length > 0" class="actions-section">
      <button class="btn btn-danger" @click="showCloseAllConfirm = true">关闭全部</button>
    </div>

    <ConfirmDialog
      :show="showCloseAllConfirm"
      title="确认关闭"
      message="确定要关闭所有浏览器实例吗？"
      type="danger"
      @confirm="handleCloseAll"
      @cancel="showCloseAllConfirm = false"
    />
  </div>
</template>

<style scoped>
.browser-manager {
  color: #1a1a2e;
}

h1 {
  font-size: 28px;
  margin-bottom: 24px;
  color: #1a1a2e;
}

h3 {
  font-size: 18px;
  margin-bottom: 16px;
  color: #1a1a2e;
}

.config-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid #e5e7eb;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.form-group {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  color: #6b7280;
}

.form-group input {
  padding: 10px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  color: #1a1a2e;
  font-size: 14px;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
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

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

.instances-section {
  margin-bottom: 24px;
}

.empty-state {
  text-align: center;
  padding: 48px;
  color: #6b7280;
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.instances-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

@media (max-width: 768px) {
  .instances-grid {
    grid-template-columns: 1fr;
  }
}

.actions-section {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}
</style>
