<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { get, post, put } from '../api'
import { toast } from '../utils/toast'

interface SystemConfig {
  redis_url: string
  agent_machine_id?: string
  feishu_webhook_url?: string
  feishu_app_id?: string
  feishu_app_secret?: string
  feishu_bitable_app_token?: string
  feishu_bitable_table_id?: string
  captcha_provider: string
  captcha_api_key?: string
  default_proxy?: string
  chrome_path?: string
  max_browser_instances: number
}

interface RedisTestResult {
  latency_ms: number
}

const config = ref<SystemConfig>({
  redis_url: '',
  agent_machine_id: '',
  feishu_webhook_url: '',
  feishu_app_id: '',
  feishu_app_secret: '',
  feishu_bitable_app_token: '',
  feishu_bitable_table_id: '',
  captcha_provider: 'yescaptcha',
  captcha_api_key: '',
  default_proxy: '',
  chrome_path: '',
  max_browser_instances: 5,
})
const testingRedis = ref(false)
const testingFeishu = ref(false)
const inputClass =
  'w-full rounded-md border border-brand-300/50 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'
const sectionClass = 'rounded-md border border-brand-300/50 bg-white p-5 shadow-sm'
const secondaryButtonClass =
  'rounded-md border border-brand-300/50 bg-white px-3 py-1.5 text-sm text-brand-700 transition hover:bg-brand-100/50 hover:text-brand-900 disabled:cursor-not-allowed disabled:opacity-60'
const primaryButtonClass =
  'rounded-md bg-brand-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700'

const loadConfig = async () => {
  const data = await get<any>('/api/system/config')
  config.value = {
    redis_url: data.redis_url || '',
    agent_machine_id: data.agent_machine_id || '',
    feishu_webhook_url: data.feishu_webhook_url || '',
    feishu_app_id: data.feishu_app_id || '',
    feishu_app_secret: data.feishu_app_secret || '',
    feishu_bitable_app_token: data.feishu_bitable_app_token || '',
    feishu_bitable_table_id: data.feishu_bitable_table_id || '',
    captcha_provider: data.captcha_provider || 'yescaptcha',
    captcha_api_key: data.captcha_api_key || '',
    default_proxy: data.default_proxy || '',
    chrome_path: data.chrome_path || '',
    max_browser_instances: data.max_browser_instances || 5,
  }
}

const handleSave = async () => {
  await put('/api/system/config', config.value)
  alert('配置保存成功\n核心配置（Redis 地址、机器码等）修改后需重启后端服务和 Worker 生效')
}

const testRedis = async () => {
  testingRedis.value = true
  try {
    const result = await post<RedisTestResult>('/api/system/test-redis', {
      redis_url: config.value.redis_url,
    })
    toast.success(`Redis 连接成功，延迟 ${result.latency_ms} ms`)
  } catch (error: any) {
    toast.error(error?.message || 'Redis 连接测试失败')
  } finally {
    testingRedis.value = false
  }
}

const testCaptcha = async () => {
  await post('/api/system/test-captcha', {
    provider: config.value.captcha_provider,
    api_key: config.value.captcha_api_key,
  })
  alert('验证码服务测试成功')
}

const testFeishuWebhook = async () => {
  testingFeishu.value = true
  try {
    await post('/api/feishu/test-webhook', {
      webhook_url: config.value.feishu_webhook_url,
    })
    toast.success('飞书 Webhook 测试成功')
  } catch (error: any) {
    toast.error(error?.message || '飞书 Webhook 测试失败')
  } finally {
    testingFeishu.value = false
  }
}

const healthCheck = async () => {
  const health = await get<any>('/api/system/health')
  const status = health.status === 'healthy' ? '健康' : '异常'
  alert(
    `系统状态：${status}\n运行时长：${Math.floor(health.uptime / 3600)} 小时\nCPU：${health.cpu_usage}\n内存：${health.memory_usage}`,
  )
}

onMounted(loadConfig)
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-6">
    <div class="space-y-1">
      <h1 class="text-lg font-semibold text-gray-900">系统设置</h1>
      <p class="text-xs text-brand-500">集中维护 Redis、机器码、验证码服务、飞书通知与浏览器基础配置。</p>
    </div>

    <form class="space-y-6" @submit.prevent="handleSave">
      <section :class="sectionClass">
        <div class="space-y-1">
          <h2 class="text-lg font-semibold text-gray-900">基础配置</h2>
          <p class="text-xs text-brand-500">这些配置会影响 Worker 通信、浏览器初始化和默认网络环境。</p>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <div class="space-y-2 md:col-span-2">
            <label class="text-xs font-medium text-brand-700">Redis 地址</label>
            <input v-model="config.redis_url" :class="inputClass" type="text" placeholder="redis://192.168.1.100:6379" required />
            <button type="button" :class="secondaryButtonClass" :disabled="testingRedis" @click="testRedis">
              {{ testingRedis ? '测试中...' : '测试连接' }}
            </button>
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">机器码</label>
            <input v-model="config.agent_machine_id" :class="inputClass" type="text" placeholder="例如: office-pc-001" />
            <p class="text-xs leading-5 text-brand-500">用于标识当前机器的 Celery Worker 队列名称，修改后需重启 Worker 生效</p>
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">最大浏览器实例数</label>
            <input v-model.number="config.max_browser_instances" :class="inputClass" type="number" min="1" max="10" required />
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">Chrome 路径</label>
            <input v-model="config.chrome_path" :class="inputClass" type="text" placeholder="留空使用系统默认" />
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">默认代理</label>
            <input v-model="config.default_proxy" :class="inputClass" type="text" placeholder="127.0.0.1:7890" />
          </div>
        </div>
      </section>

      <section :class="sectionClass">
        <div class="space-y-1">
          <h2 class="text-lg font-semibold text-gray-900">验证码服务</h2>
          <p class="text-xs text-brand-500">配置当前使用的验证码平台并验证 API Key 是否可用。</p>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">服务商</label>
            <select v-model="config.captcha_provider" :class="inputClass" required>
              <option value="yescaptcha">YesCaptcha</option>
              <option value="2captcha">2Captcha</option>
              <option value="anticaptcha">AntiCaptcha</option>
            </select>
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">API 密钥</label>
            <input v-model="config.captcha_api_key" :class="inputClass" type="password" placeholder="验证码服务 API Key" />
            <button type="button" :class="secondaryButtonClass" @click="testCaptcha">测试验证码</button>
          </div>
        </div>
      </section>

      <section :class="sectionClass">
        <div class="space-y-1">
          <h2 class="text-lg font-semibold text-gray-900">飞书配置</h2>
          <p class="text-xs text-brand-500">用于通知推送和多维表格回填，按需填写即可。</p>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <div class="space-y-2 md:col-span-2">
            <label class="text-xs font-medium text-brand-700">Webhook 地址</label>
            <input
              v-model="config.feishu_webhook_url"
              :class="inputClass"
              type="text"
              placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
            />
            <button type="button" :class="secondaryButtonClass" :disabled="testingFeishu" @click="testFeishuWebhook">
              {{ testingFeishu ? '测试中...' : '测试 Webhook' }}
            </button>
            <p class="text-xs leading-5 text-brand-500">飞书群机器人的 Webhook 地址，用于发送通知</p>
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">App ID</label>
            <input
              v-model="config.feishu_app_id"
              :class="inputClass"
              type="text"
              placeholder="cli_xxxxxxxxx（多维表格回调用，不需要可留空）"
            />
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">App Secret</label>
            <input
              v-model="config.feishu_app_secret"
              :class="inputClass"
              type="password"
              placeholder="飞书应用密钥（不需要可留空）"
            />
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">多维表格 App Token</label>
            <input
              v-model="config.feishu_bitable_app_token"
              :class="inputClass"
              type="text"
              placeholder="bascnxxxxxxxxx（不需要可留空）"
            />
          </div>

          <div class="space-y-2">
            <label class="text-xs font-medium text-brand-700">多维表格 Table ID</label>
            <input
              v-model="config.feishu_bitable_table_id"
              :class="inputClass"
              type="text"
              placeholder="tblxxxxxxxxx（不需要可留空）"
            />
          </div>
        </div>
      </section>

      <section :class="sectionClass">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div class="space-y-1">
            <h2 class="text-lg font-semibold text-gray-900">系统监控</h2>
            <p class="text-xs text-brand-500">快速查看当前服务健康状态和系统资源信息。</p>
          </div>
          <button type="button" :class="secondaryButtonClass" @click="healthCheck">健康检查</button>
        </div>
      </section>

      <div class="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p class="text-xs text-brand-500">保存后，涉及连接参数和机器标识的改动需要重启相关服务才会生效。</p>
        <button type="submit" :class="primaryButtonClass">保存配置</button>
      </div>
    </form>
  </div>
</template>
