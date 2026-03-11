"""
浏览器接口模块

提供浏览器实例管理的 REST API 接口。
"""
from typing import Dict, Any
from fastapi import APIRouter, Body

from backend.models.数据结构 import 统一响应, 成功, 失败
from backend.services import 浏览器服务
from backend.services.店铺服务 import 店铺服务实例


# 创建路由
路由 = APIRouter(prefix="/api/browser", tags=["浏览器管理"])


@路由.post("/init", summary="初始化浏览器")
async def 初始化浏览器(
    配置: Dict[str, Any] = Body(default={}, description="浏览器配置")
) -> 统一响应:
    """
    初始化 Playwright 环境

    参数:
        配置: 浏览器配置字典，包含 chrome_path, max_instances, default_proxy 等

    返回:
        统一响应: 初始化结果
    """
    try:
        await 浏览器服务.初始化浏览器(配置)
        return 成功(message="浏览器初始化成功")
    except Exception as e:
        return 失败(f"初始化浏览器失败: {str(e)}")


@路由.post("/{shop_id}/open", summary="打开浏览器")
async def 打开浏览器(shop_id: str) -> 统一响应:
    """
    打开指定店铺的浏览器

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 包含浏览器实例信息
    """
    try:
        # 检查店铺是否存在
        店铺 = await 店铺服务实例.根据ID获取(shop_id)
        if not 店铺:
            return 失败("店铺不存在")

        # 打开浏览器
        实例信息 = await 浏览器服务.打开店铺浏览器(shop_id, 店铺)
        return 成功(data=实例信息, message="浏览器已打开")
    except ValueError as e:
        return 失败(str(e))
    except Exception as e:
        return 失败(f"打开浏览器失败: {str(e)}")


@路由.post("/{shop_id}/close", summary="关闭浏览器")
async def 关闭浏览器(shop_id: str) -> 统一响应:
    """
    关闭指定店铺的浏览器

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 关闭结果
    """
    try:
        成功标志 = await 浏览器服务.关闭店铺浏览器(shop_id)
        if not 成功标志:
            return 失败("浏览器未打开或不存在")
        return 成功(message="浏览器已关闭")
    except Exception as e:
        return 失败(f"关闭浏览器失败: {str(e)}")


@路由.get("/instances", summary="获取浏览器实例列表")
async def 获取实例列表() -> 统一响应:
    """
    获取所有运行中的浏览器实例

    返回:
        统一响应: 包含浏览器实例列表
    """
    try:
        实例列表 = await 浏览器服务.获取实例列表()
        return 成功(data=实例列表)
    except Exception as e:
        return 失败(f"获取实例列表失败: {str(e)}")


@路由.post("/close-all", summary="关闭全部浏览器")
async def 关闭全部浏览器() -> 统一响应:
    """
    关闭所有浏览器实例

    返回:
        统一响应: 包含关闭的实例数量
    """
    try:
        关闭数量 = await 浏览器服务.关闭所有浏览器()
        return 成功(data={"count": 关闭数量}, message=f"已关闭 {关闭数量} 个浏览器实例")
    except Exception as e:
        return 失败(f"关闭全部浏览器失败: {str(e)}")


@路由.get("/{shop_id}/status", summary="检查浏览器状态")
async def 检查浏览器状态(shop_id: str) -> 统一响应:
    """
    检查指定店铺的浏览器状态

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 包含浏览器状态
    """
    try:
        状态 = await 浏览器服务.检查状态(shop_id)
        if not 状态:
            return 失败("浏览器未打开")
        return 成功(data=状态)
    except Exception as e:
        return 失败(f"检查浏览器状态失败: {str(e)}")
