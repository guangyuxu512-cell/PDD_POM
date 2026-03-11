<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import Modal from '../components/Modal.vue'
import { createFlow, deleteFlow, listFlows, updateFlow } from '../api/flows'
import { listAvailableTasks } from '../api/tasks'
import type { AvailableTask, Flow, FlowPayload, FlowStep } from '../api/types'
import { toast } from '../utils/toast'

type FailurePolicy = 'skip_shop' | 'continue' | 'log_and_skip' | 'retry:N' | 'abort'

interface StepDraft {
  id: string
  task: string
  failurePolicy: FailurePolicy
  retryCount: number
}

interface FlowFormModel {
  name: string
  description: string
  steps: StepDraft[]
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

const failurePolicyOptions: Array<{ value: FailurePolicy; label: string }> = [
  { value: 'skip_shop', label: '跳过该店铺' },
  { value: 'continue', label: '继续执行' },
  { value: 'log_and_skip', label: '记录并跳过' },
  { value: 'retry:N', label: '重试N次' },
  { value: 'abort', label: '终止全部' },
]

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
    task: seed?.task ?? tasks.value[0]?.name ?? '',
    failurePolicy: seed?.failurePolicy ?? 'continue',
    retryCount: seed?.retryCount ?? 2,
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
    })
  })
}

function formatPolicy(step: FlowStep) {
  if (step.on_fail.startsWith('retry:')) {
    const retryCount = Number.parseInt(step.on_fail.split(':', 2)[1] || '2', 10)
    return `重试${Number.isNaN(retryCount) ? 2 : retryCount}次`
  }

  return (
    failurePolicyOptions.find((option) => option.value === step.on_fail)?.label ??
    step.on_fail
  )
}

function getTaskDescription(taskName: string) {
  return tasks.value.find((task) => task.name === taskName)?.description || ''
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
  showEditor.value = true
}

function openEditModal(flow: Flow) {
  editingFlow.value = flow
  form.value = {
    name: flow.name,
    description: flow.description ?? '',
    steps: normalizeSteps(flow.steps),
  }
  showEditor.value = true
}

function askDelete(flow: Flow) {
  deletingFlow.value = flow
  showDeleteConfirm.value = true
}

function addStep() {
  form.value.steps.push(createStepDraft())
}

function copyStep(stepId: string) {
  const index = form.value.steps.findIndex((step) => step.id === stepId)
  if (index === -1) {
    return
  }

  const source = form.value.steps[index]
  if (!source) {
    return
  }
  const copied = createStepDraft({
    task: source.task,
    failurePolicy: source.failurePolicy,
    retryCount: source.retryCount,
  })
  form.value.steps.splice(index + 1, 0, copied)
}

function removeStep(stepId: string) {
  if (form.value.steps.length === 1) {
    toast.warning('流程至少需要一个步骤')
    return
  }

  form.value.steps = form.value.steps.filter((step) => step.id !== stepId)
}

function moveStep(fromIndex: number, toIndex: number) {
  if (fromIndex === toIndex || fromIndex < 0 || toIndex < 0) {
    return
  }

  const [moved] = form.value.steps.splice(fromIndex, 1)
  if (!moved) {
    return
  }
  form.value.steps.splice(toIndex, 0, moved)
}

function handleDragStart(stepId: string) {
  draggingStepId.value = stepId
}

function handleDrop(targetId: string) {
  if (!draggingStepId.value || draggingStepId.value === targetId) {
    draggingStepId.value = null
    return
  }

  const fromIndex = form.value.steps.findIndex((step) => step.id === draggingStepId.value)
  const toIndex = form.value.steps.findIndex((step) => step.id === targetId)
  moveStep(fromIndex, toIndex)
  draggingStepId.value = null
}

function buildPayload(): FlowPayload {
  return {
    name: form.value.name.trim(),
    description: form.value.description.trim() || undefined,
    steps: form.value.steps.map((step) => ({
      task: step.task,
      on_fail:
        step.failurePolicy === 'retry:N'
          ? `retry:${Math.max(1, step.retryCount)}`
          : step.failurePolicy,
    })),
  }
}

async function submitFlow() {
  if (!form.value.name.trim()) {
    toast.warning('请输入流程名称')
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

    showEditor.value = false
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
      <div>
        <p class="eyebrow">Flow Builder</p>
        <h1>流程模板</h1>
        <p class="page-description">按任务注册表动态编排步骤，支持拖拽排序、复制和失败策略配置。</p>
      </div>
      <button class="primary-button" @click="openCreateModal">新建流程</button>
    </header>

    <section class="summary-grid">
      <article class="summary-card">
        <span class="summary-label">流程数</span>
        <strong>{{ totalFlows }}</strong>
        <span class="summary-note">已保存模板</span>
      </article>
      <article class="summary-card">
        <span class="summary-label">步骤总数</span>
        <strong>{{ totalSteps }}</strong>
        <span class="summary-note">来自全部流程</span>
      </article>
      <article class="summary-card">
        <span class="summary-label">可用任务</span>
        <strong>{{ tasks.length }}</strong>
        <span class="summary-note">自动读取后端注册表</span>
      </article>
    </section>

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
      <div v-else class="flow-grid">
        <article v-for="flow in flows" :key="flow.id" class="flow-card">
          <div class="flow-card-header">
            <div>
              <h3>{{ flow.name }}</h3>
              <p>{{ flow.description || '未填写说明' }}</p>
            </div>
            <span class="step-count">{{ flow.steps.length }} steps</span>
          </div>

          <ol class="step-list-preview">
            <li v-for="step in flow.steps" :key="`${flow.id}-${step.task}-${step.on_fail}`">
              <span class="step-task">{{ step.task }}</span>
              <span class="step-policy">{{ formatPolicy(step) }}</span>
            </li>
          </ol>

          <div class="flow-actions">
            <button class="ghost-button" @click="openEditModal(flow)">编辑</button>
            <button class="danger-button" @click="askDelete(flow)">删除</button>
          </div>
        </article>
      </div>
    </section>

    <Modal
      :show="showEditor"
      :title="editingFlow ? '编辑流程模板' : '新建流程模板'"
      width="980px"
      @close="showEditor = false"
    >
      <form class="editor-form" @submit.prevent="submitFlow">
        <div class="field-grid">
          <label class="field">
            <span>流程名称</span>
            <input v-model="form.name" type="text" placeholder="例如：新店启用流程" />
          </label>
          <label class="field">
            <span>流程说明</span>
            <input v-model="form.description" type="text" placeholder="可选" />
          </label>
        </div>

        <section class="step-editor">
          <div class="step-editor-header">
            <div>
              <h3>步骤编排</h3>
              <p>拖拽排序，每步都从后端注册任务中选择。</p>
            </div>
            <button class="secondary-button" type="button" @click="addStep">添加步骤</button>
          </div>

          <div class="step-drafts">
            <article
              v-for="(step, index) in form.steps"
              :key="step.id"
              class="step-draft"
              draggable="true"
              @dragstart="handleDragStart(step.id)"
              @dragover.prevent
              @drop="handleDrop(step.id)"
            >
              <div class="step-draft-header">
                <div class="step-title">
                  <span class="drag-handle">≡</span>
                  <strong>步骤 {{ index + 1 }}</strong>
                </div>
                <div class="step-actions">
                  <button class="ghost-button" type="button" @click="copyStep(step.id)">复制</button>
                  <button class="danger-button" type="button" @click="removeStep(step.id)">删除</button>
                </div>
              </div>

              <div class="step-field-grid">
                <label class="field">
                  <span>任务</span>
                  <select v-model="step.task">
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
                </label>

                <label class="field">
                  <span>失败策略</span>
                  <select v-model="step.failurePolicy">
                    <option
                      v-for="option in failurePolicyOptions"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                </label>

                <label v-if="step.failurePolicy === 'retry:N'" class="field retry-field">
                  <span>重试次数</span>
                  <input v-model.number="step.retryCount" type="number" min="1" />
                </label>
              </div>
            </article>
          </div>
        </section>
      </form>

      <template #footer>
        <button class="secondary-button" @click="showEditor = false">取消</button>
        <button class="primary-button" :disabled="isSaving" @click="submitFlow">
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
  gap: 24px;
  color: #1a1a2e;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
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
  font-size: 32px;
  line-height: 1.1;
}

.page-description {
  margin-top: 10px;
  color: #64748b;
  max-width: 720px;
  line-height: 1.6;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.summary-card,
.panel,
.flow-card,
.step-draft {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
}

.summary-card {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-label {
  font-size: 13px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.summary-card strong {
  font-size: 30px;
}

.summary-note {
  color: #94a3b8;
  font-size: 14px;
}

.panel {
  padding: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 20px;
}

.panel-header h2,
.step-editor-header h3 {
  margin: 0;
  font-size: 22px;
}

.panel-header p,
.step-editor-header p {
  margin-top: 8px;
  color: #64748b;
  line-height: 1.5;
}

.flow-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 18px;
}

.flow-card {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.flow-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.flow-card-header h3 {
  margin: 0;
  font-size: 22px;
}

.flow-card-header p {
  margin-top: 8px;
  color: #64748b;
}

.step-count {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.step-list-preview {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 20px;
}

.step-list-preview li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #334155;
}

.step-task {
  font-weight: 600;
}

.step-policy {
  color: #64748b;
  font-size: 13px;
}

.flow-actions {
  display: flex;
  gap: 12px;
}

.editor-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.field-grid,
.step-field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
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

.field-hint {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.field input,
.field select {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: #ffffff;
  color: #0f172a;
  font-size: 14px;
}

.field input:focus,
.field select:focus {
  outline: none;
  border-color: #0369a1;
  box-shadow: 0 0 0 4px rgba(3, 105, 161, 0.12);
}

.step-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
}

.step-drafts {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-draft {
  padding: 18px;
}

.step-draft-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.step-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.drag-handle {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #eff6ff;
  color: #1d4ed8;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  font-weight: 700;
}

.step-actions {
  display: flex;
  gap: 12px;
}

.retry-field {
  grid-column: span 2;
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
  border-radius: 12px;
  padding: 11px 16px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.primary-button {
  background: linear-gradient(135deg, #0369a1, #0284c7);
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(2, 132, 199, 0.2);
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
.danger-button:hover {
  transform: translateY(-1px);
}

.primary-button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
  transform: none;
}

@media (max-width: 900px) {
  .page-header,
  .panel-header,
  .flow-card-header,
  .step-editor-header,
  .step-draft-header {
    flex-direction: column;
  }

  .summary-grid,
  .field-grid,
  .step-field-grid {
    grid-template-columns: 1fr;
  }

  .retry-field {
    grid-column: span 1;
  }
}
</style>
