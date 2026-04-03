<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { batchUpdateSettings, listSettings } from '../api/settings'
import { testCaptcha, testFeishu, testRedis } from '../api/system'
import type { SettingItem } from '../api/types'
import { toast } from '../utils/toast'

const categoryMap: Record<string, string> = {
  general: '通用设置',
  celery: '任务队列',
  notification: '通知配置',
  security: '安全配置',
}

const numericKeys = new Set(['app_port', 'max_concurrency'])
const booleanKeys = new Set(['browser_headless', 'auto_restart_browser'])
const TEST_KEYS = new Set(['celery_broker_url', 'captcha_api_key', 'feishu_webhook_url'])

const settingsList = ref<SettingItem[]>([])
const activeCategory = ref('general')
const isSaving = ref(false)
const formData = reactive<Record<string, string>>({})
const testResults = ref<Record<string, { ok: boolean; msg: string } | null>>({})
const testLoading = ref<Record<string, boolean>>({})

const categories = computed(() =>
  Object.entries(categoryMap)
    .filter(([key]) => settingsList.value.some(item => item.category === key))
    .map(([key, label]) => ({ key, label })),
)

const filteredSettings = computed(() =>
  settingsList.value.filter(item => item.category === activeCategory.value),
)

const resolveInputType = (item: SettingItem) => {
  if (item.encrypted) {
    return 'password'
  }
  if (numericKeys.has(item.key)) {
    return 'number'
  }
  return 'text'
}

const loadSettings = async () => {
  const data = await listSettings()
  settingsList.value = data.list

  Object.keys(formData).forEach((key) => {
    delete formData[key]
  })

  data.list.forEach((item) => {
    formData[item.key] = item.encrypted ? '' : (item.value ?? '')
  })

  if (!categories.value.some(item => item.key === activeCategory.value) && categories.value[0]) {
    activeCategory.value = categories.value[0].key
  }
}

const handleSave = async () => {
  isSaving.value = true
  try {
    const items = filteredSettings.value
      .filter((item) => {
        const value = formData[item.key]
        if (item.encrypted && !value) {
          return false
        }
        return true
      })
      .map((item) => ({
        key: item.key,
        value: formData[item.key] || null,
      }))

    await batchUpdateSettings(items)
    toast.success('设置已保存')
    await loadSettings()
  } catch (error: any) {
    toast.error(error?.message || '保存设置失败')
  } finally {
    isSaving.value = false
  }
}

onMounted(async () => {
  try {
    await loadSettings()
  } catch (error: any) {
    toast.error(error?.message || '加载系统设置失败')
  }
})

const runTest = async (key: string) => {
  if (testLoading.value[key]) return
  testLoading.value[key] = true
  testResults.value[key] = null

  let result: { success: boolean; message: string; data?: any }

  if (key === 'celery_broker_url') {
    result = await testRedis(formData[key] || undefined)
    if (result.success && result.data?.latency_ms !== undefined) {
      result.message = `连接成功，延迟 ${result.data.latency_ms}ms`
    }
  }
  else if (key === 'captcha_api_key') {
    result = await testCaptcha(formData[key] || undefined)
  }
  else if (key === 'feishu_webhook_url') {
    result = await testFeishu(formData[key] || undefined, formData['feishu_secret'] || undefined)
  }
  else {
    testLoading.value[key] = false
    return
  }

  testResults.value[key] = { ok: result.success, msg: result.message }
  testLoading.value[key] = false

  setTimeout(() => {
    testResults.value[key] = null
  }, 3000)
}
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-semibold text-gray-900">系统设置</h1>
      <p class="text-sm text-gray-500">应用运行参数统一保存在本地数据库，敏感字段以脱敏方式展示。</p>
    </header>

    <div class="flex flex-wrap gap-1 rounded-md bg-gray-100 p-0.5">
      <button
        v-for="cat in categories"
        :key="cat.key"
        :class="[
          'flex-1 rounded-md px-3 py-2 text-sm transition',
          activeCategory === cat.key
            ? 'bg-white font-medium text-gray-900 shadow-sm'
            : 'text-gray-500 hover:text-gray-900',
        ]"
        @click="activeCategory = cat.key"
      >
        {{ cat.label }}
      </button>
    </div>

    <section class="rounded-md border border-brand-200/50 bg-white p-5 shadow-sm">
      <div
        v-for="item in filteredSettings"
        :key="item.key"
        class="grid gap-4 border-b border-gray-100 py-4 last:border-b-0 md:grid-cols-[1fr_1.5fr]"
      >
        <div class="space-y-1">
          <label class="text-sm font-medium text-gray-900">
            {{ item.label || item.key }}
          </label>
          <p v-if="item.hint" class="text-xs text-gray-500">
            {{ item.hint }}
          </p>
        </div>

        <select
          v-if="booleanKeys.has(item.key)"
          v-model="formData[item.key]"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          <option value="true">true</option>
          <option value="false">false</option>
        </select>

        <div v-else-if="TEST_KEYS.has(item.key)" class="space-y-1.5">
          <div class="flex gap-2">
            <input
              v-model="formData[item.key]"
              :type="resolveInputType(item)"
              :placeholder="item.encrypted && item.has_value ? '••••••••（已设置，留空不修改）' : '请输入...'"
              class="min-w-0 flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <button
              :disabled="testLoading[item.key]"
              class="shrink-0 rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
              @click="runTest(item.key)"
            >
              {{ testLoading[item.key] ? '测试中...' : '测试连接' }}
            </button>
          </div>
          <p
            v-if="testResults[item.key]"
            :class="testResults[item.key]!.ok ? 'text-green-600' : 'text-red-600'"
            class="text-xs"
          >
            {{ testResults[item.key]!.msg }}
          </p>
        </div>

        <input
          v-else
          v-model="formData[item.key]"
          :type="resolveInputType(item)"
          :placeholder="item.encrypted && item.has_value ? '••••••••（已设置，留空不修改）' : '请输入...'"
          class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
      </div>
    </section>

    <div class="flex justify-end">
      <button
        :disabled="isSaving"
        class="rounded-md bg-brand-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        @click="handleSave"
      >
        {{ isSaving ? '保存中...' : '保存设置' }}
      </button>
    </div>
  </div>
</template>
