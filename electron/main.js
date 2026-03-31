const { app, BrowserWindow, dialog } = require('electron')
const fs = require('fs')
const http = require('http')
const path = require('path')
const { spawn, execSync } = require('child_process')

let mainWindow = null
let backendProcess = null
let celeryProcess = null

const isDev = !app.isPackaged
const rootDir = isDev ? path.resolve(__dirname, '..') : path.join(process.resourcesPath, 'app')

const backendPort = Number(process.env.BACKEND_PORT || 8000)
const frontendPort = Number(process.env.FRONTEND_PORT || 3000)
const backendBaseUrl = `http://127.0.0.1:${backendPort}`
const rendererDevUrl = process.env.ELECTRON_RENDERER_URL || `http://127.0.0.1:${frontendPort}`
const pythonExe = process.env.PYTHON || 'python'
const systemRoot = process.env.SystemRoot || 'C:\\Windows'
const system32Dir = path.join(systemRoot, 'System32')
const windowsCmdExe = process.env.ComSpec || path.join(system32Dir, 'cmd.exe')
const taskkillExe = path.join(system32Dir, 'taskkill.exe')
const netstatExe = path.join(system32Dir, 'netstat.exe')
const findstrExe = path.join(system32Dir, 'findstr.exe')

const packagedBackendExe = path.join(rootDir, 'python-backend', 'backend', 'backend.exe')
const packagedCeleryExe = path.join(rootDir, 'python-backend', 'celery-worker', 'celery-worker.exe')

function ensurePackagedFileExists(filePath, label) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`${label} 不存在: ${filePath}`)
  }
}

function createProcessEnv(extraEnv = {}) {
  return {
    ...process.env,
    ...extraEnv,
    PYTHONPATH: rootDir,
    PYTHONUTF8: '1',
    PYTHONIOENCODING: 'utf-8',
  }
}

function pipeLogs(label, child) {
  child.stdout?.setEncoding('utf8')
  child.stderr?.setEncoding('utf8')
  child.stdout?.on('data', (data) => {
    process.stdout.write(`[${label}] ${data}`)
  })
  child.stderr?.on('data', (data) => {
    process.stderr.write(`[${label}] ${data}`)
  })
}

function attachFailureDialog(label, child) {
  child.on('error', (error) => {
    dialog.showErrorBox(`${label} 启动失败`, error.message)
  })
}

function startBackend() {
  // 启动前清理上次残留的端口占用
  if (process.platform === 'win32') {
    try {
      const result = execSync(
        `"${netstatExe}" -ano | "${findstrExe}" ":${backendPort}" | "${findstrExe}" "LISTENING"`,
        {
          encoding: 'utf-8',
          stdio: ['pipe', 'pipe', 'ignore'],
          shell: windowsCmdExe,
        }
      )
      for (const line of result.trim().split(/\r?\n/)) {
        const pid = line.trim().split(/\s+/).pop()
        if (pid && pid !== '0') {
          execSync(`"${taskkillExe}" /F /T /PID ${pid}`, {
            stdio: 'ignore',
            shell: windowsCmdExe,
          })
          console.log(`[Backend] 已清理残留进程 PID=${pid}，释放端口 ${backendPort}`)
        }
      }
    } catch {}
  }

  const backendArgs = [
    '-m',
    'uvicorn',
    'backend.main:app',
    '--host',
    '127.0.0.1',
    '--port',
    String(backendPort),
  ]

  if (isDev) {
    backendProcess = spawn(
      pythonExe,
      backendArgs,
      {
        cwd: rootDir,
        env: createProcessEnv(),
      }
    )
  } else {
    ensurePackagedFileExists(packagedBackendExe, '后端程序')
    backendProcess = spawn(packagedBackendExe, [], {
      cwd: path.dirname(packagedBackendExe),
      env: createProcessEnv(),
    })
  }

  pipeLogs('Backend', backendProcess)
  attachFailureDialog('后端', backendProcess)
}

function startCelery() {
  const workerArgs = ['-m', 'celery', '-A', 'tasks.celery_app', 'worker', '-P', 'solo', '-l', process.env.CELERY_LOG_LEVEL || 'INFO']

  // 自动拼接队列名，确保监听 celery 和 worker.{机器码}
  const machineId = (process.env.AGENT_MACHINE_ID || '').trim() || 'default'
  const queues = process.env.CELERY_QUEUES || `celery,worker.${machineId}`
  const celeryEnv = createProcessEnv({
    CELERY_QUEUES: queues,
  })
  workerArgs.push('-Q', queues)

  if (isDev) {
    celeryProcess = spawn(pythonExe, workerArgs, {
      cwd: rootDir,
      env: celeryEnv,
    })
  } else {
    ensurePackagedFileExists(packagedCeleryExe, 'Celery Worker 程序')
    celeryProcess = spawn(packagedCeleryExe, [], {
      cwd: path.dirname(packagedCeleryExe),
      env: celeryEnv,
    })
  }

  pipeLogs('Celery', celeryProcess)
  attachFailureDialog('Celery Worker', celeryProcess)
}

function waitForUrl(url, retries = 40, delayMs = 1000) {
  return new Promise((resolve, reject) => {
    let attempts = 0

    const check = () => {
      const request = http.get(url, (response) => {
        response.resume()
        if (response.statusCode && response.statusCode < 500) {
          resolve(url)
          return
        }

        attempts += 1
        if (attempts >= retries) {
          reject(new Error(`访问 ${url} 失败，状态码: ${response.statusCode}`))
          return
        }
        setTimeout(check, delayMs)
      })

      request.on('error', () => {
        attempts += 1
        if (attempts >= retries) {
          reject(new Error(`访问 ${url} 超时`))
          return
        }
        setTimeout(check, delayMs)
      })

      request.setTimeout(2000, () => {
        request.destroy()
      })
    }

    check()
  })
}

async function resolveRendererUrl() {
  if (isDev) {
    try {
      return await waitForUrl(rendererDevUrl, 5, 1000)
    } catch (error) {
      console.warn(`[Electron] 未检测到前端开发服务器，回退到后端静态页: ${error.message}`)
    }
  }

  return `${backendBaseUrl}/`
}

function stopProcess(child) {
  if (!child || child.killed) {
    return
  }

  try {
    if (process.platform === 'win32' && child.pid) {
      // /F 强制终止, /T 终止整个进程树（含 uvicorn 子进程）
      execSync(`"${taskkillExe}" /F /T /PID ${child.pid}`, {
        stdio: 'ignore',
        shell: windowsCmdExe,
      })
    } else {
      child.kill('SIGTERM')
    }
  } catch (error) {
    // taskkill 可能因进程已退出而报错，忽略
    try { child.kill() } catch {}
  }
}

function stopChildProcesses() {
  stopProcess(celeryProcess)
  stopProcess(backendProcess)
  celeryProcess = null
  backendProcess = null
}

async function createWindow() {
  const rendererUrl = await resolveRendererUrl()

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 760,
    title: '自动化工作台',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  await mainWindow.loadURL(rendererUrl)
  mainWindow.setMenuBarVisibility(false)

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(async () => {
  try {
    if (process.platform === 'win32') {
      try { execSync('chcp 65001', { stdio: 'inherit', shell: windowsCmdExe }) } catch {}
    }

    startBackend()
    startCelery()
    await waitForUrl(`${backendBaseUrl}/openapi.json`)
    await createWindow()
  } catch (error) {
    dialog.showErrorBox('应用启动失败', error.message)
    stopChildProcesses()
    app.quit()
  }
})

app.on('before-quit', () => {
  stopChildProcesses()
})

app.on('window-all-closed', () => {
  app.quit()
})
