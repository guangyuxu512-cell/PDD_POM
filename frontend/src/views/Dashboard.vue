<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { get } from '../api'
import StatCard from '../components/StatCard.vue'

interface Shop {
  id: string
  name: string
  status: string
}

interface Task {
  id: string
  status: string
  created_at: string
}

const shops = ref<Shop[]>([])
const tasks = ref<Task[]>([])

const stats = computed(() => {
  const onlineShops = shops.value.filter(s => s.status === 'online').length
  const runningTasks = tasks.value.filter(t => t.status === 'running').length
  const todayTasks = tasks.value.filter(t => {
    const today = new Date().toISOString().slice(0, 10)
    return t.created_at.startsWith(today)
  }).length
  const failedTasks = tasks.value.filter(t => t.status === 'failed').length

  return [
    { label: '在线店铺', value: onlineShops, icon: '🟢', color: '#4ade80' },
    { label: '运行中任务', value: runningTasks, icon: '⚡', color: '#3b82f6' },
    { label: '今日执行', value: todayTasks, icon: '📊', color: '#8b5cf6' },
    { label: '错误数', value: failedTasks, icon: '🔴', color: '#ef4444' }
  ]
})

onMounted(async () => {
  const shopsResult = await get<{list: Shop[], total: number}>('/api/shops/')
  shops.value = shopsResult.list
  const tasksResult = await get<{list: Task[], total: number}>('/api/tasks/')
  tasks.value = tasksResult.list
})
</script>

<template>
  <div class="dashboard">
    <h1>仪表盘</h1>
    <div class="stats-grid">
      <StatCard
        v-for="stat in stats"
        :key="stat.label"
        :icon="stat.icon"
        :label="stat.label"
        :value="stat.value"
        :color="stat.color"
      />
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  color: #1a1a2e;
}

h1 {
  font-size: 28px;
  margin-bottom: 24px;
  color: #1a1a2e;
}

.stats-grid {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
