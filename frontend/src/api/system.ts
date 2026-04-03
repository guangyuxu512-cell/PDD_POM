import { api } from './index'

export async function testRedis(
  redisUrl?: string,
): Promise<{ success: boolean; message: string; data?: { latency_ms: number } }> {
  try {
    const data = await api.post<{ latency_ms: number }>('/api/system/test-redis', {
      redis_url: redisUrl ?? null,
    })
    return { success: true, message: 'Redis 连接成功', data }
  }
  catch (error: any) {
    return { success: false, message: error.message }
  }
}

export async function testCaptcha(
  apiKey?: string,
): Promise<{ success: boolean; message: string }> {
  try {
    await api.post('/api/system/test-captcha', { api_key: apiKey ?? null })
    return { success: true, message: '验证码服务连接成功' }
  }
  catch (error: any) {
    return { success: false, message: error.message }
  }
}

export async function testFeishu(
  webhookUrl?: string,
  secret?: string,
): Promise<{ success: boolean; message: string }> {
  try {
    await api.post('/api/system/test-feishu-webhook', {
      webhook_url: webhookUrl ?? null,
      secret: secret ?? null,
    })
    return { success: true, message: '飞书 Webhook 测试成功' }
  }
  catch (error: any) {
    return { success: false, message: error.message }
  }
}
