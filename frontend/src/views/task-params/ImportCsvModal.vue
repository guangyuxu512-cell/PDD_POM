<script setup lang="ts">
import Modal from '../../components/Modal.vue'
import type { AvailableTask, Flow } from '../../api/types'
import type { ImportBindingMode } from './useTaskParamsStore'
import { useTaskParamsContext } from './useTaskParamsStore'

const props = defineProps<{
  show: boolean
  availableTasks: AvailableTask[]
  flows: Flow[]
  importBindingMode: ImportBindingMode
}>()

const emit = defineEmits<{
  close: []
  imported: [mode: ImportBindingMode]
}>()

const store = useTaskParamsContext()

async function submitImport() {
  const imported = await store.handleImport()
  if (imported) {
    emit('imported', store.importBindingMode)
  }
}
</script>

<template>
  <Modal :show="show" title="CSV导入" width="720px" @close="emit('close')">
    <div class="import-form">
      <div class="form-group">
        <label>绑定方式</label>
        <div class="mode-switch">
          <button class="mode-button" :class="{ active: store.importBindingMode === 'task' }" type="button" @click="store.importBindingMode = 'task'">
            绑定任务
          </button>
          <button class="mode-button" :class="{ active: store.importBindingMode === 'flow' }" type="button" @click="store.importBindingMode = 'flow'">
            绑定流程
          </button>
        </div>
      </div>

      <div class="form-group">
        <label>{{ props.importBindingMode === 'task' ? '任务类型' : '流程模板' }}</label>
        <select v-if="props.importBindingMode === 'task'" v-model="store.importTaskName">
          <option value="">请选择任务</option>
          <option v-for="task in availableTasks" :key="task.name" :value="task.name">{{ task.name }}</option>
        </select>
        <select v-else v-model="store.importFlowId">
          <option value="">请选择流程</option>
          <option v-for="flow in flows" :key="flow.id" :value="flow.id">{{ flow.name }}</option>
        </select>
      </div>

      <div class="template-box">
        <div class="template-header">
          <h4>CSV 模板说明</h4>
          <button class="btn btn-light" @click="store.downloadTemplate">下载模板</button>
        </div>
        <p>列名：{{ store.currentTemplateColumns.join('、') }}</p>
        <p>“店铺ID”列支持填写店铺 ID 或店铺名称，导入时会自动匹配。</p>
        <p v-if="store.currentRequiredFields.length > 0">必填字段：{{ store.currentRequiredFields.join('、') }}</p>
        <p v-if="props.importBindingMode === 'flow'">流程模式下，除“店铺ID”外的列都会进入流程共享参数。</p>
        <p>{{ store.currentTemplateExample }}</p>
        <p>示例行：{{ store.currentTemplateSampleRow }}</p>
      </div>

      <div class="form-group">
        <label>上传 CSV 文件</label>
        <input type="file" accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" @change="store.handleFileChange" />
        <span class="file-name">{{ store.selectedFile?.name || '未选择文件' }}</span>
      </div>

      <div v-if="store.importSummary" class="import-result">
        <strong>导入结果</strong>
        <p>成功 {{ store.importSummary.success_count }} 条 / 跳过 {{ store.importSummary.failed_count }} 条</p>
        <p v-if="store.importSummary.errors.length > 0" class="error-text">
          {{ store.importSummary.errors.slice(0, 3).join('；') }}
        </p>
      </div>
    </div>

    <template #footer>
      <button class="btn btn-secondary" @click="emit('close')">关闭</button>
      <button class="btn btn-primary" :disabled="store.importing" @click="submitImport">
        {{ store.importing ? '导入中...' : '开始导入' }}
      </button>
    </template>
  </Modal>
</template>

<style scoped>
.import-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.mode-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.mode-button {
  border: 1px solid var(--color-primary-border);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: var(--font-size-body);
  font-weight: 600;
  cursor: pointer;
}

.mode-button.active {
  background: var(--color-primary);
  color: #ffffff;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-group label,
.template-box h4 {
  margin: 0;
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
}

.form-group select,
.form-group input[type='file'] {
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  color: var(--color-text);
}

.template-box,
.import-result {
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  background: var(--color-bg-hover);
  border: 1px solid var(--color-border);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.template-box p,
.import-result p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.file-name,
.error-text {
  color: var(--color-danger);
}

.btn {
  border: none;
  border-radius: var(--radius-md);
  padding: 10px 16px;
  font-size: var(--font-size-body);
  cursor: pointer;
}

.btn-primary {
  background: var(--color-primary);
  color: #ffffff;
}

.btn-secondary {
  background: var(--color-text-secondary);
  color: #ffffff;
}

.btn-light {
  background: var(--color-border-light);
  color: var(--color-text);
}

@media (max-width: 900px) {
  .template-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

