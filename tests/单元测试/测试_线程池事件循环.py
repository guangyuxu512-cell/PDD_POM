"""
线程池 Worker 事件循环兼容性测试
"""
from __future__ import annotations

import asyncio
import threading
from queue import Queue
from unittest.mock import AsyncMock, patch

import pytest

from backend.services import 浏览器服务 as 浏览器服务模块
from tasks import celery应用 as celery应用模块
from tasks import 执行任务 as 执行任务模块


class 假浏览器管理器:
    """用于验证线程隔离管理器的假对象。"""

    def __init__(self):
        self.playwright实例 = None
        self.初始化 = AsyncMock(side_effect=self._初始化)

    async def _初始化(self, 配置=None):
        await asyncio.sleep(0.01)
        self.playwright实例 = object()


class 测试_线程池事件循环:
    """验证 threads 池模式下的事件循环与浏览器隔离。"""

    def teardown_method(self):
        celery应用模块.关闭Worker环境()
        浏览器服务模块.管理器实例 = None
        浏览器服务模块.初始化锁 = None
        浏览器服务模块.初始化锁所属事件循环 = None

    def test_获取Worker事件循环_不同线程返回独立实例(self):
        """每个线程都应拿到独立的 Worker 事件循环。"""
        结果队列: Queue = Queue()

        def 在线程里获取事件循环():
            事件循环 = celery应用模块.获取Worker事件循环()
            结果队列.put((threading.get_ident(), 事件循环))

        线程列表 = [
            threading.Thread(target=在线程里获取事件循环),
            threading.Thread(target=在线程里获取事件循环),
        ]
        for 线程 in 线程列表:
            线程.start()
        for 线程 in 线程列表:
            线程.join()

        结果一 = 结果队列.get_nowait()
        结果二 = 结果队列.get_nowait()

        assert 结果一[0] != 结果二[0]
        assert 结果一[1] is not 结果二[1]

    @pytest.mark.asyncio
    async def test_运行异步任务_当前线程已有事件循环时回退临时线程(self):
        """当前线程已有运行中的事件循环时，也应能安全执行协程。"""

        async def 假协程():
            await asyncio.sleep(0.01)
            return threading.get_ident()

        当前线程ID = threading.get_ident()
        结果线程ID = 执行任务模块._运行异步任务(假协程())

        assert 结果线程ID != 当前线程ID

    @pytest.mark.asyncio
    async def test_运行异步任务_临时线程异常时包装为运行时错误(self):
        """临时线程中的协程异常应被统一包装，避免把底层 loop 错误直接泄露给 Celery。"""

        async def 坏协程():
            raise ValueError("boom")

        with pytest.raises(RuntimeError, match="临时线程执行协程失败"):
            执行任务模块._运行异步任务(坏协程())

    def test_浏览器服务_不同线程使用独立管理器实例(self):
        """线程池中的不同任务线程不应共享同一个 Playwright 管理器。"""
        结果队列: Queue = Queue()

        def 在线程里初始化浏览器():
            asyncio.run(浏览器服务模块.确保已初始化())
            管理器实例 = 浏览器服务模块.获取当前管理器实例()
            结果队列.put(管理器实例)

        with patch(
            "backend.services.浏览器服务.浏览器管理器",
            side_effect=lambda: 假浏览器管理器(),
        ):
            线程列表 = [
                threading.Thread(target=在线程里初始化浏览器),
                threading.Thread(target=在线程里初始化浏览器),
            ]
            for 线程 in 线程列表:
                线程.start()
            for 线程 in 线程列表:
                线程.join()

        管理器一 = 结果队列.get_nowait()
        管理器二 = 结果队列.get_nowait()

        assert 管理器一 is not None
        assert 管理器二 is not None
        assert 管理器一 is not 管理器二
        assert 管理器一.playwright实例 is not 管理器二.playwright实例
