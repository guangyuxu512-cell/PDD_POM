"""
商品列表页单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


class 测试_商品列表页:
    """测试商品列表页 POM。"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        页面.click = AsyncMock()
        页面.bring_to_front = AsyncMock()
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
    async def test_导航到商品列表(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        页面对象 = 商品列表页(模拟页面)
        页面对象.页面加载延迟 = AsyncMock()

        await 页面对象.导航到商品列表()

        模拟页面.goto.assert_awaited_once_with(
            "https://mms.pinduoduo.com/goods/goods_list?msfrom=mms_sidenav",
            wait_until="domcontentloaded",
        )
        页面对象.页面加载延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_关闭所有弹窗_优先点击关闭按钮(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        关闭按钮 = MagicMock()
        关闭按钮.click = AsyncMock()
        已返回关闭按钮 = {"done": False}

        async def 查询选择器(选择器):
            if 选择器 == "[data-testid='beast-core-icon-close']" and not 已返回关闭按钮["done"]:
                已返回关闭按钮["done"] = True
                return 关闭按钮
            return None

        模拟页面.query_selector = AsyncMock(side_effect=查询选择器)

        页面对象 = 商品列表页(模拟页面)
        页面对象.随机延迟 = AsyncMock()

        await 页面对象.关闭所有弹窗()

        关闭按钮.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_输入商品ID_填写搜索框(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        输入框 = MagicMock()
        输入框.click = AsyncMock()
        输入框.fill = AsyncMock()
        搜索框定位器 = MagicMock()
        搜索框定位器.first = 输入框
        模拟页面.locator.side_effect = lambda selector: {
            "[data-tracking-viewid='goods_id'] input": 搜索框定位器,
        }[selector]

        页面对象 = 商品列表页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()
        页面对象.随机延迟 = AsyncMock()

        await 页面对象.输入商品ID("123456")

        页面对象.操作前延迟.assert_awaited_once()
        页面对象.随机延迟.assert_awaited_once_with(0.2, 0.5)
        输入框.fill.assert_awaited_once_with("123456")
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_点击查询(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        页面对象 = 商品列表页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        await 页面对象.点击查询()

        页面对象.操作前延迟.assert_awaited_once()
        模拟页面.click.assert_awaited_once_with(
            "button[data-tracking-click-viewid='ele_inquire']",
            timeout=10000,
        )
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_等待搜索结果_优先等待列表容器(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        模拟页面.wait_for_selector = AsyncMock()
        页面对象 = 商品列表页(模拟页面)
        页面对象.随机延迟 = AsyncMock()

        await 页面对象.等待搜索结果()

        模拟页面.wait_for_selector.assert_awaited_once_with("table tbody", timeout=5000)
        页面对象.随机延迟.assert_awaited_once_with(1.0, 2.0)

    @pytest.mark.asyncio
    async def test_点击发布相似(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        页面对象 = 商品列表页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        await 页面对象.点击发布相似()

        页面对象.操作前延迟.assert_awaited_once()
        模拟页面.click.assert_awaited_once_with(
            "a[data-tracking-viewid='new_similar']",
            timeout=10000,
        )
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_确认发布相似弹窗(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        页面对象 = 商品列表页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.页面加载延迟 = AsyncMock()

        await 页面对象.确认发布相似弹窗()

        页面对象.操作前延迟.assert_awaited_once()
        模拟页面.click.assert_awaited_once_with(
            "button[data-tracking-viewid='el_release_similar_pop_ups']",
            timeout=10000,
        )
        页面对象.页面加载延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_等待搜索结果_无等待方法时回退随机延迟(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        delattr(模拟页面, "wait_for_selector")
        页面对象 = 商品列表页(模拟页面)
        页面对象.随机延迟 = AsyncMock()

        await 页面对象.等待搜索结果()

        页面对象.随机延迟.assert_awaited_once_with(1.0, 2.0)

    @pytest.mark.asyncio
    async def test_切回前台(self, 模拟页面):
        from pages.商品列表页 import 商品列表页

        页面对象 = 商品列表页(模拟页面)

        await 页面对象.切回前台()

        模拟页面.bring_to_front.assert_awaited_once()
