"""
外部机器接入测试脚本。

用途：
1. 启动时调用注册接口：POST /api/workers/register
2. 后台每隔一段时间上报心跳：POST /api/workers/heartbeat
3. 直接订阅 Celery 队列 worker.{machine_id}，收到任务后更新机器状态并模拟执行

说明：
- 本脚本严格按 Agent 已有 API 约定工作：
  - 注册：POST /api/workers/register
  - 心跳：POST /api/workers/heartbeat
  - 状态回调：PUT /api/workers/{machine_id}/status
- 所有 HTTP 请求都基于 --server-url，默认指向 Agent 端口 http://localhost:8001

PowerShell 示例：
    $env:SERVER_URL = "http://localhost:8001"
    $env:REDIS_URL = "redis://192.168.0.43:6380/0"
    $env:MACHINE_ID = "test-machine-001"
    $env:X_RPA_KEY = "test-rpa-key"
    python scripts/machine_worker.py

启动第二台机器：
    python scripts/machine_worker.py --machine-id test-machine-002 --machine-name "测试机B"
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from socket import timeout as 套接字超时
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from kombu import Connection, Consumer, Queue


load_dotenv()


默认服务端地址 = "http://localhost:8001"
默认Redis地址 = "redis://192.168.0.43:6380/0"
默认机器编号 = "test-machine-001"
默认队列前缀 = "worker"
默认RPA密钥 = ""
默认模拟执行秒数 = 3
默认心跳间隔秒数 = 30
默认请求超时秒数 = 10.0
默认重连等待秒数 = 3.0
注册路径 = "/api/workers/register"
心跳路径 = "/api/workers/heartbeat"
状态路径模板 = "/api/workers/{machine_id}/status"


def 当前时间文本() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def 日志(机器编号: str, 消息: str) -> None:
    print(f"[{当前时间文本()}] [机器 {机器编号}] {消息}")


def 规范化地址(服务端地址: str, 路径或地址: str) -> str:
    if 路径或地址.startswith("http://") or 路径或地址.startswith("https://"):
        return 路径或地址
    return f"{服务端地址.rstrip('/')}/{路径或地址.lstrip('/')}"


def 解析JSON响应(响应: httpx.Response) -> Any:
    try:
        return 响应.json()
    except json.JSONDecodeError:
        return {"raw_text": 响应.text}


def 解包业务响应(响应数据: Any) -> Any:
    if not isinstance(响应数据, dict) or "code" not in 响应数据:
        return 响应数据

    if 响应数据.get("code") != 0:
        raise RuntimeError(响应数据.get("msg") or "服务端返回失败")

    return 响应数据.get("data")


def 构建请求头(RPA密钥: str) -> dict[str, str]:
    密钥 = RPA密钥.strip()
    if not 密钥:
        raise ValueError("X_RPA_KEY 不能为空")
    return {"X-RPA-KEY": 密钥}


@dataclass(frozen=True)
class 运行配置:
    服务端地址: str
    Redis地址: str
    机器编号: str
    机器名称: str
    RPA密钥: str
    队列前缀: str
    模拟执行秒数: int
    心跳间隔秒数: float
    请求超时秒数: float
    重连等待秒数: float

    @property
    def 队列名(self) -> str:
        return f"{self.队列前缀}.{self.机器编号}"

    @property
    def 注册地址(self) -> str:
        return 规范化地址(self.服务端地址, 注册路径)

    @property
    def 心跳地址(self) -> str:
        return 规范化地址(self.服务端地址, 心跳路径)

    @property
    def 状态更新地址(self) -> str:
        return 规范化地址(
            self.服务端地址,
            状态路径模板.format(machine_id=self.机器编号),
        )

    @property
    def 请求头(self) -> dict[str, str]:
        return 构建请求头(self.RPA密钥)


class 外部机器执行器:
    def __init__(self, 配置: 运行配置):
        self.配置 = 配置
        self._停止事件 = threading.Event()
        self._状态锁 = threading.Lock()
        self._当前状态 = "idle"
        self._当前任务ID: Optional[str] = None
        self._心跳线程 = threading.Thread(
            target=self._心跳循环,
            name=f"heartbeat-{配置.机器编号}",
            daemon=True,
        )

    def 运行(self) -> None:
        self._安装信号处理()
        日志(self.配置.机器编号, f"启动外部机器脚本，监听队列 {self.配置.队列名}")
        self.注册机器()
        self._更新机器状态("idle")
        self._心跳线程.start()

        try:
            self._消费队列()
        finally:
            self._停止事件.set()
            self._心跳线程.join(timeout=1)
            self._更新机器状态("offline")
            日志(self.配置.机器编号, "脚本已退出")

    def 注册机器(self) -> None:
        请求体 = {
            "machine_id": self.配置.机器编号,
            "machine_name": self.配置.机器名称,
        }

        数据 = self._发送请求(
            "POST",
            self.配置.注册地址,
            json=请求体,
            headers=self.配置.请求头,
        )
        业务数据 = 解包业务响应(数据)
        日志(
            self.配置.机器编号,
            f"注册成功，服务端返回：{json.dumps(业务数据, ensure_ascii=False, default=str)}",
        )

    def _发送心跳(self) -> None:
        请求体 = {
            "machine_id": self.配置.机器编号,
            "shadowbot_running": self.获取状态() == "running",
        }

        try:
            数据 = self._发送请求(
                "POST",
                self.配置.心跳地址,
                json=请求体,
                headers=self.配置.请求头,
            )
            业务数据 = 解包业务响应(数据)
            日志(
                self.配置.机器编号,
                f"心跳上报成功，shadowbot_running={请求体['shadowbot_running']}，返回："
                f"{json.dumps(业务数据, ensure_ascii=False, default=str)}",
            )
        except Exception as 异常:
            日志(self.配置.机器编号, f"心跳上报失败（忽略）：{异常}")

    def _心跳循环(self) -> None:
        self._发送心跳()
        while not self._停止事件.wait(self.配置.心跳间隔秒数):
            self._发送心跳()

    def _消费队列(self) -> None:
        队列 = Queue(name=self.配置.队列名, routing_key=self.配置.队列名, durable=True)

        while not self._停止事件.is_set():
            try:
                with Connection(self.配置.Redis地址) as 连接:
                    with Consumer(
                        连接,
                        queues=[队列],
                        callbacks=[self._收到任务消息],
                        accept=["json"],
                    ):
                        日志(self.配置.机器编号, "Celery 队列监听已就绪，等待任务")
                        while not self._停止事件.is_set():
                            try:
                                连接.drain_events(timeout=1)
                            except 套接字超时:
                                continue
            except KeyboardInterrupt:
                self._停止事件.set()
            except Exception as 异常:
                日志(
                    self.配置.机器编号,
                    f"队列连接异常：{异常}，{self.配置.重连等待秒数:g} 秒后重连",
                )
                if self._停止事件.wait(self.配置.重连等待秒数):
                    return

    def _收到任务消息(self, 消息体: Any, 消息对象) -> None:
        上下文 = self._解析任务消息(消息体, 消息对象)
        任务ID = 上下文["task_id"]
        任务名 = 上下文["task_name"]
        执行秒数 = 上下文["sleep_seconds"]
        载荷 = 上下文["payload"]

        self.设置状态("running", 任务ID)
        self._更新机器状态("running")
        日志(
            self.配置.机器编号,
            f"收到任务：task_id={任务ID}，task={任务名}，执行秒数={执行秒数}，"
            f"消息体={json.dumps(载荷, ensure_ascii=False, default=str)}",
        )

        try:
            if self._停止事件.wait(执行秒数):
                raise RuntimeError("执行过程中收到停止信号")

            结果 = {
                "machine_id": self.配置.机器编号,
                "queue_name": self.配置.队列名,
                "task_id": 任务ID,
                "task_name": 任务名,
                "echo": 载荷,
                "finished_at": datetime.now().isoformat(),
            }
            日志(
                self.配置.机器编号,
                f"任务执行完成：task_id={任务ID}，结果={json.dumps(结果, ensure_ascii=False)}",
            )
            self._更新机器状态("idle")
            消息对象.ack()
        except Exception as 异常:
            self._更新机器状态("error")
            日志(self.配置.机器编号, f"任务执行失败：task_id={任务ID}，原因={异常}")
            消息对象.ack()
        finally:
            self.设置状态("idle", None)

    def _解析任务消息(self, 消息体: Any, 消息对象) -> dict[str, Any]:
        headers = dict(getattr(消息对象, "headers", {}) or {})
        properties = dict(getattr(消息对象, "properties", {}) or {})

        参数列表: list[Any] = []
        关键字参数: dict[str, Any] = {}
        任务载荷: dict[str, Any] = {}

        if isinstance(消息体, dict):
            关键字参数 = dict(消息体)
            任务载荷 = dict(消息体)
        elif isinstance(消息体, (list, tuple)):
            if len(消息体) >= 2 and isinstance(消息体[1], dict):
                if isinstance(消息体[0], (list, tuple)):
                    参数列表 = list(消息体[0])
                else:
                    参数列表 = [消息体[0]]
                关键字参数 = dict(消息体[1])
                任务载荷 = dict(关键字参数)
                if 参数列表 and isinstance(参数列表[0], dict):
                    任务载荷 = {**参数列表[0], **任务载荷}
            elif len(消息体) == 1 and isinstance(消息体[0], dict):
                关键字参数 = dict(消息体[0])
                任务载荷 = dict(消息体[0])
            else:
                任务载荷 = {"body": 消息体}
        else:
            任务载荷 = {"body": 消息体}

        if isinstance(关键字参数.get("payload"), dict):
            任务载荷 = {**关键字参数["payload"], **任务载荷}

        任务ID = (
            headers.get("id")
            or properties.get("correlation_id")
            or 任务载荷.get("task_id")
            or uuid.uuid4().hex
        )
        任务名 = (
            headers.get("task")
            or 任务载荷.get("task")
            or 任务载荷.get("task_name")
            or "echo-test"
        )

        执行秒数原值 = (
            任务载荷.get("sleep_seconds")
            or 任务载荷.get("simulate_seconds")
            or 任务载荷.get("duration_seconds")
            or self.配置.模拟执行秒数
        )
        try:
            执行秒数 = max(0, int(执行秒数原值))
        except (TypeError, ValueError):
            执行秒数 = self.配置.模拟执行秒数

        return {
            "task_id": str(任务ID),
            "task_name": str(任务名),
            "args": 参数列表,
            "kwargs": 关键字参数,
            "payload": 任务载荷,
            "sleep_seconds": 执行秒数,
        }

    def _更新机器状态(self, 状态: str) -> None:
        请求体 = {"status": 状态}

        try:
            数据 = self._发送请求(
                "PUT",
                self.配置.状态更新地址,
                json=请求体,
                headers=self.配置.请求头,
            )
            业务数据 = 解包业务响应(数据)
            日志(
                self.配置.机器编号,
                f"状态回调成功：status={状态}，返回="
                f"{json.dumps(业务数据, ensure_ascii=False, default=str)}",
            )
        except Exception as 异常:
            日志(
                self.配置.机器编号,
                f"状态回调失败（忽略）：status={状态}，原因={异常}",
            )

    def _发送请求(self, 方法: str, 地址: str, **kwargs: Any) -> Any:
        with httpx.Client(timeout=self.配置.请求超时秒数) as 客户端:
            响应 = 客户端.request(方法, 地址, **kwargs)
            响应.raise_for_status()
            return 解析JSON响应(响应)

    def 设置状态(self, 状态: str, 任务ID: Optional[str]) -> None:
        with self._状态锁:
            self._当前状态 = 状态
            self._当前任务ID = 任务ID

    def 获取状态(self) -> str:
        with self._状态锁:
            return self._当前状态

    def _安装信号处理(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            return

        def 处理退出信号(signum, _frame) -> None:
            日志(self.配置.机器编号, f"收到退出信号 {signum}，准备停止")
            self._停止事件.set()

        signal.signal(signal.SIGINT, 处理退出信号)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, 处理退出信号)


def 解析命令行参数() -> argparse.Namespace:
    解析器 = argparse.ArgumentParser(description="外部机器接入测试脚本")
    解析器.add_argument("--server-url", default=os.getenv("SERVER_URL", 默认服务端地址))
    解析器.add_argument("--redis-url", default=os.getenv("REDIS_URL", 默认Redis地址))
    解析器.add_argument("--machine-id", default=os.getenv("MACHINE_ID", 默认机器编号))
    解析器.add_argument(
        "--machine-name",
        default=os.getenv("MACHINE_NAME", "").strip(),
        help="注册时上报的机器名称；为空时回退到 machine-id",
    )
    解析器.add_argument(
        "--rpa-key",
        default=os.getenv("X_RPA_KEY", 默认RPA密钥).strip(),
        help="请求头使用的 X-RPA-KEY；默认从 .env 的 X_RPA_KEY 读取",
    )
    解析器.add_argument(
        "--queue-prefix",
        default=os.getenv("TASK_QUEUE_PREFIX", 默认队列前缀),
    )
    解析器.add_argument(
        "--simulate-seconds",
        type=int,
        default=int(os.getenv("SIMULATE_SECONDS", str(默认模拟执行秒数))),
    )
    解析器.add_argument(
        "--heartbeat-interval",
        type=float,
        default=float(os.getenv("HEARTBEAT_INTERVAL_SECONDS", str(默认心跳间隔秒数))),
    )
    解析器.add_argument(
        "--request-timeout",
        type=float,
        default=float(os.getenv("REQUEST_TIMEOUT_SECONDS", str(默认请求超时秒数))),
    )
    解析器.add_argument(
        "--retry-delay",
        type=float,
        default=float(os.getenv("RETRY_DELAY_SECONDS", str(默认重连等待秒数))),
    )
    return 解析器.parse_args()


def 构建配置(参数: argparse.Namespace) -> 运行配置:
    机器编号 = 参数.machine_id.strip()
    if not 机器编号:
        raise ValueError("MACHINE_ID 不能为空")
    if not 参数.rpa_key.strip():
        raise ValueError("X_RPA_KEY 不能为空")
    if not 参数.redis_url.strip():
        raise ValueError("REDIS_URL 不能为空")

    机器名称 = 参数.machine_name.strip() or 机器编号

    return 运行配置(
        服务端地址=参数.server_url.strip(),
        Redis地址=参数.redis_url.strip(),
        机器编号=机器编号,
        机器名称=机器名称,
        RPA密钥=参数.rpa_key.strip(),
        队列前缀=参数.queue_prefix.strip(),
        模拟执行秒数=max(0, 参数.simulate_seconds),
        心跳间隔秒数=max(1.0, 参数.heartbeat_interval),
        请求超时秒数=max(1.0, 参数.request_timeout),
        重连等待秒数=max(1.0, 参数.retry_delay),
    )


def main() -> int:
    参数 = 解析命令行参数()
    配置 = 构建配置(参数)
    执行器 = 外部机器执行器(配置)
    执行器.运行()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
