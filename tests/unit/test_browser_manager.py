"""
浏览器管理器单元测试
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class 测试_浏览器管理器:
    @pytest.mark.asyncio
    async def test_打开店铺_使用最大化启动参数(self):
        from browser.manager import 浏览器管理器
        import browser.manager as 管理器模块

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

    def test_获取页面_命中登录页时标记重新登录(self):
        from browser.manager import 浏览器管理器

        管理器 = 浏览器管理器()
        模拟页面 = MagicMock()
        模拟页面.url = "https://mms.pinduoduo.com/login"
        模拟浏览器 = MagicMock()
        模拟浏览器.pages = [模拟页面]
        管理器.实例集["shop-1"] = {
            "页面": 模拟页面,
            "page": 模拟页面,
            "浏览器": 模拟浏览器,
            "店铺名称": "店铺A",
        }

        页面 = 管理器.获取页面("shop-1")

        assert 页面 is 模拟页面
        assert "shop-1" in 管理器.需要重新登录店铺
        assert 管理器.实例集["shop-1"]["需要重新登录"] is True

    @pytest.mark.asyncio
    async def test_安全获取页面_恢复成功后重试(self):
        from browser.manager import 浏览器管理器

        管理器 = 浏览器管理器()
        恢复后页面 = MagicMock()
        管理器.实例集["shop-1"] = {"店铺配置": {"name": "店铺A"}}

        with patch.object(管理器, "获取页面", side_effect=[RuntimeError("浏览器上下文已关闭，需要恢复"), 恢复后页面]), \
                patch("browser.manager.浏览器恢复实例.尝试恢复", new=AsyncMock(return_value=True)) as 模拟恢复:
            页面 = await 管理器.安全获取页面("shop-1")

        assert 页面 is 恢复后页面
        模拟恢复.assert_awaited_once()
