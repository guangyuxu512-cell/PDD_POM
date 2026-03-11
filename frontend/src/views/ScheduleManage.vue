<script setup lang="ts">
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

function getOverlapPolicyLabel(policy: string) {
  if (policy === 'skip') {
    return '跳过本轮'
  }

  if (policy === 'parallel') {
    return '允许并行'
  }

  return '等上轮完成'
}

function getRuntimeStatus(schedule: Schedule) {
  if (!schedule.enabled) {
    return {
      key: 'paused',
      label: '已暂停',
      color: '#64748b',
      background: 'rgba(148, 163, 184, 0.2)',
    }
  }

  const lastRunAt = parseDateTime(schedule.last_run_at)?.getTime()
  const now = Date.now()
  const activeWindow = schedule.interval_seconds
    ? Math.min(schedule.interval_seconds * 1000, 5 * 60 * 1000)
    : 60 * 1000

  if (lastRunAt && now - lastRunAt < activeWindow) {
    return {
      key: 'executing',
      label: '执行中',
      color: '#b45309',
      background: 'rgba(245, 158, 11, 0.18)',
    }
  }

  return {
    key: 'running',
    label: '运行中',
    color: '#047857',
    background: 'rgba(16, 185, 129, 0.14)',
  }
}

function getRecentResultLabel(schedule: Schedule) {
  if (!schedule.last_run_at) {
    return '暂无执行记录'
  }

  const runtimeStatus = getRuntimeStatus(schedule)
  if (runtimeStatus.key === 'executing') {
    return '执行中'
  }

  if (!schedule.enabled) {
    return '暂停中'
  }

  return '最近已触发'
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
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Schedule Control</p>
        <h1>定时任务</h1>
        <p class="page-description">
          通过固定间隔或 Cron 表达式调度流程模板，暂停与恢复都直接映射后端 schedules API。
        </p>
      </div>
      <button class="primary-button" @click="openCreateModal">新建定时任务</button>
    </header>

    <section class="summary-grid">
      <article class="summary-card">
        <span class="summary-label">总任务数</span>
        <strong>{{ totalSchedules }}</strong>
        <span class="summary-note">全部定时计划</span>
      </article>
      <article class="summary-card">
        <span class="summary-label">运行中</span>
        <strong>{{ enabledSchedules }}</strong>
        <span class="summary-note">计划保持启用</span>
      </article>
      <article class="summary-card">
        <span class="summary-label">已暂停</span>
        <strong>{{ pausedSchedules }}</strong>
        <span class="summary-note">不会继续触发</span>
      </article>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <h2>任务列表</h2>
          <p>运行状态中的“执行中”按最近触发时间做前端推断，后端当前未单独提供计划执行态字段。</p>
        </div>
      </div>

      <div v-if="isLoading" class="empty-state">正在加载定时任务...</div>
      <div v-else-if="schedules.length === 0" class="empty-state">
        <p>当前还没有定时任务。</p>
        <button class="secondary-button" @click="openCreateModal">创建第一条计划</button>
      </div>
      <div v-else class="schedule-grid">
        <article v-for="schedule in schedules" :key="schedule.id" class="schedule-card">
          <div class="schedule-card-header">
            <div>
              <div class="schedule-status">
                <span
                  class="status-dot"
                  :style="{ background: getRuntimeStatus(schedule).color }"
                />
                <span
                  class="status-pill"
                  :style="{
                    color: getRuntimeStatus(schedule).color,
                    background: getRuntimeStatus(schedule).background,
                  }"
                >
                  {{ getRuntimeStatus(schedule).label }}
                </span>
              </div>
              <h3>{{ schedule.name }}</h3>
              <p>{{ getFlowName(schedule.flow_id) }}</p>
            </div>
            <span class="trigger-pill">{{ getTriggerLabel(schedule) }}</span>
          </div>

          <dl class="schedule-meta">
            <div>
              <dt>店铺</dt>
              <dd>{{ schedule.shop_ids.map(getShopName).join('、') }}</dd>
            </div>
            <div>
              <dt>并发</dt>
              <dd>{{ schedule.concurrency }}</dd>
            </div>
            <div>
              <dt>未完成策略</dt>
              <dd>{{ getOverlapPolicyLabel(schedule.overlap_policy) }}</dd>
            </div>
            <div>
              <dt>上轮执行时间</dt>
              <dd>{{ formatDateTime(schedule.last_run_at) }}</dd>
            </div>
            <div>
              <dt>最近结果</dt>
              <dd>{{ getRecentResultLabel(schedule) }}</dd>
            </div>
            <div>
              <dt>下次触发</dt>
              <dd>{{ formatDateTime(schedule.next_run_at) }}</dd>
            </div>
          </dl>

          <div class="schedule-actions">
            <button class="ghost-button" @click="openEditModal(schedule)">编辑</button>
            <button
              class="secondary-button"
              :disabled="actioningId === schedule.id"
              @click="toggleSchedule(schedule)"
            >
              {{ schedule.enabled ? '暂停' : '恢复' }}
            </button>
            <button class="danger-button" @click="askDelete(schedule)">删除</button>
          </div>
        </article>
      </div>
    </section>

    <Modal
      :show="showEditor"
      :title="editingSchedule ? '编辑定时任务' : '新建定时任务'"
      width="920px"
      @close="showEditor = false"
    >
      <form class="editor-form" @submit.prevent="submitSchedule">
        <div class="field-grid">
          <label class="field">
            <span>任务名称</span>
            <input v-model="form.name" type="text" placeholder="例如：每日巡检" />
          </label>
          <label class="field">
            <span>流程模板</span>
            <select v-model="form.flowId">
              <option disabled value="">请选择流程</option>
              <option v-for="flow in flows" :key="flow.id" :value="flow.id">
                {{ flow.name }}
              </option>
            </select>
          </label>
        </div>

        <div class="field-grid">
          <label class="field">
            <span>并发数</span>
            <select v-model.number="form.concurrency">
              <option :value="1">1</option>
              <option :value="2">2</option>
              <option :value="3">3</option>
              <option :value="5">5</option>
              <option :value="10">10</option>
            </select>
          </label>
          <label class="field">
            <span>上轮未完成策略</span>
            <select v-model="form.overlapPolicy">
              <option value="wait">等完成</option>
              <option value="skip">跳过本轮</option>
              <option value="parallel">允许并行</option>
            </select>
          </label>
        </div>

        <section class="selector-panel">
          <div class="selector-panel-header">
            <div>
              <h3>选择店铺</h3>
              <p>可多选，执行时将复用这些目标。</p>
            </div>
          </div>
          <div class="shop-grid">
            <label v-for="shop in shops" :key="shop.id" class="shop-option">
              <input v-model="form.shopIds" type="checkbox" :value="shop.id" />
              <div>
                <strong>{{ shop.name }}</strong>
                <span>{{ shop.username || shop.id }}</span>
              </div>
            </label>
          </div>
        </section>

        <section class="selector-panel">
          <div class="selector-panel-header">
            <div>
              <h3>触发方式</h3>
              <p>固定间隔按分钟填写，Cron 使用标准 5 段表达式。</p>
            </div>
          </div>

          <div class="mode-switch">
            <button
              class="mode-button"
              :class="{ active: form.triggerMode === 'interval' }"
              type="button"
              @click="form.triggerMode = 'interval'"
            >
              固定间隔
            </button>
            <button
              class="mode-button"
              :class="{ active: form.triggerMode === 'cron' }"
              type="button"
              @click="form.triggerMode = 'cron'"
            >
              Cron 表达式
            </button>
          </div>

          <label v-if="form.triggerMode === 'interval'" class="field">
            <span>固定间隔（分钟）</span>
            <input v-model.number="form.intervalMinutes" type="number" min="1" />
          </label>

          <label v-else class="field">
            <span>Cron 表达式</span>
            <input v-model="form.cronExpr" type="text" placeholder="例如：*/30 * * * *" />
          </label>
        </section>
      </form>

      <template #footer>
        <button class="secondary-button" @click="showEditor = false">取消</button>
        <button class="primary-button" :disabled="isSaving" @click="submitSchedule">
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
  color: #b45309;
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
  max-width: 760px;
  line-height: 1.6;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.summary-card,
.panel,
.schedule-card,
.selector-panel {
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
  margin-bottom: 18px;
}

.panel-header h2,
.selector-panel-header h3 {
  margin: 0;
  font-size: 22px;
}

.panel-header p,
.selector-panel-header p {
  margin-top: 8px;
  color: #64748b;
  line-height: 1.5;
}

.schedule-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 18px;
}

.schedule-card {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.schedule-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.schedule-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-pill,
.trigger-pill {
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.trigger-pill {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
  white-space: nowrap;
}

.schedule-card-header h3 {
  margin: 0;
  font-size: 22px;
}

.schedule-card-header p {
  margin-top: 8px;
  color: #64748b;
}

.schedule-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 18px;
}

.schedule-meta div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.schedule-meta dt {
  color: #94a3b8;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.schedule-meta dd {
  color: #334155;
  line-height: 1.5;
}

.schedule-actions {
  display: flex;
  gap: 12px;
}

.editor-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field-grid {
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
  border-color: #b45309;
  box-shadow: 0 0 0 4px rgba(180, 83, 9, 0.12);
}

.selector-panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.shop-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.shop-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.shop-option input {
  margin-top: 2px;
}

.shop-option strong {
  display: block;
}

.shop-option span {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.mode-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.mode-button {
  border: 1px solid #cbd5e1;
  border-radius: 14px;
  padding: 12px 14px;
  background: #f8fafc;
  color: #334155;
  font-weight: 700;
  cursor: pointer;
}

.mode-button.active {
  border-color: transparent;
  background: linear-gradient(135deg, #b45309, #f59e0b);
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(245, 158, 11, 0.25);
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
  background: linear-gradient(135deg, #b45309, #f59e0b);
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(245, 158, 11, 0.22);
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

.primary-button:disabled,
.secondary-button:disabled,
.danger-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
  transform: none;
}

@media (max-width: 900px) {
  .page-header,
  .schedule-card-header,
  .schedule-meta,
  .schedule-actions {
    flex-direction: column;
  }

  .summary-grid,
  .field-grid,
  .shop-grid,
  .mode-switch {
    grid-template-columns: 1fr;
  }
}
</style>
