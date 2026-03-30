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
  <div class="task-list-tab">
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
      <p class="toolbar-tip">批量启用、禁用前至少选择一个筛选条件；批量重置默认处理当前筛选结果。</p>
    </div>

    <div class="table-container">
      <table class="task-param-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>店铺</th>
            <th>任务类型</th>
            <th>启用</th>
            <th>参数摘要</th>
            <th>状态</th>
            <th>执行次数</th>
            <th>结果摘要</th>
            <th>执行结果</th>
            <th>错误信息</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="12" class="empty-state">加载中...</td>
          </tr>
          <tr v-else-if="taskParams.length === 0">
            <td colspan="12" class="empty-state">暂无任务参数记录</td>
          </tr>
          <template v-else>
            <tr v-for="taskParam in taskParams" :key="taskParam.id" :class="{ 'is-disabled': !taskParam.enabled }">
              <td>{{ taskParam.id }}</td>
              <td class="cell-wrap">{{ store.formatShopLabel(taskParam) }}</td>
              <td>{{ taskParam.task_name }}</td>
              <td>
                <label class="switch">
                  <input
                    type="checkbox"
                    :checked="taskParam.enabled"
                    :disabled="store.isRowActioning(taskParam.id)"
                    @change="emit('toggle-enabled', taskParam)"
                  />
                  <span class="switch-slider" />
                  <span class="switch-label">{{ taskParam.enabled ? '启用' : '禁用' }}</span>
                </label>
              </td>
              <td class="cell-wide">
                <span
                  class="tooltip-trigger cell-ellipsis cell-wide"
                  @mouseenter="store.showJsonTooltip($event, taskParam.params)"
                  @mouseleave="store.scheduleHideJsonTooltip"
                >
                  {{ store.formatParamSummary(taskParam.params) }}
                </span>
              </td>
              <td>
                <StatusBadge :status="taskParam.status" type="task" />
              </td>
              <td>{{ taskParam.run_count }}</td>
              <td class="cell-ellipsis" :title="store.formatJsonTooltip(taskParam.result)">
                {{ store.formatResultSummary(taskParam.result) }}
              </td>
              <td>
                <span
                  class="tooltip-trigger cell-ellipsis"
                  @mouseenter="store.showJsonTooltip($event, taskParam.result)"
                  @mouseleave="store.scheduleHideJsonTooltip"
                >
                  {{ store.formatExecutionResult(taskParam.result) }}
                </span>
              </td>
              <td class="cell-ellipsis error-text" :title="taskParam.error || '-'">
                {{ taskParam.error || '-' }}
              </td>
              <td>{{ store.formatDateTime(taskParam.created_at) }}</td>
              <td>
                <div class="action-group">
                  <button
                    v-if="taskParam.status !== 'pending'"
                    class="btn-action btn-reset"
                    :disabled="store.isRowActioning(taskParam.id)"
                    @click="emit('reset', taskParam)"
                  >
                    重置
                  </button>
                  <button
                    class="btn-action btn-delete"
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

<style scoped src="./TaskListTab.css"></style>

