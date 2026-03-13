"""
发布相似商品任务收尾恢复测试
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class 假页面:
    """用于收尾场景的轻量页面替身。"""

    def __init__(self, 已关闭: bool, 上下文=None):
        self._已关闭 = 已关闭
        self.context = 上下文

    def is_closed(self) -> bool:
        return self._已关闭


class 测试_发布相似商品任务收尾恢复:
    """验证发布页关闭后的主页面恢复逻辑。"""

    @pytest.mark.asyncio
    async def test_安全截图并关闭_主页面已关闭时自动新开商品列表页(self):
        from tasks.发布相似商品任务 import 发布相似商品任务

        新主页面 = 假页面(False)
        浏览器上下文 = SimpleNamespace(new_page=AsyncMock(return_value=新主页面))
        发布页对象 = MagicMock()
        发布页对象.页面 = 假页面(False, 上下文=浏览器上下文)
        发布页对象.截图当前状态 = AsyncMock(return_value="publish.png")
        发布页对象.关闭当前标签页 = AsyncMock()

        旧商品列表对象 = MagicMock()
        旧商品列表对象.页面 = 假页面(True)
        旧商品列表对象.切回前台 = AsyncMock()

        新商品列表对象 = MagicMock()
        新商品列表对象.导航到商品列表 = AsyncMock()
        新商品列表对象.切回前台 = AsyncMock()

        with patch("tasks.发布相似商品任务.商品列表页", return_value=新商品列表对象):
            任务 = 发布相似商品任务()
            await 任务._安全截图并关闭(发布页对象, 旧商品列表对象)

        发布页对象.截图当前状态.assert_awaited_once()
        发布页对象.关闭当前标签页.assert_awaited_once()
        浏览器上下文.new_page.assert_awaited_once()
        新商品列表对象.导航到商品列表.assert_awaited_once()
        新商品列表对象.切回前台.assert_awaited_once()
        旧商品列表对象.切回前台.assert_not_awaited()
