"""
登录页单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


class 测试_登录页:
    """测试拼多多登录页 POM"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = AsyncMock()
        页面.goto = AsyncMock()
        页面.wait_for_url = AsyncMock()
        页面.query_selector = AsyncMock(return_value=None)
        页面.screenshot = AsyncMock()
        页面.get_by_text = MagicMock()
        页面.get_by_placeholder = MagicMock()
        页面.get_by_test_id = MagicMock()
        页面.mouse = MagicMock()
        页面.mouse.move = AsyncMock()
        页面.mouse.click = AsyncMock()
        页面.mouse.down = AsyncMock()
        页面.mouse.up = AsyncMock()
        页面.mouse.wheel = AsyncMock()
        页面.keyboard = MagicMock()
        页面.keyboard.type = AsyncMock()
        页面.keyboard.press = AsyncMock()
        页面.url = "https://mms.pinduoduo.com/login/"
        return 页面

    @pytest.mark.asyncio
    async def test_初始化地址(self, 模拟页面):
        from pages.登录页 import 登录页

        登录 = 登录页(模拟页面)

        assert 登录.登录地址 == "https://mms.pinduoduo.com/login/"
        assert 登录.首页地址 == "https://mms.pinduoduo.com/home"

    @pytest.mark.asyncio
    async def test_切换账号登录(self, 模拟页面):
        from pages.登录页 import 登录页

        登录 = 登录页(模拟页面)
        登录.安全点击_文本 = AsyncMock()
        登录.随机延迟 = AsyncMock()

        await 登录.切换账号登录()

        登录.安全点击_文本.assert_awaited_once_with("账号登录")

    @pytest.mark.asyncio
    async def test_填写手机号和密码(self, 模拟页面):
        from pages.登录页 import 登录页

        登录 = 登录页(模拟页面)
        登录.安全填写_占位符 = AsyncMock()

        await 登录.填写手机号("13800138000")
        await 登录.填写密码("abc123")

        assert 登录.安全填写_占位符.await_args_list[0].args == ("请输入账号名/手机号", "13800138000")
        assert 登录.安全填写_占位符.await_args_list[1].args == ("请输入密码", "abc123")

    @pytest.mark.asyncio
    async def test_点击登录使用_test_id(self, 模拟页面):
        from pages.登录页 import 登录页

        登录按钮 = MagicMock()
        登录按钮.click = AsyncMock()
        模拟页面.get_by_test_id.return_value = 登录按钮

        登录 = 登录页(模拟页面)
        登录.随机延迟 = AsyncMock()

        await 登录.点击登录()

        模拟页面.get_by_test_id.assert_called_once_with("beast-core-button")
        登录按钮.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_检测Cookie是否有效(self, 模拟页面):
        from pages.登录页 import 登录页

        模拟页面.url = "https://mms.pinduoduo.com/home"
        登录 = 登录页(模拟页面)
        登录.访问首页 = AsyncMock()

        assert await 登录.检测Cookie是否有效() is True

    @pytest.mark.asyncio
    async def test_检测短信验证码(self, 模拟页面):
        from pages.登录页 import 登录页

        模拟页面.query_selector.return_value = MagicMock()
        登录 = 登录页(模拟页面)

        assert await 登录.检测短信验证码() is True
        模拟页面.query_selector.assert_awaited_once_with(
            "[placeholder*='请输入短信验证码'], [placeholder*='短信验证码']"
        )

    @pytest.mark.asyncio
    async def test_是否登录成功_命中首页URL(self, 模拟页面):
        from pages.登录页 import 登录页

        模拟页面.url = "https://mms.pinduoduo.com/home"
        登录 = 登录页(模拟页面)

        assert await 登录.是否登录成功() is True
        模拟页面.wait_for_url.assert_awaited_once_with("**/home**", timeout=10000)

    @pytest.mark.asyncio
    async def test_是否登录成功_context_destroyed后检查当前URL(self, 模拟页面):
        from pages.登录页 import 登录页

        模拟页面.wait_for_url.side_effect = Exception("context destroyed")
        模拟页面.url = "https://mms.pinduoduo.com/home"
        登录 = 登录页(模拟页面)
        登录.随机延迟 = AsyncMock()

        assert await 登录.是否登录成功() is True
        登录.随机延迟.assert_awaited_once_with(3, 5)
