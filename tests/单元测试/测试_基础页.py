"""
基础页单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


class 测试_基础页:
    """测试 基础页 的所有方法"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = AsyncMock()
        页面.goto = AsyncMock()
        页面.click = AsyncMock()
        页面.wait_for_selector = AsyncMock()
        页面.screenshot = AsyncMock()
        页面.mouse = MagicMock()
        页面.mouse.move = AsyncMock()
        页面.mouse.click = AsyncMock()
        页面.mouse.wheel = AsyncMock()
        页面.keyboard = MagicMock()
        页面.keyboard.type = AsyncMock()
        页面.keyboard.press = AsyncMock()

        # 模拟元素
        模拟元素 = AsyncMock()
        模拟元素.is_visible = AsyncMock(return_value=True)
        模拟元素.bounding_box = AsyncMock(
            return_value={"x": 100, "y": 100, "width": 200, "height": 50}
        )
        页面.query_selector = AsyncMock(return_value=模拟元素)

        return 页面

    @pytest.mark.asyncio
    async def test_导航(self, 模拟页面):
        from pages.基础页 import 基础页
        基础 = 基础页(模拟页面)
        await 基础.导航("https://example.com")
        模拟页面.goto.assert_called_once()

    @pytest.mark.asyncio
    async def test_安全点击(self, 模拟页面):
        from pages.基础页 import 基础页
        基础 = 基础页(模拟页面)
        await 基础.安全点击("#btn")
        模拟页面.wait_for_selector.assert_called()
        # 现在使用真人模拟器，所以检查 mouse.click 而不是 click
        模拟页面.mouse.click.assert_called()

    @pytest.mark.asyncio
    async def test_安全填写(self, 模拟页面):
        from pages.基础页 import 基础页
        基础 = 基础页(模拟页面)
        await 基础.安全填写("#input", "abc")
        # 现在使用真人模拟器，可能有打错字的情况，所以 >= 3
        assert 模拟页面.keyboard.type.call_count >= 3

    @pytest.mark.asyncio
    async def test_截图(self, 模拟页面):
        from pages.基础页 import 基础页
        基础 = 基础页(模拟页面)
        路径 = await 基础.截图("测试截图")
        assert 路径.endswith(".png")
        模拟页面.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_元素是否存在_存在(self, 模拟页面):
        from pages.基础页 import 基础页
        模拟元素 = MagicMock()
        模拟页面.query_selector.return_value = 模拟元素
        基础 = 基础页(模拟页面)
        assert await 基础.元素是否存在("#el") == True

    @pytest.mark.asyncio
    async def test_元素是否存在_不存在(self, 模拟页面):
        from pages.基础页 import 基础页
        模拟页面.query_selector.return_value = None
        基础 = 基础页(模拟页面)
        assert await 基础.元素是否存在("#el") == False
