import { computed, inject, onBeforeUnmount, onMounted, ref, type InjectionKey, type ShallowUnwrapRef } from 'vue'

import {
  batchDisableFlowParams,
  batchEnableFlowParams,
  batchResetFlowParams,
  clearFlowParams,
  deleteFlowParam,
  disableFlowParam,
  enableFlowParam,
  importFlowParams,
  listFlowParams,
  resetFlowParam,
} from '../../api/flowParams'
import { listFlows } from '../../api/flows'
import { listShops } from '../../api/shops'
import { listAvailableTasks } from '../../api/tasks'
import {
  batchDisableTaskParams,
  batchEnableTaskParams,
  batchResetTaskParams,
  clearTaskParams,
  deleteTaskParam,
  disableTaskParam,
  enableTaskParam,
  importTaskParamsCsv,
  listTaskParamBatchOptions,
  listTaskParamResults,
  listTaskParams,
  resetTaskParam,
} from '../../api/taskParams'
import type {
  AvailableTask,
  Flow,
  FlowParam,
  FlowParamBatchPayload,
  FlowParamFilters,
  FlowParamImportResult,
  Shop,
  TaskFieldSchema,
  TaskInputSchema,
  TaskParam,
  TaskParamBatchOption,
  TaskParamBatchPayload,
  TaskParamFilters,
  TaskParamImportResult,
} from '../../api/types'
import { toast } from '../../utils/toast'

export type BatchActionKey = '' | 'reset' | 'enable' | 'disable'
export type ImportBindingMode = 'task' | 'flow'
export type TabKey = 'taskList' | 'resultList' | 'flowParams'

type JsonTooltipState = {
  visible: boolean
  content: string
  left: number
  top: number
  width: number
}

type StepResultItem = {
  name: string
  status: string
  detail: Record<string, unknown>
}

const pageSize = 10
const tooltipMaxWidth = 500
const tooltipViewportPadding = 16
const tooltipGap = 10

function getSchemaFieldMap(schema?: TaskInputSchema | null): Record<string, TaskFieldSchema> {
  return schema?.model_fields ?? schema?.properties ?? {}
}

function getSchemaRequiredFields(schema?: TaskInputSchema | null): string[] {
  return schema?.required_fields ?? schema?.required ?? []
}

function normalizeJson(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>
  }

  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>
      }
    } catch {
      return {}
    }
  }

  return {}
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return '--'
  }

  const date = new Date(value.replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) {
    return '--'
  }

  return date.toLocaleString('zh-CN', { hour12: false })
}

function formatSummary(source: unknown, limit = 4) {
  const record = normalizeJson(source)
  const keys = Object.keys(record)
  if (keys.length === 0) {
    return '-'
  }

  return keys
    .slice(0, limit)
    .map((key) => `${key}: ${String(record[key] ?? '')}`)
    .join(' / ')
}

function useJsonTooltip() {
  const jsonTooltip = ref<JsonTooltipState>({
    visible: false,
    content: '-',
    left: 0,
    top: 0,
    width: tooltipMaxWidth,
  })

  let tooltipHideTimer: ReturnType<typeof setTimeout> | null = null

  function clearTooltipHideTimer() {
    if (tooltipHideTimer) {
      clearTimeout(tooltipHideTimer)
      tooltipHideTimer = null
    }
  }

  function formatJsonTooltip(source: unknown) {
    const record = normalizeJson(source)
    if (!Object.keys(record).length) {
      return '-'
    }
    return JSON.stringify(record, null, 2)
  }

  function showJsonTooltip(event: MouseEvent, source: unknown) {
    clearTooltipHideTimer()
    const currentTarget = event.currentTarget
    if (!(currentTarget instanceof HTMLElement)) {
      return
    }

    const rect = currentTarget.getBoundingClientRect()
    const tooltipWidth = Math.min(
      tooltipMaxWidth,
      Math.max(240, window.innerWidth - tooltipViewportPadding * 2),
    )
    const maxLeft = Math.max(
      tooltipViewportPadding,
      window.innerWidth - tooltipWidth - tooltipViewportPadding,
    )
    const maxTop = Math.max(
      tooltipViewportPadding,
      window.innerHeight - tooltipViewportPadding - 160,
    )

    jsonTooltip.value = {
      visible: true,
      content: formatJsonTooltip(source),
      left: Math.min(Math.max(rect.left, tooltipViewportPadding), maxLeft),
      top: Math.min(rect.bottom + tooltipGap, maxTop),
      width: tooltipWidth,
    }
  }

  function scheduleHideJsonTooltip() {
    clearTooltipHideTimer()
    tooltipHideTimer = window.setTimeout(() => {
      jsonTooltip.value.visible = false
      tooltipHideTimer = null
    }, 120)
  }

  function keepJsonTooltipOpen() {
    clearTooltipHideTimer()
  }

  function hideJsonTooltip() {
    clearTooltipHideTimer()
    jsonTooltip.value.visible = false
  }

  return {
    jsonTooltip,
    clearTooltipHideTimer,
    formatJsonTooltip,
    showJsonTooltip,
    scheduleHideJsonTooltip,
    keepJsonTooltipOpen,
    hideJsonTooltip,
  }
}

export function useTaskParamsStore() {
  const availableTasks = ref<AvailableTask[]>([])
  const flows = ref<Flow[]>([])
  const shops = ref<Shop[]>([])
  const batchOptions = ref<TaskParamBatchOption[]>([])
  const taskParams = ref<TaskParam[]>([])
  const resultTaskParams = ref<TaskParam[]>([])
  const flowParams = ref<FlowParam[]>([])
  const taskParamTotal = ref(0)
  const resultTotal = ref(0)
  const flowParamTotal = ref(0)
  const taskListPage = ref(1)
  const resultPage = ref(1)
  const flowParamPage = ref(1)
  const activeTab = ref<TabKey>('taskList')
  const loading = ref(false)
  const showImportModal = ref(false)
  const showClearConfirm = ref(false)
  const selectedFile = ref<File | null>(null)
  const importBindingMode = ref<ImportBindingMode>('task')
  const importTaskName = ref('')
  const importFlowId = ref('')
  const importing = ref(false)
  const importSummary = ref<TaskParamImportResult | FlowParamImportResult | null>(null)
  const rowActioningIds = ref<number[]>([])
  const batchAction = ref<BatchActionKey>('')
  const expandedStepResultKey = ref<string | null>(null)

  const taskListFilters = ref({ task_name: '', status: '', shop_id: '', batch_id: '' })
  const resultFilters = ref({
    task_name: '',
    status: '',
    shop_id: '',
    batch_id: '',
    updated_from: '',
    updated_to: '',
  })
  const flowParamFilters = ref({ flow_id: '', status: '', shop_id: '' })

  const {
    jsonTooltip,
    clearTooltipHideTimer,
    formatJsonTooltip,
    showJsonTooltip,
    scheduleHideJsonTooltip,
    keepJsonTooltipOpen,
    hideJsonTooltip,
  } = useJsonTooltip()

  const isTaskListTab = computed(() => activeTab.value === 'taskList')
  const isFlowParamsTab = computed(() => activeTab.value === 'flowParams')
  const totalPages = computed(() => {
    const totalCount = isTaskListTab.value
      ? taskParamTotal.value
      : isFlowParamsTab.value
        ? flowParamTotal.value
        : resultTotal.value
    return Math.max(1, Math.ceil(totalCount / pageSize))
  })
  const currentPage = computed(() => {
    if (activeTab.value === 'taskList') return taskListPage.value
    if (activeTab.value === 'flowParams') return flowParamPage.value
    return resultPage.value
  })
  const currentTotal = computed(() => {
    if (activeTab.value === 'taskList') return taskParamTotal.value
    if (activeTab.value === 'flowParams') return flowParamTotal.value
    return resultTotal.value
  })
  const taskOptions = computed(() => availableTasks.value.map((task) => task.name))
  const flowOptions = computed(() => flows.value)
  const currentTask = computed(
    () => availableTasks.value.find((task) => task.name === importTaskName.value) ?? null,
  )
  const currentTemplateColumns = computed(() => {
    const fields = importBindingMode.value === 'flow'
      ? collectFlowTemplateFields(importFlowId.value)
      : Object.keys(getSchemaFieldMap(currentTask.value?.input_schema))
    return ['店铺ID', ...fields]
  })
  const currentTemplateSampleRow = computed(() =>
    currentTemplateColumns.value.map((column) => (column === '店铺ID' ? '示例店铺名称' : '示例值')).join(','),
  )
  const currentTemplateExample = computed(() => {
    const dynamicColumns = currentTemplateColumns.value.slice(1)
    if (dynamicColumns.length === 0) {
      return '当前模板只包含店铺ID列。'
    }

    return importBindingMode.value === 'flow'
      ? `流程共享参数列：${dynamicColumns.join('、')}`
      : `任务参数列：${dynamicColumns.join('、')}`
  })
  const currentRequiredFields = computed(() => {
    if (importBindingMode.value === 'flow') {
      return collectFlowRequiredFields(importFlowId.value)
    }
    return getSchemaRequiredFields(currentTask.value?.input_schema)
  })
  const currentTemplateFileName = computed(() => {
    if (importBindingMode.value === 'flow') {
      const flowName = flows.value.find((flow) => flow.id === importFlowId.value)?.name || '流程参数'
      return `${flowName}_模板.csv`
    }

    return `${importTaskName.value || '任务参数'}_模板.csv`
  })
  const shopNameMap = computed<Record<string, string>>(() =>
    Object.fromEntries(shops.value.map((shop) => [shop.id, shop.name])),
  )

  function collectFlowTemplateFields(flowId: string) {
    const flow = flows.value.find((item) => item.id === flowId)
    const fieldMap = new Map<string, TaskFieldSchema>()

    for (const step of flow?.steps ?? []) {
      const task = availableTasks.value.find((item) => item.name === step.task)
      for (const [fieldName, schema] of Object.entries(getSchemaFieldMap(task?.input_schema))) {
        if (!fieldMap.has(fieldName)) {
          fieldMap.set(fieldName, schema)
        }
      }
    }

    return [...fieldMap.keys()]
  }

  function collectFlowRequiredFields(flowId: string) {
    const flow = flows.value.find((item) => item.id === flowId)
    const required = new Set<string>()

    for (const step of flow?.steps ?? []) {
      const task = availableTasks.value.find((item) => item.name === step.task)
      for (const fieldName of getSchemaRequiredFields(task?.input_schema)) {
        required.add(fieldName)
      }
    }

    return [...required]
  }

  function getDefaultImportTaskName(preferredTaskName = taskListFilters.value.task_name) {
    if (preferredTaskName && taskOptions.value.includes(preferredTaskName)) {
      return preferredTaskName
    }
    return taskOptions.value[0] || ''
  }

  function normalizeTaskFilters() {
    if (taskListFilters.value.task_name && !taskOptions.value.includes(taskListFilters.value.task_name)) {
      taskListFilters.value.task_name = ''
    }
    if (resultFilters.value.task_name && !taskOptions.value.includes(resultFilters.value.task_name)) {
      resultFilters.value.task_name = ''
    }
  }

  function syncImportTaskName(preferredTaskName = taskListFilters.value.task_name) {
    if (importTaskName.value && taskOptions.value.includes(importTaskName.value)) {
      return
    }
    importTaskName.value = getDefaultImportTaskName(preferredTaskName)
  }

  function syncImportFlowId() {
    if (importFlowId.value && flowOptions.value.some((flow) => flow.id === importFlowId.value)) {
      return
    }
    importFlowId.value = flowOptions.value[0]?.id || ''
  }

  function buildTaskListFilters(page = taskListPage.value): TaskParamFilters {
    return {
      page,
      page_size: pageSize,
      shop_id: taskListFilters.value.shop_id || undefined,
      task_name: taskListFilters.value.task_name || undefined,
      status: taskListFilters.value.status || undefined,
      batch_id: taskListFilters.value.batch_id || undefined,
      sort_by: 'created_at',
      sort_order: 'desc',
    }
  }

  function buildResultFilters(page = resultPage.value): TaskParamFilters {
    return {
      page,
      page_size: pageSize,
      shop_id: resultFilters.value.shop_id || undefined,
      task_name: resultFilters.value.task_name || undefined,
      status: resultFilters.value.status || 'success,failed',
      batch_id: resultFilters.value.batch_id || undefined,
      updated_from: resultFilters.value.updated_from || undefined,
      updated_to: resultFilters.value.updated_to || undefined,
      sort_by: 'updated_at',
      sort_order: 'desc',
    }
  }

  function buildFlowParamFilters(page = flowParamPage.value): FlowParamFilters {
    return {
      page,
      page_size: pageSize,
      shop_id: flowParamFilters.value.shop_id || undefined,
      flow_id: flowParamFilters.value.flow_id || undefined,
      status: flowParamFilters.value.status || undefined,
      sort_by: 'created_at',
      sort_order: 'desc',
    }
  }

  function buildBatchPayload(): TaskParamBatchPayload {
    return {
      shop_id: taskListFilters.value.shop_id || undefined,
      task_name: taskListFilters.value.task_name || undefined,
      status: taskListFilters.value.status || undefined,
      batch_id: taskListFilters.value.batch_id || undefined,
    }
  }

  function buildFlowParamBatchPayload(): FlowParamBatchPayload {
    return {
      shop_id: flowParamFilters.value.shop_id || undefined,
      flow_id: flowParamFilters.value.flow_id || undefined,
      status: flowParamFilters.value.status || undefined,
    }
  }

  function buildBatchOptionFilters(): TaskParamFilters {
    if (activeTab.value === 'taskList') {
      return {
        shop_id: taskListFilters.value.shop_id || undefined,
        task_name: taskListFilters.value.task_name || undefined,
        status: taskListFilters.value.status || undefined,
      }
    }

    return {
      shop_id: resultFilters.value.shop_id || undefined,
      task_name: resultFilters.value.task_name || undefined,
      status: resultFilters.value.status || 'success,failed',
    }
  }

  function hasExplicitBatchFilter() {
    return Boolean(
      taskListFilters.value.shop_id
      || taskListFilters.value.task_name
      || taskListFilters.value.status
      || taskListFilters.value.batch_id,
    )
  }

  function hasExplicitFlowParamFilter() {
    return Boolean(
      flowParamFilters.value.shop_id || flowParamFilters.value.flow_id || flowParamFilters.value.status,
    )
  }

  function isRowActioning(id: number) {
    return rowActioningIds.value.includes(id)
  }

  function setRowActioning(id: number, actioning: boolean) {
    if (actioning) {
      if (!rowActioningIds.value.includes(id)) {
        rowActioningIds.value = [...rowActioningIds.value, id]
      }
      return
    }

    rowActioningIds.value = rowActioningIds.value.filter((itemId) => itemId !== id)
  }

  function formatParamSummary(params: unknown) {
    return formatSummary(params, 4)
  }

  function formatResultSummary(result: unknown) {
    return formatSummary(result, 4)
  }

  function formatExecutionResult(result: unknown) {
    return formatSummary(result, 2)
  }

  function formatBatchOptionLabel(option: TaskParamBatchOption) {
    const latestDate = option.latest_updated_at ? option.latest_updated_at.slice(0, 10) : '--'
    return `批次 ${option.batch_id} (${latestDate}, ${option.record_count}条)`
  }

  function formatShopLabel(taskParam: TaskParam) {
    const shopName = shopNameMap.value[taskParam.shop_id] || taskParam.shop_name
    return shopName ? `${shopName}（${taskParam.shop_id}）` : `#${taskParam.shop_id}`
  }

  function formatFlowParamShopLabel(flowParam: FlowParam) {
    const shopName = shopNameMap.value[flowParam.shop_id] || flowParam.shop_name
    return shopName ? `${shopName}（${flowParam.shop_id}）` : `#${flowParam.shop_id}`
  }

  function getFlowName(flowId: string) {
    const matchedFlow = flows.value.find((flow) => flow.id === flowId)
    return matchedFlow?.name || flowId.slice(0, 8)
  }

  function formatFlowProgress(flowParam: FlowParam) {
    const matchedFlow = flows.value.find((flow) => flow.id === flowParam.flow_id)
    return `${flowParam.current_step} / ${matchedFlow?.steps.length || '?'}`
  }

  function formatStepResultsSummary(stepResults: unknown) {
    const record = normalizeJson(stepResults)
    const stepNames = Object.keys(record)
    if (!stepNames.length) {
      return '-'
    }
    return stepNames.slice(0, 3).join(' / ')
  }

  function getStepResultItems(stepResults: unknown): StepResultItem[] {
    const record = normalizeJson(stepResults)
    return Object.entries(record).map(([name, rawDetail]) => {
      const detail = normalizeJson(rawDetail)
      return { name, status: String(detail.status || 'pending'), detail }
    })
  }

  function formatStepResultTag(step: StepResultItem) {
    const iconMap: Record<string, string> = {
      completed: '✓',
      failed: '✕',
      running: '…',
      waiting_barrier: '…',
      merged_skip: '↷',
    }
    return `${step.name} ${iconMap[step.status] || '…'}`
  }

  function getStepResultStatusClass(status: string) {
    const statusMap: Record<string, string> = {
      completed: 'bg-emerald-100 text-emerald-800',
      failed: 'bg-rose-100 text-rose-800',
      running: 'bg-amber-100 text-amber-800',
      waiting_barrier: 'bg-brand-100 text-brand-700',
      merged_skip: 'bg-brand-300/40 text-brand-700',
    }
    return statusMap[status] || 'bg-brand-100 text-brand-700'
  }

  function getStepResultToggleKey(flowParamId: number, stepName: string) {
    return `${flowParamId}:${stepName}`
  }

  function toggleStepResultDetail(flowParamId: number, stepName: string) {
    const targetKey = getStepResultToggleKey(flowParamId, stepName)
    expandedStepResultKey.value = expandedStepResultKey.value === targetKey ? null : targetKey
  }

  function isStepResultDetailOpen(flowParamId: number, stepName: string) {
    return expandedStepResultKey.value === getStepResultToggleKey(flowParamId, stepName)
  }

  function replaceTaskParam(updatedTaskParam: TaskParam) {
    taskParams.value = taskParams.value.map((taskParam) => taskParam.id === updatedTaskParam.id ? updatedTaskParam : taskParam)
    resultTaskParams.value = resultTaskParams.value.map((taskParam) => taskParam.id === updatedTaskParam.id ? updatedTaskParam : taskParam)
  }

  async function loadShops() {
    try {
      const result = await listShops()
      shops.value = result.list
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '加载店铺列表失败')
    }
  }

  async function loadAvailableTaskOptions() {
    try {
      availableTasks.value = await listAvailableTasks()
      normalizeTaskFilters()
      syncImportTaskName()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '加载任务类型失败')
    }
  }

  async function loadFlows() {
    try {
      const result = await listFlows()
      flows.value = result.list
      syncImportFlowId()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '加载流程列表失败')
    }
  }

  async function loadBatchOptions() {
    try {
      batchOptions.value = await listTaskParamBatchOptions(buildBatchOptionFilters())
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '加载批次列表失败')
    }
  }

  async function loadTaskParams(page = taskListPage.value) {
    loading.value = true
    try {
      const result = await listTaskParams(buildTaskListFilters(page))
      taskListPage.value = page
      taskParams.value = result.list
      taskParamTotal.value = result.total
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '加载任务参数失败')
    } finally {
      loading.value = false
    }
  }

  async function loadResultTaskParams(page = resultPage.value) {
    loading.value = true
    try {
      const result = await listTaskParamResults(buildResultFilters(page))
      resultPage.value = page
      resultTaskParams.value = result.list
      resultTotal.value = result.total
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '加载执行结果失败')
    } finally {
      loading.value = false
    }
  }

  async function loadFlowParams(page = flowParamPage.value) {
    loading.value = true
    try {
      const result = await listFlowParams(buildFlowParamFilters(page))
      flowParamPage.value = page
      flowParams.value = result.list
      flowParamTotal.value = result.total
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '加载流程参数失败')
    } finally {
      loading.value = false
    }
  }

  function handleTaskListSearch() {
    void loadBatchOptions()
    void loadTaskParams(1)
  }

  function handleResultSearch() {
    void loadBatchOptions()
    void loadResultTaskParams(1)
  }

  function handleFlowParamSearch() {
    void loadFlowParams(1)
  }

  function handleTabChange(tab: TabKey) {
    if (activeTab.value === tab) {
      return
    }

    activeTab.value = tab
    if (tab === 'flowParams') {
      void loadFlowParams(1)
      return
    }

    void loadBatchOptions()
    if (tab === 'taskList') {
      void loadTaskParams(1)
      return
    }

    void loadResultTaskParams(1)
  }

  function handlePageChange(page: number) {
    if (page < 1 || page > totalPages.value) {
      return
    }

    if (activeTab.value === 'taskList') {
      void loadTaskParams(page)
      return
    }

    if (activeTab.value === 'flowParams') {
      void loadFlowParams(page)
      return
    }

    void loadResultTaskParams(page)
  }

  function openImportModal() {
    if (taskOptions.value.length === 0 && flowOptions.value.length === 0) {
      toast.warning('暂无可导入的任务类型或流程')
      return
    }

    if (importBindingMode.value === 'task' && taskOptions.value.length === 0 && flowOptions.value.length > 0) {
      importBindingMode.value = 'flow'
    }

    if (importBindingMode.value === 'flow' && flowOptions.value.length === 0 && taskOptions.value.length > 0) {
      importBindingMode.value = 'task'
    }

    if (importBindingMode.value === 'task' && taskOptions.value.length === 0) {
      toast.warning('暂无可导入的任务类型')
      return
    }

    if (importBindingMode.value === 'flow' && flowOptions.value.length === 0) {
      toast.warning('暂无可绑定的流程')
      return
    }

    importTaskName.value = getDefaultImportTaskName()
    syncImportFlowId()
    selectedFile.value = null
    importSummary.value = null
    showImportModal.value = true
  }

  function closeImportModal() {
    showImportModal.value = false
  }

  function handleFileChange(event: Event) {
    const input = event.target as HTMLInputElement
    selectedFile.value = input.files?.[0] ?? null
  }

  async function handleImport() {
    if (importBindingMode.value === 'task' && !importTaskName.value) {
      toast.warning('请选择任务类型')
      return false
    }

    if (importBindingMode.value === 'flow' && !importFlowId.value) {
      toast.warning('请选择流程')
      return false
    }

    if (!selectedFile.value) {
      toast.warning('请选择 CSV 文件')
      return false
    }

    importing.value = true
    try {
      const result = importBindingMode.value === 'task'
        ? await importTaskParamsCsv(importTaskName.value, selectedFile.value)
        : await importFlowParams(importFlowId.value, selectedFile.value)
      importSummary.value = result
      toast.success(`导入完成：成功 ${result.success_count} 条，跳过 ${result.failed_count} 条`)
      return true
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '导入 CSV 失败')
      return false
    } finally {
      importing.value = false
    }
  }

  async function refreshAfterImport(mode = importBindingMode.value) {
    if (mode === 'task') {
      await loadTaskParams(1)
      await loadBatchOptions()
      return
    }

    activeTab.value = 'flowParams'
    await loadFlowParams(1)
  }

  async function handleToggleFlowParamEnabled(flowParam: FlowParam) {
    setRowActioning(flowParam.id, true)
    try {
      const updatedFlowParam = flowParam.enabled ? await disableFlowParam(flowParam.id) : await enableFlowParam(flowParam.id)
      flowParams.value = flowParams.value.map((item) => (item.id === updatedFlowParam.id ? updatedFlowParam : item))
      toast.success(flowParam.enabled ? '流程参数已禁用' : '流程参数已启用')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '切换流程参数启用状态失败')
      await loadFlowParams(flowParamPage.value)
    } finally {
      setRowActioning(flowParam.id, false)
    }
  }

  async function handleResetFlowParam(flowParam: FlowParam) {
    setRowActioning(flowParam.id, true)
    try {
      const updatedFlowParam = await resetFlowParam(flowParam.id)
      flowParams.value = flowParams.value.map((item) => (item.id === updatedFlowParam.id ? updatedFlowParam : item))
      toast.success('流程参数已重置为待执行')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '重置流程参数失败')
    } finally {
      setRowActioning(flowParam.id, false)
    }
  }

  async function handleDeleteFlowParam(id: number) {
    setRowActioning(id, true)
    try {
      await deleteFlowParam(id)
      toast.success('流程参数已删除')
      if (flowParams.value.length === 1 && flowParamPage.value > 1) {
        await loadFlowParams(flowParamPage.value - 1)
      } else {
        await loadFlowParams(flowParamPage.value)
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '删除流程参数失败')
    } finally {
      setRowActioning(id, false)
    }
  }

  async function handleToggleTaskParamEnabled(taskParam: TaskParam) {
    setRowActioning(taskParam.id, true)
    try {
      const updatedTaskParam = taskParam.enabled ? await disableTaskParam(taskParam.id) : await enableTaskParam(taskParam.id)
      replaceTaskParam(updatedTaskParam)
      toast.success(taskParam.enabled ? '记录已禁用' : '记录已启用')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '切换启用状态失败')
      await loadTaskParams(taskListPage.value)
    } finally {
      setRowActioning(taskParam.id, false)
    }
  }

  async function handleResetTaskParam(taskParam: TaskParam) {
    setRowActioning(taskParam.id, true)
    try {
      const updatedTaskParam = await resetTaskParam(taskParam.id)
      replaceTaskParam(updatedTaskParam)
      toast.success('记录已重置为待执行')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '重置记录失败')
    } finally {
      setRowActioning(taskParam.id, false)
    }
  }

  async function handleDeleteTaskParam(id: number) {
    setRowActioning(id, true)
    try {
      await deleteTaskParam(id)
      toast.success('记录已删除')
      if (taskParams.value.length === 1 && taskListPage.value > 1) {
        await loadTaskParams(taskListPage.value - 1)
      } else {
        await loadTaskParams(taskListPage.value)
      }
      await loadBatchOptions()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '删除记录失败')
    } finally {
      setRowActioning(id, false)
    }
  }

  async function handleClear() {
    try {
      const result = activeTab.value === 'flowParams'
        ? await clearFlowParams(buildFlowParamFilters())
        : await clearTaskParams(buildTaskListFilters())
      toast.success(`已清空 ${result.deleted_count} 条记录`)
      showClearConfirm.value = false
      if (activeTab.value === 'flowParams') {
        await loadFlowParams(1)
        return
      }

      await loadTaskParams(1)
      await loadBatchOptions()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '清空记录失败')
    }
  }

  async function runBatchAction(action: Exclude<BatchActionKey, ''>) {
    if (action !== 'reset' && !hasExplicitBatchFilter()) {
      toast.warning('批量启用或批量禁用前，请至少选择一个筛选条件')
      return
    }

    batchAction.value = action
    const payload = buildBatchPayload()

    try {
      if (action === 'reset') {
        const result = await batchResetTaskParams(payload)
        toast.success(`已重置 ${result.updated_count} 条记录`)
      }
      if (action === 'enable') {
        const result = await batchEnableTaskParams(payload)
        toast.success(`已启用 ${result.updated_count} 条记录`)
      }
      if (action === 'disable') {
        const result = await batchDisableTaskParams(payload)
        toast.success(`已禁用 ${result.updated_count} 条记录`)
      }

      await loadTaskParams(1)
      await loadBatchOptions()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '批量操作失败')
    } finally {
      batchAction.value = ''
    }
  }

  async function runFlowParamBatchAction(action: Exclude<BatchActionKey, ''>) {
    if (action !== 'reset' && !hasExplicitFlowParamFilter()) {
      toast.warning('批量启用或批量禁用前，请至少选择一个筛选条件')
      return
    }

    batchAction.value = action
    const payload = buildFlowParamBatchPayload()

    try {
      if (action === 'reset') {
        const result = await batchResetFlowParams(payload)
        toast.success(`已重置 ${result.updated_count} 条流程参数`)
      }
      if (action === 'enable') {
        const result = await batchEnableFlowParams(payload)
        toast.success(`已启用 ${result.updated_count} 条流程参数`)
      }
      if (action === 'disable') {
        const result = await batchDisableFlowParams(payload)
        toast.success(`已禁用 ${result.updated_count} 条流程参数`)
      }

      await loadFlowParams(1)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '批量操作失败')
    } finally {
      batchAction.value = ''
    }
  }

  function downloadTemplate() {
    const rows = [currentTemplateColumns.value.join(','), currentTemplateSampleRow.value]
    const blob = new Blob([`\uFEFF${rows.join('\n')}`], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = currentTemplateFileName.value
    link.click()
    URL.revokeObjectURL(link.href)
  }

  onMounted(() => {
    void loadAvailableTaskOptions()
    void loadFlows()
    void loadShops()
    void loadBatchOptions()
    void loadTaskParams()
  })

  onBeforeUnmount(() => {
    clearTooltipHideTimer()
  })

  return {
    activeTab,
    availableTasks,
    batchAction,
    batchOptions,
    closeImportModal,
    currentPage,
    currentRequiredFields,
    currentTemplateColumns,
    currentTemplateExample,
    currentTemplateFileName,
    currentTemplateSampleRow,
    currentTotal,
    downloadTemplate,
    expandedStepResultKey,
    flowOptions,
    flowParamFilters,
    flowParamPage,
    flowParamTotal,
    flowParams,
    flows,
    formatBatchOptionLabel,
    formatDateTime,
    formatExecutionResult,
    formatFlowParamShopLabel,
    formatFlowProgress,
    formatJsonTooltip,
    formatParamSummary,
    formatResultSummary,
    formatShopLabel,
    formatStepResultTag,
    formatStepResultsSummary,
    getFlowName,
    getStepResultItems,
    getStepResultStatusClass,
    handleClear,
    handleDeleteFlowParam,
    handleDeleteTaskParam,
    handleFileChange,
    handleFlowParamSearch,
    handleImport,
    handlePageChange,
    handleResetFlowParam,
    handleResetTaskParam,
    handleResultSearch,
    handleTabChange,
    handleTaskListSearch,
    handleToggleFlowParamEnabled,
    handleToggleTaskParamEnabled,
    hideJsonTooltip,
    importBindingMode,
    importFlowId,
    importSummary,
    importTaskName,
    importing,
    isFlowParamsTab,
    isRowActioning,
    isStepResultDetailOpen,
    isTaskListTab,
    jsonTooltip,
    keepJsonTooltipOpen,
    loading,
    openImportModal,
    refreshAfterImport,
    resultFilters,
    resultPage,
    resultTaskParams,
    resultTotal,
    rowActioningIds,
    runBatchAction,
    runFlowParamBatchAction,
    scheduleHideJsonTooltip,
    selectedFile,
    shopNameMap,
    shops,
    showClearConfirm,
    showImportModal,
    showJsonTooltip,
    taskListFilters,
    taskListPage,
    taskOptions,
    taskParamTotal,
    taskParams,
    totalPages,
    toggleStepResultDetail,
  }
}

export type TaskParamsStore = ShallowUnwrapRef<ReturnType<typeof useTaskParamsStore>>

export const taskParamsStoreKey: InjectionKey<TaskParamsStore> = Symbol('task-params-store')

export function useTaskParamsContext() {
  const store = inject(taskParamsStoreKey)
  if (!store) {
    throw new Error('Task params store has not been provided')
  }
  return store
}
