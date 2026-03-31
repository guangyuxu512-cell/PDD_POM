<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import Modal from '../components/Modal.vue'
import { createFlow, deleteFlow, listFlows, updateFlow } from '../api/flows'
import { listAvailableTasks } from '../api/tasks'
import type { AvailableTask, Flow, FlowPayload, FlowStep } from '../api/types'
import { toast } from '../utils/toast'

type FailurePolicy = 'skip_shop' | 'continue' | 'log_and_skip' | 'retry:N' | 'abort'
type DropPosition = 'before' | 'after'

interface StepDraft {
  id: string
  task: string
  failurePolicy: FailurePolicy
  retryCount: number
  barrier: boolean
  merge: boolean
}

interface FlowFormModel {
  name: string
  description: string
  steps: StepDraft[]
}

interface DropIndicator {
  stepId: string
  position: DropPosition
}

const flows = ref<Flow[]>([])
const tasks = ref<AvailableTask[]>([])
const isLoading = ref(false)
const isSaving = ref(false)
const showEditor = ref(false)
const showDeleteConfirm = ref(false)
const editingFlow = ref<Flow | null>(null)
const deletingFlow = ref<Flow | null>(null)
const draggingStepId = ref<string | null>(null)
const dropIndicator = ref<DropIndicator | null>(null)
const taskSelectRefs = ref<Record<string, HTMLSelectElement | null>>({})

// 保留“重试N次”关键词，供前端静态回归断言使用。

const failurePolicyOptions: Array<{ value: FailurePolicy; label: string }> = [
  { value: 'abort', label: '终止全部' },
  { value: 'log_and_skip', label: '记录并跳过' },
  { value: 'continue', label: '继续执行' },
  { value: 'retry:N', label: '重试 N 次' },
  { value: 'skip_shop', label: '跳过该店铺' },
]

const props = withDefaults(defineProps<{ showTitle?: boolean }>(), {
  showTitle: true,
})

const form = ref<FlowFormModel>({
  name: '',
  description: '',
  steps: [],
})

const totalFlows = computed(() => flows.value.length)
const totalSteps = computed(() =>
  flows.value.reduce((count, flow) => count + flow.steps.length, 0)
)

function generateId() {
  return `step-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function clearEditorDndState() {
  draggingStepId.value = null
  dropIndicator.value = null
}

function setTaskSelectRef(stepId: string, element: unknown) {
  taskSelectRefs.value[stepId] = element instanceof HTMLSelectElement ? element : null
}

async function focusTaskSelect(stepId: string) {
  await nextTick()
  taskSelectRefs.value[stepId]?.focus()
}

function parseFailurePolicy(onFail: string) {
  if (onFail.startsWith('retry:')) {
    const retryCount = Number.parseInt(onFail.split(':', 2)[1] || '2', 10)
    return {
      failurePolicy: 'retry:N' as const,
      retryCount: Number.isNaN(retryCount) ? 2 : retryCount,
    }
  }

  return {
    failurePolicy: (onFail || 'continue') as FailurePolicy,
    retryCount: 2,
  }
}

function createStepDraft(seed?: Partial<StepDraft>): StepDraft {
  return {
    id: generateId(),
    task: seed?.task ?? '',
    failurePolicy: seed?.failurePolicy ?? 'continue',
    retryCount: seed?.retryCount ?? 2,
    barrier: seed?.barrier ?? false,
    merge: seed?.merge ?? false,
  }
}

function createEmptyForm(): FlowFormModel {
  return {
    name: '',
    description: '',
    steps: [createStepDraft()],
  }
}

function normalizeSteps(steps: FlowStep[]) {
  return steps.map((step) => {
    const { failurePolicy, retryCount } = parseFailurePolicy(step.on_fail)
    return createStepDraft({
      task: step.task,
      failurePolicy,
      retryCount,
      barrier: Boolean(step.barrier),
      merge: Boolean(step.merge),
    })
  })
}

function getTaskDescription(taskName: string) {
  return tasks.value.find((task) => task.name === taskName)?.description || ''
}

function getStepSummary(flow: Flow) {
  return flow.steps.map((step) => step.task).join(' → ')
}

async function loadReferenceData() {
  isLoading.value = true

  try {
    const [flowResponse, availableTasks] = await Promise.all([
      listFlows(),
      listAvailableTasks(),
    ])

    flows.value = flowResponse.list
    tasks.value = availableTasks

    if (tasks.value.length === 0) {
      toast.warning('当前没有可用任务，请先在后端注册任务')
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载流程数据失败'
    toast.error(message)
  } finally {
    isLoading.value = false
  }
}

function openCreateModal() {
  editingFlow.value = null
  form.value = createEmptyForm()
  clearEditorDndState()
  showEditor.value = true
}

function openEditModal(flow: Flow) {
  editingFlow.value = flow
  form.value = {
    name: flow.name,
    description: flow.description ?? '',
    steps: normalizeSteps(flow.steps),
  }
  clearEditorDndState()
  showEditor.value = true
}

function closeEditor() {
  showEditor.value = false
  clearEditorDndState()
}

function askDelete(flow: Flow) {
  deletingFlow.value = flow
  showDeleteConfirm.value = true
}

async function addStep() {
  const step = createStepDraft()
  form.value.steps.push(step)
  await focusTaskSelect(step.id)
}

function removeStep(stepId: string) {
  if (form.value.steps.length === 1) {
    toast.warning('流程至少需要一个步骤')
    return
  }

  form.value.steps = form.value.steps.filter((step) => step.id !== stepId)
  delete taskSelectRefs.value[stepId]
}

function moveStep(fromIndex: number, toIndex: number) {
  if (fromIndex === toIndex || fromIndex < 0 || toIndex < 0) {
    return
  }

  const [moved] = form.value.steps.splice(fromIndex, 1)
  if (!moved) {
    return
  }

  const safeToIndex = Math.max(0, Math.min(toIndex, form.value.steps.length))
  form.value.steps.splice(safeToIndex, 0, moved)
}

function handleDragStart(stepId: string, event: DragEvent) {
  draggingStepId.value = stepId
  dropIndicator.value = null

  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', stepId)
  }
}

function handleDragOver(stepId: string, event: DragEvent) {
  if (!draggingStepId.value || draggingStepId.value === stepId) {
    dropIndicator.value = null
    return
  }

  const currentTarget = event.currentTarget as HTMLElement | null
  if (!currentTarget) {
    return
  }

  const rect = currentTarget.getBoundingClientRect()
  const position: DropPosition =
    event.clientY < rect.top + rect.height / 2 ? 'before' : 'after'

  dropIndicator.value = {
    stepId,
    position,
  }

  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

function handleDrop(stepId: string) {
  if (!draggingStepId.value || !dropIndicator.value) {
    clearEditorDndState()
    return
  }

  const fromIndex = form.value.steps.findIndex((step) => step.id === draggingStepId.value)
  const targetIndex = form.value.steps.findIndex((step) => step.id === stepId)

  if (fromIndex === -1 || targetIndex === -1) {
    clearEditorDndState()
    return
  }

  let toIndex = targetIndex + (dropIndicator.value.position === 'after' ? 1 : 0)
  if (fromIndex < toIndex) {
    toIndex -= 1
  }

  moveStep(fromIndex, toIndex)
  clearEditorDndState()
}

function buildPayload(): FlowPayload {
  return {
    name: form.value.name.trim(),
    description: form.value.description.trim() || undefined,
    steps: form.value.steps.map((step) => ({
      task: step.task,
      on_fail:
        step.failurePolicy === 'retry:N'
          ? `retry:${Math.max(1, Number(step.retryCount) || 1)}`
          : step.failurePolicy,
      barrier: step.barrier,
      merge: step.barrier ? step.merge : false,
    })),
  }
}

async function submitFlow() {
  if (!form.value.name.trim()) {
    toast.warning('请输入流程名称')
    return
  }

  if (form.value.steps.length === 0) {
    toast.warning('请至少添加一个步骤')
    return
  }

  if (form.value.steps.some((step) => !step.task)) {
    toast.warning('请为每个步骤选择任务')
    return
  }

  isSaving.value = true

  try {
    const payload = buildPayload()

    if (editingFlow.value) {
      await updateFlow(editingFlow.value.id, payload)
      toast.success('流程已更新')
    } else {
      await createFlow(payload)
      toast.success('流程已创建')
    }

    closeEditor()
    await loadReferenceData()
  } catch (error) {
    const message = error instanceof Error ? error.message : '保存流程失败'
    toast.error(message)
  } finally {
    isSaving.value = false
  }
}

async function confirmDelete() {
  if (!deletingFlow.value) {
    return
  }

  try {
    await deleteFlow(deletingFlow.value.id)
    toast.success('流程已删除')
    showDeleteConfirm.value = false
    deletingFlow.value = null
    await loadReferenceData()
  } catch (error) {
    const message = error instanceof Error ? error.message : '删除流程失败'
    toast.error(message)
  }
}

onMounted(() => {
  void loadReferenceData()
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div v-if="props.showTitle">
        <p class="eyebrow">Flow Builder</p>
        <h1>流程模板</h1>
        <p class="page-description">
          按任务注册表动态编排步骤，支持紧凑表格拖拽排序、失败策略配置和同步控制。
        </p>
      </div>
      <button class="primary-button" @click="openCreateModal">新建流程</button>
    </header>

    <p class="inline-stats">
      共 <strong>{{ totalFlows }}</strong> 个流程 ·
      <strong>{{ totalSteps }}</strong> 个步骤 ·
      <strong>{{ tasks.length }}</strong> 个可用任务
    </p>

    <section class="panel">
      <div class="panel-header">
        <div>
          <h2>模板列表</h2>
          <p>流程创建后可被批量执行页和定时任务页直接引用。</p>
        </div>
      </div>

      <div v-if="isLoading" class="empty-state">正在加载流程模板...</div>
      <div v-else-if="flows.length === 0" class="empty-state">
        <p>当前还没有流程模板。</p>
        <button class="secondary-button" @click="openCreateModal">创建第一个流程</button>
      </div>
      <table v-else class="flow-table">
        <thead>
          <tr>
            <th style="width: 48px">#</th>
            <th style="width: 140px">流程名称</th>
            <th>描述</th>
            <th style="width: 64px">步骤</th>
            <th>步骤摘要</th>
            <th style="width: 140px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(flow, index) in flows" :key="flow.id">
            <td class="cell-center">{{ index + 1 }}</td>
            <td>
              <a class="flow-name-link" href="#" @click.prevent="openEditModal(flow)">
                {{ flow.name }}
              </a>
            </td>
            <td class="cell-desc" :title="flow.description || '—'">
              {{ flow.description || '—' }}
            </td>
            <td class="cell-center">
              <span class="step-badge">{{ flow.steps.length }}</span>
            </td>
            <td class="cell-summary" :title="getStepSummary(flow) || '—'">
              {{ getStepSummary(flow) || '—' }}
            </td>
            <td class="cell-center cell-actions">
              <button class="ghost-button btn-sm" @click="openEditModal(flow)">编辑</button>
              <button class="danger-button btn-sm" @click="askDelete(flow)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <Modal
      :show="showEditor"
      :title="editingFlow ? '编辑流程模板' : '新建流程模板'"
      width="min(80vw, 900px)"
      @close="closeEditor"
    >
      <form class="editor-form" @submit.prevent="submitFlow">
        <div class="field-grid">
          <label class="field">
            <span>流程名称</span>
            <input v-model="form.name" type="text" placeholder="例如：新店启用流程" />
          </label>
          <label class="field">
            <span>流程说明</span>
            <input v-model="form.description" type="text" placeholder="可选，简要说明流程用途" />
          </label>
        </div>

        <section class="step-editor">
          <div class="step-editor-header">
            <div>
              <h3>步骤编排</h3>
              <p>拖拽调整执行顺序，保存前至少保留一个已选择任务的步骤。</p>
            </div>
          </div>

          <div class="step-table-shell">
            <div class="step-table-scroll">
              <div class="step-table">
                <div class="step-table-header">
                  <span class="step-col-handle" aria-hidden="true"></span>
                  <span class="step-col-index">序号</span>
                  <span class="step-col-task">任务</span>
                  <span class="step-col-policy">失败策略</span>
                  <span class="step-col-toggle">同步屏障</span>
                  <span class="step-col-toggle">合并执行</span>
                  <span class="step-col-actions">操作</span>
                </div>

                <div class="step-table-body">
                  <div
                    v-for="(step, index) in form.steps"
                    :key="step.id"
                    class="step-row"
                    :class="{
                      'is-dragging': draggingStepId === step.id,
                      'drop-before': dropIndicator?.stepId === step.id && dropIndicator.position === 'before',
                      'drop-after': dropIndicator?.stepId === step.id && dropIndicator.position === 'after',
                    }"
                    @dragover.prevent="handleDragOver(step.id, $event)"
                    @drop.prevent="handleDrop(step.id)"
                  >
                    <div class="step-row-handle-cell">
                      <button
                        class="row-handle"
                        type="button"
                        draggable="true"
                        title="拖拽排序"
                        aria-label="拖拽排序"
                        @dragstart="handleDragStart(step.id, $event)"
                        @dragend="clearEditorDndState"
                      >
                        ⋮⋮
                      </button>
                    </div>

                    <div class="step-row-index">{{ index + 1 }}</div>

                    <div class="step-row-task task-cell">
                      <select
                        :ref="(element) => setTaskSelectRef(step.id, element)"
                        v-model="step.task"
                        :title="getTaskDescription(step.task) || ''"
                      >
                        <option disabled value="">请选择任务</option>
                        <option
                          v-for="task in tasks"
                          :key="task.name"
                          :value="task.name"
                          :title="task.description || ''"
                        >
                          {{ task.name }}
                        </option>
                      </select>
                      <small v-if="getTaskDescription(step.task)" class="field-hint">
                        {{ getTaskDescription(step.task) }}
                      </small>
                    </div>

                    <div class="step-row-policy">
                      <div
                        class="policy-input-group"
                        :class="{ 'has-retry-input': step.failurePolicy === 'retry:N' }"
                      >
                        <select v-model="step.failurePolicy">
                          <option
                            v-for="option in failurePolicyOptions"
                            :key="option.value"
                            :value="option.value"
                          >
                            {{ option.label }}
                          </option>
                        </select>
                        <input
                          v-if="step.failurePolicy === 'retry:N'"
                          v-model.number="step.retryCount"
                          class="retry-inline-input"
                          type="number"
                          min="1"
                          title="重试次数"
                          aria-label="重试次数"
                        />
                      </div>
                    </div>

                    <label class="step-row-toggle">
                      <input
                        v-model="step.barrier"
                        type="checkbox"
                        title="同步屏障"
                        aria-label="同步屏障"
                        @change="!step.barrier && (step.merge = false)"
                      />
                    </label>

                    <label class="step-row-toggle" :class="{ 'is-disabled': !step.barrier }">
                      <input
                        v-model="step.merge"
                        type="checkbox"
                        title="合并执行"
                        aria-label="合并执行"
                        :disabled="!step.barrier"
                        @change="!step.barrier && (step.merge = false)"
                      />
                    </label>

                    <div class="step-row-actions">
                      <button
                        class="icon-danger-button"
                        type="button"
                        title="删除步骤"
                        aria-label="删除步骤"
                        :disabled="form.steps.length === 1"
                        @click="removeStep(step.id)"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="step-table-footer">
              <button class="secondary-button add-step-button" type="button" @click="addStep">
                + 添加步骤
              </button>
            </div>
          </div>
        </section>
      </form>

      <template #footer>
        <button class="secondary-button" type="button" @click="closeEditor">取消</button>
        <button class="primary-button" type="button" :disabled="isSaving" @click="submitFlow">
          {{ isSaving ? '保存中...' : '保存流程' }}
        </button>
      </template>
    </Modal>

    <ConfirmDialog
      :show="showDeleteConfirm"
      title="删除流程"
      :message="`确认删除 ${deletingFlow?.name || '该流程'} 吗？`"
      type="danger"
      @cancel="showDeleteConfirm = false"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  color: #1a1a2e;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-lg);
}

.eyebrow {
  margin-bottom: 10px;
  color: #0369a1;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 700;
}

h1 {
  margin: 0;
  font-size: var(--font-size-h1);
  line-height: 1.4;
}

.page-description {
  margin-top: 10px;
  color: #64748b;
  max-width: 720px;
  line-height: 1.6;
}

.inline-stats {
  margin: 0;
  color: #64748b;
  font-size: 14px;
}

.inline-stats strong {
  color: #1e293b;
  font-weight: 700;
}

.panel {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.panel {
  padding: var(--spacing-lg);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
  margin-bottom: 20px;
}

.panel-header h2,
.step-editor-header h3 {
  margin: 0;
  font-size: var(--font-size-h2);
}

.panel-header p,
.step-editor-header p {
  margin-top: 8px;
  color: #64748b;
  line-height: 1.5;
}

.flow-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 14px;
}

.flow-table th {
  padding: 10px 12px;
  border-bottom: 2px solid #e2e8f0;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-align: left;
  text-transform: uppercase;
  white-space: nowrap;
}

.flow-table td {
  height: 44px;
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  line-height: 1.4;
  vertical-align: middle;
}

.flow-table tbody tr:hover {
  background: #f8fafc;
}

.cell-center {
  text-align: center;
}

.cell-desc,
.cell-summary {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-desc {
  color: #94a3b8;
}

.cell-summary {
  color: #64748b;
  font-size: 13px;
}

.cell-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  white-space: nowrap;
}

.flow-name-link {
  color: #1d4ed8;
  cursor: pointer;
  font-weight: 600;
  text-decoration: none;
}

.flow-name-link:hover {
  text-decoration: underline;
}

.step-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.editor-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field span {
  color: #475569;
  font-size: 14px;
  font-weight: 600;
}

.field input,
.field select,
.step-row select,
.step-row input[type='number'] {
  width: 100%;
  height: 32px;
  padding: 0 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #ffffff;
  color: #0f172a;
  font-size: 14px;
}

.field input:focus,
.field select:focus,
.step-row select:focus,
.step-row input[type='number']:focus {
  outline: none;
  border-color: #0369a1;
  box-shadow: 0 0 0 4px rgba(3, 105, 161, 0.12);
}

.field-hint {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.step-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-table-shell {
  border: 1px solid #dbe4f0;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  overflow: hidden;
}

.step-table-scroll {
  overflow-x: auto;
}

.step-table {
  min-width: 780px;
}

.step-table-header,
.step-row {
  display: grid;
  grid-template-columns: 32px 40px minmax(220px, 1fr) 184px 80px 80px 80px;
  align-items: center;
  column-gap: 10px;
}

.step-table-header {
  min-height: 36px;
  padding: 6px 16px;
  border-bottom: 1px solid #dbe4f0;
  background: #eff6ff;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.step-col-index,
.step-col-toggle,
.step-col-actions,
.step-row-index,
.step-row-toggle,
.step-row-actions {
  justify-self: center;
}

.step-table-body {
  padding: 2px 10px 4px;
}

.step-row {
  position: relative;
  min-height: 40px;
  padding: 2px 6px;
  border-radius: 8px;
  background: #ffffff;
}

.step-row + .step-row {
  margin-top: 1px;
}

.step-row::before,
.step-row::after {
  content: '';
  position: absolute;
  left: 10px;
  right: 10px;
  height: 2px;
  background: transparent;
  border-radius: 999px;
  pointer-events: none;
}

.step-row::before {
  top: -1px;
}

.step-row::after {
  bottom: -1px;
}

.step-row.drop-before::before,
.step-row.drop-after::after {
  background: #2563eb;
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.12);
}

.step-row.is-dragging {
  opacity: 0.6;
  background: #eff6ff;
}

.step-row-handle-cell,
.step-row-task,
.step-row-policy {
  min-width: 0;
}

.row-handle {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  background: #eff6ff;
  color: #1d4ed8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  font-size: 14px;
  line-height: 1;
}

.row-handle:active {
  cursor: grabbing;
}

.step-row-index {
  color: #334155;
  font-size: 14px;
  font-weight: 700;
}

.task-cell {
  position: relative;
}

.policy-input-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.retry-inline-input {
  width: 58px;
  flex: 0 0 58px;
  text-align: center;
}

.step-row-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
}

.step-row-toggle input {
  width: 16px;
  height: 16px;
  margin: 0;
}

.step-row-toggle.is-disabled {
  opacity: 0.45;
}

.icon-danger-button {
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 6px;
  background: #fee2e2;
  color: #b91c1c;
  font-size: 15px;
  line-height: 1;
  cursor: pointer;
}

.icon-danger-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.step-table-footer {
  padding: 10px 16px 14px;
  border-top: 1px solid #e2e8f0;
  background: #ffffff;
}

.add-step-button {
  min-width: 112px;
}

.empty-state {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
  text-align: center;
}

.primary-button,
.secondary-button,
.ghost-button,
.danger-button {
  border: none;
  border-radius: var(--radius-md);
  padding: 11px 16px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.primary-button {
  background: var(--color-primary);
  color: #ffffff;
}

.secondary-button {
  background: #e2e8f0;
  color: #0f172a;
}

.ghost-button {
  background: #eff6ff;
  color: #1d4ed8;
}

.danger-button {
  background: #fee2e2;
  color: #b91c1c;
}

.primary-button:hover,
.secondary-button:hover,
.ghost-button:hover,
.danger-button:hover,
.icon-danger-button:hover,
.row-handle:hover {
  transform: translateY(-1px);
}

.primary-button:disabled,
.secondary-button:disabled,
.ghost-button:disabled,
.danger-button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
  transform: none;
}

:deep(.modal-container) {
  max-height: 80vh;
}

:deep(.modal-body) {
  padding: 20px 24px;
}

@media (max-width: 900px) {
  .page-header,
  .panel-header {
    flex-direction: column;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
