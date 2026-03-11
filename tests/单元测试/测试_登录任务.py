"""
登录任务单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class 测试_登录任务:
    """测试登录任务的各种场景"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = AsyncMock()
        页面.goto = AsyncMock()
        页面.wait_for_selector = AsyncMock()
        页面.screenshot = AsyncMock(return_value=b"fake_screenshot")

        # 创建 mock 元素（默认）
        模拟元素 = MagicMock()
        模拟元素.is_visible = AsyncMock(return_value=True)
        模拟元素.bounding_box = AsyncMock(return_value={"x": 100, "y": 100, "width": 200, "height": 50})

        页面.query_selector = AsyncMock(return_value=模拟元素)

        # mouse 和 keyboard
        页面.mouse = MagicMock()
        页面.mouse.move = AsyncMock()
        页面.mouse.click = AsyncMock()
        页面.mouse.down = AsyncMock()
        页面.mouse.up = AsyncMock()
        页面.mouse.wheel = AsyncMock()

        页面.keyboard = MagicMock()
        页面.keyboard.type = AsyncMock()
        页面.keyboard.press = AsyncMock()

        return 页面

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)  # 屏蔽真实回调
    async def test_登录成功(self, 模拟回调, 模拟页面):
        """测试登录成功的场景"""
        # 创建 mock 元素
        模拟元素 = MagicMock()
        模拟元素.is_visible = AsyncMock(return_value=True)
        模拟元素.bounding_box = AsyncMock(return_value={"x": 100, "y": 100, "width": 200, "height": 50})

        # 模拟登录成功：无验证码 + 登录成功标志存在
        def 选择器判断(选择器):
            if ".captcha-container" in 选择器:
                return None  # 没有验证码
            else:
                return 模拟元素  # 其他元素存在

        模拟页面.query_selector = AsyncMock(side_effect=选择器判断)

        from tasks.登录任务 import 登录任务
        任务 = 登录任务()
        结果 = await 任务.执行(模拟页面, {"username": "test", "password": "123"})
        assert 结果 == "成功"

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_遇到验证码(self, 模拟回调, 模拟页面):
        """测试遇到验证码的场景"""
        # 创建 mock 元素
        模拟元素 = MagicMock()
        模拟元素.is_visible = AsyncMock(return_value=True)
        模拟元素.bounding_box = AsyncMock(return_value={"x": 100, "y": 100, "width": 200, "height": 50})

        # 模拟出现验证码：所有元素都存在
        模拟页面.query_selector = AsyncMock(return_value=模拟元素)

        from tasks.登录任务 import 登录任务
        任务 = 登录任务()
        结果 = await 任务.执行(模拟页面, {"username": "test", "password": "123"})
        assert 结果 == "需要验证码"

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_登录异常截图(self, 模拟回调, 模拟页面):
        """测试登录异常时的截图"""
        # 创建 mock 元素
        模拟元素 = MagicMock()
        模拟元素.is_visible = AsyncMock(return_value=True)
        模拟元素.bounding_box = AsyncMock(return_value={"x": 100, "y": 100, "width": 200, "height": 50})

        # 模拟未知状态：既没验证码也没成功标志
        def 选择器判断(选择器):
            if ".captcha-container" in 选择器 or ".user-info" in 选择器:
                return None  # 验证码和成功标志都不存在
            else:
                return 模拟元素  # 其他元素存在

        模拟页面.query_selector = AsyncMock(side_effect=选择器判断)

        from tasks.登录任务 import 登录任务
        任务 = 登录任务()
        with pytest.raises(Exception, match="登录结果未知"):
            await 任务.执行(模拟页面, {"username": "test", "password": "123"})
