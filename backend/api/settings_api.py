"""
系统设置接口模块

提供 settings 表的列表与更新接口。
"""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Body, HTTPException

from backend.logging_config import get_logger
from backend.models.data_structure import 成功, 统一响应
from backend.utils.settings import batch_update_settings, list_settings, update_setting
from tasks.celery_app import 刷新Celery配置


路由 = APIRouter(prefix="/api/settings", tags=["系统设置"])
日志记录器 = get_logger()
Celery配置键 = {"celery_broker_url", "celery_result_backend"}


def _规范化配置值(key: str, value: Any) -> Any:
    """修正常见 Redis URL 格式问题，避免保存脏配置。"""
    if key in Celery配置键 and isinstance(value, str):
        return re.sub(r"/:(\d+)(?=[/?]|$)", r":\1", value.strip())
    return value


def _按需刷新Celery配置(keys: list[str]) -> None:
    """相关配置更新后同步刷新 Celery 客户端配置。"""
    if not any(key in Celery配置键 for key in keys):
        return

    try:
        刷新Celery配置()
    except Exception as 异常:
        日志记录器.warning(f"刷新 Celery 配置失败（忽略）: {异常}")


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
        update_setting(key, _规范化配置值(key, body.get("value")))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"配置项 {key} 不存在") from exc

    _按需刷新Celery配置([key])
    return 成功(message="配置已更新")


@路由.post("/batch", summary="批量更新配置")
async def 批量更新(
    body: dict[str, Any] = Body(..., description="批量更新项"),
) -> 统一响应:
    """批量更新配置项。"""
    items = body.get("items", [])
    规范化更新项: list[dict[str, Any]] = []
    更新键列表: list[str] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        key = str(item.get("key") or "").strip()
        规范化更新项.append(
            {
                **item,
                "key": key,
                "value": _规范化配置值(key, item.get("value")),
            }
        )
        if key:
            更新键列表.append(key)

    updated_count = batch_update_settings(规范化更新项)
    _按需刷新Celery配置(更新键列表)
    return 成功(message=f"已更新 {updated_count} 项配置")
