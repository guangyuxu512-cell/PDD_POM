"""
Celery 桥接任务模块

提供群晖 Agent 远程触发本机任务执行的唯一桥接入口。
"""
import asyncio
from typing import Optional, Dict, Any

from backend.services.task_service import 任务服务实例
from tasks.celery_app import celery_app, 初始化Worker环境, 获取Worker事件循环


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
    raise RuntimeError("桥接任务检测到已有运行中的事件循环，无法重复创建事件循环")


@celery_app.task(name="桥接执行任务")
def 桥接执行任务(
    shop_id: str,
    task_name: str,
    params: Optional[Dict[str, Any]] = None,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Celery 桥接执行入口

    参数:
        shop_id: 店铺 ID
        task_name: 任务名称
        params: 任务参数（可选）
        task_id: 已存在的任务 ID（可选）

    返回:
        Dict[str, Any]: 执行结果
    """
    if not shop_id:
        raise ValueError("shop_id 不能为空")

    if not task_name:
        raise ValueError("task_name 不能为空")

    初始化Worker环境()

    if not task_id:
        任务记录 = _运行异步任务(
            任务服务实例.创建任务记录(
                shop_id=shop_id,
                task_name=task_name,
                params=params
            )
        )
        task_id = 任务记录["task_id"]

    return _运行异步任务(
        任务服务实例.统一执行任务(
            task_id=task_id,
            shop_id=shop_id,
            task_name=task_name,
            params=params,
            来源="celery"
        )
    )
