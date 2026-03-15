"""售后页单元测试。"""
from unittest.mock import AsyncMock, MagicMock

import pytest


class 测试_售后页:
    """测试售后页 POM。"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        页面.goto = AsyncMock()
        页面.wait_for_selector = AsyncMock()
        页面.query_selector = AsyncMock(return_value=None)
        页面.query_selector_all = AsyncMock(return_value=[])
        页面.evaluate = AsyncMock()
        页面.click = AsyncMock()
        页面.locator = MagicMock()
        页面.url = "https://mms.pinduoduo.com/aftersales/list"
        页面.mouse = MagicMock()
        页面.mouse.move = AsyncMock()
        页面.mouse.click = AsyncMock()
        页面.mouse.down = AsyncMock()
        页面.mouse.up = AsyncMock()
        页面.mouse.wheel = AsyncMock()
        页面.keyboard = MagicMock()
        页面.keyboard.type = AsyncMock()
        页面.keyboard.press = AsyncMock()
        页面.get_by_text = MagicMock()
        页面.get_by_placeholder = MagicMock()
        return 页面

    @pytest.mark.asyncio
    async def test_导航到售后列表_打开固定URL(self, 模拟页面):
        from pages.售后页 import 售后页

        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.页面加载延迟 = AsyncMock()

        await 页面对象.导航到售后列表()

        模拟页面.goto.assert_awaited_once_with(
            "https://mms.pinduoduo.com/aftersales/list",
            wait_until="domcontentloaded",
        )
        页面对象.操作前延迟.assert_awaited_once()
        页面对象.页面加载延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_搜索订单_正确填写并点击查询(self, 模拟页面):
        from pages.售后页 import 售后页
        from selectors.售后页选择器 import 售后页选择器

        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()
        页面对象.安全填写 = AsyncMock()
        页面对象.安全点击 = AsyncMock()

        await 页面对象.搜索订单("ORDER-001")

        页面对象.安全填写.assert_awaited_once_with(
            售后页选择器.搜索输入框.主选择器,
            "ORDER-001",
        )
        页面对象.安全点击.assert_awaited_once_with(售后页选择器.搜索按钮.主选择器)
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_获取第N行信息_返回正确的字典结构(self, 模拟页面):
        from pages.售后页 import 售后页

        模拟页面.evaluate = AsyncMock(
            return_value={
                "订单号": "240001",
                "售后类型": "仅退款",
                "退款金额": "¥12.30",
                "商品名称": "测试商品",
            }
        )
        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        结果 = await 页面对象.获取第N行信息(2)

        assert 结果 == {
            "订单号": "240001",
            "售后类型": "仅退款",
            "退款金额": "¥12.30",
            "商品名称": "测试商品",
        }
        模拟页面.evaluate.assert_awaited_once()
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_点击同意退款_调用正确选择器(self, 模拟页面):
        from pages.售后页 import 售后页
        from selectors.售后页选择器 import 售后页选择器

        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()
        页面对象.安全点击 = AsyncMock()

        await 页面对象.点击同意退款()

        页面对象.安全点击.assert_awaited_once_with(售后页选择器.同意退款按钮.主选择器)
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_处理确认弹窗_等待后点击确定(self, 模拟页面):
        from pages.售后页 import 售后页
        from selectors.售后页选择器 import 售后页选择器

        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()
        页面对象.点击弹窗确定 = AsyncMock()

        assert await 页面对象.处理确认弹窗() is True

        模拟页面.wait_for_selector.assert_awaited_once_with(
            售后页选择器.确认弹窗.主选择器,
            timeout=5000,
        )
        页面对象.点击弹窗确定.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_翻页_检查disabled逻辑(self, 模拟页面):
        from pages.售后页 import 售后页
        from selectors.售后页选择器 import 售后页选择器

        def 构造定位器(aria_disabled: str, class_name: str):
            元素 = MagicMock()
            元素.get_attribute = AsyncMock(
                side_effect=lambda 属性名: {
                    "aria-disabled": aria_disabled,
                    "class": class_name,
                }.get(属性名)
            )
            定位器 = MagicMock()
            定位器.first = 元素
            return 定位器

        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()
        页面对象.安全点击 = AsyncMock()

        模拟页面.locator.return_value = 构造定位器("true", "ant-pagination-next ant-pagination-disabled")
        assert await 页面对象.翻页() is False
        页面对象.安全点击.assert_not_awaited()

        页面对象.操作前延迟.reset_mock()
        页面对象.操作后延迟.reset_mock()
        页面对象.安全点击.reset_mock()
        模拟页面.locator.return_value = 构造定位器("false", "ant-pagination-next")

        assert await 页面对象.翻页() is True
        页面对象.安全点击.assert_awaited_once_with(售后页选择器.下一页按钮.主选择器)
        页面对象.操作后延迟.assert_awaited_once()
