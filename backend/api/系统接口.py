"""
系统接口模块

提供系统配置和健康检查的 REST API 接口。
"""
import asyncio
from time import perf_counter
from typing import Dict, Any, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Body

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
    Redis连接测试请求,
)
from backend.配置 import 配置实例
from backend.services.系统服务 import 系统服务实例


# 创建路由
路由 = APIRouter(prefix="/api/system", tags=["系统配置"])


@路由.get("/config", summary="获取系统配置")
async def 获取系统配置() -> 统一响应:
    """
    获取系统配置（脱敏后）

    返回:
        统一响应: 包含系统配置的响应
    """
    try:
        配置 = await 系统服务实例.获取配置()
        return 成功(data=配置)
    except Exception as e:
        return 失败(f"获取系统配置失败: {str(e)}")


@路由.put("/config", summary="更新系统配置")
async def 更新系统配置(
    配置: Dict[str, Any] = Body(..., description="新的配置项")
) -> 统一响应:
    """
    更新系统配置

    参数:
        配置: 新的配置项（只接受白名单字段）

    返回:
        统一响应: 更新后的配置
    """
    try:
        新配置 = await 系统服务实例.更新配置(配置)
        return 成功(data=新配置, message="配置已更新")
    except ValueError as e:
        return 失败(str(e))
    except Exception as e:
        return 失败(f"更新系统配置失败: {str(e)}")


@路由.post("/test-redis", summary="测试 Redis 连接")
async def 测试Redis连接(
    请求: Optional[Redis连接测试请求] = Body(default=None, description="Redis 连接信息")
) -> 统一响应:
    """
    测试 Redis 连接

    参数:
        请求: Redis 连接信息，可为空；为空时回退到系统配置

    返回:
        统一响应: 包含连接耗时
    """
    Redis地址 = (请求.redis_url if 请求 else None) or 配置实例.REDIS_URL
    Redis地址 = Redis地址.strip() if Redis地址 else ""

    if not Redis地址:
        return 失败("Redis 连接失败: Redis 地址不能为空")

    客户端 = None
    try:
        客户端 = aioredis.from_url(Redis地址)
        开始时间 = perf_counter()
        await asyncio.wait_for(客户端.ping(), timeout=5)
        延迟毫秒 = round((perf_counter() - 开始时间) * 1000, 2)
        return 成功(
            data={"latency_ms": 延迟毫秒},
            message="Redis 连接成功"
        )
    except asyncio.TimeoutError:
        return 失败("Redis 连接失败: 连接超时（5秒）")
    except Exception as e:
        return 失败(f"Redis 连接失败: {str(e)}")
    finally:
        if 客户端 is not None:
            try:
                # 中文注释：关闭 Redis 连接也属于外部 IO，这里单独做超时和异常兜底，避免覆盖主响应。
                关闭方法 = getattr(客户端, "aclose", None)
                if callable(关闭方法):
                    await asyncio.wait_for(关闭方法(), timeout=5)
                else:
                    await asyncio.wait_for(客户端.close(), timeout=5)
            except Exception as e:
                print(f"[系统接口] 关闭 Redis 连接失败（忽略）: {e}")


@路由.get("/health", summary="健康检查")
async def 健康检查() -> 统一响应:
    """
    健康检查

    返回:
        统一响应: 系统健康状态
    """
    try:
        健康状态 = await 系统服务实例.健康检查()
        return 成功(data=健康状态)
    except Exception as e:
        return 失败(f"健康检查失败: {str(e)}")
