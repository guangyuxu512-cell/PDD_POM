<script setup lang="ts">
import StatusBadge from './StatusBadge.vue'

interface Log {
  id: string
  timestamp: string
  level: string
  source: string
  message: string
  shop_name?: string
}

interface Props {
  logs: Log[]
  loading?: boolean
  showShop?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false,
  showShop: false
})
</script>

<template>
  <div class="table-container">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    <div v-else-if="logs.length === 0" class="empty-state">
      <p>暂无数据</p>
    </div>
    <table v-else class="log-table">
      <thead>
        <tr>
          <th style="width: 180px">时间</th>
          <th v-if="showShop" style="width: 120px">店铺</th>
          <th style="width: 100px">级别</th>
          <th style="width: 120px">来源</th>
          <th>内容</th>
          <th v-if="$slots.actions" style="width: 100px">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td>{{ log.timestamp }}</td>
          <td v-if="showShop">{{ log.shop_name || '-' }}</td>
          <td>
            <StatusBadge :status="log.level" type="log" />
          </td>
          <td>{{ log.source }}</td>
          <td>{{ log.message }}</td>
          <td v-if="$slots.actions">
            <slot name="actions" :log="log" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-container {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  min-height: 200px;
  position: relative;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: #6b7280;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.log-table {
  width: 100%;
  border-collapse: collapse;
}

.log-table thead {
  background: #f9fafb;
}

.log-table th {
  padding: 16px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  color: #1a1a2e;
}

.log-table tbody tr {
  border-bottom: 1px solid #e5e7eb;
  transition: background 0.2s;
}

.log-table tbody tr:nth-child(even) {
  background: #f9fafb;
}

.log-table tbody tr:hover {
  background: #eff6ff;
}

.log-table td {
  padding: 16px;
  font-size: 14px;
  color: #1a1a2e;
}
</style>
