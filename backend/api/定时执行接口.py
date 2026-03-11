"""
定时执行接口模块

提供定时计划 CRUD 与启停接口。
"""
from __future__ import annotations

from fastapi import APIRouter

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
    定时任务创建请求,
    定时任务更新请求,
)
from backend.services.定时执行服务 import 定时执行服务实例


路由 = APIRouter(prefix="/api/schedules", tags=["定时执行"])


@路由.get("", include_in_schema=False)
@路由.get("/", summary="获取定时计划列表")
async def 获取定时计划列表() -> 统一响应:
    """获取全部定时计划。"""
    try:
        return 成功(data=await 定时执行服务实例.获取全部())
    except Exception as e:
        return 失败(f"获取定时计划列表失败: {str(e)}")


@路由.post("", include_in_schema=False)
@路由.post("/", summary="创建定时计划")
async def 创建定时计划(请求: 定时任务创建请求) -> 统一响应:
    """创建定时计划。"""
    try:
        计划 = await 定时执行服务实例.创建(请求.model_dump(exclude_none=True))
        return 成功(data=计划, message="创建成功")
    except Exception as e:
        return 失败(f"创建定时计划失败: {str(e)}")


@路由.put("/{schedule_id}", summary="更新定时计划")
async def 更新定时计划(schedule_id: str, 请求: 定时任务更新请求) -> 统一响应:
    """更新定时计划。"""
    try:
        计划 = await 定时执行服务实例.更新(
            schedule_id,
            请求.model_dump(exclude_unset=True),
        )
        if not 计划:
            return 失败("定时计划不存在")
        return 成功(data=计划, message="更新成功")
    except Exception as e:
        return 失败(f"更新定时计划失败: {str(e)}")


@路由.delete("/{schedule_id}", summary="删除定时计划")
async def 删除定时计划(schedule_id: str) -> 统一响应:
    """删除定时计划。"""
    try:
        成功标志 = await 定时执行服务实例.删除(schedule_id)
        if not 成功标志:
            return 失败("定时计划不存在")
        return 成功(message="删除成功")
    except Exception as e:
        return 失败(f"删除定时计划失败: {str(e)}")


@路由.post("/{schedule_id}/pause", summary="暂停定时计划")
async def 暂停定时计划(schedule_id: str) -> 统一响应:
    """暂停定时计划。"""
    try:
        计划 = await 定时执行服务实例.暂停(schedule_id)
        if not 计划:
            return 失败("定时计划不存在")
        return 成功(data=计划, message="暂停成功")
    except Exception as e:
        return 失败(f"暂停定时计划失败: {str(e)}")


@路由.post("/{schedule_id}/resume", summary="恢复定时计划")
async def 恢复定时计划(schedule_id: str) -> 统一响应:
    """恢复已暂停的定时计划。"""
    try:
        计划 = await 定时执行服务实例.恢复(schedule_id)
        if not 计划:
            return 失败("定时计划不存在")
        return 成功(data=计划, message="恢复成功")
    except Exception as e:
        return 失败(f"恢复定时计划失败: {str(e)}")
