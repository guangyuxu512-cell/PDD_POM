"""
定时计划 Celery 任务模块

负责在 Celery Worker 中触发定时计划对应的批量执行。
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from backend.services.定时执行服务 import 定时执行服务实例
from tasks.celery应用 import celery应用, 初始化Worker环境, 获取Worker事件循环


def _运行异步任务(协程):
    """在同步 Celery Task 中执行异步协程。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
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

    协程.close()
    raise RuntimeError("定时任务检测到已有运行中的事件循环，无法重复创建事件循环")


@celery应用.task(name="执行定时计划")
def 执行定时计划(*, schedule_id: str) -> Dict[str, Any]:
    """执行指定的定时计划。"""
    if not schedule_id:
        raise ValueError("schedule_id 不能为空")

    初始化Worker环境()
    return _运行异步任务(定时执行服务实例.触发计划(schedule_id))
