"""
心跳服务模块

后台定时向群晖 Agent 发送在线心跳。
"""
import asyncio
from typing import Any, Optional

import httpx

from backend.配置 import 配置实例


def 构建请求头() -> Optional[dict[str, str]]:
    """构造 Agent 心跳请求头。"""
    密钥 = str(配置实例.X_RPA_KEY or "").strip()
    if not 密钥:
        return None
    return {"X-RPA-KEY": 密钥}


def 校验业务响应(响应: httpx.Response) -> None:
    """校验 Agent 的统一业务响应。"""
    try:
        响应数据: Any = 响应.json()
    except ValueError:
        return

    if isinstance(响应数据, dict) and 响应数据.get("code") not in (None, 0):
        raise RuntimeError(响应数据.get("msg") or "Agent 返回失败")


class 心跳服务:
    """后台心跳服务"""

    def __init__(self):
        """初始化心跳服务"""
        self._心跳任务: Optional[asyncio.Task] = None
        self._停止事件: Optional[asyncio.Event] = None

    async def 启动(self) -> None:
        """
        启动心跳服务

        已启动时重复调用会直接返回。
        """
        if self._心跳任务 and not self._心跳任务.done():
            return

        self._停止事件 = asyncio.Event()
        self._心跳任务 = asyncio.create_task(self._循环发送心跳())

    async def 停止(self) -> None:
        """
        停止心跳服务

        未启动时重复调用会直接返回。
        """
        if not self._心跳任务:
            return

        if self._停止事件:
            self._停止事件.set()

        try:
            await self._心跳任务
        except asyncio.CancelledError:
            pass
        except Exception as e:
            # 中文注释：心跳任务属于附属能力，停止阶段出现异常只记录，不能影响主服务退出。
            print(f"[心跳服务] 停止心跳任务时发生异常（忽略）: {e}")

        self._心跳任务 = None
        self._停止事件 = None

    async def _循环发送心跳(self) -> None:
        """按固定间隔循环发送心跳"""
        while self._停止事件 and not self._停止事件.is_set():
            try:
                # 中文注释：心跳上报失败不能让后台循环退出，否则主服务会悄悄失去心跳能力。
                await self._发送心跳()
            except Exception as e:
                print(f"[心跳服务] 心跳循环异常（忽略）: {e}")

            try:
                await asyncio.wait_for(self._停止事件.wait(), timeout=30)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                # 中文注释：等待停止事件时的异常同样只记录，避免心跳循环被意外打断。
                print(f"[心跳服务] 等待停止事件异常（忽略）: {e}")
                continue

    async def _发送心跳(self) -> None:
        """发送单次心跳，请求失败时静默忽略"""
        if not 配置实例.AGENT_MACHINE_ID or not 配置实例.AGENT_HEARTBEAT_URL:
            return

        请求头 = 构建请求头()
        if not 请求头:
            print("[心跳服务] 心跳已跳过：未配置 X_RPA_KEY")
            return

        数据 = {
            "machine_id": 配置实例.AGENT_MACHINE_ID,
            "shadowbot_running": False,
        }

        try:
            # 中文注释：显式限制 HTTP 超时，避免网络异常时把心跳协程长时间挂住。
            async with httpx.AsyncClient(timeout=5.0) as 客户端:
                响应 = await asyncio.wait_for(
                    客户端.post(配置实例.AGENT_HEARTBEAT_URL, json=数据, headers=请求头),
                    timeout=5
                )
                响应.raise_for_status()
                校验业务响应(响应)
        except Exception as e:
            print(f"[心跳服务] 发送心跳失败（忽略）: {e}")
            return


心跳服务实例 = 心跳服务()
