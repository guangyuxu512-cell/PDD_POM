const mockShops = [
  {
    id: 'shop_001',
    name: '旗舰店A',
    username: 'flagship_a',
    proxy: '127.0.0.1:7890',
    status: 'online',
    last_login: '2026-03-06 10:30:00',
    cookie_status: 'valid',
    smtp_host: 'imap.qq.com',
    smtp_port: 993,
    smtp_user: 'flagship_a@qq.com',
    smtp_protocol: 'IMAP'
  },
  {
    id: 'shop_002',
    name: '专营店B',
    username: 'store_b',
    proxy: '',
    status: 'offline',
    last_login: '2026-03-05 18:20:00',
    cookie_status: 'valid',
    smtp_host: 'imap.163.com',
    smtp_port: 993,
    smtp_user: 'store_b@163.com',
    smtp_protocol: 'IMAP'
  },
  {
    id: 'shop_003',
    name: '测试店C',
    username: 'test_c',
    proxy: '127.0.0.1:7891',
    status: 'expired',
    last_login: '2026-02-28 14:15:00',
    cookie_status: 'expired',
    smtp_host: 'smtp.gmail.com',
    smtp_port: 587,
    smtp_user: 'test_c@gmail.com',
    smtp_protocol: 'SMTP'
  }
]

const mockTasks = [
  {
    id: 'task_001',
    shop_id: 'shop_001',
    shop_name: '旗舰店A',
    task_name: '登录',
    status: 'success',
    created_at: '2026-03-06 10:30:00',
    finished_at: '2026-03-06 10:30:45',
    result: '登录成功'
  },
  {
    id: 'task_002',
    shop_id: 'shop_001',
    shop_name: '旗舰店A',
    task_name: '处理订单',
    status: 'running',
    created_at: '2026-03-06 11:00:00',
    finished_at: null,
    result: null
  },
  {
    id: 'task_003',
    shop_id: 'shop_002',
    shop_name: '专营店B',
    task_name: '登录',
    status: 'failed',
    created_at: '2026-03-06 09:15:00',
    finished_at: '2026-03-06 09:15:30',
    result: '验证码识别失败'
  },
  {
    id: 'task_004',
    shop_id: 'shop_003',
    shop_name: '测试店C',
    task_name: '检查邮件',
    status: 'pending',
    created_at: '2026-03-06 11:30:00',
    finished_at: null,
    result: null
  },
  {
    id: 'task_005',
    shop_id: 'shop_001',
    shop_name: '旗舰店A',
    task_name: '发货',
    status: 'success',
    created_at: '2026-03-06 08:00:00',
    finished_at: '2026-03-06 08:05:20',
    result: '已发货 15 个订单'
  }
]

const mockLogs = Array.from({ length: 20 }, (_, i) => ({
  id: `log_${String(i + 1).padStart(3, '0')}`,
  timestamp: new Date(Date.now() - i * 300000).toISOString().replace('T', ' ').slice(0, 19),
  level: ['INFO', 'WARN', 'ERROR'][Math.floor(Math.random() * 3)],
  source: ['task', 'browser', 'captcha', 'system'][Math.floor(Math.random() * 4)],
  message: [
    '浏览器实例启动成功',
    '检测到滑块验证码',
    '订单处理完成',
    'Cookie 即将过期',
    '代理连接超时',
    '验证码识别成功',
    '邮件发送成功',
    '页面加载超时',
    '登录状态检查通过',
    '任务队列已满'
  ][i % 10]
}))

const mockBrowserInstances = [
  {
    id: 'browser_001',
    shop_id: 'shop_001',
    shop_name: '旗舰店A',
    status: 'running',
    created_at: '2026-03-06 10:30:00',
    memory_usage: '245MB',
    cpu_usage: '3.2%'
  },
  {
    id: 'browser_002',
    shop_id: 'shop_002',
    shop_name: '专营店B',
    status: 'idle',
    created_at: '2026-03-06 09:15:00',
    memory_usage: '180MB',
    cpu_usage: '0.5%'
  }
]

const mockSystemConfig = {
  max_browser_instances: 5,
  task_timeout: 300,
  captcha_provider: 'yescaptcha',
  redis_url: 'redis://192.168.1.100:6379',
  agent_machine_id: 'office-pc-001',
  agent_callback_url: 'http://192.168.1.100:5000/callback'
}

const mockSystemHealth = {
  status: 'healthy',
  uptime: 86400,
  cpu_usage: '12.5%',
  memory_usage: '1.2GB / 8GB',
  disk_usage: '45GB / 256GB',
  redis_connected: true,
  database_connected: true
}

export async function mockGet<T>(url: string): Promise<T> {
  await new Promise(resolve => setTimeout(resolve, 300))

  if (url === '/api/shops') {
    return mockShops as T
  }
  if (url === '/api/tasks') {
    return mockTasks as T
  }
  if (url === '/api/logs') {
    return mockLogs as T
  }
  if (url === '/api/browser/instances') {
    return mockBrowserInstances as T
  }
  if (url === '/api/system/config') {
    return mockSystemConfig as T
  }
  if (url === '/api/system/health') {
    return mockSystemHealth as T
  }

  throw new Error(`Mock not implemented for: ${url}`)
}

export async function mockPost<T>(_url: string, _data?: any): Promise<T> {
  await new Promise(resolve => setTimeout(resolve, 300))
  return { success: true } as T
}

export async function mockPut<T>(_url: string, _data?: any): Promise<T> {
  await new Promise(resolve => setTimeout(resolve, 300))
  return { success: true } as T
}

export async function mockDel<T>(_url: string): Promise<T> {
  await new Promise(resolve => setTimeout(resolve, 300))
  return { success: true } as T
}
