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
  showShop: false,
})
</script>

<template>
  <div class="overflow-hidden rounded-md border border-brand-300/50 bg-white shadow-sm">
    <div v-if="loading" class="flex min-h-[220px] flex-col items-center justify-center gap-3 text-brand-500">
      <span class="h-8 w-8 animate-spin rounded-full border-2 border-brand-300/50 border-t-brand-500" />
      <p class="text-sm">加载中...</p>
    </div>

    <div v-else-if="logs.length === 0" class="flex min-h-[220px] items-center justify-center text-sm text-brand-500">
      暂无数据
    </div>

    <div v-else class="overflow-x-auto">
      <table class="min-w-full table-fixed">
        <thead class="bg-brand-700/10 text-xs font-medium uppercase tracking-wider text-brand-700">
          <tr>
            <th class="w-44 px-4 py-3 text-right font-medium">时间</th>
            <th v-if="showShop" class="w-36 px-4 py-3 text-left font-medium">店铺</th>
            <th class="w-28 px-4 py-3 text-left font-medium">级别</th>
            <th class="w-32 px-4 py-3 text-left font-medium">来源</th>
            <th class="px-4 py-3 text-left font-medium">内容</th>
            <th v-if="$slots.actions" class="w-28 px-4 py-3 text-right font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id" class="border-b border-brand-300/30 hover:bg-brand-100/50">
            <td class="px-4 py-3 text-right font-mono text-xs text-brand-500">
              {{ log.timestamp }}
            </td>
            <td v-if="showShop" class="px-4 py-3 text-sm text-gray-900">
              {{ log.shop_name || '-' }}
            </td>
            <td class="px-4 py-3 text-sm text-gray-900">
              <StatusBadge :status="log.level" type="log" />
            </td>
            <td class="px-4 py-3 font-mono text-xs uppercase tracking-wide text-brand-500">
              {{ log.source }}
            </td>
            <td class="px-4 py-3 text-sm leading-6 text-gray-900">
              {{ log.message }}
            </td>
            <td v-if="$slots.actions" class="px-4 py-3 text-right text-sm text-gray-900">
              <slot name="actions" :log="log" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
