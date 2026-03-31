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
    <div class="space-y-5">
      <div class="space-y-2">
        <label class="text-sm font-medium text-gray-800">绑定方式</label>
        <div class="grid grid-cols-2 gap-2">
          <button
            type="button"
            class="rounded-md border px-3 py-2.5 text-sm font-semibold transition"
            :class="store.importBindingMode === 'task'
              ? 'border-brand-500 bg-brand-900 text-white'
              : 'border-brand-300 bg-white text-gray-700 hover:bg-brand-100'"
            @click="store.importBindingMode = 'task'"
          >
            绑定任务
          </button>
          <button
            type="button"
            class="rounded-md border px-3 py-2.5 text-sm font-semibold transition"
            :class="store.importBindingMode === 'flow'
              ? 'border-brand-500 bg-brand-900 text-white'
              : 'border-brand-300 bg-white text-gray-700 hover:bg-brand-100'"
            @click="store.importBindingMode = 'flow'"
          >
            绑定流程
          </button>
        </div>
      </div>

      <div class="space-y-2">
        <label class="text-sm font-medium text-gray-800">
          {{ props.importBindingMode === 'task' ? '任务类型' : '流程模板' }}
        </label>
        <select
          v-if="props.importBindingMode === 'task'"
          v-model="store.importTaskName"
          class="w-full rounded-md border border-brand-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          <option value="">请选择任务</option>
          <option v-for="task in availableTasks" :key="task.name" :value="task.name">
            {{ task.name }}
          </option>
        </select>
        <select
          v-else
          v-model="store.importFlowId"
          class="w-full rounded-md border border-brand-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          <option value="">请选择流程</option>
          <option v-for="flow in flows" :key="flow.id" :value="flow.id">
            {{ flow.name }}
          </option>
        </select>
      </div>

      <div class="space-y-1.5 rounded-md border border-brand-300/50 bg-brand-100/40 p-4">
        <div class="flex items-center justify-between gap-3">
          <h4 class="text-sm font-medium text-gray-800">CSV 模板说明</h4>
          <button
            type="button"
            class="rounded-md border border-brand-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-brand-100"
            @click="store.downloadTemplate"
          >
            下载模板
          </button>
        </div>
        <p class="text-sm text-gray-700">列名：{{ store.currentTemplateColumns.join('、') }}</p>
        <p class="text-sm text-gray-700">“店铺ID”列支持填写店铺 ID 或店铺名称，导入时会自动匹配。</p>
        <p v-if="store.currentRequiredFields.length > 0" class="text-sm text-gray-700">
          必填字段：{{ store.currentRequiredFields.join('、') }}
        </p>
        <p v-if="props.importBindingMode === 'flow'" class="text-sm text-gray-700">
          流程模式下，除“店铺ID”外的列都会进入流程共享参数。
        </p>
        <p class="text-sm text-gray-700">{{ store.currentTemplateExample }}</p>
        <p class="text-sm text-gray-700">示例行：{{ store.currentTemplateSampleRow }}</p>
      </div>

      <div class="space-y-2">
        <label class="text-sm font-medium text-gray-800">上传 CSV 文件</label>
        <input
          type="file"
          accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          class="block w-full rounded-md border border-brand-300 bg-white px-3 py-2 text-sm text-gray-700 file:mr-3 file:rounded-md file:border-0 file:bg-brand-700 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-white hover:file:bg-brand-900"
          @change="store.handleFileChange"
        />
        <span class="text-xs text-gray-600">
          {{ store.selectedFile?.name || '未选择文件' }}
        </span>
      </div>

      <div
        v-if="store.importSummary"
        class="space-y-1 rounded-md border border-brand-300/50 bg-brand-100/40 p-4"
      >
        <strong class="text-sm font-medium text-gray-800">导入结果</strong>
        <p class="text-sm text-gray-700">
          成功 {{ store.importSummary.success_count }} 条 / 跳过 {{ store.importSummary.failed_count }} 条
        </p>
        <p v-if="store.importSummary.errors.length > 0" class="text-sm text-rose-600">
          {{ store.importSummary.errors.slice(0, 3).join('；') }}
        </p>
      </div>
    </div>

    <template #footer>
      <button
        type="button"
        class="rounded-md border border-brand-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-brand-100"
        @click="emit('close')"
      >
        关闭
      </button>
      <button
        type="button"
        class="rounded-md bg-brand-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="store.importing"
        @click="submitImport"
      >
        {{ store.importing ? '导入中...' : '开始导入' }}
      </button>
    </template>
  </Modal>
</template>

