"""售后页单元测试。"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class 测试_售后页:
    """测试售后页 POM。"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        页面.goto = AsyncMock()
        页面.wait_for_selector = AsyncMock()
        页面.wait_for_load_state = AsyncMock()
        页面.query_selector = AsyncMock(return_value=None)
        页面.query_selector_all = AsyncMock(return_value=[])
        页面.evaluate = AsyncMock()
        页面.click = AsyncMock()
        页面.screenshot = AsyncMock()
        页面.locator = MagicMock()
        页面.url = "https://mms.pinduoduo.com/aftersales/list"
        页面.context = MagicMock()
        页面.context.pages = [页面]
        页面.context.wait_for_event = AsyncMock()
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

    @pytest.mark.asyncio
    async def test_扫描所有待处理_含翻页循环(self, 模拟页面):
        from pages.售后页 import 售后页

        页面对象 = 售后页(模拟页面)
        页面对象.切换待处理 = AsyncMock()
        页面对象.获取售后单数量 = AsyncMock(side_effect=[2, 1])
        页面对象.获取第N行信息 = AsyncMock(
            side_effect=[
                {"订单号": "A-1", "售后类型": "仅退款"},
                {"订单号": "A-2", "售后类型": "退货退款"},
                {"订单号": "A-3", "售后类型": "换货"},
            ]
        )
        页面对象.翻页 = AsyncMock(side_effect=[True, False])

        结果 = await 页面对象.扫描所有待处理()

        assert 结果 == [
            {"订单号": "A-1", "售后类型": "仅退款"},
            {"订单号": "A-2", "售后类型": "退货退款"},
            {"订单号": "A-3", "售后类型": "换货"},
        ]
        页面对象.切换待处理.assert_awaited_once()
        assert 页面对象.获取第N行信息.await_count == 3
        assert 页面对象.翻页.await_count == 2

    @pytest.mark.asyncio
    async def test_点击详情并切换标签_等待并切换到新标签(self, 模拟页面):
        from pages.售后页 import 售后页

        新页面 = MagicMock()
        新页面.url = "https://mms.pinduoduo.com/aftersales/detail"
        新页面.wait_for_load_state = AsyncMock()
        新页面.wait_for_selector = AsyncMock()
        模拟页面.context.wait_for_event = AsyncMock(return_value=新页面)

        页面对象 = 售后页(模拟页面)
        页面对象.点击第N行详情 = AsyncMock()
        页面对象._等待详情页区域 = AsyncMock(return_value=True)

        await 页面对象.点击详情并切换标签(3)

        页面对象.点击第N行详情.assert_awaited_once_with(3)
        模拟页面.context.wait_for_event.assert_awaited_once_with("page", timeout=10000)
        新页面.wait_for_load_state.assert_awaited_once_with("domcontentloaded")
        assert 页面对象._详情页 is 新页面

    @pytest.mark.asyncio
    async def test_抓取详情页完整信息_返回完整dict(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(
            return_value={
                "订单编号": "O-1001",
                "售后类型": "仅退款",
                "售后状态": "待商家处理",
                "退款金额": 6.08,
                "申请原因": "不想要了",
                "可用按钮列表": ["同意退款", "拒绝"],
                "商家已回复": True,
            }
        )
        详情页.wait_for_selector = AsyncMock()

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()
        页面对象._等待详情页区域 = AsyncMock(return_value=True)

        结果 = await 页面对象.抓取详情页完整信息()

        assert 结果["订单编号"] == "O-1001"
        assert 结果["售后类型"] == "仅退款"
        assert 结果["可用按钮列表"] == ["同意退款", "拒绝"]
        assert 结果["商家已回复"] is True
        详情页.evaluate.assert_awaited_once()
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_点击指定按钮_JS执行(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(side_effect=[True, False])

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        assert await 页面对象.点击指定按钮("同意退款") is True
        页面对象.操作后延迟.assert_awaited_once()

        页面对象.操作后延迟.reset_mock()
        assert await 页面对象.点击指定按钮("不存在按钮") is False
        页面对象.操作后延迟.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_读取当前所有按钮_返回列表(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(return_value=["同意退款", "拒绝", "添加留言"])

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        结果 = await 页面对象.读取当前所有按钮()

        assert 结果 == ["同意退款", "拒绝", "添加留言"]
        详情页.evaluate.assert_awaited_once()
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_检查订单是否待处理_兼容两种待处理文案(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(side_effect=["当前状态：待商家处理", "状态：已完成"])

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        assert await 页面对象.检查订单是否待处理() is True
        assert await 页面对象.检查订单是否待处理() is False

    @pytest.mark.asyncio
    async def test_关闭详情标签_关闭后清空引用(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.is_closed = MagicMock(return_value=False)
        详情页.close = AsyncMock()

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页

        await 页面对象.关闭详情标签()

        详情页.close.assert_awaited_once()
        assert 页面对象._详情页 is None

    @pytest.mark.asyncio
    async def test_详情页截图_保存到截图目录(self, 模拟页面, tmp_path):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.screenshot = AsyncMock()

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        with patch("pages.售后页.配置实例") as 配置实例模拟:
            配置实例模拟.DATA_DIR = str(tmp_path)
            结果 = await 页面对象.详情页截图("detail-case")

        assert 结果 == str(tmp_path / "screenshots" / "detail-case.png")
        详情页.screenshot.assert_awaited_once_with(
            path=str(tmp_path / "screenshots" / "detail-case.png"),
            full_page=True,
        )
