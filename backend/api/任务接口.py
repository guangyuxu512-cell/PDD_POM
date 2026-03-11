"""
任务接口模块

提供任务管理的 REST API 接口。
"""
from typing import Optional
from fastapi import APIRouter, Query, Request

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
    任务执行请求,
)
from backend.services.任务服务 import 任务服务实例


# 创建路由
路由 = APIRouter(prefix="/api/tasks", tags=["任务管理"])


@路由.get("/", summary="获取任务列表")
async def 获取任务列表(
    shop_id: Optional[str] = Query(None, description="店铺 ID"),
    status: Optional[str] = Query(None, description="任务状态"),
    task_name: Optional[str] = Query(None, description="任务名称"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小")
) -> 统一响应:
    """
    获取任务列表（分页 + 筛选）

    参数:
        shop_id: 店铺 ID（可选）
        status: 任务状态（可选）
        task_name: 任务名称（可选）
        page: 页码（从 1 开始）
        page_size: 每页大小（1-100）

    返回:
        统一响应: 包含分页数据的响应
    """
    try:
        结果 = await 任务服务实例.获取任务列表(
            shop_id=shop_id,
            status=status,
            task_name=task_name,
            page=page,
            page_size=page_size
        )
        return 成功(data=结果)
    except Exception as e:
        return 失败(f"获取任务列表失败: {str(e)}")


@路由.post("/execute", summary="触发任务")
async def 触发任务(request: Request, 请求: 任务执行请求 = None) -> 统一响应:
    """
    触发任务

    参数:
        request: FastAPI 请求对象
        请求: 任务执行请求

    返回:
        统一响应: 包含任务信息
    """
    try:
        # 打印原始请求体，看 Agent 到底发了什么
        body = await request.body()
        print(f"[调试] 原始请求体: {body.decode('utf-8', errors='replace')}")

        print(f"[调试] 收到请求: shop_id='{请求.shop_id}', task_name='{请求.task_name}', repr='{repr(请求.task_name)}'")
        任务 = await 任务服务实例.触发任务(
            shop_id=请求.shop_id,
            task_name=请求.task_name,
            params=请求.params
        )
        return 成功(data=任务, message="任务已触发")
    except Exception as e:
        return 失败(f"触发任务失败: {str(e)}")


@路由.get("/{task_id}", summary="获取任务详情")
async def 获取任务详情(task_id: str) -> 统一响应:
    """
    获取任务详情

    参数:
        task_id: 任务 ID

    返回:
        统一响应: 包含任务详情
    """
    try:
        任务 = await 任务服务实例.获取任务详情(task_id)
        if not 任务:
            return 失败("任务不存在")
        return 成功(data=任务)
    except Exception as e:
        return 失败(f"获取任务详情失败: {str(e)}")


@路由.post("/{task_id}/cancel", summary="取消任务")
async def 取消任务(task_id: str) -> 统一响应:
    """
    取消任务（仅限 pending 状态）

    参数:
        task_id: 任务 ID

    返回:
        统一响应: 取消结果
    """
    try:
        成功标志 = await 任务服务实例.取消任务(task_id)
        if not 成功标志:
            return 失败("任务不存在或状态不是 pending")
        return 成功(message="任务已取消")
    except Exception as e:
        return 失败(f"取消任务失败: {str(e)}")


@路由.delete("/{task_id}", summary="删除任务")
async def 删除任务(task_id: str) -> 统一响应:
    """
    删除任务记录

    参数:
        task_id: 任务 ID

    返回:
        统一响应: 删除结果
    """
    try:
        成功标志 = await 任务服务实例.删除任务(task_id)
        if not 成功标志:
            return 失败("任务不存在")
        return 成功(message="任务已删除")
    except Exception as e:
        return 失败(f"删除任务失败: {str(e)}")


@路由.delete("/history/clear", summary="清空历史记录")
async def 清空历史记录() -> 统一响应:
    """
    删除所有已完成和已失败的任务记录

    返回:
        统一响应: 删除结果
    """
    try:
        删除数量 = await 任务服务实例.清空历史记录()
        return 成功(data={"count": 删除数量}, message=f"已清空 {删除数量} 条历史记录")
    except Exception as e:
        return 失败(f"清空历史记录失败: {str(e)}")
