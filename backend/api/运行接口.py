"""
运行接口模块

提供运行中心查询与取消接口。
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from backend.models.数据结构 import 统一响应, 成功, 失败
from backend.services.执行服务 import 执行服务实例
from backend.services.运行服务 import 运行服务实例


路由 = APIRouter(prefix="/api/runs", tags=["运行中心"])


@路由.get("", include_in_schema=False)
@路由.get("/", summary="获取运行列表")
async def 获取运行列表(
    status: Optional[str] = Query(None, description="运行状态"),
    mode: Optional[str] = Query(None, description="运行模式"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
) -> 统一响应:
    """分页获取运行列表。"""
    try:
        return 成功(
            data=await 运行服务实例.获取运行列表(
                status=status,
                mode=mode,
                page=page,
                page_size=page_size,
            )
        )
    except Exception as e:
        return 失败(f"获取运行列表失败: {str(e)}")


@路由.get("/{run_id}", summary="获取运行详情")
async def 获取运行详情(run_id: str) -> 统一响应:
    """获取单条运行详情。"""
    try:
        运行 = await 运行服务实例.根据ID获取(run_id)
        if not 运行:
            return 失败("运行不存在")
        return 成功(data=运行)
    except Exception as e:
        return 失败(f"获取运行详情失败: {str(e)}")


@路由.get("/{run_id}/items", summary="获取运行项列表")
async def 获取运行项列表(
    run_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=500, description="每页大小"),
) -> 统一响应:
    """分页获取运行项列表。"""
    try:
        运行 = await 运行服务实例.根据ID获取(run_id)
        if not 运行:
            return 失败("运行不存在")
        return 成功(data=await 运行服务实例.获取运行项列表(run_id, page=page, page_size=page_size))
    except Exception as e:
        return 失败(f"获取运行项列表失败: {str(e)}")


@路由.get("/{run_id}/steps", summary="获取运行步骤列表")
async def 获取运行步骤列表(run_id: str) -> 统一响应:
    """获取运行下全部步骤记录。"""
    try:
        运行 = await 运行服务实例.根据ID获取(run_id)
        if not 运行:
            return 失败("运行不存在")
        return 成功(data=await 运行服务实例.获取运行步骤列表(run_id))
    except Exception as e:
        return 失败(f"获取运行步骤列表失败: {str(e)}")


@路由.post("/{run_id}/cancel", summary="取消运行")
async def 取消运行(run_id: str) -> 统一响应:
    """取消指定运行。"""
    try:
        结果 = await 执行服务实例.停止批次(batch_id=run_id)
        return 成功(data=结果, message="运行已取消")
    except Exception as e:
        return 失败(f"取消运行失败: {str(e)}")
