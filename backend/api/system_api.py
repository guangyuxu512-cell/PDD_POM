"""
系统接口模块

提供系统配置和健康检查的 REST API 接口。
"""
import asyncio
import base64
import hashlib
import hmac
import time
from time import perf_counter
from typing import Dict, Any, Optional

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter, Body

from backend.models.data_structure import (
    统一响应,
    成功,
    失败,
    Redis连接测试请求,
    验证码测试请求,
    飞书Webhook测试请求,
)
from backend.config import 配置实例
from backend.logging_config import get_logger
from backend.services.system_service import 系统服务实例


# 创建路由
路由 = APIRouter(prefix="/api/system", tags=["系统配置"])
日志记录器 = get_logger()


def _生成飞书签名(时间戳: str, 密钥: str) -> str:
    """按飞书机器人签名规则生成 sign。"""
    待签名字符串 = f"{时间戳}\n{密钥}"
    签名摘要 = hmac.new(待签名字符串.encode("utf-8"), digestmod=hashlib.sha256).digest()
    return base64.b64encode(签名摘要).decode("utf-8")


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
                日志记录器.warning(f"关闭 Redis 连接失败（忽略）: {e}")


@路由.post("/test-captcha", summary="测试验证码服务")
async def 测试验证码服务(
    请求: Optional[验证码测试请求] = Body(default=None, description="验证码服务信息")
) -> 统一响应:
    """
    测试验证码服务可用性。

    参数:
        请求: 验证码服务信息，可为空；为空时回退到系统配置
    """
    服务商 = ((请求.captcha_provider if 请求 else None) or 配置实例.CAPTCHA_PROVIDER or "yescaptcha").strip().lower()
    API密钥 = ((请求.captcha_api_key if 请求 else None) or 配置实例.CAPTCHA_API_KEY or "").strip()

    if not API密钥:
        return 失败("验证码测试失败: API Key 不能为空")

    if 服务商 != "yescaptcha":
        return 失败(f"验证码测试失败: 暂不支持的服务商 {服务商}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as 客户端:
            响应 = await 客户端.post(
                "https://api.yescaptcha.com/getBalance",
                json={"clientKey": API密钥},
            )
            响应.raise_for_status()
            响应数据 = 响应.json()
    except Exception as e:
        return 失败(f"验证码测试失败: {str(e)}")

    if 响应数据.get("errorId", 1) != 0:
        错误描述 = 响应数据.get("errorDescription") or "未知错误"
        return 失败(f"验证码测试失败: {错误描述}")

    余额 = 响应数据.get("balance")
    return 成功(data={"balance": 余额}, message="验证码服务连接成功")


@路由.post("/test-feishu-webhook", summary="测试飞书 Webhook")
async def 测试飞书Webhook(
    请求: Optional[飞书Webhook测试请求] = Body(default=None, description="飞书 Webhook 信息")
) -> 统一响应:
    """
    测试飞书 Webhook 连通性。

    参数:
        请求: Webhook 信息，可为空；为空时回退到系统配置
    """
    Webhook地址 = ((请求.webhook_url if 请求 else None) or 配置实例.FEISHU_WEBHOOK_URL or "").strip()
    签名密钥 = ((请求.secret if 请求 else None) or 配置实例.FEISHU_SECRET or "").strip()

    if not Webhook地址:
        return 失败("飞书 Webhook 测试失败: Webhook 地址不能为空")

    消息体: dict[str, Any] = {
        "msg_type": "text",
        "content": {"text": "RPA 系统连接测试，Webhook 配置正常。"},
    }

    if 签名密钥:
        时间戳 = str(int(time.time()))
        消息体["timestamp"] = 时间戳
        消息体["sign"] = _生成飞书签名(时间戳, 签名密钥)

    try:
        async with httpx.AsyncClient(timeout=10.0) as 客户端:
            响应 = await 客户端.post(Webhook地址, json=消息体)
            响应.raise_for_status()
            响应数据 = 响应.json()
    except Exception as e:
        return 失败(f"飞书 Webhook 测试失败: {str(e)}")

    if 响应数据.get("code") == 0 or 响应数据.get("StatusCode") == 0:
        return 成功(message="飞书 Webhook 测试成功")

    错误信息 = 响应数据.get("msg") or 响应数据.get("Message") or "未知错误"
    return 失败(f"飞书 Webhook 测试失败: {错误信息}")


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


@路由.get("/metrics", summary="运行指标")
async def 获取运行指标() -> 统一响应:
    """返回基础运行指标。"""
    try:
        指标数据 = await 系统服务实例.获取指标()
        return 成功(data=指标数据)
    except Exception as e:
        return 失败(f"获取运行指标失败: {str(e)}")
