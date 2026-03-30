<script setup lang="ts">
import { computed, provide, proxyRefs } from 'vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import type { FlowParam, TaskParam } from '../api/types'
import FlowParamsTab from './task-params/FlowParamsTab.vue'
import ImportCsvModal from './task-params/ImportCsvModal.vue'
import JsonTooltip from './task-params/JsonTooltip.vue'
import TaskListTab from './task-params/TaskListTab.vue'
import TaskResultTab from './task-params/TaskResultTab.vue'
import { taskParamsStoreKey, useTaskParamsStore, type BatchActionKey, type TabKey } from './task-params/useTaskParamsStore'

const props = withDefaults(defineProps<{ showTitle?: boolean }>(), { showTitle: true })
const store = proxyRefs(useTaskParamsStore())
provide(taskParamsStoreKey, store)

const tabLabels: Array<{ key: TabKey; label: string }> = [
  { key: 'taskList', label: '任务列表' },
  { key: 'resultList', label: '执行结果' },
  { key: 'flowParams', label: '流程参数' },
]

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
  <div class="task-params-manage">
    <div class="header">
      <div v-if="props.showTitle">
        <h1>任务参数管理</h1>
        <p class="header-tip">导入后的记录会长期保留，可按需禁用、重置或查看执行结果。</p>
      </div>
      <div v-if="canManageCurrentTab" class="header-actions">
        <button class="btn btn-secondary" @click="store.showClearConfirm = true">清空</button>
        <button class="btn btn-primary" @click="store.openImportModal">导入CSV</button>
      </div>
    </div>

    <div class="tabs">
      <button v-for="tab in tabLabels" :key="tab.key" class="tab-button" :class="{ 'is-active': store.activeTab === tab.key }" @click="store.handleTabChange(tab.key)">
        {{ tab.label }}
      </button>
    </div>

    <div v-if="store.isTaskListTab" class="filters">
      <select v-model="store.taskListFilters.task_name" class="filter-select" @change="store.handleTaskListSearch">
        <option value="">全部任务类型</option>
        <option v-for="task in store.availableTasks" :key="task.name" :value="task.name">{{ task.name }}</option>
      </select>
      <select v-model="store.taskListFilters.status" class="filter-select" @change="store.handleTaskListSearch">
        <option value="">全部状态</option><option value="pending">待执行</option><option value="running">执行中</option><option value="success">成功</option><option value="failed">失败</option><option value="skipped">跳过</option>
      </select>
      <select v-model="store.taskListFilters.shop_id" class="filter-select" @change="store.handleTaskListSearch">
        <option value="">全部店铺</option>
        <option v-for="shop in store.shops" :key="shop.id" :value="shop.id">{{ shop.name }}（{{ shop.id }}）</option>
      </select>
      <select v-model="store.taskListFilters.batch_id" class="filter-select" @change="store.handleTaskListSearch">
        <option value="">全部批次</option>
        <option v-for="option in store.batchOptions" :key="option.batch_id" :value="option.batch_id">{{ store.formatBatchOptionLabel(option) }}</option>
      </select>
      <button class="btn btn-light" @click="store.handleTaskListSearch">刷新</button>
    </div>

    <div v-else-if="store.activeTab === 'resultList'" class="filters">
      <select v-model="store.resultFilters.task_name" class="filter-select" @change="store.handleResultSearch">
        <option value="">全部任务类型</option>
        <option v-for="task in store.availableTasks" :key="task.name" :value="task.name">{{ task.name }}</option>
      </select>
      <select v-model="store.resultFilters.status" class="filter-select" @change="store.handleResultSearch">
        <option value="">全部执行状态</option><option value="success">成功</option><option value="failed">失败</option><option value="running">执行中</option><option value="cancelled">已取消</option>
      </select>
      <select v-model="store.resultFilters.shop_id" class="filter-select" @change="store.handleResultSearch">
        <option value="">全部店铺</option>
        <option v-for="shop in store.shops" :key="shop.id" :value="shop.id">{{ shop.name }}（{{ shop.id }}）</option>
      </select>
      <select v-model="store.resultFilters.batch_id" class="filter-select" @change="store.handleResultSearch">
        <option value="">全部批次</option>
        <option v-for="option in store.batchOptions" :key="option.batch_id" :value="option.batch_id">{{ store.formatBatchOptionLabel(option) }}</option>
      </select>
      <input v-model="store.resultFilters.updated_from" class="filter-date" type="date" @change="store.handleResultSearch" />
      <input v-model="store.resultFilters.updated_to" class="filter-date" type="date" @change="store.handleResultSearch" />
      <button class="btn btn-light" @click="store.handleResultSearch">刷新</button>
    </div>

    <div v-else class="filters">
      <select v-model="store.flowParamFilters.flow_id" class="filter-select" @change="store.handleFlowParamSearch">
        <option value="">全部流程</option>
        <option v-for="flow in store.flows" :key="flow.id" :value="flow.id">{{ flow.name }}</option>
      </select>
      <select v-model="store.flowParamFilters.status" class="filter-select" @change="store.handleFlowParamSearch">
        <option value="">全部状态</option><option value="pending">待执行</option><option value="running">执行中</option><option value="success">成功</option><option value="failed">失败</option>
      </select>
      <select v-model="store.flowParamFilters.shop_id" class="filter-select" @change="store.handleFlowParamSearch">
        <option value="">全部店铺</option>
        <option v-for="shop in store.shops" :key="shop.id" :value="shop.id">{{ shop.name }}（{{ shop.id }}）</option>
      </select>
      <button class="btn btn-light" @click="store.handleFlowParamSearch">刷新</button>
    </div>

    <component :is="currentTabComponent" v-bind="currentTabProps" @toggle-enabled="handleToggleEnabled" @reset="handleReset" @delete="handleDelete" @batch-action="handleBatchAction" />

    <div class="pagination">
      <button class="btn-page" :disabled="store.currentPage <= 1" @click="store.handlePageChange(store.currentPage - 1)">上一页</button>
      <span class="page-info">第 {{ store.currentPage }} / {{ store.totalPages }} 页，共 {{ store.currentTotal }} 条</span>
      <button class="btn-page" :disabled="store.currentPage >= store.totalPages" @click="store.handlePageChange(store.currentPage + 1)">下一页</button>
    </div>

    <ImportCsvModal :show="store.showImportModal" :available-tasks="store.availableTasks" :flows="store.flows" :import-binding-mode="store.importBindingMode" @close="store.closeImportModal" @imported="handleImported" />
    <ConfirmDialog :show="store.showClearConfirm" title="确认清空" message="确定要按当前筛选条件清空记录吗？" type="danger" @confirm="store.handleClear" @cancel="store.showClearConfirm = false" />
    <JsonTooltip />
  </div>
</template>

<style scoped src="./task-params/TaskParamsManage.css"></style>
