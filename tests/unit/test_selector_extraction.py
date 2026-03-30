"""
选择器提取单元测试
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from pdd_selectors.selector_config import 选择器配置


class 测试_选择器提取:
    """测试 pdd_selectors 包行为。"""

    def test_选择器配置_所有选择器按主备顺序返回(self):
        配置 = 选择器配置("main", ["backup1", "backup2"])

        assert 配置.所有选择器() == ["main", "backup1", "backup2"]

    @pytest.mark.asyncio
    async def test_商品列表页输入框按选择器列表回退(self, monkeypatch):
        from pages.product_list_page import 商品列表页
        from pdd_selectors.product_list_page_selector import 商品列表页选择器

        模拟页面 = MagicMock()
        失败输入框 = MagicMock()
        失败输入框.click = AsyncMock(side_effect=Exception("bad selector"))
        成功输入框 = MagicMock()
        成功输入框.click = AsyncMock()
        成功输入框.fill = AsyncMock()
        失败定位器 = MagicMock()
        失败定位器.first = 失败输入框
        成功定位器 = MagicMock()
        成功定位器.first = 成功输入框
        模拟页面.locator.side_effect = lambda selector: {
            "bad-selector": 失败定位器,
            "good-selector": 成功定位器,
        }[selector]
        模拟页面.mouse = MagicMock()
        模拟页面.mouse.move = AsyncMock()
        模拟页面.mouse.click = AsyncMock()
        模拟页面.mouse.down = AsyncMock()
        模拟页面.mouse.up = AsyncMock()
        模拟页面.mouse.wheel = AsyncMock()
        模拟页面.keyboard = MagicMock()
        模拟页面.keyboard.type = AsyncMock()
        模拟页面.keyboard.press = AsyncMock()
        模拟页面.get_by_text = MagicMock()
        monkeypatch.setattr(商品列表页选择器, "商品ID搜索框", 选择器配置("bad-selector", ["good-selector"]))

        页面对象 = 商品列表页(模拟页面)
        页面对象.随机延迟 = AsyncMock()

        await 页面对象.输入商品ID("1001")

        失败输入框.click.assert_awaited_once()
        成功输入框.fill.assert_awaited_once_with("1001")
