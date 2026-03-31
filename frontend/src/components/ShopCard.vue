<script setup lang="ts">
import type { Shop } from '../api/types'

import StatusBadge from './StatusBadge.vue'

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
  <div class="border-b border-gray-100 px-4 py-3 transition-colors hover:bg-gray-50">
    <div class="flex flex-col gap-4 lg:grid lg:grid-cols-[minmax(0,2.2fr)_minmax(0,1.2fr)_minmax(0,1.4fr)_auto] lg:items-center">
      <div class="min-w-0">
        <div class="flex items-start gap-3">
          <StatusBadge :status="shop.status" type="shop" />
          <div class="min-w-0 space-y-1">
            <div class="flex flex-wrap items-center gap-2">
              <p class="truncate text-sm font-medium text-gray-900">
                {{ shop.name }}
              </p>
              <span class="rounded-full bg-gray-100 px-2 py-0.5 font-mono text-[11px] text-gray-500">
                {{ shop.id }}
              </span>
            </div>
            <p class="truncate font-mono text-xs text-gray-500">
              {{ shop.username || '未填写账号' }}
            </p>
          </div>
        </div>
      </div>

      <div class="grid gap-1">
        <div class="flex items-center gap-2 text-sm text-gray-900">
          <span class="text-xs text-gray-500">邮箱</span>
          <span class="truncate">{{ shop.smtp_user || '未配置' }}</span>
        </div>
        <div class="flex items-center gap-2 text-sm text-gray-900">
          <span class="text-xs text-gray-500">协议</span>
          <span class="font-mono text-xs uppercase text-gray-500">
            {{ shop.smtp_protocol || 'imap' }}
          </span>
        </div>
      </div>

      <div class="grid gap-1">
        <div class="flex items-center gap-2 text-sm text-gray-900">
          <span class="text-xs text-gray-500">代理</span>
          <span class="truncate">{{ shop.proxy || '无代理' }}</span>
        </div>
        <div class="flex items-center gap-2 text-sm text-gray-900">
          <span class="text-xs text-gray-500">最近登录</span>
          <span class="truncate font-mono text-xs text-gray-500">
            {{ shop.last_login || '暂无记录' }}
          </span>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-3 lg:justify-end">
        <button
          type="button"
          class="text-xs font-medium text-gray-500 transition hover:text-gray-700"
          @click="emit('openBrowser', shop.id)"
        >
          打开
        </button>
        <button
          type="button"
          class="text-xs font-medium text-gray-500 transition hover:text-gray-700"
          @click="emit('edit', shop)"
        >
          编辑
        </button>
        <button
          type="button"
          class="text-xs font-medium text-gray-500 transition hover:text-gray-700"
          @click="emit('checkStatus', shop.id)"
        >
          检查
        </button>
        <button
          type="button"
          class="text-xs font-medium text-gray-500 transition hover:text-gray-700"
          @click="emit('delete', shop.id)"
        >
          删除
        </button>
      </div>
    </div>
  </div>
</template>
