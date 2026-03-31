<script setup lang="ts">
import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
  Tab,
  TabGroup,
  TabList,
  TabPanel,
  TabPanels,
} from '@headlessui/vue'
import { computed, onMounted, ref } from 'vue'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import Modal from '../components/Modal.vue'
import { listFlows } from '../api/flows'
import {
  createSchedule,
  deleteSchedule,
  listSchedules,
  pauseSchedule,
  resumeSchedule,
  updateSchedule,
} from '../api/schedules'
import { listShops } from '../api/shops'
import type { Flow, Schedule, SchedulePayload, Shop } from '../api/types'
import { toast } from '../utils/toast'

type TriggerMode = 'interval' | 'cron'

interface ScheduleFormModel {
  name: string
  flowId: string
  shopIds: string[]
  concurrency: number
  triggerMode: TriggerMode
  intervalMinutes: number
  cronExpr: string
  overlapPolicy: 'wait' | 'skip' | 'parallel'
}

const flows = ref<Flow[]>([])
const shops = ref<Shop[]>([])
const schedules = ref<Schedule[]>([])
const isLoading = ref(false)
const isSaving = ref(false)
const actioningId = ref('')
const showEditor = ref(false)
const showDeleteConfirm = ref(false)
const editingSchedule = ref<Schedule | null>(null)
const deletingSchedule = ref<Schedule | null>(null)

const props = withDefaults(defineProps<{ showTitle?: boolean }>(), {
  showTitle: true,
})

const form = ref<ScheduleFormModel>({
  name: '',
  flowId: '',
  shopIds: [],
  concurrency: 1,
  triggerMode: 'interval',
  intervalMinutes: 60,
  cronExpr: '*/30 * * * *',
  overlapPolicy: 'wait',
})

const totalSchedules = computed(() => schedules.value.length)
const enabledSchedules = computed(() => schedules.value.filter((schedule) => schedule.enabled).length)
const pausedSchedules = computed(() => schedules.value.filter((schedule) => !schedule.enabled).length)

function parseDateTime(value?: string | null) {
  if (!value) {
    return null
  }

  const date = new Date(value.replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) {
    return null
  }

  return date
}

function formatDateTime(value?: string | null) {
  const date = parseDateTime(value)
  if (!date) {
    return '--'
  }

  return date.toLocaleString('zh-CN', {
    hour12: false,
  })
}

function getFlowName(flowId: string) {
  return flows.value.find((flow) => flow.id === flowId)?.name ?? flowId
}

function getShopName(shopId: string) {
  return shops.value.find((shop) => shop.id === shopId)?.name ?? shopId
}

function getTriggerLabel(schedule: Schedule) {
  if (schedule.interval_seconds) {
    const minutes = Math.max(1, Math.round(schedule.interval_seconds / 60))
    return `每 ${minutes} 分钟`
  }

  return schedule.cron_expr || '--'
}

function getShopSummary(schedule: Schedule) {
  return schedule.shop_ids.map(getShopName).join('、') || '--'
}

function createEmptyForm(): ScheduleFormModel {
  return {
    name: '',
    flowId: flows.value[0]?.id ?? '',
    shopIds: [],
    concurrency: 1,
    triggerMode: 'interval',
    intervalMinutes: 60,
    cronExpr: '*/30 * * * *',
    overlapPolicy: 'wait',
  }
}

function toForm(schedule: Schedule): ScheduleFormModel {
  return {
    name: schedule.name,
    flowId: schedule.flow_id,
    shopIds: [...schedule.shop_ids],
    concurrency: schedule.concurrency,
    triggerMode: schedule.interval_seconds ? 'interval' : 'cron',
    intervalMinutes: schedule.interval_seconds
      ? Math.max(1, Math.round(schedule.interval_seconds / 60))
      : 60,
    cronExpr: schedule.cron_expr ?? '*/30 * * * *',
    overlapPolicy: (schedule.overlap_policy as ScheduleFormModel['overlapPolicy']) ?? 'wait',
  }
}

async function loadReferenceData() {
  isLoading.value = true

  try {
    const [flowResponse, shopResponse, scheduleResponse] = await Promise.all([
      listFlows(),
      listShops(),
      listSchedules(),
    ])

    flows.value = flowResponse.list
    shops.value = shopResponse.list
    schedules.value = scheduleResponse.list
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载定时任务失败'
    toast.error(message)
  } finally {
    isLoading.value = false
  }
}

function openCreateModal() {
  editingSchedule.value = null
  form.value = createEmptyForm()
  showEditor.value = true
}

function openEditModal(schedule: Schedule) {
  editingSchedule.value = schedule
  form.value = toForm(schedule)
  showEditor.value = true
}

function askDelete(schedule: Schedule) {
  deletingSchedule.value = schedule
  showDeleteConfirm.value = true
}

function buildPayload(): SchedulePayload {
  const payload: SchedulePayload = {
    name: form.value.name.trim(),
    flow_id: form.value.flowId,
    shop_ids: [...form.value.shopIds],
    concurrency: form.value.concurrency,
    overlap_policy: form.value.overlapPolicy,
    interval_seconds: null,
    cron_expr: null,
  }

  if (form.value.triggerMode === 'interval') {
    payload.interval_seconds = Math.max(1, form.value.intervalMinutes) * 60
  } else {
    payload.cron_expr = form.value.cronExpr.trim()
  }

  return payload
}

async function submitSchedule() {
  if (!form.value.name.trim()) {
    toast.warning('请输入任务名称')
    return
  }

  if (!form.value.flowId) {
    toast.warning('请选择流程模板')
    return
  }

  if (form.value.shopIds.length === 0) {
    toast.warning('请至少选择一个店铺')
    return
  }

  if (form.value.triggerMode === 'cron' && !form.value.cronExpr.trim()) {
    toast.warning('请输入 Cron 表达式')
    return
  }

  isSaving.value = true

  try {
    const payload = buildPayload()

    if (editingSchedule.value) {
      await updateSchedule(editingSchedule.value.id, payload)
      toast.success('定时任务已更新')
    } else {
      await createSchedule(payload)
      toast.success('定时任务已创建')
    }

    showEditor.value = false
    await loadReferenceData()
  } catch (error) {
    const message = error instanceof Error ? error.message : '保存定时任务失败'
    toast.error(message)
  } finally {
    isSaving.value = false
  }
}

async function toggleSchedule(schedule: Schedule) {
  actioningId.value = schedule.id

  try {
    if (schedule.enabled) {
      await pauseSchedule(schedule.id)
      toast.success('已暂停定时任务')
    } else {
      await resumeSchedule(schedule.id)
      toast.success('已恢复定时任务')
    }

    await loadReferenceData()
  } catch (error) {
    const message = error instanceof Error ? error.message : '更新任务状态失败'
    toast.error(message)
  } finally {
    actioningId.value = ''
  }
}

async function confirmDelete() {
  if (!deletingSchedule.value) {
    return
  }

  actioningId.value = deletingSchedule.value.id

  try {
    await deleteSchedule(deletingSchedule.value.id)
    toast.success('定时任务已删除')
    showDeleteConfirm.value = false
    deletingSchedule.value = null
    await loadReferenceData()
  } catch (error) {
    const message = error instanceof Error ? error.message : '删除定时任务失败'
    toast.error(message)
  } finally {
    actioningId.value = ''
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
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-amber-600">Schedule Control</p>
        <h1 class="text-lg font-semibold text-gray-900">定时任务</h1>
        <p class="max-w-3xl text-sm text-gray-500">
          通过固定间隔或 Cron 表达式调度流程模板，暂停与恢复都直接映射后端 schedules API。
        </p>
      </div>
      <button
        class="inline-flex items-center justify-center rounded-md bg-brand-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-brand-700"
        @click="openCreateModal"
      >
        新建定时任务
      </button>
    </header>

    <section class="rounded-md border border-brand-200/50 bg-white px-4 py-3 shadow-sm">
      <p class="inline-stats text-sm text-gray-500">
        共 <strong class="font-semibold text-gray-900">{{ totalSchedules }}</strong> 条计划 ·
        <strong class="font-semibold text-gray-900">{{ enabledSchedules }}</strong> 条启用 ·
        <strong class="font-semibold text-gray-900">{{ pausedSchedules }}</strong> 条暂停
      </p>
    </section>

    <section class="rounded-md border border-brand-200/50 bg-white shadow-sm">
      <div class="flex flex-col gap-2 border-b border-gray-100 px-5 py-4 sm:flex-row sm:items-start sm:justify-between">
        <div class="space-y-1">
          <h2 class="text-sm font-medium text-gray-900">任务列表</h2>
          <p class="text-xs text-gray-500">定时任务统一使用表格展示，启停、编辑和删除都在同一行完成。</p>
        </div>
      </div>

      <div v-if="isLoading" class="px-6 py-12 text-center text-sm text-gray-400">⏳ 正在加载定时任务...</div>
      <div v-else-if="schedules.length === 0" class="space-y-4 px-6 py-12 text-center">
        <p class="text-sm text-gray-400">🗓️ 当前还没有定时任务。</p>
        <button
          class="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
          @click="openCreateModal"
        >
          创建第一条计划
        </button>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="schedule-table min-w-[1040px] w-full table-fixed divide-y divide-gray-200">
          <thead class="bg-brand-50 text-xs font-medium uppercase tracking-wider text-gray-500">
            <tr>
              <th class="w-20 px-4 py-3 text-center">开关</th>
              <th class="w-44 px-4 py-3 text-left">任务名称</th>
              <th class="w-44 px-4 py-3 text-left">执行流程</th>
              <th class="w-40 px-4 py-3 text-left">执行周期</th>
              <th class="w-44 px-4 py-3 text-left">上次执行</th>
              <th class="w-44 px-4 py-3 text-left">下次执行</th>
              <th class="w-28 px-4 py-3 text-center">目标店铺数</th>
              <th class="w-36 px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 text-sm text-gray-900">
            <tr
              v-for="schedule in schedules"
              :key="schedule.id"
              class="border-b border-gray-100 transition hover:bg-gray-50/50"
            >
              <td class="px-4 py-3 text-center">
                <label class="switch inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    class="peer sr-only"
                    :checked="schedule.enabled"
                    :disabled="actioningId === schedule.id"
                    @change="toggleSchedule(schedule)"
                  />
                  <span class="switch-slider relative h-6 w-11 rounded-full bg-gray-200 transition after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:shadow-sm after:transition-all peer-checked:bg-brand-500 peer-checked:after:translate-x-5 peer-disabled:opacity-50" />
                </label>
              </td>
              <td class="px-4 py-3">
                <a
                  class="name-link font-medium text-gray-900 underline-offset-4 transition hover:text-gray-700 hover:underline"
                  href="#"
                  @click.prevent="openEditModal(schedule)"
                >
                  {{ schedule.name }}
                </a>
              </td>
              <td class="truncate px-4 py-3 text-xs text-gray-500" :title="getFlowName(schedule.flow_id)">
                {{ getFlowName(schedule.flow_id) }}
              </td>
              <td class="px-4 py-3 text-xs text-gray-500">{{ getTriggerLabel(schedule) }}</td>
              <td class="px-4 py-3 text-right font-mono text-xs text-gray-500">{{ formatDateTime(schedule.last_run_at) }}</td>
              <td class="px-4 py-3 text-right font-mono text-xs text-gray-500">{{ formatDateTime(schedule.next_run_at) }}</td>
              <td class="px-4 py-3 text-center" :title="getShopSummary(schedule)">
                <span class="count-badge inline-flex items-center justify-center rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700">
                  {{ schedule.shop_ids.length }}
                </span>
              </td>
              <td class="cell-actions whitespace-nowrap px-4 py-3 text-center">
                <button
                  class="text-xs font-medium text-gray-500 transition hover:text-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="actioningId === schedule.id"
                  @click="openEditModal(schedule)"
                >
                  编辑
                </button>
                <button
                  class="ml-3 text-xs font-medium text-rose-600 transition hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="actioningId === schedule.id"
                  @click="askDelete(schedule)"
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
      :title="editingSchedule ? '编辑定时任务' : '新建定时任务'"
      width="min(80vw, 900px)"
      @close="showEditor = false"
    >
      <form class="space-y-4" @submit.prevent="submitSchedule">
        <section class="space-y-4">
          <div class="grid gap-4 md:grid-cols-2">
            <label class="space-y-2">
              <span class="text-xs font-medium text-gray-600">任务名称</span>
              <input
                v-model="form.name"
                type="text"
                placeholder="例如：每日巡检"
                class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </label>

            <div class="space-y-2">
              <span class="text-xs font-medium text-gray-600">流程模板</span>
              <Listbox v-model="form.flowId">
                <div class="relative">
                  <ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
                    {{ form.flowId ? getFlowName(form.flowId) : '请选择流程' }}
                  </ListboxButton>
                  <transition
                    enter-active-class="transition duration-100 ease-out"
                    enter-from-class="scale-95 opacity-0"
                    enter-to-class="scale-100 opacity-100"
                    leave-active-class="transition duration-75 ease-in"
                    leave-from-class="scale-100 opacity-100"
                    leave-to-class="scale-95 opacity-0"
                  >
                    <ListboxOptions class="absolute z-20 mt-2 max-h-64 w-full overflow-auto rounded-md border border-brand-200/50 bg-white py-1 shadow-lg">
                      <ListboxOption disabled value="" v-slot="{ active }">
                        <li :class="['cursor-not-allowed px-3 py-2 text-sm text-gray-300', active ? 'bg-gray-50' : '']">
                          请选择流程
                        </li>
                      </ListboxOption>
                      <ListboxOption
                        v-for="flow in flows"
                        :key="flow.id"
                        :value="flow.id"
                        v-slot="{ active, selected }"
                      >
                        <li
                          :class="[
                            'cursor-pointer px-3 py-2 text-sm text-gray-700',
                            active ? 'bg-gray-100 text-gray-900' : '',
                            selected ? 'font-medium text-gray-900' : '',
                          ]"
                        >
                          {{ flow.name }}
                        </li>
                      </ListboxOption>
                    </ListboxOptions>
                  </transition>
                </div>
              </Listbox>
            </div>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <div class="space-y-2">
              <span class="text-xs font-medium text-gray-600">并发数</span>
              <Listbox v-model="form.concurrency">
                <div class="relative">
                  <ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
                    {{ form.concurrency }}
                  </ListboxButton>
                  <transition
                    enter-active-class="transition duration-100 ease-out"
                    enter-from-class="scale-95 opacity-0"
                    enter-to-class="scale-100 opacity-100"
                    leave-active-class="transition duration-75 ease-in"
                    leave-from-class="scale-100 opacity-100"
                    leave-to-class="scale-95 opacity-0"
                  >
                    <ListboxOptions class="absolute z-20 mt-2 w-full overflow-auto rounded-md border border-brand-200/50 bg-white py-1 shadow-lg">
                      <ListboxOption v-for="count in [1, 2, 3, 5, 10]" :key="count" :value="count" v-slot="{ active, selected }">
                        <li
                          :class="[
                            'cursor-pointer px-3 py-2 text-sm text-gray-700',
                            active ? 'bg-gray-100 text-gray-900' : '',
                            selected ? 'font-medium text-gray-900' : '',
                          ]"
                        >
                          {{ count }}
                        </li>
                      </ListboxOption>
                    </ListboxOptions>
                  </transition>
                </div>
              </Listbox>
            </div>

            <div class="space-y-2">
              <span class="text-xs font-medium text-gray-600">上轮未完成策略</span>
              <Listbox v-model="form.overlapPolicy">
                <div class="relative">
                  <ListboxButton class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500">
                    {{
                      form.overlapPolicy === 'wait'
                        ? '等完成'
                        : form.overlapPolicy === 'skip'
                          ? '跳过本轮'
                          : '允许并行'
                    }}
                  </ListboxButton>
                  <transition
                    enter-active-class="transition duration-100 ease-out"
                    enter-from-class="scale-95 opacity-0"
                    enter-to-class="scale-100 opacity-100"
                    leave-active-class="transition duration-75 ease-in"
                    leave-from-class="scale-100 opacity-100"
                    leave-to-class="scale-95 opacity-0"
                  >
                    <ListboxOptions class="absolute z-20 mt-2 w-full overflow-auto rounded-md border border-brand-200/50 bg-white py-1 shadow-lg">
                      <ListboxOption value="wait" v-slot="{ active, selected }">
                        <li
                          :class="[
                            'cursor-pointer px-3 py-2 text-sm text-gray-700',
                            active ? 'bg-gray-100 text-gray-900' : '',
                            selected ? 'font-medium text-gray-900' : '',
                          ]"
                        >
                          等完成
                        </li>
                      </ListboxOption>
                      <ListboxOption value="skip" v-slot="{ active, selected }">
                        <li
                          :class="[
                            'cursor-pointer px-3 py-2 text-sm text-gray-700',
                            active ? 'bg-gray-100 text-gray-900' : '',
                            selected ? 'font-medium text-gray-900' : '',
                          ]"
                        >
                          跳过本轮
                        </li>
                      </ListboxOption>
                      <ListboxOption value="parallel" v-slot="{ active, selected }">
                        <li
                          :class="[
                            'cursor-pointer px-3 py-2 text-sm text-gray-700',
                            active ? 'bg-gray-100 text-gray-900' : '',
                            selected ? 'font-medium text-gray-900' : '',
                          ]"
                        >
                          允许并行
                        </li>
                      </ListboxOption>
                    </ListboxOptions>
                  </transition>
                </div>
              </Listbox>
            </div>
          </div>
        </section>

        <section class="border-t border-gray-100 pt-4">
          <div class="mb-4 space-y-1">
            <h3 class="text-sm font-medium text-gray-900">选择店铺</h3>
            <p class="text-xs text-gray-500">可多选，执行时将复用这些目标。</p>
          </div>
          <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <label
              v-for="shop in shops"
              :key="shop.id"
              class="rounded-md border border-brand-200/50 bg-gray-50 px-3 py-3 transition hover:border-gray-300 hover:bg-white"
            >
              <span class="flex items-start gap-3">
                <input
                  v-model="form.shopIds"
                  type="checkbox"
                  :value="shop.id"
                  class="mt-0.5 h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-brand-500"
                />
                <span class="min-w-0 space-y-1">
                  <strong class="block truncate text-sm font-medium text-gray-900">{{ shop.name }}</strong>
                  <span class="block truncate text-xs text-gray-500">{{ shop.username || shop.id }}</span>
                </span>
              </span>
            </label>
          </div>
        </section>

        <section class="border-t border-gray-100 pt-4">
          <div class="mb-4 space-y-1">
            <h3 class="text-sm font-medium text-gray-900">触发方式</h3>
            <p class="text-xs text-gray-500">固定间隔按分钟填写，Cron 使用标准 5 段表达式。</p>
          </div>

          <TabGroup
            :selectedIndex="form.triggerMode === 'interval' ? 0 : 1"
            @change="(index) => (form.triggerMode = index === 0 ? 'interval' : 'cron')"
          >
            <TabList class="grid grid-cols-2 gap-2 rounded-md bg-gray-100 p-1">
              <Tab v-slot="{ selected }" as="template">
                <button
                  class="rounded-md px-3 py-2 text-sm font-medium transition"
                  :class="selected ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
                >
                  固定间隔
                </button>
              </Tab>
              <Tab v-slot="{ selected }" as="template">
                <button
                  class="rounded-md px-3 py-2 text-sm font-medium transition"
                  :class="selected ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
                >
                  Cron 表达式
                </button>
              </Tab>
            </TabList>

            <TabPanels class="mt-4">
              <TabPanel class="rounded-md border border-brand-200/50 bg-gray-50 p-4">
                <label class="space-y-2">
                  <span class="text-xs font-medium text-gray-600">固定间隔（分钟）</span>
                  <input
                    v-model.number="form.intervalMinutes"
                    type="number"
                    min="1"
                    class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </label>
              </TabPanel>
              <TabPanel class="rounded-md border border-brand-200/50 bg-gray-50 p-4">
                <label class="space-y-2">
                  <span class="text-xs font-medium text-gray-600">Cron 表达式</span>
                  <input
                    v-model="form.cronExpr"
                    type="text"
                    placeholder="例如：*/30 * * * *"
                    class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </label>
              </TabPanel>
            </TabPanels>
          </TabGroup>
        </section>
      </form>

      <template #footer>
        <button
          class="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
          @click="showEditor = false"
        >
          取消
        </button>
        <button
          class="rounded-md bg-brand-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="isSaving"
          @click="submitSchedule"
        >
          {{ isSaving ? '保存中...' : '保存任务' }}
        </button>
      </template>
    </Modal>

    <ConfirmDialog
      :show="showDeleteConfirm"
      title="删除定时任务"
      :message="`确认删除 ${deletingSchedule?.name || '该任务'} 吗？`"
      type="danger"
      @cancel="showDeleteConfirm = false"
      @confirm="confirmDelete"
    />
  </div>
</template>
