<script setup lang="ts">
import { computed, provide, proxyRefs } from 'vue'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import type { FlowParam, TaskParam } from '../api/types'
import FlowParamsTab from './task-params/FlowParamsTab.vue'
import ImportCsvModal from './task-params/ImportCsvModal.vue'
import JsonTooltip from './task-params/JsonTooltip.vue'
import TaskListTab from './task-params/TaskListTab.vue'
import TaskResultTab from './task-params/TaskResultTab.vue'
import { taskParamsStoreKey, type BatchActionKey, type TabKey, useTaskParamsStore } from './task-params/useTaskParamsStore'

const props = withDefaults(defineProps<{ showTitle?: boolean }>(), { showTitle: true })
const store = proxyRefs(useTaskParamsStore())
provide(taskParamsStoreKey, store)

const tabLabels: Array<{ key: TabKey; label: string }> = [
  { key: 'taskList', label: '任务列表' },
  { key: 'resultList', label: '执行结果' },
  { key: 'flowParams', label: '流程参数' },
]
const filterClass =
  'rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'
const secondaryButtonClass =
  'rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 transition hover:bg-gray-50'
const primaryButtonClass =
  'rounded-md bg-brand-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-brand-700'

const currentTabComponent = computed(() =>
  store.activeTab === 'flowParams' ? FlowParamsTab : store.activeTab === 'resultList' ? TaskResultTab : TaskListTab,
)
const currentTabProps = computed(() => {
  if (store.activeTab === 'flowParams') return { flowParams: store.flowParams, loading: store.loading, flows: store.flows, shopNameMap: store.shopNameMap }
  if (store.activeTab === 'resultList') return { resultTaskParams: store.resultTaskParams, loading: store.loading, shopNameMap: store.shopNameMap }
  return { taskParams: store.taskParams, loading: store.loading, shopNameMap: store.shopNameMap }
})
const canManageCurrentTab = computed(() => store.isTaskListTab || store.isFlowParamsTab)

function handleToggleEnabled(record: TaskParam | FlowParam) {
  if (store.activeTab === 'flowParams') return void store.handleToggleFlowParamEnabled(record as FlowParam)
  void store.handleToggleTaskParamEnabled(record as TaskParam)
}

function handleReset(record: TaskParam | FlowParam) {
  if (store.activeTab === 'flowParams') return void store.handleResetFlowParam(record as FlowParam)
  void store.handleResetTaskParam(record as TaskParam)
}

function handleDelete(id: number) {
  if (store.activeTab === 'flowParams') return void store.handleDeleteFlowParam(id)
  void store.handleDeleteTaskParam(id)
}

function handleBatchAction(action: Exclude<BatchActionKey, ''>) {
  if (store.activeTab === 'flowParams') return void store.runFlowParamBatchAction(action)
  void store.runBatchAction(action)
}

function handleImported() {
  void store.refreshAfterImport()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div v-if="props.showTitle" class="space-y-1">
        <h1 class="text-lg font-semibold text-gray-900">任务参数管理</h1>
        <p class="text-xs text-gray-500">导入后的记录会长期保留，可按需筛选、禁用、重置或查看执行结果。</p>
      </div>
      <div v-if="canManageCurrentTab" class="flex flex-wrap gap-2">
        <button type="button" :class="secondaryButtonClass" @click="store.showClearConfirm = true">清空</button>
        <button type="button" :class="primaryButtonClass" @click="store.openImportModal">导入 CSV</button>
      </div>
    </div>

    <div class="flex flex-wrap gap-1 rounded-md bg-brand-200/30 p-0.5">
      <button v-for="tab in tabLabels" :key="tab.key" type="button" :class="['rounded-md px-3 py-2 text-sm transition', store.activeTab === tab.key ? 'bg-white font-medium text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700']" @click="store.handleTabChange(tab.key)">
        {{ tab.label }}
      </button>
    </div>

    <div v-if="store.isTaskListTab" class="grid gap-3 rounded-md border border-brand-200/50 bg-white p-4 shadow-sm lg:grid-cols-5">
      <select v-model="store.taskListFilters.task_name" :class="filterClass" @change="store.handleTaskListSearch"><option value="">全部任务类型</option><option v-for="task in store.availableTasks" :key="task.name" :value="task.name">{{ task.name }}</option></select>
      <select v-model="store.taskListFilters.status" :class="filterClass" @change="store.handleTaskListSearch"><option value="">全部状态</option><option value="pending">待执行</option><option value="running">执行中</option><option value="success">成功</option><option value="failed">失败</option><option value="skipped">跳过</option></select>
      <select v-model="store.taskListFilters.shop_id" :class="filterClass" @change="store.handleTaskListSearch"><option value="">全部店铺</option><option v-for="shop in store.shops" :key="shop.id" :value="shop.id">{{ shop.name }}（{{ shop.id }}）</option></select>
      <select v-model="store.taskListFilters.batch_id" :class="filterClass" @change="store.handleTaskListSearch"><option value="">全部批次</option><option v-for="option in store.batchOptions" :key="option.batch_id" :value="option.batch_id">{{ store.formatBatchOptionLabel(option) }}</option></select>
      <button type="button" :class="secondaryButtonClass" @click="store.handleTaskListSearch">刷新</button>
    </div>

    <div v-else-if="store.activeTab === 'resultList'" class="grid gap-3 rounded-md border border-brand-200/50 bg-white p-4 shadow-sm lg:grid-cols-6">
      <select v-model="store.resultFilters.task_name" :class="filterClass" @change="store.handleResultSearch"><option value="">全部任务类型</option><option v-for="task in store.availableTasks" :key="task.name" :value="task.name">{{ task.name }}</option></select>
      <select v-model="store.resultFilters.status" :class="filterClass" @change="store.handleResultSearch"><option value="">全部执行状态</option><option value="success">成功</option><option value="failed">失败</option><option value="running">执行中</option><option value="cancelled">已取消</option></select>
      <select v-model="store.resultFilters.shop_id" :class="filterClass" @change="store.handleResultSearch"><option value="">全部店铺</option><option v-for="shop in store.shops" :key="shop.id" :value="shop.id">{{ shop.name }}（{{ shop.id }}）</option></select>
      <select v-model="store.resultFilters.batch_id" :class="filterClass" @change="store.handleResultSearch"><option value="">全部批次</option><option v-for="option in store.batchOptions" :key="option.batch_id" :value="option.batch_id">{{ store.formatBatchOptionLabel(option) }}</option></select>
      <input v-model="store.resultFilters.updated_from" :class="filterClass" type="date" @change="store.handleResultSearch" />
      <input v-model="store.resultFilters.updated_to" :class="filterClass" type="date" @change="store.handleResultSearch" />
    </div>

    <div v-else class="grid gap-3 rounded-md border border-brand-200/50 bg-white p-4 shadow-sm lg:grid-cols-4">
      <select v-model="store.flowParamFilters.flow_id" :class="filterClass" @change="store.handleFlowParamSearch"><option value="">全部流程</option><option v-for="flow in store.flows" :key="flow.id" :value="flow.id">{{ flow.name }}</option></select>
      <select v-model="store.flowParamFilters.status" :class="filterClass" @change="store.handleFlowParamSearch"><option value="">全部状态</option><option value="pending">待执行</option><option value="running">执行中</option><option value="success">成功</option><option value="failed">失败</option></select>
      <select v-model="store.flowParamFilters.shop_id" :class="filterClass" @change="store.handleFlowParamSearch"><option value="">全部店铺</option><option v-for="shop in store.shops" :key="shop.id" :value="shop.id">{{ shop.name }}（{{ shop.id }}）</option></select>
      <button type="button" :class="secondaryButtonClass" @click="store.handleFlowParamSearch">刷新</button>
    </div>

    <component :is="currentTabComponent" v-bind="currentTabProps" @toggle-enabled="handleToggleEnabled" @reset="handleReset" @delete="handleDelete" @batch-action="handleBatchAction" />

    <div class="flex flex-col gap-3 rounded-md border border-brand-200/50 bg-white px-4 py-3 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <span class="text-xs text-gray-500">第 {{ store.currentPage }} / {{ store.totalPages }} 页，共 {{ store.currentTotal }} 条</span>
      <div class="flex gap-2">
        <button type="button" :class="secondaryButtonClass" :disabled="store.currentPage <= 1" @click="store.handlePageChange(store.currentPage - 1)">上一页</button>
        <button type="button" :class="secondaryButtonClass" :disabled="store.currentPage >= store.totalPages" @click="store.handlePageChange(store.currentPage + 1)">下一页</button>
      </div>
    </div>

    <ImportCsvModal :show="store.showImportModal" :available-tasks="store.availableTasks" :flows="store.flows" :import-binding-mode="store.importBindingMode" @close="store.closeImportModal" @imported="handleImported" />
    <ConfirmDialog :show="store.showClearConfirm" title="确认清空" message="确定要按当前筛选条件清空记录吗？" type="danger" @confirm="store.handleClear" @cancel="store.showClearConfirm = false" />
    <JsonTooltip />
  </div>
</template>
