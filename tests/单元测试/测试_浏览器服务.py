"""
浏览器服务健壮性测试
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.services import 浏览器服务 as 浏览器服务模块


class 假浏览器管理器:
    """用于测试并发初始化的假管理器"""

    def __init__(self):
        self.playwright实例 = None
        self.初始化 = AsyncMock(side_effect=self._初始化)

    async def _初始化(self, 配置=None):
        await asyncio.sleep(0.01)
        self.playwright实例 = object()


class 测试_浏览器服务:
    """测试浏览器服务的防御性加固"""

    def teardown_method(self):
        浏览器服务模块.管理器实例 = None
        浏览器服务模块.初始化锁 = None
        浏览器服务模块.初始化锁所属事件循环 = None

    @pytest.mark.asyncio
    async def test_确保已初始化_并发调用时只初始化一次(self):
        """并发调用确保已初始化时，只允许一次真正的 Playwright 初始化"""
        假管理器实例 = 假浏览器管理器()

        with patch("backend.services.浏览器服务.浏览器管理器", return_value=假管理器实例):
            await asyncio.gather(
                浏览器服务模块.确保已初始化(),
                浏览器服务模块.确保已初始化(),
            )

        assert 浏览器服务模块.管理器实例 is 假管理器实例
        假管理器实例.初始化.assert_awaited_once()
