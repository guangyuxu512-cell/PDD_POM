<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { AvailableTask, Flow, Shop } from '../../api/types'
import { toast } from '../../utils/toast'

type ExecuteMode = 'flow' | 'task'

const props = defineProps<{
  flows: Flow[]
  tasks: AvailableTask[]
  shops: Shop[]
  isLoading: boolean
  hasActiveBatch: boolean
  isStarting: boolean
  isStopping: boolean
}>()

const emit = defineEmits<{
  start: [payload: { flow_id?: string; task_name?: string; shop_ids: string[]; concurrency: number }]
  stop: []
}>()

const mode = ref<ExecuteMode>('flow')
const selectedFlowId = ref('')
const selectedTaskName = ref('')
const selectedShopIds = ref<string[]>([])
const concurrency = ref(1)

const totalShops = computed(() => props.shops.length)
const isAllSelected = computed(
  () => totalShops.value > 0 && selectedShopIds.value.length === totalShops.value,
)

watch(
  () => props.flows,
  (flows) => {
    if (!selectedFlowId.value && flows[0]) {
      selectedFlowId.value = flows[0].id
    }
  },
  { immediate: true },
)

watch(
  () => props.tasks,
  (tasks) => {
    if (!selectedTaskName.value && tasks[0]) {
      selectedTaskName.value = tasks[0].name
    }
  },
  { immediate: true },
)

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedShopIds.value = []
    return
  }

  selectedShopIds.value = props.shops.map((shop) => shop.id)
}

function submitStart() {
  if (selectedShopIds.value.length === 0) {
    toast.warning('请至少选择一个店铺')
    return
  }

  if (mode.value === 'flow' && !selectedFlowId.value) {
    toast.warning('请选择流程模板')
    return
  }

  if (mode.value === 'task' && !selectedTaskName.value) {
    toast.warning('请选择单个任务')
    return
  }

  emit('start', {
    flow_id: mode.value === 'flow' ? selectedFlowId.value : undefined,
    task_name: mode.value === 'task' ? selectedTaskName.value : undefined,
    shop_ids: selectedShopIds.value,
    concurrency: concurrency.value,
  })
}
</script>

<template>
  <section class="panel setup-panel">
    <div class="panel-header">
      <div>
        <h2>执行配置</h2>
        <p>流程和任务选项会自动读取后端当前可用的数据。</p>
      </div>
    </div>

    <div v-if="isLoading" class="empty-state">正在加载执行配置...</div>
    <div v-else class="setup-form">
      <div class="mode-switch">
        <button class="mode-button" :class="{ active: mode === 'flow' }" @click="mode = 'flow'">流程模式</button>
        <button class="mode-button" :class="{ active: mode === 'task' }" @click="mode = 'task'">单任务模式</button>
      </div>

      <label v-if="mode === 'flow'" class="field">
        <span>流程模板</span>
        <select v-model="selectedFlowId">
          <option disabled value="">请选择流程模板</option>
          <option v-for="flow in flows" :key="flow.id" :value="flow.id">{{ flow.name }} · {{ flow.steps.length }} 步</option>
        </select>
      </label>

      <label v-else class="field">
        <span>单个任务</span>
        <select v-model="selectedTaskName">
          <option disabled value="">请选择任务</option>
          <option v-for="task in tasks" :key="task.name" :value="task.name">{{ task.name }} · {{ task.description }}</option>
        </select>
      </label>

      <label class="field">
        <span>并发数量</span>
        <select v-model.number="concurrency">
          <option :value="1">1</option>
          <option :value="2">2</option>
          <option :value="3">3</option>
          <option :value="5">5</option>
          <option :value="10">10</option>
        </select>
      </label>

      <section class="shop-selector">
        <div class="shop-selector-header">
          <div>
            <h3>目标店铺</h3>
            <p>已选择 {{ selectedShopIds.length }} / {{ totalShops }}</p>
          </div>
          <button class="secondary-button" @click="toggleSelectAll">{{ isAllSelected ? '取消全选' : '全选' }}</button>
        </div>

        <div v-if="shops.length === 0" class="shop-empty">暂无可执行店铺</div>
        <div v-else class="shop-option-grid">
          <label v-for="shop in shops" :key="shop.id" class="shop-option">
            <input v-model="selectedShopIds" type="checkbox" :value="shop.id" />
            <div>
              <strong>{{ shop.name }}</strong>
              <span>{{ shop.username || shop.id }}</span>
            </div>
          </label>
        </div>
      </section>

      <div class="action-row">
        <button class="primary-button" :disabled="isStarting" @click="submitStart">
          {{ isStarting ? '启动中...' : '开始执行' }}
        </button>
        <button class="danger-button" :disabled="!hasActiveBatch || isStopping" @click="emit('stop')">
          {{ isStopping ? '停止中...' : '全部停止' }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: var(--spacing-lg);
}

.panel-header {
  margin-bottom: var(--spacing-md);
}

.panel-header h2 {
  margin: 0;
  font-size: var(--font-size-h2);
}

.panel-header p {
  margin-top: var(--spacing-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.setup-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.mode-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.mode-button {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  background: var(--color-bg-hover);
  color: var(--color-text-secondary);
  font-weight: 700;
  cursor: pointer;
}

.mode-button.active {
  border-color: transparent;
  background: var(--color-primary);
  color: #ffffff;
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.field span {
  color: var(--color-text-secondary);
  font-size: var(--font-size-body);
  font-weight: 600;
}

.field select {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  color: var(--color-text);
  font-size: var(--font-size-body);
}

.shop-selector {
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  background: var(--color-bg-hover);
  border: 1px solid var(--color-border);
}

.shop-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
  margin-bottom: 14px;
}

.shop-selector-header h3 {
  margin: 0;
  font-size: var(--font-size-h3);
}

.shop-selector-header p,
.shop-option span,
.shop-empty {
  color: var(--color-text-secondary);
}

.shop-selector-header p {
  margin-top: 6px;
}

.shop-option-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  max-height: 280px;
  overflow: auto;
}

.shop-option {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: 12px;
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
}

.shop-option span {
  display: block;
  margin-top: 4px;
  font-size: 13px;
}

.shop-empty {
  text-align: center;
  padding: var(--spacing-md) 0;
}

.action-row {
  display: flex;
  gap: var(--spacing-sm);
}

.primary-button,
.secondary-button,
.danger-button {
  border: none;
  border-radius: var(--radius-md);
  padding: 11px 16px;
  font-size: var(--font-size-body);
  font-weight: 600;
  cursor: pointer;
}

.primary-button {
  background: var(--color-primary);
  color: #ffffff;
}

.secondary-button {
  background: var(--color-border);
  color: var(--color-text);
}

.danger-button {
  background: var(--color-danger-light);
  color: #b91c1c;
}

.empty-state {
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  text-align: center;
}

@media (max-width: 900px) {
  .shop-selector-header,
  .action-row {
    flex-direction: column;
  }
}
</style>
