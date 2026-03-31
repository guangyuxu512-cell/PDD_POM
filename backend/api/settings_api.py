"""
系统设置接口模块

提供 settings 表的列表与更新接口。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from backend.models.data_structure import 成功, 统一响应
from backend.utils.settings import batch_update_settings, list_settings, update_setting


路由 = APIRouter(prefix="/api/settings", tags=["系统设置"])


@路由.get("", summary="获取所有配置")
async def 获取配置列表() -> 统一响应:
    """返回全部系统配置项。"""
    return 成功(data={"list": list_settings()})


@路由.put("/{key}", summary="更新配置")
async def 更新配置(
    key: str,
    body: dict[str, Any] = Body(..., description="配置值"),
) -> 统一响应:
    """更新单个配置项。"""
    try:
        update_setting(key, body.get("value"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"配置项 {key} 不存在") from exc

    return 成功(message="配置已更新")


@路由.post("/batch", summary="批量更新配置")
async def 批量更新(
    body: dict[str, Any] = Body(..., description="批量更新项"),
) -> 统一响应:
    """批量更新配置项。"""
    items = body.get("items", [])
    updated_count = batch_update_settings(items)
    return 成功(message=f"已更新 {updated_count} 项配置")
