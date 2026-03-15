"""规则接口模块。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Query

from backend.models.数据结构 import 统一响应, 成功, 失败
from backend.services.规则服务 import 默认动作列表, 规则服务实例


路由 = APIRouter(prefix="/api/rules", tags=["规则引擎"])


@路由.get("", include_in_schema=False)
@路由.get("/", summary="获取规则列表")
async def 获取规则列表(
    platform: str | None = Query(default=None),
    business: str | None = Query(default=None),
    shop_id: str | None = Query(default=None),
) -> 统一响应:
    try:
        规则列表 = await 规则服务实例.获取规则列表(platform=platform, business=business, shop_id=shop_id)
        return 成功(data={"list": 规则列表, "total": len(规则列表)})
    except Exception as 异常:
        return 失败(f"获取规则列表失败: {异常}")


@路由.get("/{rule_id}", summary="获取规则详情")
async def 获取规则详情(rule_id: int) -> 统一响应:
    try:
        规则 = await 规则服务实例.获取规则(rule_id)
        if not 规则:
            return 失败("规则不存在")
        return 成功(data=规则)
    except Exception as 异常:
        return 失败(f"获取规则详情失败: {异常}")


@路由.post("", include_in_schema=False)
@路由.post("/", summary="创建规则")
async def 创建规则(请求体: dict[str, Any] = Body(...)) -> 统一响应:
    try:
        规则 = await 规则服务实例.创建规则(请求体)
        return 成功(data=规则, message="创建成功")
    except Exception as 异常:
        return 失败(f"创建规则失败: {异常}")


@路由.put("/{rule_id}", summary="更新规则")
async def 更新规则(rule_id: int, 请求体: dict[str, Any] = Body(...)) -> 统一响应:
    try:
        规则 = await 规则服务实例.更新规则(rule_id, 请求体)
        if not 规则:
            return 失败("规则不存在")
        return 成功(data=规则, message="更新成功")
    except Exception as 异常:
        return 失败(f"更新规则失败: {异常}")


@路由.delete("/{rule_id}", summary="删除规则")
async def 删除规则(rule_id: int) -> 统一响应:
    try:
        成功标志 = await 规则服务实例.删除规则(rule_id)
        if not 成功标志:
            return 失败("规则不存在")
        return 成功(message="删除成功")
    except Exception as 异常:
        return 失败(f"删除规则失败: {异常}")


@路由.put("/{rule_id}/toggle", summary="切换规则启用状态")
async def 切换启用状态(rule_id: int, 请求体: dict[str, Any] = Body(...)) -> 统一响应:
    try:
        if "enabled" not in 请求体:
            return 失败("enabled 不能为空")
        成功标志 = await 规则服务实例.切换启用(rule_id, bool(请求体.get("enabled")))
        if not 成功标志:
            return 失败("规则不存在")
        规则 = await 规则服务实例.获取规则(rule_id)
        return 成功(data=规则, message="切换成功")
    except Exception as 异常:
        return 失败(f"切换规则启用状态失败: {异常}")


@路由.post("/match", summary="测试规则匹配")
async def 测试规则匹配(请求体: dict[str, Any] = Body(...)) -> 统一响应:
    try:
        platform = str(请求体.get("platform") or "").strip()
        business = str(请求体.get("business") or "").strip()
        shop_id = str(请求体.get("shop_id") or "*").strip() or "*"
        数据 = 请求体.get("data") or {}

        if not platform:
            return 失败("platform 不能为空")
        if not business:
            return 失败("business 不能为空")
        if not isinstance(数据, dict):
            return 失败("data 必须是对象")

        命中规则 = await 规则服务实例._查找命中规则(platform, business, shop_id, 数据)
        if 命中规则:
            return 成功(
                data={
                    "rule_name": 命中规则.get("name"),
                    "rule_id": 命中规则.get("id"),
                    "actions": 命中规则.get("actions") or [],
                }
            )

        return 成功(
            data={
                "rule_name": "默认规则",
                "rule_id": None,
                "actions": 默认动作列表,
            }
        )
    except Exception as 异常:
        return 失败(f"测试规则匹配失败: {异常}")
