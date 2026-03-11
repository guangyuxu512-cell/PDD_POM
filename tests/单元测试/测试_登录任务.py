"""
登录任务单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class 测试_登录任务:
    """测试拼多多登录任务的关键分支"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        页面.url = "https://mms.pinduoduo.com/login/"
        return 页面

    @pytest.fixture
    def 模拟登录页(self, tmp_path):
        登录页实例 = MagicMock()
        登录页实例.访问首页 = AsyncMock()
        登录页实例.加载Cookie = AsyncMock(return_value=False)
        登录页实例.检测Cookie是否有效 = AsyncMock(return_value=False)
        登录页实例.导航 = AsyncMock()
        登录页实例.切换账号登录 = AsyncMock()
        登录页实例.填写手机号 = AsyncMock()
        登录页实例.填写密码 = AsyncMock()
        登录页实例.点击登录 = AsyncMock()
        登录页实例.检测滑块验证码 = AsyncMock(return_value=False)
        登录页实例.检测短信验证码 = AsyncMock(return_value=False)
        登录页实例.是否登录成功 = AsyncMock(return_value=True)
        登录页实例.保存Cookie = AsyncMock()
        登录页实例.截图登录状态 = AsyncMock(return_value="test.png")
        登录页实例._获取Cookie文件路径 = MagicMock(return_value=tmp_path / "shop-1.json")
        return 登录页实例

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_手机号密码登录成功(self, 模拟回调, 模拟页面, 模拟登录页):
        """无 Cookie 时走手机号密码登录并保存 Cookie"""
        from tasks.登录任务 import 登录任务

        with patch("tasks.登录任务.登录页", return_value=模拟登录页):
            任务 = 登录任务()
            结果 = await 任务.执行(
                模拟页面,
                {"shop_id": "shop-1", "username": "13800138000", "password": "abc123"},
            )

        assert 结果 == "成功"
        模拟登录页.导航.assert_awaited_once()
        模拟登录页.切换账号登录.assert_awaited_once()
        模拟登录页.填写手机号.assert_awaited_once_with("13800138000")
        模拟登录页.填写密码.assert_awaited_once_with("abc123")
        模拟登录页.点击登录.assert_awaited_once()
        模拟登录页.保存Cookie.assert_awaited_once_with("shop-1")

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_Cookie有效时直接成功(self, 模拟回调, 模拟页面, 模拟登录页, tmp_path):
        """本地 Cookie 有效时跳过密码登录"""
        from tasks.登录任务 import 登录任务

        Cookie文件 = tmp_path / "shop-1.json"
        Cookie文件.write_text("[]", encoding="utf-8")
        模拟登录页._获取Cookie文件路径.return_value = Cookie文件
        模拟登录页.加载Cookie.return_value = True
        模拟登录页.检测Cookie是否有效.return_value = True

        with patch("tasks.登录任务.登录页", return_value=模拟登录页):
            任务 = 登录任务()
            结果 = await 任务.执行(
                模拟页面,
                {"shop_id": "shop-1", "username": "13800138000", "password": "abc123"},
            )

        assert 结果 == "成功"
        模拟登录页.加载Cookie.assert_awaited_once_with("shop-1")
        模拟登录页.检测Cookie是否有效.assert_awaited_once()
        模拟登录页.导航.assert_not_called()
        模拟登录页.保存Cookie.assert_not_called()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_短信验证码验证通过后登录成功(self, 模拟回调, 模拟页面, 模拟登录页):
        """检测到短信验证码后，人工输入完成并跳转首页时返回成功"""
        from tasks.登录任务 import 登录任务

        模拟登录页.检测短信验证码.return_value = True

        async def 模拟等待(_秒):
            模拟页面.url = "https://mms.pinduoduo.com/home"

        with patch("tasks.登录任务.登录页", return_value=模拟登录页), patch(
            "tasks.登录任务.asyncio.sleep", new_callable=AsyncMock
        ) as 模拟睡眠:
            模拟睡眠.side_effect = 模拟等待
            任务 = 登录任务()
            结果 = await 任务.执行(
                模拟页面,
                {"shop_id": "shop-1", "username": "13800138000", "password": "abc123"},
            )

        assert 结果 == "成功"
        模拟睡眠.assert_awaited_once_with(3)
        assert 模拟登录页.截图登录状态.await_count == 2
        模拟登录页.保存Cookie.assert_awaited_once_with("shop-1")

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_短信验证码等待超时返回失败(self, 模拟回调, 模拟页面, 模拟登录页):
        """检测到短信验证码后，120 秒内未跳转首页时返回失败"""
        from tasks.登录任务 import 登录任务

        模拟登录页.检测短信验证码.return_value = True

        with patch("tasks.登录任务.登录页", return_value=模拟登录页), patch(
            "tasks.登录任务.asyncio.sleep", new_callable=AsyncMock
        ) as 模拟睡眠:
            任务 = 登录任务()
            结果 = await 任务.执行(
                模拟页面,
                {"shop_id": "shop-1", "username": "13800138000", "password": "abc123"},
            )

        assert 结果 == "失败"
        assert 模拟睡眠.await_count == 40
        assert 模拟登录页.截图登录状态.await_count == 2
        模拟登录页.保存Cookie.assert_not_called()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_滑块验证码时返回需要验证码(self, 模拟回调, 模拟页面, 模拟登录页):
        """兼容旧调用时检测到滑块验证码，返回等待人工处理"""
        from tasks.登录任务 import 登录任务

        模拟登录页.检测滑块验证码.return_value = True

        with patch("tasks.登录任务.登录页", return_value=模拟登录页):
            任务 = 登录任务()
            结果 = await 任务.执行(
                模拟页面,
                {"username": "13800138000", "password": "abc123"},
            )

        assert 结果 == "需要验证码"
        模拟登录页.截图登录状态.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_context_destroyed后仍可判定登录成功(self, 模拟回调, 模拟页面, 模拟登录页):
        """登录结果检测抛出 context destroyed 时，仍通过首页 URL 判定成功"""
        from tasks.登录任务 import 登录任务

        async def 点击后跳转():
            模拟页面.url = "https://mms.pinduoduo.com/home"

        模拟登录页.点击登录.side_effect = 点击后跳转
        模拟登录页.是否登录成功.side_effect = Exception("context destroyed")

        with patch("tasks.登录任务.登录页", return_value=模拟登录页):
            任务 = 登录任务()
            结果 = await 任务.执行(
                模拟页面,
                {"shop_id": "shop-1", "username": "13800138000", "password": "abc123"},
            )

        assert 结果 == "成功"
        模拟登录页.保存Cookie.assert_awaited_once_with("shop-1")
