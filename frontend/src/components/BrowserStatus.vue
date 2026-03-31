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
  <div class="rounded-md border border-gray-200 bg-white p-4 shadow-sm">
    <div class="flex items-start justify-between gap-3">
      <div class="space-y-1">
        <div class="flex items-center gap-2">
          <span
            :class="[
              'h-2 w-2 rounded-full',
              instance.status === 'running' ? 'bg-emerald-500' : 'bg-gray-300',
            ]"
          />
          <p class="text-sm font-medium text-gray-900">
            {{ instance.shop_name || instance.shop_id }}
          </p>
        </div>
        <p class="text-xs text-gray-500">
          {{ instance.status === 'running' ? '运行中' : '空闲' }}
        </p>
      </div>

      <button
        type="button"
        class="rounded-md bg-rose-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-rose-700"
        @click="emit('close', instance.shop_id)"
      >
        关闭
      </button>
    </div>

    <dl class="mt-4 grid gap-3 sm:grid-cols-3">
      <div>
        <dt class="text-xs text-gray-500">运行时长</dt>
        <dd class="mt-1 font-mono text-sm text-gray-900">{{ getRuntime(instance.created_at) }}</dd>
      </div>
      <div>
        <dt class="text-xs text-gray-500">内存</dt>
        <dd class="mt-1 font-mono text-sm text-gray-900">{{ instance.memory_usage || '-' }}</dd>
      </div>
      <div>
        <dt class="text-xs text-gray-500">CPU</dt>
        <dd class="mt-1 font-mono text-sm text-gray-900">{{ instance.cpu_usage || '-' }}</dd>
      </div>
    </dl>
  </div>
</template>
