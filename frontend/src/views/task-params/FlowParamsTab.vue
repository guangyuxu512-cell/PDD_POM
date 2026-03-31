<script setup lang="ts">
import StatusBadge from '../../components/StatusBadge.vue'
import type { Flow, FlowParam } from '../../api/types'
import type { BatchActionKey } from './useTaskParamsStore'
import { useTaskParamsContext } from './useTaskParamsStore'

defineProps<{
  flowParams: FlowParam[]
  loading: boolean
  flows: Flow[]
  shopNameMap: Record<string, string>
}>()

const emit = defineEmits<{
  'toggle-enabled': [flowParam: FlowParam]
  reset: [flowParam: FlowParam]
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
    <div class="flex flex-wrap items-center gap-2 rounded-md border border-gray-200 bg-white px-4 py-3 shadow-sm">
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
      <span class="ml-auto text-xs text-gray-400">流程参数支持按流程、状态、店铺筛选后批量重置、启用和禁用。</span>
    </div>

    <!-- 表格 -->
    <div class="overflow-x-auto rounded-md border border-gray-200 bg-white shadow-sm">
      <table class="min-w-[1328px] w-full table-fixed divide-y divide-gray-200">
        <thead class="bg-gray-50/60 text-xs font-medium uppercase tracking-wider text-gray-500">
          <tr>
            <th class="w-16 px-4 py-3 text-center">ID</th>
            <th class="w-32 px-4 py-3 text-left">店铺</th>
            <th class="w-28 px-4 py-3 text-left">流程名称</th>
            <th class="w-20 px-4 py-3 text-center">启用</th>
            <th class="w-48 px-4 py-3 text-left">共享参数</th>
            <th class="w-20 px-4 py-3 text-center">步骤进度</th>
            <th class="w-24 px-4 py-3 text-center">状态</th>
            <th class="w-40 px-4 py-3 text-left">执行结果</th>
            <th class="w-40 px-4 py-3 text-left">错误信息</th>
            <th class="w-36 px-4 py-3 text-right">创建时间</th>
            <th class="w-28 px-4 py-3 text-center">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 text-sm text-gray-900">
          <tr v-if="loading">
            <td colspan="11" class="px-4 py-8 text-center text-sm text-gray-400">加载中...</td>
          </tr>
          <tr v-else-if="flowParams.length === 0">
            <td colspan="11" class="px-4 py-8 text-center text-sm text-gray-400">暂无流程参数记录</td>
          </tr>
          <template v-else>
            <tr
              v-for="flowParam in flowParams"
              :key="flowParam.id"
              :class="['transition hover:bg-gray-50/50', flowParam.enabled ? '' : 'opacity-50']"
            >
              <td class="px-4 py-3 text-center font-mono text-xs text-gray-500">{{ flowParam.id }}</td>
              <td class="truncate px-4 py-3 text-left">{{ store.formatFlowParamShopLabel(flowParam) }}</td>
              <td class="px-4 py-3 text-left">{{ store.getFlowName(flowParam.flow_id) }}</td>
              <td class="px-4 py-3 text-center">
                <label class="inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    class="peer sr-only"
                    :checked="flowParam.enabled"
                    :disabled="store.isRowActioning(flowParam.id)"
                    @change="emit('toggle-enabled', flowParam)"
                  />
                  <span
                    class="relative h-5 w-9 rounded-full bg-gray-200 transition after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:shadow-sm after:transition-all peer-checked:bg-gray-900 peer-checked:after:translate-x-4 peer-disabled:opacity-50"
                  />
                </label>
              </td>
              <td class="px-4 py-3 text-left">
                <span
                  class="block w-full cursor-help truncate"
                  @mouseenter="store.showJsonTooltip($event, flowParam.params)"
                  @mouseleave="store.scheduleHideJsonTooltip"
                >
                  {{ store.formatParamSummary(flowParam.params) }}
                </span>
              </td>
              <td class="px-4 py-3 text-center font-mono">{{ store.formatFlowProgress(flowParam) }}</td>
              <td class="px-4 py-3 text-center">
                <StatusBadge :status="flowParam.status" type="task" />
              </td>
              <td class="px-4 py-3 text-left">
                <div class="flex flex-wrap gap-1" :title="store.formatStepResultsSummary(flowParam.step_results)">
                  <button
                    v-for="step in store.getStepResultItems(flowParam.step_results)"
                    :key="`${flowParam.id}-${step.name}`"
                    type="button"
                    :class="['rounded-full px-2.5 py-1 text-xs font-bold transition hover:opacity-80', store.getStepResultStatusClass(step.status)]"
                    @click="store.toggleStepResultDetail(flowParam.id, step.name)"
                  >
                    {{ store.formatStepResultTag(step) }}
                  </button>
                  <span v-if="store.getStepResultItems(flowParam.step_results).length === 0" class="text-gray-400">-</span>
                  <div
                    v-for="step in store.getStepResultItems(flowParam.step_results)"
                    v-show="store.isStepResultDetailOpen(flowParam.id, step.name)"
                    :key="`${flowParam.id}-${step.name}-detail`"
                    class="mt-1 w-full rounded-md border border-gray-200 bg-gray-50 p-2"
                  >
                    <strong class="mb-1 block text-xs text-gray-700">{{ step.name }}</strong>
                    <pre class="whitespace-pre-wrap break-words text-xs text-gray-600">{{ store.formatJsonTooltip(step.detail) }}</pre>
                  </div>
                </div>
              </td>
              <td class="truncate px-4 py-3 text-left text-rose-600" :title="flowParam.error || '-'">
                {{ flowParam.error || '-' }}
              </td>
              <td class="px-4 py-3 text-right font-mono text-xs text-gray-500">{{ store.formatDateTime(flowParam.created_at) }}</td>
              <td class="whitespace-nowrap px-4 py-3 text-center">
                <div class="inline-flex gap-2">
                  <button
                    v-if="flowParam.status !== 'pending'"
                    class="text-xs font-medium text-gray-500 transition hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="store.isRowActioning(flowParam.id)"
                    @click="emit('reset', flowParam)"
                  >
                    重置
                  </button>
                  <button
                    class="text-xs font-medium text-rose-600 transition hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="store.isRowActioning(flowParam.id)"
                    @click="emit('delete', flowParam.id)"
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
