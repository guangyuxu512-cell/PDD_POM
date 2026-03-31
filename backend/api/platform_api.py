"""
平台接口模块

提供当前支持的平台列表。
"""
from fastapi import APIRouter

import platforms  # noqa: F401
from backend.models.data_structure import 成功, 统一响应
from platforms.base.base_platform import list_platforms


路由 = APIRouter(prefix="/api", tags=["平台"])


@路由.get("/platforms", summary="获取平台列表")
async def 获取平台列表() -> 统一响应:
    """返回当前已注册的平台清单。"""
    return 成功(data={"list": list_platforms()})
