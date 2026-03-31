<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  status?: string
  type?: 'shop' | 'task' | 'log'
}

interface StatusConfig {
  text: string
  dotClass: string
  textClass: string
  pulse?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  status: 'offline',
  type: 'task',
})

const statusConfig = computed<StatusConfig>(() => {
  if (props.type === 'shop') {
    const configs: Record<string, StatusConfig> = {
      online: { text: '在线', dotClass: 'bg-emerald-500', textClass: 'text-emerald-700' },
      offline: { text: '离线', dotClass: 'bg-gray-300', textClass: 'text-gray-500' },
      expired: { text: '过期', dotClass: 'bg-amber-400', textClass: 'text-amber-700' },
      logging: { text: '登录中', dotClass: 'bg-amber-400', textClass: 'text-amber-700', pulse: true },
      logging_in: { text: '登录中', dotClass: 'bg-amber-400', textClass: 'text-amber-700', pulse: true },
    }

    return configs[props.status] || {
      text: props.status,
      dotClass: 'bg-gray-300',
      textClass: 'text-gray-500',
    }
  }

  if (props.type === 'task') {
    const configs: Record<string, StatusConfig> = {
      pending: { text: '等待中', dotClass: 'bg-gray-300', textClass: 'text-gray-500' },
      waiting: { text: '等待中', dotClass: 'bg-gray-300', textClass: 'text-gray-500' },
      running: { text: '运行中', dotClass: 'bg-amber-400', textClass: 'text-amber-700', pulse: true },
      success: { text: '成功', dotClass: 'bg-emerald-500', textClass: 'text-emerald-700' },
      completed: { text: '已完成', dotClass: 'bg-emerald-500', textClass: 'text-emerald-700' },
      failed: { text: '失败', dotClass: 'bg-rose-500', textClass: 'text-rose-700' },
      stopped: { text: '已停止', dotClass: 'bg-gray-400', textClass: 'text-gray-600' },
      skipped: { text: '跳过', dotClass: 'bg-gray-400', textClass: 'text-gray-600' },
      cancelled: { text: '已取消', dotClass: 'bg-gray-400', textClass: 'text-gray-600' },
    }

    return configs[props.status] || {
      text: props.status,
      dotClass: 'bg-gray-300',
      textClass: 'text-gray-500',
    }
  }

  const configs: Record<string, StatusConfig> = {
    INFO: { text: 'INFO', dotClass: 'bg-gray-400', textClass: 'text-gray-600' },
    WARN: { text: 'WARN', dotClass: 'bg-amber-400', textClass: 'text-amber-700' },
    ERROR: { text: 'ERROR', dotClass: 'bg-rose-500', textClass: 'text-rose-700' },
  }

  return configs[props.status] || {
    text: props.status,
    dotClass: 'bg-gray-300',
    textClass: 'text-gray-500',
  }
})
</script>

<template>
  <span :class="['inline-flex items-center gap-2 whitespace-nowrap text-xs font-medium', statusConfig.textClass]">
    <span
      :class="[
        'h-1.5 w-1.5 rounded-full',
        statusConfig.dotClass,
        statusConfig.pulse ? 'animate-pulse' : '',
      ]"
    />
    {{ statusConfig.text }}
  </span>
</template>
