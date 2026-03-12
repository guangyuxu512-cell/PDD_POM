"""
浏览器管理器单元测试
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class 测试_浏览器管理器:
    @pytest.mark.asyncio
    async def test_打开店铺_使用最大化启动参数(self):
        from browser.管理器 import 浏览器管理器
        import browser.管理器 as 管理器模块

        管理器 = 浏览器管理器()
        模拟页面 = MagicMock()
        模拟上下文 = MagicMock()
        模拟上下文.pages = [模拟页面]
        模拟上下文.on = MagicMock()
        启动持久上下文 = AsyncMock(return_value=模拟上下文)
        管理器.playwright实例 = MagicMock()
        管理器.playwright实例.chromium.launch_persistent_context = 启动持久上下文
        管理器.用户目录工厂 = MagicMock()
        管理器.用户目录工厂.获取或创建.return_value = "E:/profiles/shop-1"

        with patch.object(管理器模块.配置实例, "MAX_BROWSER_INSTANCES", 5), \
                patch.object(管理器模块.配置实例, "DEFAULT_PROXY", ""), \
                patch.object(管理器模块.配置实例, "CHROME_PATH", ""):
            结果 = await 管理器.打开店铺("shop-1", {"headless": False})

        assert 结果["页面"] is 模拟页面
        启动参数 = 启动持久上下文.await_args
        assert 启动参数.args[0] == "E:/profiles/shop-1"
        assert 启动参数.kwargs["viewport"] is None
        assert "--start-maximized" in 启动参数.kwargs["args"]
