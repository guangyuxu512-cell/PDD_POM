<script setup lang="ts">
import StatusBadge from './StatusBadge.vue'

interface Shop {
  id: string
  name: string
  username?: string | null
  proxy?: string | null
  status: string
  last_login?: string | null
  cookie_status?: string | null
  smtp_user?: string | null
  smtp_host?: string | null
  smtp_port?: number | null
  smtp_protocol?: string | null
}

interface Props {
  shop: Shop
}

defineProps<Props>()

const emit = defineEmits<{
  openBrowser: [shopId: string]
  edit: [shop: Shop]
  checkStatus: [shopId: string]
  delete: [shopId: string]
}>()
</script>

<template>
  <div class="shop-card">
    <div class="shop-header">
      <div class="shop-title">
        <StatusBadge :status="shop.status" type="shop" />
        <div class="shop-meta">
          <span class="shop-id">ID: {{ shop.id }}</span>
          <span class="shop-name">{{ shop.name }}</span>
        </div>
      </div>
    </div>
    <div class="shop-info">
      <div class="info-row">
        <span class="label">账号：</span>
        <span>{{ shop.username }}</span>
      </div>
      <div class="info-row">
        <span class="label">代理：</span>
        <span>{{ shop.proxy || '无' }}</span>
      </div>
      <div class="info-row">
        <span class="label">最后登录：</span>
        <span>{{ shop.last_login }}</span>
      </div>
      <div class="info-row">
        <span class="label">邮箱：</span>
        <span>{{ shop.smtp_user || '未配置' }}</span>
      </div>
    </div>
    <div class="shop-actions">
      <button class="btn-action btn-open" @click="emit('openBrowser', shop.id)">打开</button>
      <button class="btn-action btn-edit" @click="emit('edit', shop)">编辑</button>
      <button class="btn-action btn-check" @click="emit('checkStatus', shop.id)">检查</button>
      <button class="btn-action btn-delete" @click="emit('delete', shop.id)">删除</button>
    </div>
  </div>
</template>

<style scoped>
.shop-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.shop-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.shop-header {
  margin-bottom: 16px;
}

.shop-title {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.shop-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.shop-id {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
  word-break: break-all;
}

.shop-name {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  line-height: 1.4;
  word-break: break-word;
}

.shop-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.info-row {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #1a1a2e;
}

.label {
  color: #6b7280;
  min-width: 80px;
}

.shop-actions {
  display: flex;
  gap: 8px;
}

.btn-action {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  color: white;
}

.btn-open {
  background: #10b981;
}

.btn-open:hover {
  background: #059669;
}

.btn-edit {
  background: #3b82f6;
}

.btn-edit:hover {
  background: #2563eb;
}

.btn-check {
  background: #6b7280;
}

.btn-check:hover {
  background: #4b5563;
}

.btn-delete {
  background: #ef4444;
}

.btn-delete:hover {
  background: #dc2626;
}
</style>
