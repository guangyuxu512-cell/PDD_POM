"""
定时计划 Celery 任务模块

负责在 Celery Worker 中触发定时计划对应的批量执行。
"""
from __future__ import annotations

from typing import Any, Dict

from backend.services.scheduled_execute_service import 定时执行服务实例
from tasks.async_utils import 运行异步任务
from tasks.celery_app import celery_app, 初始化Worker环境

def _运行异步任务(协程):
    """兼容旧调用点，统一委托给共享异步桥接工具。"""
    return 运行异步任务(协程)


@celery_app.task(name="执行定时计划")
def 执行定时计划(*, schedule_id: str) -> Dict[str, Any]:
    """执行指定的定时计划。"""
    if not schedule_id:
        raise ValueError("schedule_id 不能为空")

    初始化Worker环境()
    return _运行异步任务(定时执行服务实例.触发计划(schedule_id))
