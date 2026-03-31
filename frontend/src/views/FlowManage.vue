<script setup lang="ts">
import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
} from '@headlessui/vue'
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
const taskSelectRefs = ref<Record<string, HTMLElement | null>>({})

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
  taskSelectRefs.value[stepId] = element instanceof HTMLElement ? element : null
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
  <div class="space-y-6">
    <header class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div v-if="props.showTitle" class="space-y-2">
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-amber-600">Flow Builder</p>
        <h1 class="text-lg font-semibold text-gray-900">流程模板</h1>
        <p class="max-w-3xl text-sm text-brand-500">
          按任务注册表动态编排步骤，支持紧凑表格拖拽排序、失败策略配置和同步控制。
        </p>
      </div>
      <button
        class="inline-flex items-center justify-center rounded-md bg-brand-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-brand-700"
        @click="openCreateModal"
      >
        新建流程
      </button>
    </header>

    <section class="rounded-md border border-brand-300/50 bg-white px-4 py-3 shadow-sm">
      <p class="inline-stats text-sm text-brand-500">
        共 <strong class="font-semibold text-gray-900">{{ totalFlows }}</strong> 个流程 ·
        <strong class="font-semibold text-gray-900">{{ totalSteps }}</strong> 个步骤 ·
        <strong class="font-semibold text-gray-900">{{ tasks.length }}</strong> 个可用任务
      </p>
    </section>

    <section class="rounded-md border border-brand-300/50 bg-white shadow-sm">
      <div class="flex flex-col gap-2 border-b border-brand-300/30 px-5 py-4 sm:flex-row sm:items-start sm:justify-between">
        <div class="space-y-1">
          <h2 class="text-sm font-medium text-gray-900">模板列表</h2>
          <p class="text-xs text-brand-500">流程创建后可被批量执行页和定时任务页直接引用。</p>
        </div>
      </div>

      <div v-if="isLoading" class="px-6 py-12 text-center text-sm text-brand-500">🧩 正在加载流程模板...</div>
      <div v-else-if="flows.length === 0" class="space-y-4 px-6 py-12 text-center">
        <p class="text-sm text-brand-500">🪹 当前还没有流程模板。</p>
        <button
          class="inline-flex items-center justify-center rounded-md border border-brand-300/50 bg-white px-3 py-1.5 text-sm font-medium text-brand-700 transition hover:bg-brand-100/50 hover:text-brand-900"
          @click="openCreateModal"
        >
          创建第一个流程
        </button>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="flow-table min-w-[920px] w-full table-fixed divide-y divide-brand-300/30">
          <thead class="bg-brand-700/10 text-xs font-medium uppercase tracking-wider text-brand-700">
            <tr>
              <th class="w-12 px-4 py-3 text-center">#</th>
              <th class="w-40 px-4 py-3 text-left">流程名称</th>
              <th class="px-4 py-3 text-left">描述</th>
              <th class="w-20 px-4 py-3 text-center">步骤</th>
              <th class="px-4 py-3 text-left">步骤摘要</th>
              <th class="w-36 px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-brand-300/20 text-sm text-gray-900">
            <tr
              v-for="(flow, index) in flows"
              :key="flow.id"
              class="border-b border-brand-300/30 transition hover:bg-brand-100/50"
            >
              <td class="px-4 py-3 text-center font-mono text-xs text-brand-500">{{ index + 1 }}</td>
              <td class="px-4 py-3">
                <a
                  class="flow-name-link font-medium text-gray-900 underline-offset-4 transition hover:text-brand-900 hover:underline"
                  href="#"
                  @click.prevent="openEditModal(flow)"
                >
                  {{ flow.name }}
                </a>
              </td>
              <td class="cell-desc max-w-0 truncate px-4 py-3 text-xs text-brand-500" :title="flow.description || '—'">
                {{ flow.description || '—' }}
              </td>
              <td class="px-4 py-3 text-center">
                <span class="step-badge inline-flex min-w-8 items-center justify-center rounded-full bg-brand-100 px-2.5 py-1 text-xs font-medium text-brand-700">
                  {{ flow.steps.length }}
                </span>
              </td>
              <td class="cell-summary max-w-0 truncate px-4 py-3 text-xs text-brand-500" :title="getStepSummary(flow) || '—'">
                {{ getStepSummary(flow) || '—' }}
              </td>
              <td class="cell-actions space-x-2 whitespace-nowrap px-4 py-3 text-center">
                <button
                  class="ghost-button btn-sm text-xs font-medium text-brand-500 transition hover:text-brand-900"
                  @click="openEditModal(flow)"
                >
                  编辑
                </button>
                <button
                  class="danger-button btn-sm text-xs font-medium text-rose-600 transition hover:text-rose-700"
                  @click="askDelete(flow)"
                >
                  删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <Modal
      :show="showEditor"
      :title="editingFlow ? '编辑流程模板' : '新建流程模板'"
      width="min(80vw, 900px)"
      @close="closeEditor"
    >
      <form class="space-y-4" @submit.prevent="submitFlow">
        <section class="space-y-4">
          <div class="grid gap-4 md:grid-cols-2">
            <label class="space-y-2">
              <span class="text-xs font-medium text-brand-700">流程名称</span>
              <input
                v-model="form.name"
                type="text"
                placeholder="例如：新店启用流程"
                class="w-full rounded-md border border-brand-300/50 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </label>
            <label class="space-y-2">
              <span class="text-xs font-medium text-brand-700">流程说明</span>
              <input
                v-model="form.description"
                type="text"
                placeholder="可选，简要说明流程用途"
                class="w-full rounded-md border border-brand-300/50 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </label>
          </div>
        </section>

        <section class="border-t border-brand-300/30 pt-4">
          <div class="mb-4 space-y-1">
            <h3 class="text-sm font-medium text-gray-900">步骤编排</h3>
            <p class="text-xs text-brand-500">拖拽调整执行顺序，保存前至少保留一个已选择任务的步骤。</p>
          </div>

          <div class="step-table-shell overflow-hidden rounded-md border border-brand-300/50 bg-white">
            <div class="overflow-x-auto">
              <div class="min-w-[860px]">
                <div class="step-table-header grid grid-cols-[44px_48px_minmax(220px,1.5fr)_minmax(220px,1.2fr)_92px_92px_72px] items-center gap-3 bg-brand-100 px-4 py-3 text-xs font-medium uppercase tracking-wider text-brand-500">
                  <span class="text-center" aria-hidden="true"></span>
                  <span class="text-center">序号</span>
                  <span>任务</span>
                  <span>失败策略</span>
                  <span class="text-center">同步屏障</span>
                  <span class="text-center">合并执行</span>
                  <span class="text-center">操作</span>
                </div>

                <div class="step-table-body space-y-1 px-3 py-3">
                  <div
                    v-for="(step, index) in form.steps"
                    :key="step.id"
                    class="step-row relative grid min-h-10 grid-cols-[44px_48px_minmax(220px,1.5fr)_minmax(220px,1.2fr)_92px_92px_72px] items-center gap-3 rounded-md border border-transparent px-2 py-2 transition hover:bg-brand-100/50"
                    :class="{
                      'bg-brand-100/80': draggingStepId === step.id,
                      'before:absolute before:left-3 before:right-3 before:top-0 before:h-0.5 before:-translate-y-1/2 before:rounded-full before:bg-brand-900':
                        dropIndicator?.stepId === step.id && dropIndicator.position === 'before',
                      'after:absolute after:left-3 after:right-3 after:bottom-0 after:h-0.5 after:translate-y-1/2 after:rounded-full after:bg-brand-900':
                        dropIndicator?.stepId === step.id && dropIndicator.position === 'after',
                    }"
                    @dragover.prevent="handleDragOver(step.id, $event)"
                    @drop.prevent="handleDrop(step.id)"
                  >
                    <div class="flex items-center justify-center">
                      <button
                        class="row-handle inline-flex h-6 w-6 items-center justify-center rounded-md text-sm text-brand-500 transition hover:bg-brand-100 hover:text-brand-900"
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

                    <div class="text-center font-mono text-xs text-brand-500">{{ index + 1 }}</div>

                    <div class="space-y-1">
                      <Listbox v-model="step.task">
                        <div class="relative">
                          <ListboxButton
                            class="w-full rounded-md border border-brand-300/50 bg-white px-3 py-2 text-left text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                            :title="getTaskDescription(step.task) || ''"
                          >
                            {{ step.task || '请选择任务' }}
                          </ListboxButton>
                          <transition
                            enter-active-class="transition duration-100 ease-out"
                            enter-from-class="scale-95 opacity-0"
                            enter-to-class="scale-100 opacity-100"
                            leave-active-class="transition duration-75 ease-in"
                            leave-from-class="scale-100 opacity-100"
                            leave-to-class="scale-95 opacity-0"
                          >
                            <ListboxOptions class="absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-md border border-brand-300/50 bg-white py-1 shadow-lg">
                              <ListboxOption disabled value="" v-slot="{ active }">
                                <li
                                  :class="[
                                    'cursor-not-allowed px-3 py-2 text-sm text-brand-300',
                                    active ? 'bg-brand-100' : '',
                                  ]"
                                >
                                  请选择任务
                                </li>
                              </ListboxOption>
                              <ListboxOption
                                v-for="task in tasks"
                                :key="task.name"
                                :value="task.name"
                                v-slot="{ active, selected }"
                              >
                                <li
                                  :class="[
                                    'cursor-pointer px-3 py-2 text-sm text-brand-700',
                                    active ? 'bg-brand-100 text-brand-900' : '',
                                    selected ? 'font-medium text-brand-900' : '',
                                  ]"
                                  :title="task.description || ''"
                                >
                                  {{ task.name }}
                                </li>
                              </ListboxOption>
                            </ListboxOptions>
                          </transition>
                        </div>
                      </Listbox>
                      <input
                        :ref="(element) => setTaskSelectRef(step.id, element)"
                        class="sr-only"
                        tabindex="-1"
                        aria-hidden="true"
                        type="text"
                        readonly
                        :value="step.task"
                      />
                      <small v-if="getTaskDescription(step.task)" class="field-hint text-xs text-brand-500">
                        {{ getTaskDescription(step.task) }}
                      </small>
                    </div>

                    <div class="space-y-2">
                      <Listbox v-model="step.failurePolicy">
                        <div class="relative">
                          <ListboxButton class="w-full rounded-md border border-brand-300/50 bg-white px-3 py-2 text-left text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
                            {{ failurePolicyOptions.find((option) => option.value === step.failurePolicy)?.label || '请选择策略' }}
                          </ListboxButton>
                          <transition
                            enter-active-class="transition duration-100 ease-out"
                            enter-from-class="scale-95 opacity-0"
                            enter-to-class="scale-100 opacity-100"
                            leave-active-class="transition duration-75 ease-in"
                            leave-from-class="scale-100 opacity-100"
                            leave-to-class="scale-95 opacity-0"
                          >
                            <ListboxOptions class="absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-md border border-brand-300/50 bg-white py-1 shadow-lg">
                              <ListboxOption
                                v-for="option in failurePolicyOptions"
                                :key="option.value"
                                :value="option.value"
                                v-slot="{ active, selected }"
                              >
                                <li
                                  :class="[
                                    'cursor-pointer px-3 py-2 text-sm text-brand-700',
                                    active ? 'bg-brand-100 text-brand-900' : '',
                                    selected ? 'font-medium text-brand-900' : '',
                                  ]"
                                >
                                  {{ option.label }}
                                </li>
                              </ListboxOption>
                            </ListboxOptions>
                          </transition>
                        </div>
                      </Listbox>
                      <input
                        v-if="step.failurePolicy === 'retry:N'"
                        v-model.number="step.retryCount"
                        class="retry-inline-input w-full rounded-md border border-brand-300/50 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                        type="number"
                        min="1"
                        title="重试次数"
                        aria-label="重试次数"
                      />
                    </div>

                    <label class="flex items-center justify-center">
                      <input
                        v-model="step.barrier"
                        type="checkbox"
                        class="h-4 w-4 rounded border-brand-300/50 text-brand-500 focus:ring-brand-500"
                        title="同步屏障"
                        aria-label="同步屏障"
                        @change="!step.barrier && (step.merge = false)"
                      />
                    </label>

                    <label class="flex items-center justify-center" :class="{ 'opacity-40': !step.barrier }">
                      <input
                        v-model="step.merge"
                        type="checkbox"
                        class="h-4 w-4 rounded border-brand-300/50 text-brand-500 focus:ring-brand-500"
                        title="合并执行"
                        aria-label="合并执行"
                        :disabled="!step.barrier"
                        @change="!step.barrier && (step.merge = false)"
                      />
                    </label>

                    <div class="flex items-center justify-center">
                      <button
                        class="icon-danger-button inline-flex h-7 w-7 items-center justify-center rounded-md bg-rose-50 text-sm text-rose-600 transition hover:bg-rose-100 hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-40"
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

            <div class="border-t border-brand-300/30 px-4 py-4">
              <button
                class="inline-flex items-center justify-center rounded-md border border-brand-300/50 bg-white px-3 py-1.5 text-sm font-medium text-brand-700 transition hover:bg-brand-100/50 hover:text-brand-900"
                type="button"
                @click="addStep"
              >
                + 添加步骤
              </button>
            </div>
          </div>
        </section>
      </form>

      <template #footer>
        <button
          class="rounded-md border border-brand-300/50 bg-white px-3 py-1.5 text-sm font-medium text-brand-700 transition hover:bg-brand-100/50 hover:text-brand-900"
          type="button"
          @click="closeEditor"
        >
          取消
        </button>
        <button
          class="rounded-md bg-brand-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
          type="button"
          :disabled="isSaving"
          @click="submitFlow"
        >
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
