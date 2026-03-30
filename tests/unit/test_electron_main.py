from pathlib import Path


def 读取主进程文件() -> str:
    return Path("electron/main.js").read_text(encoding="utf-8")


def test_Celery启动_默认监听默认队列与机器队列():
    主进程文件 = 读取主进程文件()

    assert "const machineId = (process.env.AGENT_MACHINE_ID || '').trim() || 'default'" in 主进程文件
    assert "const queues = process.env.CELERY_QUEUES || `celery,worker.${machineId}`" in 主进程文件
    assert "workerArgs.push('-Q', queues)" in 主进程文件


def test_Celery启动_打包模式也透传拼接后的队列():
    主进程文件 = 读取主进程文件()

    assert "const celeryEnv = createProcessEnv({" in 主进程文件
    assert "CELERY_QUEUES: queues" in 主进程文件
    assert 主进程文件.count("env: celeryEnv") == 2


def test_应用启动_切换UTF8代码页失败时不中断启动():
    主进程文件 = 读取主进程文件()
    启动代码块 = 主进程文件[主进程文件.index("app.whenReady().then(async () => {"):]

    assert "const { spawn, execSync } = require('child_process')" in 主进程文件
    assert "const windowsCmdExe = process.env.ComSpec || path.join(system32Dir, 'cmd.exe')" in 主进程文件
    assert "if (process.platform === 'win32')" in 启动代码块
    assert "try { execSync('chcp 65001', { stdio: 'inherit', shell: windowsCmdExe }) } catch {}" in 启动代码块
    assert 启动代码块.index("execSync('chcp 65001', { stdio: 'inherit', shell: windowsCmdExe })") < 启动代码块.index("startBackend()")


def test_启动后端前_会先清理监听端口的残留进程():
    主进程文件 = 读取主进程文件()
    后端启动代码块 = 主进程文件[主进程文件.index("function startBackend() {"):主进程文件.index("function startCelery() {")]

    assert 'const netstatExe = path.join(system32Dir, \'netstat.exe\')' in 主进程文件
    assert 'const findstrExe = path.join(system32Dir, \'findstr.exe\')' in 主进程文件
    assert 'const taskkillExe = path.join(system32Dir, \'taskkill.exe\')' in 主进程文件
    assert '"${netstatExe}" -ano | "${findstrExe}" ":${backendPort}" | "${findstrExe}" "LISTENING"' in 后端启动代码块
    assert "stdio: ['pipe', 'pipe', 'ignore']" in 后端启动代码块
    assert "shell: windowsCmdExe" in 后端启动代码块
    assert 'execSync(`"${taskkillExe}" /F /T /PID ${pid}`, {' in 后端启动代码块
    assert "console.log(`[Backend] 已清理残留进程 PID=${pid}，释放端口 ${backendPort}`)" in 后端启动代码块


def test_关闭子进程_Windows下使用taskkill终止整个进程树():
    主进程文件 = 读取主进程文件()
    关闭进程代码块 = 主进程文件[主进程文件.index("function stopProcess(child) {"):主进程文件.index("function stopChildProcesses() {")]

    assert "if (process.platform === 'win32' && child.pid)" in 关闭进程代码块
    assert 'execSync(`"${taskkillExe}" /F /T /PID ${child.pid}`, {' in 关闭进程代码块
    assert "shell: windowsCmdExe" in 关闭进程代码块
    assert "child.kill('SIGTERM')" in 关闭进程代码块
    assert "try { child.kill() } catch {}" in 关闭进程代码块
