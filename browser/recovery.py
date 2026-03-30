"""
浏览器自动恢复模块

用于在页面或上下文异常关闭后重建浏览器实例。
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Optional

from backend.logging_config import get_logger
from backend.services.log_service import 日志服务实例


日志记录器 = get_logger()


class 浏览器恢复器:
    """管理店铺浏览器的自动恢复节流与重试。"""

    MAX_RECOVERY_ATTEMPTS = 3
    RECOVERY_COOLDOWN_SECONDS = 5

    def __init__(self) -> None:
        self._恢复计数: dict[str, int] = {}
        self._上次恢复时间: dict[str, float] = {}

    async def _记录恢复日志(
        self,
        店铺ID: str,
        店铺名称: Optional[str],
        级别: str,
        消息: str,
        详情: Optional[str] = None,
    ) -> None:
        try:
            await 日志服务实例.写入日志(
                shop_id=店铺ID,
                shop_name=店铺名称,
                level=级别,
                source="browser_recovery",
                message=消息,
                detail=详情,
            )
        except Exception as 异常:
            日志记录器.warning(f"写入浏览器恢复日志失败: shop_id={店铺ID}, error={异常}")

    async def 尝试恢复(self, 管理器: Any, 店铺ID: str, 店铺配置: Optional[dict[str, Any]]) -> bool:
        """尝试重建指定店铺的浏览器上下文。"""
        连续恢复次数 = self._恢复计数.get(店铺ID, 0)
        if 连续恢复次数 >= self.MAX_RECOVERY_ATTEMPTS:
            日志记录器.error(f"店铺 {店铺ID} 连续恢复失败次数已达上限: {连续恢复次数}")
            await self._记录恢复日志(
                店铺ID,
                (店铺配置 or {}).get("name"),
                "ERROR",
                "浏览器恢复已达到最大重试次数",
                f"连续失败次数: {连续恢复次数}",
            )
            return False

        当前时间 = time.time()
        上次恢复时间 = self._上次恢复时间.get(店铺ID, 0.0)
        剩余冷却 = self.RECOVERY_COOLDOWN_SECONDS - (当前时间 - 上次恢复时间)
        if 剩余冷却 > 0:
            await asyncio.sleep(剩余冷却)

        店铺配置 = dict(店铺配置 or {})
        店铺名称 = 店铺配置.get("name")
        self._上次恢复时间[店铺ID] = time.time()

        try:
            if 店铺ID in getattr(管理器, "实例集", {}):
                try:
                    await 管理器.关闭店铺(店铺ID)
                except Exception:
                    getattr(管理器, "实例集", {}).pop(店铺ID, None)

            await 管理器.打开店铺(店铺ID, 店铺配置)
            self.重置恢复计数(店铺ID)
            日志记录器.success(f"店铺 {店铺ID} 浏览器恢复成功")
            await self._记录恢复日志(店铺ID, 店铺名称, "INFO", "浏览器恢复成功")
            return True
        except Exception as 异常:
            self._恢复计数[店铺ID] = 连续恢复次数 + 1
            日志记录器.error(f"店铺 {店铺ID} 浏览器恢复失败: {异常}")
            await self._记录恢复日志(
                店铺ID,
                店铺名称,
                "ERROR",
                "浏览器恢复失败",
                str(异常),
            )
            return False

    def 重置恢复计数(self, 店铺ID: str) -> None:
        self._恢复计数.pop(店铺ID, None)
        self._上次恢复时间.pop(店铺ID, None)


浏览器恢复实例 = 浏览器恢复器()

