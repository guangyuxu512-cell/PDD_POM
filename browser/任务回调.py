"""
任务回调模块

提供 @自动回调 装饰器和 上报() 函数，用于 Worker 向 Agent 上报任务执行状态。
"""
import asyncio
from functools import wraps
from typing import Any, Callable, Optional, Dict
import httpx

from backend.配置 import 配置实例


# 全局回调地址
回调地址: Optional[str] = None


def 设置回调地址(地址: str) -> None:
    """
    设置 Agent 回调地址

    Args:
        地址: Agent 的回调 URL
    """
    global 回调地址
    回调地址 = 地址
    print(f"✓ 回调地址已设置: {地址}")


def 构建请求头() -> Optional[Dict[str, str]]:
    """构造 Agent 回调请求头。"""
    密钥 = str(配置实例.X_RPA_KEY or "").strip()
    if not 密钥:
        return None
    return {"X-RPA-KEY": 密钥}


def 校验业务响应(响应: httpx.Response) -> None:
    """校验 Agent 的统一业务响应。"""
    try:
        响应数据 = 响应.json()
    except ValueError:
        return

    if isinstance(响应数据, dict) and 响应数据.get("code") not in (None, 0):
        raise RuntimeError(响应数据.get("msg") or "Agent 返回失败")


async def _回调(数据: dict) -> None:
    """
    内部回调函数，向 Agent 发送 POST 请求

    Args:
        数据: 要发送的回调数据
    """
    if not 回调地址:
        # 如果没有设置回调地址，静默返回
        return

    请求头 = 构建请求头()
    if not 请求头:
        print("⚠ 回调已跳过：未配置 X_RPA_KEY")
        return

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            响应 = await client.post(回调地址, json=数据, headers=请求头)
            响应.raise_for_status()
            校验业务响应(响应)
    except Exception as e:
        # 回调失败静默处理，不影响任务执行
        print(f"⚠ 回调失败（静默）: {e}")


async def 上报(步骤: str, shop_id: str = None, **额外数据) -> None:
    """
    手动上报任务执行的中间状态（通过 SSE 推送日志给前端）

    注意：此函数只负责推送 SSE 实时日志给前端，不触发 Agent 回调。
    Agent 回调由 @自动回调 装饰器在任务开始、成功、失败时自动触发。

    Args:
        步骤: 当前执行步骤的描述
        shop_id: 店铺 ID（可选，如果提供则自动查询店铺名称）
        **额外数据: 额外的数据字段

    Example:
        await 上报("遇到滑块验证码", shop_id)
        await 上报("正在识别验证码", shop_id)
    """
    # 根据 shop_id 查询店铺名称
    shop_name = None
    if shop_id:
        try:
            from backend.services.店铺服务 import 店铺服务实例
            店铺 = await 店铺服务实例.根据ID获取(shop_id)
            if 店铺:
                shop_name = 店铺.get("name")
            else:
                # 如果查询不到店铺，使用 shop_id 前 8 位
                shop_name = shop_id[:8] if len(shop_id) >= 8 else shop_id
        except Exception as e:
            # 查询失败，使用 shop_id 前 8 位
            shop_name = shop_id[:8] if len(shop_id) >= 8 else shop_id
            print(f"⚠ 查询店铺名称失败: {e}")

    # 通过日志服务推送 SSE 日志给前端
    try:
        from backend.services.日志服务 import 日志服务实例
        await 日志服务实例.写入日志(
            shop_id=shop_id,
            shop_name=shop_name,
            level="INFO",
            source="task",
            message=步骤,
            detail=额外数据 if 额外数据 else None
        )
    except Exception as e:
        # 日志推送失败不影响任务执行
        print(f"⚠ 日志推送失败（静默）: {e}")


def 自动回调(任务名: str) -> Callable:
    """
    自动回调装饰器

    装饰 Task 的执行方法，自动在任务开始、成功、失败时回调 Agent。

    Args:
        任务名: 任务的名称，用于标识任务类型

    Returns:
        装饰器函数

    Example:
        class 登录任务:
            @自动回调("登录")
            async def 执行(self, 页面, 配置: dict):
                # 任务逻辑
                return "成功"
    """
    def 装饰器(函数: Callable) -> Callable:
        @wraps(函数)
        async def 包装函数(*args, **kwargs) -> Any:
            # 任务开始时回调
            await _回调({
                "task": 任务名,
                "status": "running",
                "step": f"{任务名}开始执行"
            })

            try:
                # 执行任务
                结果 = await 函数(*args, **kwargs)

                # 任务成功时回调
                await _回调({
                    "task": 任务名,
                    "status": "success",
                    "result": 结果
                })

                return 结果

            except Exception as 异常:
                # 任务失败时回调
                await _回调({
                    "task": 任务名,
                    "status": "failed",
                    "error": str(异常)
                })

                # 重新抛出异常
                raise

        return 包装函数

    return 装饰器
