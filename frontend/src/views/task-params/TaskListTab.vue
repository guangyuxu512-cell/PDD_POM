<script setup lang="ts">
import StatusBadge from '../../components/StatusBadge.vue'
import type { TaskParam } from '../../api/types'
import type { BatchActionKey } from './useTaskParamsStore'
import { useTaskParamsContext } from './useTaskParamsStore'

defineProps<{
  taskParams: TaskParam[]
  loading: boolean
  shopNameMap: Record<string, string>
}>()

const emit = defineEmits<{
  'toggle-enabled': [taskParam: TaskParam]
  reset: [taskParam: TaskParam]
  delete: [id: number]
  'batch-action': [action: Exclude<BatchActionKey, ''>]
}>()

const store = useTaskParamsContext()

function triggerBatchAction(action: Exclude<BatchActionKey, ''>) {
  emit('batch-action', action)
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <!-- 批量操作工具栏 -->
    <div class="flex flex-wrap items-center gap-2 rounded-md border border-brand-200/50 bg-white px-4 py-3 shadow-sm">
      <button
        class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-50"
        :disabled="store.batchAction !== ''"
        @click="triggerBatchAction('reset')"
      >
        {{ store.batchAction === 'reset' ? '批量重置中...' : '批量重置' }}
      </button>
      <button
        class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-50"
        :disabled="store.batchAction !== ''"
        @click="triggerBatchAction('enable')"
      >
        {{ store.batchAction === 'enable' ? '批量启用中...' : '批量启用' }}
      </button>
      <button
        class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-50"
        :disabled="store.batchAction !== ''"
        @click="triggerBatchAction('disable')"
      >
        {{ store.batchAction === 'disable' ? '批量禁用中...' : '批量禁用' }}
      </button>
      <span class="ml-auto text-xs text-gray-400">批量启用、禁用前至少选择一个筛选条件；批量重置默认处理当前筛选结果。</span>
    </div>

    <!-- 表格 -->
    <div class="overflow-x-auto rounded-md border border-brand-200/50 bg-white shadow-sm">
      <table class="min-w-[1488px] w-full table-fixed divide-y divide-brand-200/50">
        <thead class="bg-brand-50 text-xs font-medium uppercase tracking-wider text-brand-700">
          <tr>
            <th class="w-16 px-4 py-3 text-center">ID</th>
            <th class="w-32 px-4 py-3 text-left">店铺</th>
            <th class="w-28 px-4 py-3 text-left">任务类型</th>
            <th class="w-20 px-4 py-3 text-center">启用</th>
            <th class="w-48 px-4 py-3 text-left">参数摘要</th>
            <th class="w-24 px-4 py-3 text-center">状态</th>
            <th class="w-20 px-4 py-3 text-center">执行次数</th>
            <th class="w-40 px-4 py-3 text-left">结果摘要</th>
            <th class="w-40 px-4 py-3 text-left">执行结果</th>
            <th class="w-40 px-4 py-3 text-left">错误信息</th>
            <th class="w-36 px-4 py-3 text-right">创建时间</th>
            <th class="w-28 px-4 py-3 text-center">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-brand-200/50 text-sm text-gray-900">
          <tr v-if="loading">
            <td colspan="12" class="px-4 py-8 text-center text-sm text-gray-400">加载中...</td>
          </tr>
          <tr v-else-if="taskParams.length === 0">
            <td colspan="12" class="px-4 py-8 text-center text-sm text-gray-400">暂无任务参数记录</td>
          </tr>
          <template v-else>
            <tr
              v-for="taskParam in taskParams"
              :key="taskParam.id"
              :class="['transition hover:bg-gray-50/50', taskParam.enabled ? '' : 'opacity-50']"
            >
              <td class="px-4 py-3 text-center font-mono text-xs text-gray-500">{{ taskParam.id }}</td>
              <td class="truncate px-4 py-3 text-left">{{ store.formatShopLabel(taskParam) }}</td>
              <td class="px-4 py-3 text-left">{{ taskParam.task_name }}</td>
              <td class="px-4 py-3 text-center">
                <label class="inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    class="peer sr-only"
                    :checked="taskParam.enabled"
                    :disabled="store.isRowActioning(taskParam.id)"
                    @change="emit('toggle-enabled', taskParam)"
                  />
                  <span
                    class="relative h-5 w-9 rounded-full bg-gray-200 transition after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:shadow-sm after:transition-all peer-checked:bg-brand-500 peer-checked:after:translate-x-4 peer-disabled:opacity-50"
                  />
                </label>
              </td>
              <td class="px-4 py-3 text-left">
                <span
                  class="block w-full cursor-help truncate"
                  @mouseenter="store.showJsonTooltip($event, taskParam.params)"
                  @mouseleave="store.scheduleHideJsonTooltip"
                >
                  {{ store.formatParamSummary(taskParam.params) }}
                </span>
              </td>
              <td class="px-4 py-3 text-center">
                <StatusBadge :status="taskParam.status" type="task" />
              </td>
              <td class="px-4 py-3 text-center font-mono">{{ taskParam.run_count }}</td>
              <td class="truncate px-4 py-3 text-left" :title="store.formatJsonTooltip(taskParam.result)">
                {{ store.formatResultSummary(taskParam.result) }}
              </td>
              <td class="px-4 py-3 text-left">
                <span
                  class="block w-full cursor-help truncate"
                  @mouseenter="store.showJsonTooltip($event, taskParam.result)"
                  @mouseleave="store.scheduleHideJsonTooltip"
                >
                  {{ store.formatExecutionResult(taskParam.result) }}
                </span>
              </td>
              <td class="truncate px-4 py-3 text-left text-rose-600" :title="taskParam.error || '-'">
                {{ taskParam.error || '-' }}
              </td>
              <td class="px-4 py-3 text-right font-mono text-xs text-gray-500">{{ store.formatDateTime(taskParam.created_at) }}</td>
              <td class="whitespace-nowrap px-4 py-3 text-center">
                <div class="inline-flex gap-2">
                  <button
                    v-if="taskParam.status !== 'pending'"
                    class="text-xs font-medium text-brand-700 transition hover:text-brand-900 disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="store.isRowActioning(taskParam.id)"
                    @click="emit('reset', taskParam)"
                  >
                    重置
                  </button>
                  <button
                    class="text-xs font-medium text-rose-600 transition hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="store.isRowActioning(taskParam.id)"
                    @click="emit('delete', taskParam.id)"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
