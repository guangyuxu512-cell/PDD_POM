"""
浏览器最大化与页面复用修复测试
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class 测试_浏览器复用修复:
    """验证浏览器管理器的最大化与页面刷新逻辑。"""

    @pytest.mark.asyncio
    async def test_打开店铺_补充_no_viewport_参数(self):
        from browser.管理器 import 浏览器管理器
        import browser.管理器 as 管理器模块

        管理器 = 浏览器管理器()
        模拟页面 = MagicMock()
        模拟页面.is_closed.return_value = False
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
            await 管理器.打开店铺("shop-1", {"headless": False})

        启动参数 = 启动持久上下文.await_args
        assert 启动参数.kwargs["viewport"] is None
        assert 启动参数.kwargs["no_viewport"] is True
        assert "--start-maximized" in 启动参数.kwargs["args"]

    def test_获取页面_缓存页关闭时自动刷新到现有页面(self):
        from browser.管理器 import 浏览器管理器

        管理器 = 浏览器管理器()
        已关闭页面 = MagicMock()
        已关闭页面.is_closed.return_value = True
        新页面 = MagicMock()
        新页面.is_closed.return_value = False
        模拟上下文 = MagicMock()
        模拟上下文.pages = [新页面]

        管理器.实例集["shop-1"] = {
            "浏览器": 模拟上下文,
            "页面": 已关闭页面,
            "page": 已关闭页面,
        }

        页面 = 管理器.获取页面("shop-1")

        assert 页面 is 新页面
        assert 管理器.实例集["shop-1"]["页面"] is 新页面
        assert 管理器.实例集["shop-1"]["page"] is 新页面

    def test_获取页面_所有页面都关闭时抛错(self):
        from browser.管理器 import 浏览器管理器

        管理器 = 浏览器管理器()
        已关闭页面 = MagicMock()
        已关闭页面.is_closed.return_value = True
        关闭页2 = MagicMock()
        关闭页2.is_closed.return_value = True
        模拟上下文 = MagicMock()
        模拟上下文.pages = [关闭页2]

        管理器.实例集["shop-1"] = {
            "浏览器": 模拟上下文,
            "页面": 已关闭页面,
            "page": 已关闭页面,
        }

        with pytest.raises(RuntimeError, match="所有页面已关闭"):
            管理器.获取页面("shop-1")
