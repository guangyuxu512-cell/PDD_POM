"""
浏览器恢复器测试
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from browser.recovery import 浏览器恢复实例


class 测试_浏览器恢复器:
    @pytest.fixture(autouse=True)
    def 清理恢复状态(self):
        浏览器恢复实例._恢复计数.clear()
        浏览器恢复实例._上次恢复时间.clear()
        yield
        浏览器恢复实例._恢复计数.clear()
        浏览器恢复实例._上次恢复时间.clear()

    @pytest.mark.asyncio
    async def test_尝试恢复_成功时重建浏览器(self):
        管理器 = type("假管理器", (), {})()
        管理器.实例集 = {"shop-1": {"页面": object()}}
        管理器.关闭店铺 = AsyncMock()
        管理器.打开店铺 = AsyncMock()

        with patch.object(浏览器恢复实例, "RECOVERY_COOLDOWN_SECONDS", 0), patch(
            "browser.recovery.日志服务实例.写入日志",
            new=AsyncMock(),
        ):
            结果 = await 浏览器恢复实例.尝试恢复(管理器, "shop-1", {"name": "店铺A"})

        assert 结果 is True
        管理器.关闭店铺.assert_awaited_once_with("shop-1")
        管理器.打开店铺.assert_awaited_once_with("shop-1", {"name": "店铺A"})
        assert "shop-1" not in 浏览器恢复实例._恢复计数

    @pytest.mark.asyncio
    async def test_尝试恢复_超过上限时直接放弃(self):
        浏览器恢复实例._恢复计数["shop-1"] = 浏览器恢复实例.MAX_RECOVERY_ATTEMPTS
        管理器 = type("假管理器", (), {"实例集": {}, "关闭店铺": AsyncMock(), "打开店铺": AsyncMock()})()

        with patch("browser.recovery.日志服务实例.写入日志", new=AsyncMock()):
            结果 = await 浏览器恢复实例.尝试恢复(管理器, "shop-1", {"name": "店铺A"})

        assert 结果 is False
        管理器.关闭店铺.assert_not_awaited()
        管理器.打开店铺.assert_not_awaited()

