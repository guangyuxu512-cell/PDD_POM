"""
推广页单元测试
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from selectors.选择器配置 import 选择器配置


class 测试_推广页:
    """测试推广页 POM。"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        页面.goto = AsyncMock()
        页面.go_back = AsyncMock()
        页面.click = AsyncMock()
        页面.wait_for_selector = AsyncMock()
        页面.query_selector = AsyncMock(return_value=None)
        页面.query_selector_all = AsyncMock(return_value=[])
        页面.evaluate = AsyncMock()
        页面.url = "https://yingxiao.pinduoduo.com/goods/promotion/list?msfrom=mms_sidenav"
        页面.locator = MagicMock()
        页面.keyboard = MagicMock()
        页面.keyboard.press = AsyncMock()
        页面.mouse = MagicMock()
        页面.mouse.wheel = AsyncMock()
        return 页面

    @pytest.mark.asyncio
    async def test_导航到全站推广页_打开固定URL(self, 模拟页面):
        from pages.推广页 import 推广页

        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()

        await 页面对象.导航到全站推广页()

        模拟页面.goto.assert_awaited_once_with(
            "https://yingxiao.pinduoduo.com/goods/promotion/list?msfrom=mms_sidenav",
            wait_until="domcontentloaded",
        )
        页面对象._随机等待.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_点击添加推广商品_按选择器回退(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        async def 点击副作用(选择器, timeout=10000):
            if 选择器 == "bad-selector":
                raise RuntimeError("bad")
            return None

        monkeypatch.setattr(推广页选择器, "添加推广商品按钮", 选择器配置("bad-selector", ["good-selector"]))
        模拟页面.click.side_effect = 点击副作用

        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()

        结果 = await 页面对象.点击添加推广商品()

        assert 结果 is True
        assert 模拟页面.click.await_args_list[0].args[0] == "bad-selector"
        assert 模拟页面.click.await_args_list[1].args[0] == "good-selector"

    @pytest.mark.asyncio
    async def test_获取列表商品ID_提取12位数字并去重(self, 模拟页面):
        from pages.推广页 import 推广页

        行1 = MagicMock()
        行1.inner_text = AsyncMock(return_value="商品ID 123456789012 文案")
        行2 = MagicMock()
        行2.inner_text = AsyncMock(return_value="另一个 123456789012 和 987654321098")
        模拟页面.query_selector_all = AsyncMock(return_value=[行1, 行2])

        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()

        结果 = await 页面对象.获取列表商品ID()

        assert 结果 == ["123456789012", "987654321098"]

    @pytest.mark.asyncio
    async def test_点击开启推广_点击失败时使用JS兜底(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        monkeypatch.setattr(推广页选择器, "开启推广按钮", 选择器配置("bad-button", ["good-button"]))

        async def 点击副作用(选择器, timeout=10000):
            raise RuntimeError("click failed")

        模拟页面.click.side_effect = 点击副作用
        模拟页面.evaluate = AsyncMock(return_value=None)
        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()
        页面对象._random_wait_after_click = AsyncMock()

        结果 = await 页面对象.点击开启推广()

        assert 结果 is True
        模拟页面.mouse.wheel.assert_awaited_once()
        模拟页面.evaluate.assert_awaited()
