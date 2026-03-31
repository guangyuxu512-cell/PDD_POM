<script setup lang="ts">
import StatusBadge from '../../components/StatusBadge.vue'
import type { TaskParam } from '../../api/types'
import { useTaskParamsContext } from './useTaskParamsStore'

defineProps<{
  resultTaskParams: TaskParam[]
  loading: boolean
  shopNameMap: Record<string, string>
}>()

const store = useTaskParamsContext()
</script>

<template>
  <div class="overflow-x-auto rounded-md border border-brand-300/50 bg-white shadow-sm">
    <table class="min-w-[1088px] w-full table-fixed divide-y divide-brand-300/30">
      <thead class="bg-brand-700/10 text-xs font-medium uppercase tracking-wider text-brand-700">
        <tr>
          <th class="w-16 px-4 py-3 text-center">ID</th>
          <th class="w-32 px-4 py-3 text-left">店铺</th>
          <th class="w-28 px-4 py-3 text-left">任务类型</th>
          <th class="w-48 px-4 py-3 text-left">参数摘要</th>
          <th class="w-48 px-4 py-3 text-left">结果摘要</th>
          <th class="w-24 px-4 py-3 text-center">状态</th>
          <th class="w-40 px-4 py-3 text-left">错误信息</th>
          <th class="w-36 px-4 py-3 text-right">执行时间</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-brand-300/20 text-sm text-gray-900">
        <tr v-if="loading">
          <td colspan="8" class="px-4 py-8 text-center text-sm text-brand-500">加载中...</td>
        </tr>
        <tr v-else-if="resultTaskParams.length === 0">
          <td colspan="8" class="px-4 py-8 text-center text-sm text-brand-500">暂无执行结果记录</td>
        </tr>
        <template v-else>
          <tr
            v-for="taskParam in resultTaskParams"
            :key="`${taskParam.task_name}-${taskParam.id}-${taskParam.batch_id || ''}`"
            class="transition hover:bg-brand-100/50"
          >
            <td class="px-4 py-3 text-center font-mono text-xs text-brand-500">{{ taskParam.id }}</td>
            <td class="truncate px-4 py-3 text-left">{{ store.formatShopLabel(taskParam) }}</td>
            <td class="px-4 py-3 text-left">{{ taskParam.task_name }}</td>
            <td class="px-4 py-3 text-left">
              <span
                class="block w-full cursor-help truncate"
                @mouseenter="store.showJsonTooltip($event, taskParam.params)"
                @mouseleave="store.scheduleHideJsonTooltip"
              >
                {{ store.formatParamSummary(taskParam.params) }}
              </span>
            </td>
            <td class="px-4 py-3 text-left">
              <span
                class="block w-full cursor-help truncate"
                @mouseenter="store.showJsonTooltip($event, taskParam.result)"
                @mouseleave="store.scheduleHideJsonTooltip"
              >
                {{ store.formatResultSummary(taskParam.result) }}
              </span>
            </td>
            <td class="px-4 py-3 text-center">
              <StatusBadge :status="taskParam.status" type="task" />
            </td>
            <td class="truncate px-4 py-3 text-left text-rose-600" :title="taskParam.error || '-'">
              {{ taskParam.error || '-' }}
            </td>
            <td class="px-4 py-3 text-right font-mono text-xs text-brand-500">{{ store.formatDateTime(taskParam.updated_at) }}</td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>
