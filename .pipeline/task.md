### 步骤 1：修改 `electron/main.js`

**文件：** `electron/main.js`

**改动 1** — 顶部 import：

```jsx
// 把
const { spawn } = require('child_process')
// 改为
const { spawn, execSync } = require('child_process')
```

**改动 2** — `startCelery()` 函数，自动拼接队列：

```jsx
function startCelery() {
  const workerArgs = ['-m', 'celery', '-A', 'tasks.celery_app', 'worker', '-P', 'solo', '-l', process.env.CELERY_LOG_LEVEL || 'INFO']
  
  // 自动拼接队列名，确保监听 celery 和 worker.{机器码}
  const machineId = (process.env.AGENT_MACHINE_ID || '').trim() || 'default'
  const queues = process.env.CELERY_QUEUES || `celery,worker.${machineId}`
  workerArgs.push('-Q', queues)

  // 以下不变...
```

**改动 3** — `app.whenReady()` 前加 UTF-8 代码页：

```jsx
app.whenReady().then(async () => {
  try {
    if (process.platform === 'win32') {
      try { execSync('chcp 65001', { stdio: 'ignore' }) } catch {}
    }
    
    startBackend()
    startCelery()
    // 以下不变...
```

### 步骤 2：验收

```bash
npx electron .
```

**期望：**

1. 控制台中文正常显示，不再乱码
2. Celery 输出 `[queues]` 段包含 `celery` **和** `worker.office-pc-001`
3. 点击"开始执行"后，任务从"等待中"变为"正在执行"

### 检查清单

- [ ]  `main.js` — `execSync('chcp 65001')` 解决乱码
- [ ]  `main.js` — `startCelery()` 自动拼接 `worker.{AGENT_MACHINE_ID}` 队列
- [ ]  Celery Worker 监听到两个队列
- [ ]  任务不再卡在"等待中"