"""售后配置接口。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from backend.models.数据结构 import 统一响应, 成功, 失败
from backend.services.售后配置服务 import 售后配置服务实例


路由 = APIRouter(prefix="/api/aftersale-config", tags=["售后配置"])


@路由.get("", include_in_schema=False)
@路由.get("/", summary="获取所有店铺售后配置")
async def 获取所有店铺售后配置() -> 统一响应:
    try:
        配置列表 = await 售后配置服务实例.获取所有配置()
        return 成功(data=配置列表)
    except Exception as 异常:
        return 失败(f"获取售后配置列表失败: {异常}")


@路由.get("/{shop_id}", summary="获取指定店铺售后配置")
async def 获取店铺售后配置(shop_id: str) -> 统一响应:
    try:
        配置 = await 售后配置服务实例.获取配置(shop_id)
        return 成功(data=配置)
    except Exception as 异常:
        return 失败(f"获取售后配置失败: {异常}")


@路由.put("/{shop_id}", summary="更新指定店铺售后配置")
async def 更新店铺售后配置(
    shop_id: str,
    请求体: dict[str, Any] = Body(...),
) -> 统一响应:
    try:
        配置 = await 售后配置服务实例.更新配置(shop_id, 请求体)
        return 成功(data=配置, message="更新成功")
    except Exception as 异常:
        return 失败(f"更新售后配置失败: {异常}")


@路由.delete("/{shop_id}", summary="删除指定店铺售后配置")
async def 删除店铺售后配置(shop_id: str) -> 统一响应:
    try:
        删除成功 = await 售后配置服务实例.删除配置(shop_id)
        if not 删除成功:
            return 失败("配置不存在")
        return 成功(message="删除成功")
    except Exception as 异常:
        return 失败(f"删除售后配置失败: {异常}")
