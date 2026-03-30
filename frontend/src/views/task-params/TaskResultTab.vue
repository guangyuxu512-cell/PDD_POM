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
  <div class="table-container">
    <table class="task-param-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>店铺</th>
          <th>任务类型</th>
          <th>参数摘要</th>
          <th>结果摘要</th>
          <th>状态</th>
          <th>错误信息</th>
          <th>执行时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="8" class="empty-state">加载中...</td>
        </tr>
        <tr v-else-if="resultTaskParams.length === 0">
          <td colspan="8" class="empty-state">暂无执行结果记录</td>
        </tr>
        <template v-else>
          <tr v-for="taskParam in resultTaskParams" :key="`${taskParam.task_name}-${taskParam.id}-${taskParam.batch_id || ''}`">
            <td>{{ taskParam.id }}</td>
            <td class="cell-wrap">{{ store.formatShopLabel(taskParam) }}</td>
            <td>{{ taskParam.task_name }}</td>
            <td class="cell-wide">
              <span
                class="tooltip-trigger cell-ellipsis cell-wide"
                @mouseenter="store.showJsonTooltip($event, taskParam.params)"
                @mouseleave="store.scheduleHideJsonTooltip"
              >
                {{ store.formatParamSummary(taskParam.params) }}
              </span>
            </td>
            <td class="cell-wide">
              <span
                class="tooltip-trigger cell-ellipsis cell-wide"
                @mouseenter="store.showJsonTooltip($event, taskParam.result)"
                @mouseleave="store.scheduleHideJsonTooltip"
              >
                {{ store.formatResultSummary(taskParam.result) }}
              </span>
            </td>
            <td>
              <StatusBadge :status="taskParam.status" type="task" />
            </td>
            <td class="cell-ellipsis error-text" :title="taskParam.error || '-'">
              {{ taskParam.error || '-' }}
            </td>
            <td>{{ store.formatDateTime(taskParam.updated_at) }}</td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<style scoped src="./TaskResultTab.css"></style>

