**文件：** `electron/main.js`

### 改动 1：`chcp` 改用 `stdio: 'inherit'`

```jsx
// 把
try { execSync('chcp 65001', { stdio: 'ignore' }) } catch {}
// 改为
try { execSync('chcp 65001', { stdio: 'inherit' }) } catch {}
```

### 改动 2：`stopProcess` 改用 `taskkill` 强杀进程树

```jsx
function stopProcess(child) {
  if (!child || child.killed) {
    return
  }

  try {
    if (process.platform === 'win32' && child.pid) {
      // /F 强制终止, /T 终止整个进程树（含 uvicorn 子进程）
      execSync(`taskkill /F /T /PID ${child.pid}`, { stdio: 'ignore' })
    } else {
      child.kill('SIGTERM')
    }
  } catch (error) {
    // taskkill 可能因进程已退出而报错，忽略
    try { child.kill() } catch {}
  }
}
```

### 改动 3：启动前清理残留端口占用

在 `startBackend()` 函数**最前面**加一段端口清理：

```jsx
function startBackend() {
  // 启动前清理上次残留的端口占用
  if (process.platform === 'win32') {
    try {
      const result = execSync(
        `netstat -ano | findstr ":${backendPort}" | findstr "LISTENING"`,
        { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'] }
      )
      for (const line of result.trim().split('\n')) {
        const pid = line.trim().split(/\s+/).pop()
        if (pid && pid !== '0') {
          execSync(`taskkill /F /T /PID ${pid}`, { stdio: 'ignore' })
          console.log(`[Backend] 已清理残留进程 PID=${pid}，释放端口 ${backendPort}`)
        }
      }
    } catch {}
  }

  const backendArgs = [
    // ... 以下不变
```

### 验收

```bash
npx electron .
```

**期望：**

1. ✅ 控制台中文正常显示（不再乱码）
2. ✅ 关闭后再重启，不再报 `[Errno 10048]` 端口冲突
3. ✅ 队列双监听 `celery` + `worker.office-pc-001`（已修好）
4. ✅ 任务能正常执行（已修好）

### 检查清单

- [ ]  `chcp 65001` 改为 `stdio: 'inherit'`
- [ ]  `stopProcess` 使用 `taskkill /F /T /PID`
- [ ]  `startBackend` 启动前清理残留端口
- [ ]  重启无端口冲突，控制台无乱码