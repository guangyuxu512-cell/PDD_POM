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
    assert "if (process.platform === 'win32')" in 启动代码块
    assert "try { execSync('chcp 65001', { stdio: 'ignore' }) } catch {}" in 启动代码块
    assert 启动代码块.index("execSync('chcp 65001', { stdio: 'ignore' })") < 启动代码块.index("startBackend()")
