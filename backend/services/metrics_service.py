"""
指标服务模块

提供基础运行指标统计，供健康检查和监控接口读取。
"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict


class 指标服务:
    """进程内基础指标统计。"""

    def __init__(self) -> None:
        self._锁 = threading.Lock()
        self._启动时间 = time.monotonic()
        self._任务总数 = 0
        self._成功任务数 = 0
        self._失败任务数 = 0
        self._运行中任务数 = 0
        self._任务耗时累计毫秒 = 0.0
        self._已完成任务数 = 0
        self._请求总数 = 0
        self._请求耗时累计毫秒 = 0.0

    def 重置(self) -> None:
        """重置统计信息，便于测试隔离。"""
        with self._锁:
            self._启动时间 = time.monotonic()
            self._任务总数 = 0
            self._成功任务数 = 0
            self._失败任务数 = 0
            self._运行中任务数 = 0
            self._任务耗时累计毫秒 = 0.0
            self._已完成任务数 = 0
            self._请求总数 = 0
            self._请求耗时累计毫秒 = 0.0

    def 获取运行秒数(self) -> int:
        return max(int(time.monotonic() - self._启动时间), 0)

    def 记录任务开始(self) -> None:
        with self._锁:
            self._任务总数 += 1
            self._运行中任务数 += 1

    def 记录任务完成(self, 成功: bool, 耗时毫秒: float) -> None:
        with self._锁:
            self._运行中任务数 = max(self._运行中任务数 - 1, 0)
            self._任务耗时累计毫秒 += max(float(耗时毫秒 or 0.0), 0.0)
            self._已完成任务数 += 1
            if 成功:
                self._成功任务数 += 1
            else:
                self._失败任务数 += 1

    def 记录请求(self, 耗时毫秒: float) -> None:
        with self._锁:
            self._请求总数 += 1
            self._请求耗时累计毫秒 += max(float(耗时毫秒 or 0.0), 0.0)

    def 获取快照(self) -> Dict[str, Any]:
        with self._锁:
            平均任务耗时 = (
                round(self._任务耗时累计毫秒 / self._已完成任务数, 2)
                if self._已完成任务数
                else 0.0
            )
            平均请求耗时 = (
                round(self._请求耗时累计毫秒 / self._请求总数, 2)
                if self._请求总数
                else 0.0
            )
            return {
                "tasks_total": self._任务总数,
                "tasks_success": self._成功任务数,
                "tasks_failed": self._失败任务数,
                "tasks_running": self._运行中任务数,
                "avg_task_duration_ms": 平均任务耗时,
                "requests_total": self._请求总数,
                "avg_request_duration_ms": 平均请求耗时,
                "uptime_seconds": self.获取运行秒数(),
            }


指标服务实例 = 指标服务()

