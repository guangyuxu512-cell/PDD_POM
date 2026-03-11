<script setup lang="ts">
interface BrowserInstance {
  id: string
  shop_id: string
  shop_name: string
  status: string
  created_at: string
  memory_usage: string
  cpu_usage: string
}

interface Props {
  instance: BrowserInstance
}

defineProps<Props>()

const emit = defineEmits<{
  close: [shopId: string]
}>()

const getRuntime = (createdAt: string) => {
  const start = new Date(createdAt).getTime()
  const now = Date.now()
  const diff = Math.floor((now - start) / 1000)
  const hours = Math.floor(diff / 3600)
  const minutes = Math.floor((diff % 3600) / 60)
  return `${hours}h ${minutes}m`
}
</script>

<template>
  <div class="instance-card">
    <div class="instance-header">
      <div class="instance-title">
        <span class="status-dot" :class="instance.status"></span>
        <span class="shop-name">{{ instance.shop_name || instance.shop_id }}</span>
      </div>
      <span class="instance-status">{{ instance.status === 'running' ? '运行中' : '空闲' }}</span>
    </div>
    <div class="instance-info">
      <div class="info-item">
        <span class="label">运行时长：</span>
        <span>{{ getRuntime(instance.created_at) }}</span>
      </div>
      <div class="info-item">
        <span class="label">内存：</span>
        <span>{{ instance.memory_usage || '-' }}</span>
      </div>
      <div class="info-item">
        <span class="label">CPU：</span>
        <span>{{ instance.cpu_usage || '-' }}</span>
      </div>
    </div>
    <div class="instance-actions">
      <button class="btn-close" @click="emit('close', instance.shop_id)">关闭</button>
    </div>
  </div>
</template>

<style scoped>
.instance-card {
  background: #16213e;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #0f3460;
  transition: all 0.2s;
}

.instance-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.instance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #0f3460;
}

.instance-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4ade80;
}

.status-dot.idle {
  background: #9ca3af;
}

.shop-name {
  font-size: 16px;
  font-weight: 600;
}

.instance-status {
  font-size: 12px;
  color: #a0a0a0;
}

.instance-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  font-size: 14px;
}

.label {
  color: #a0a0a0;
  min-width: 80px;
}

.instance-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #0f3460;
}

.btn-close {
  padding: 6px 16px;
  background: #7f1d1d;
  border: none;
  border-radius: 4px;
  color: #e0e0e0;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #991b1b;
}
</style>
