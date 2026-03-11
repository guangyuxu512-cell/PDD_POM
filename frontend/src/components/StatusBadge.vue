<script setup lang="ts">
interface Props {
  status?: string
  type?: 'shop' | 'task' | 'log'
}

const props = withDefaults(defineProps<Props>(), {
  status: 'offline',
  type: 'task'
})

const getStatusConfig = (): { text: string; color: string; bg: string; pulse?: boolean } => {
  if (props.type === 'shop') {
    const configs: Record<string, { text: string; color: string; bg: string }> = {
      online: { text: '在线', color: '#4ade80', bg: 'rgba(74, 222, 128, 0.1)' },
      offline: { text: '离线', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
      expired: { text: '过期', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' }
    }
    return configs[props.status] || { text: props.status, color: '#a0a0a0', bg: 'rgba(160, 160, 160, 0.1)' }
  }

  if (props.type === 'task') {
    const configs: Record<string, { text: string; color: string; bg: string; pulse?: boolean }> = {
      pending: { text: '等待中', color: '#9ca3af', bg: 'rgba(156, 163, 175, 0.1)' },
      running: { text: '运行中', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)', pulse: true },
      success: { text: '成功', color: '#4ade80', bg: 'rgba(74, 222, 128, 0.1)' },
      failed: { text: '失败', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' }
    }
    return configs[props.status] || { text: props.status, color: '#a0a0a0', bg: 'rgba(160, 160, 160, 0.1)' }
  }

  if (props.type === 'log') {
    const configs: Record<string, { text: string; color: string; bg: string }> = {
      INFO: { text: 'INFO', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' },
      WARN: { text: 'WARN', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' },
      ERROR: { text: 'ERROR', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' }
    }
    return configs[props.status] || { text: props.status, color: '#a0a0a0', bg: 'rgba(160, 160, 160, 0.1)' }
  }

  return { text: props.status, color: '#a0a0a0', bg: 'rgba(160, 160, 160, 0.1)' }
}

const config = getStatusConfig()
</script>

<template>
  <span
    class="status-badge"
    :class="{ pulse: config.pulse }"
    :style="{ color: config.color, background: config.bg }"
  >
    {{ config.text }}
  </span>
</template>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}
</style>
