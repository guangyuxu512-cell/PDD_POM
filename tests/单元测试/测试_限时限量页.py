"""
限时限量页单元测试
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from selectors.选择器配置 import 选择器配置


class 测试_限时限量页:
    """测试限时限量页 POM。"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        页面.goto = AsyncMock()
        页面.click = AsyncMock()
        页面.wait_for_selector = AsyncMock()
        页面.url = "https://mms.pinduoduo.com/tool/promotion/create?tool_full_channel=10921_77271"
        页面.locator = MagicMock()
        页面.keyboard = MagicMock()
        页面.keyboard.press = AsyncMock()
        页面.mouse = MagicMock()
        页面.mouse.move = AsyncMock()
        页面.mouse.click = AsyncMock()
        页面.mouse.down = AsyncMock()
        页面.mouse.up = AsyncMock()
        页面.mouse.wheel = AsyncMock()
        页面.get_by_text = MagicMock()
        页面.get_by_placeholder = MagicMock()
        return 页面

    @pytest.mark.asyncio
    async def test_导航到创建页_打开固定URL并等待加载(self, 模拟页面):
        from pages.限时限量页 import 限时限量页

        页面对象 = 限时限量页(模拟页面)
        页面对象.页面加载延迟 = AsyncMock()

        await 页面对象.导航到创建页()

        模拟页面.goto.assert_awaited_once_with(
            "https://mms.pinduoduo.com/tool/promotion/create?tool_full_channel=10921_77271",
            wait_until="domcontentloaded",
        )
        页面对象.页面加载延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_点击展开更多设置_按选择器回退(self, 模拟页面, monkeypatch):
        from pages.限时限量页 import 限时限量页
        from selectors.限时限量页选择器 import 限时限量页选择器

        async def 点击副作用(选择器, timeout=10000):
            if 选择器 == "bad-selector":
                raise RuntimeError("bad selector")
            return None

        monkeypatch.setattr(限时限量页选择器, "展开更多设置按钮", 选择器配置("bad-selector", ["good-selector"]))
        模拟页面.click.side_effect = 点击副作用

        页面对象 = 限时限量页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        await 页面对象.点击展开更多设置()

        assert 模拟页面.click.await_args_list[0].args[0] == "bad-selector"
        assert 模拟页面.click.await_args_list[1].args[0] == "good-selector"
        页面对象.操作前延迟.assert_awaited_once()
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_弹窗输入商品ID_前后延迟并填写(self, 模拟页面, monkeypatch):
        from pages.限时限量页 import 限时限量页
        from selectors.限时限量页选择器 import 限时限量页选择器

        失败输入框 = MagicMock()
        失败输入框.click = AsyncMock(side_effect=RuntimeError("bad"))
        成功输入框 = MagicMock()
        成功输入框.click = AsyncMock()
        成功输入框.fill = AsyncMock()
        失败定位器 = MagicMock()
        失败定位器.first = 失败输入框
        成功定位器 = MagicMock()
        成功定位器.first = 成功输入框

        monkeypatch.setattr(限时限量页选择器, "选择商品弹窗_搜索输入框", 选择器配置("bad-input", ["good-input"]))
        模拟页面.locator.side_effect = lambda selector: {
            "bad-input": 失败定位器,
            "good-input": 成功定位器,
        }[selector]

        页面对象 = 限时限量页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()
        页面对象.随机延迟 = AsyncMock()

        await 页面对象.弹窗输入商品ID("998877")

        模拟页面.keyboard.press.assert_awaited_once_with("Control+A")
        成功输入框.fill.assert_awaited_once_with("998877")
        页面对象.随机延迟.assert_awaited_once_with(0.2, 0.5)

    @pytest.mark.asyncio
    async def test_输入商品折扣_清空后输入(self, 模拟页面, monkeypatch):
        from pages.限时限量页 import 限时限量页
        from selectors.限时限量页选择器 import 限时限量页选择器

        输入框 = MagicMock()
        输入框.click = AsyncMock()
        输入框.fill = AsyncMock()
        定位器 = MagicMock()
        定位器.first = 输入框
        模拟页面.locator.return_value = 定位器
        monkeypatch.setattr(
            限时限量页选择器,
            "商品行折扣输入框",
            staticmethod(lambda 商品ID: 选择器配置("row-discount")),
        )

        页面对象 = 限时限量页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()
        页面对象.随机延迟 = AsyncMock()

        assert await 页面对象.输入商品折扣("1001", 6) is True

        模拟页面.keyboard.press.assert_awaited_once_with("Control+A")
        输入框.fill.assert_awaited_once_with("6")
        页面对象.操作后延迟.assert_awaited_once()

    def test_商品行折扣输入框_主选择器带placeholder精确匹配(self):
        from selectors.限时限量页选择器 import 限时限量页选择器

        选择器 = 限时限量页选择器.商品行折扣输入框("1001")
        assert '@placeholder="1～9.7"' in 选择器.主选择器
        assert 'contains(text(), "1001")' in 选择器.备选选择器[0]

    @pytest.mark.asyncio
    async def test_等待创建成功_成功与失败路径(self, 模拟页面, monkeypatch):
        from pages.限时限量页 import 限时限量页
        from selectors.限时限量页选择器 import 限时限量页选择器

        monkeypatch.setattr(限时限量页选择器, "创建成功提示", 选择器配置("success-tip"))

        页面对象 = 限时限量页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        assert await 页面对象.等待创建成功() is True
        页面对象.操作后延迟.assert_awaited_once()

        模拟页面.wait_for_selector.reset_mock(side_effect=True)
        模拟页面.wait_for_selector.side_effect = RuntimeError("timeout")
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        assert await 页面对象.等待创建成功() is False
        页面对象.操作后延迟.assert_not_awaited()
