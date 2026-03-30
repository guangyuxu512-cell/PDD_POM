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
  <div class="flow-params-tab">
    <div class="toolbar">
      <div class="toolbar-actions">
        <button class="btn btn-light" :disabled="store.batchAction !== ''" @click="triggerBatchAction('reset')">
          {{ store.batchAction === 'reset' ? '批量重置中...' : '批量重置' }}
        </button>
        <button class="btn btn-light" :disabled="store.batchAction !== ''" @click="triggerBatchAction('enable')">
          {{ store.batchAction === 'enable' ? '批量启用中...' : '批量启用' }}
        </button>
        <button class="btn btn-light" :disabled="store.batchAction !== ''" @click="triggerBatchAction('disable')">
          {{ store.batchAction === 'disable' ? '批量禁用中...' : '批量禁用' }}
        </button>
      </div>
      <p class="toolbar-tip">流程参数支持按流程、状态、店铺筛选后批量重置、启用和禁用。</p>
    </div>

    <div class="table-container">
      <table class="task-param-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>店铺</th>
            <th>流程名称</th>
            <th>启用</th>
            <th>共享参数</th>
            <th>步骤进度</th>
            <th>状态</th>
            <th>执行结果</th>
            <th>错误信息</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="11" class="empty-state">加载中...</td>
          </tr>
          <tr v-else-if="flowParams.length === 0">
            <td colspan="11" class="empty-state">暂无流程参数记录</td>
          </tr>
          <template v-else>
            <tr v-for="flowParam in flowParams" :key="flowParam.id" :class="{ 'is-disabled': !flowParam.enabled }">
              <td>{{ flowParam.id }}</td>
              <td class="cell-wrap">{{ store.formatFlowParamShopLabel(flowParam) }}</td>
              <td>{{ store.getFlowName(flowParam.flow_id) }}</td>
              <td>
                <label class="switch">
                  <input
                    type="checkbox"
                    :checked="flowParam.enabled"
                    :disabled="store.isRowActioning(flowParam.id)"
                    @change="emit('toggle-enabled', flowParam)"
                  />
                  <span class="switch-slider" />
                  <span class="switch-label">{{ flowParam.enabled ? '启用' : '禁用' }}</span>
                </label>
              </td>
              <td class="cell-wide">
                <span
                  class="tooltip-trigger cell-ellipsis cell-wide"
                  @mouseenter="store.showJsonTooltip($event, flowParam.params)"
                  @mouseleave="store.scheduleHideJsonTooltip"
                >
                  {{ store.formatParamSummary(flowParam.params) }}
                </span>
              </td>
              <td>{{ store.formatFlowProgress(flowParam) }}</td>
              <td>
                <StatusBadge :status="flowParam.status" type="task" />
              </td>
              <td class="cell-wide">
                <div class="step-result-list" :title="store.formatStepResultsSummary(flowParam.step_results)">
                  <button
                    v-for="step in store.getStepResultItems(flowParam.step_results)"
                    :key="`${flowParam.id}-${step.name}`"
                    type="button"
                    class="step-result-tag"
                    :class="store.getStepResultStatusClass(step.status)"
                    @click="store.toggleStepResultDetail(flowParam.id, step.name)"
                  >
                    {{ store.formatStepResultTag(step) }}
                  </button>
                  <span v-if="store.getStepResultItems(flowParam.step_results).length === 0" class="cell-ellipsis">-</span>
                  <div
                    v-for="step in store.getStepResultItems(flowParam.step_results)"
                    v-show="store.isStepResultDetailOpen(flowParam.id, step.name)"
                    :key="`${flowParam.id}-${step.name}-detail`"
                    class="step-result-detail"
                  >
                    <strong>{{ step.name }}</strong>
                    <pre>{{ store.formatJsonTooltip(step.detail) }}</pre>
                  </div>
                </div>
              </td>
              <td class="cell-ellipsis error-text" :title="flowParam.error || '-'">
                {{ flowParam.error || '-' }}
              </td>
              <td>{{ store.formatDateTime(flowParam.created_at) }}</td>
              <td>
                <div class="action-group">
                  <button
                    v-if="flowParam.status !== 'pending'"
                    class="btn-action btn-reset"
                    :disabled="store.isRowActioning(flowParam.id)"
                    @click="emit('reset', flowParam)"
                  >
                    重置
                  </button>
                  <button
                    class="btn-action btn-delete"
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

<style scoped src="./FlowParamsTab.css"></style>

