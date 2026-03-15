<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { get, put, post } from '../api'
import { toast } from '../utils/toast'

interface SystemConfig {
  redis_url: string
  agent_machine_id?: string
  captcha_provider: string
  captcha_api_key?: string
  default_proxy?: string
  chrome_path?: string
  max_browser_instances: number
}

const config = ref<SystemConfig>({
  redis_url: '',
  agent_machine_id: '',
  captcha_provider: 'yescaptcha',
  captcha_api_key: '',
  default_proxy: '',
  chrome_path: '',
  max_browser_instances: 5
})

const testingRedis = ref(false)

interface RedisTestResult {
  latency_ms: number
}

const loadConfig = async () => {
  const data = await get<any>('/api/system/config')
  config.value = {
    redis_url: data.redis_url || '',
    agent_machine_id: data.agent_machine_id || '',
    captcha_provider: data.captcha_provider || 'yescaptcha',
    captcha_api_key: data.captcha_api_key || '',
    default_proxy: data.default_proxy || '',
    chrome_path: data.chrome_path || '',
    max_browser_instances: data.max_browser_instances || 5
  }
}

const handleSave = async () => {
  await put('/api/system/config', config.value)
  alert('配置保存成功\n机器码修改后需重启 Worker 生效')
}

const testRedis = async () => {
  testingRedis.value = true
  try {
    const result = await post<RedisTestResult>('/api/system/test-redis', {
      redis_url: config.value.redis_url
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
    api_key: config.value.captcha_api_key
  })
  alert('验证码服务测试成功')
}

const healthCheck = async () => {
  const health = await get<any>('/api/system/health')
  const status = health.status === 'healthy' ? '健康' : '异常'
  alert(`系统状态：${status}\n运行时长：${Math.floor(health.uptime / 3600)}小时\nCPU：${health.cpu_usage}\n内存：${health.memory_usage}`)
}

onMounted(loadConfig)
</script>

<template>
  <div class="settings">
    <h1>系统设置</h1>

    <div class="settings-container">
      <form class="settings-form" @submit.prevent="handleSave">
        <div class="form-section">
          <h3>基础配置</h3>
          <div class="form-group">
            <label>Redis 地址</label>
            <input v-model="config.redis_url" type="text" placeholder="redis://192.168.1.100:6379" required />
            <button type="button" class="btn-test" :disabled="testingRedis" @click="testRedis">
              {{ testingRedis ? '测试中...' : '测试连接' }}
            </button>
          </div>

          <div class="form-group">
            <label>机器码</label>
            <input v-model="config.agent_machine_id" type="text" placeholder="例如: office-pc-001" />
            <span class="hint">用于标识当前机器的 Celery Worker 队列名称，修改后需重启 Worker 生效</span>
          </div>

          <div class="form-group">
            <label>最大浏览器实例数</label>
            <input v-model.number="config.max_browser_instances" type="number" min="1" max="10" required />
          </div>

          <div class="form-group">
            <label>Chrome 路径</label>
            <input v-model="config.chrome_path" type="text" placeholder="留空使用系统默认" />
          </div>

          <div class="form-group">
            <label>默认代理</label>
            <input v-model="config.default_proxy" type="text" placeholder="127.0.0.1:7890" />
          </div>
        </div>

        <div class="form-section">
          <h3>验证码服务</h3>
          <div class="form-group">
            <label>服务商</label>
            <select v-model="config.captcha_provider" required>
              <option value="yescaptcha">YesCaptcha</option>
              <option value="2captcha">2Captcha</option>
              <option value="anticaptcha">AntiCaptcha</option>
            </select>
          </div>

          <div class="form-group">
            <label>API 密钥</label>
            <input v-model="config.captcha_api_key" type="password" placeholder="验证码服务 API Key" />
            <button type="button" class="btn-test" @click="testCaptcha">测试验证码</button>
          </div>
        </div>

        <div class="form-section">
          <h3>系统监控</h3>
          <button type="button" class="btn btn-secondary" @click="healthCheck">健康检查</button>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary btn-large">保存配置</button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.settings {
  color: #1a1a2e;
}

h1 {
  font-size: 28px;
  margin-bottom: 24px;
  color: #1a1a2e;
}

h3 {
  font-size: 18px;
  margin-bottom: 16px;
  color: #1a1a2e;
}

.settings-container {
  max-width: 800px;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.form-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
  position: relative;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.hint {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.5;
}

.form-group input,
.form-group select {
  padding: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #1a1a2e;
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
}

.btn-test {
  margin-top: 8px;
  padding: 8px 16px;
  background: #f3f4f6;
  border: none;
  border-radius: 6px;
  color: #1a1a2e;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  align-self: flex-start;
}

.btn-test:hover {
  background: #e5e7eb;
}

.btn-test:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #f3f4f6;
  color: #1a1a2e;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.btn-large {
  padding: 14px 32px;
  font-size: 16px;
}

.form-actions {
  display: flex;
  justify-content: center;
  padding-top: 8px;
}
</style>
