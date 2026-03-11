"""
商品列表页单元测试
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock


class 模拟弹窗信息:
    def __init__(self, 新页面):
        self.value = asyncio.Future()
        self.value.set_result(新页面)


class 模拟弹窗上下文:
    def __init__(self, 新页面):
        self.信息 = 模拟弹窗信息(新页面)

    async def __aenter__(self):
        return self.信息

    async def __aexit__(self, exc_type, exc, tb):
        return False


class 测试_商品列表页:
    """测试商品列表页 POM。"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        页面.goto = AsyncMock()
        页面.query_selector = AsyncMock(return_value=None)
        页面.get_by_text = MagicMock()
        页面.get_by_role = MagicMock()
        页面.get_by_test_id = MagicMock()
        页面.locator = MagicMock()
        页面.mouse = MagicMock()
        页面.mouse.move = AsyncMock()
        页面.mouse.click = AsyncMock()
        页面.mouse.down = AsyncMock()
        页面.mouse.up = AsyncMock()
        页面.mouse.wheel = AsyncMock()
        页面.keyboard = MagicMock()
        页面.keyboard.type = AsyncMock()
        页面.keyboard.press = AsyncMock()

        文本定位器 = MagicMock()
        文本定位器.count = AsyncMock(return_value=0)
        文本定位器.first = MagicMock()
        文本定位器.first.click = AsyncMock()
        页面.get_by_text.return_value = 文本定位器
        return 页面

    @pytest.mark.asyncio
    async def test_导航后自动关闭弹窗(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        页面对象 = 商品列表页(模拟页面)
        页面对象.随机延迟 = AsyncMock()
        页面对象.关闭所有弹窗 = AsyncMock()

        await 页面对象.导航()

        模拟页面.goto.assert_awaited_once_with(
            "https://mms.pinduoduo.com/goods/goods_list?msfrom=mms_sidenav",
            wait_until="domcontentloaded",
        )
        页面对象.关闭所有弹窗.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_关闭所有弹窗_优先点击关闭按钮(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        关闭按钮 = MagicMock()
        关闭按钮.click = AsyncMock()
        模拟页面.query_selector = AsyncMock(side_effect=[关闭按钮, None, None, None])

        页面对象 = 商品列表页(模拟页面)
        页面对象.随机延迟 = AsyncMock()

        await 页面对象.关闭所有弹窗()

        关闭按钮.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_搜索商品_切换条件并填写商品ID(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        搜索切换 = MagicMock()
        搜索切换.click = AsyncMock()
        搜索入口 = MagicMock()
        搜索入口.first = 搜索切换

        输入框 = MagicMock()
        输入框.click = AsyncMock()
        输入框.fill = AsyncMock()
        商品ID容器 = MagicMock()
        商品ID容器.get_by_test_id.return_value = 输入框
        DIV定位器 = MagicMock()
        DIV定位器.filter.return_value = 商品ID容器

        查询按钮 = MagicMock()
        查询按钮.click = AsyncMock()

        模拟页面.locator.side_effect = lambda selector: {"i": 搜索入口, "div": DIV定位器}[selector]
        模拟页面.get_by_role.return_value = 查询按钮

        页面对象 = 商品列表页(模拟页面)
        页面对象.随机延迟 = AsyncMock()
        页面对象.安全点击_文本 = AsyncMock()

        await 页面对象.搜索商品("123456")

        搜索切换.click.assert_awaited_once()
        页面对象.安全点击_文本.assert_awaited_once_with("商品ID")
        输入框.fill.assert_awaited_once_with("123456")
        查询按钮.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_点击发布相似品_返回新页面(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        发布链接 = MagicMock()
        发布链接.click = AsyncMock()
        链接结果 = MagicMock()
        链接结果.first = 发布链接
        A定位器 = MagicMock()
        A定位器.filter.return_value = 链接结果

        确认按钮 = MagicMock()
        确认按钮.click = AsyncMock()
        按钮集合 = MagicMock()
        按钮集合.first = 确认按钮
        模态框 = MagicMock()
        模态框.get_by_test_id.return_value = 按钮集合

        新页面 = MagicMock()
        新页面.wait_for_load_state = AsyncMock()

        模拟页面.locator.side_effect = lambda selector: {"a": A定位器}[selector]
        模拟页面.get_by_test_id.return_value = 模态框
        模拟页面.expect_popup.return_value = 模拟弹窗上下文(新页面)

        页面对象 = 商品列表页(模拟页面)
        页面对象.随机延迟 = AsyncMock()

        结果页面 = await 页面对象.点击发布相似品()

        assert 结果页面 is 新页面
        发布链接.click.assert_awaited_once()
        确认按钮.click.assert_awaited_once()
        新页面.wait_for_load_state.assert_awaited_once_with("domcontentloaded")
