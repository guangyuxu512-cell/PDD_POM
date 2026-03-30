"""
异步工具函数

供 Celery 同步任务调用异步代码使用。
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any

from tasks.celery_app import 获取Worker事件循环


def 在线程中执行临时协程(协程) -> Any:
    """当当前线程已有运行中的事件循环时，退回到临时线程执行协程。"""
    结果容器: dict[str, Any] = {}
    完成事件 = threading.Event()

    def _执行():
        try:
            结果容器["result"] = asyncio.run(协程)
        except Exception as e:
            结果容器["error"] = e
        finally:
            完成事件.set()

    线程 = threading.Thread(target=_执行, daemon=True)
    线程.start()
    完成事件.wait()

    if "error" in 结果容器:
        raise RuntimeError(f"临时线程执行协程失败: {结果容器['error']}") from 结果容器["error"]

    return 结果容器.get("result")


def 运行异步任务(协程) -> Any:
    """
    在同步 Celery task 中执行异步协程。

    优先复用 Worker 事件循环；当前线程已有运行中的事件循环时退回临时线程；
    Worker 事件循环不可用时回退到 asyncio.run。

    参数:
        协程: 待执行的协程对象

    返回:
        Any: 协程执行结果
    """
    try:
        当前事件循环 = asyncio.get_running_loop()
    except RuntimeError:
        当前事件循环 = None

    if 当前事件循环 is not None:
        return 在线程中执行临时协程(协程)

    try:
        事件循环 = 获取Worker事件循环()
        asyncio.set_event_loop(事件循环)
    except Exception as e:
        print(f"[Celery] 获取 Worker 事件循环失败，回退到临时事件循环: {e}")
        return asyncio.run(协程)

    try:
        return 事件循环.run_until_complete(协程)
    except Exception as e:
        raise RuntimeError(f"Worker 事件循环执行协程失败: {e}") from e
