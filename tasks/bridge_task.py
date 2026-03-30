"""
Celery 桥接任务模块

提供群晖 Agent 远程触发本机任务执行的唯一桥接入口。
"""
from typing import Optional, Dict, Any

from backend.services.task_service import 任务服务实例
from tasks.async_utils import 运行异步任务
from tasks.celery_app import celery_app, 初始化Worker环境


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
        任务记录 = 运行异步任务(
            任务服务实例.创建任务记录(
                shop_id=shop_id,
                task_name=task_name,
                params=params
            )
        )
        task_id = 任务记录["task_id"]

    return 运行异步任务(
        任务服务实例.统一执行任务(
            task_id=task_id,
            shop_id=shop_id,
            task_name=task_name,
            params=params,
            来源="celery"
        )
    )
