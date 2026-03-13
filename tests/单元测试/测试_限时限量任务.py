"""
限时限量任务单元测试
"""
import importlib
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class 测试_限时限量任务:
    """测试限时限量任务编排。"""

    @pytest.fixture
    def 模拟页面(self):
        return MagicMock()

    @pytest.fixture
    def 模拟限时限量页(self):
        页面对象 = MagicMock()
        页面对象.导航到创建页 = AsyncMock()
        页面对象.点击展开更多设置 = AsyncMock()
        页面对象.勾选自动创建 = AsyncMock()
        页面对象.点击选择商品 = AsyncMock()
        页面对象.弹窗输入商品ID = AsyncMock()
        页面对象.弹窗点击查询 = AsyncMock()
        页面对象.弹窗等待结果 = AsyncMock()
        页面对象.弹窗勾选第一行 = AsyncMock()
        页面对象.弹窗点击确认选择 = AsyncMock()
        页面对象.填写折扣 = AsyncMock()
        页面对象.点击确认设置 = AsyncMock()
        页面对象.点击创建 = AsyncMock()
        页面对象.等待创建成功 = AsyncMock(return_value=True)
        页面对象.截图 = AsyncMock(return_value="limit.png")
        return 页面对象

    def test_注册名为_限时限量(self):
        """任务应以限时限量名称注册。"""
        from tasks import 注册表 as 注册表模块
        import tasks.限时限量任务 as 限时限量任务模块

        原注册表 = deepcopy(注册表模块.任务注册表)

        try:
            注册表模块.清空任务注册表()
            限时限量任务模块 = importlib.reload(限时限量任务模块)
            限时限量任务 = 限时限量任务模块.限时限量任务
            assert 注册表模块.获取任务类("限时限量") is 限时限量任务
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_缺少_新商品ID_返回跳过(self, 模拟回调, 模拟页面):
        from tasks.限时限量任务 import 限时限量任务

        任务 = 限时限量任务()

        with patch("tasks.限时限量任务.上报", new_callable=AsyncMock) as 模拟上报:
            结果 = await 任务.执行(
                模拟页面,
                {"shop_id": "shop-1", "task_param": {"折扣": 6}},
            )

        assert 结果 == "跳过：无新商品ID"
        模拟上报.assert_any_await("跳过：无新商品ID", "shop-1")

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_缺少_折扣_抛出_ValueError(self, 模拟回调, 模拟页面):
        from tasks.限时限量任务 import 限时限量任务

        任务 = 限时限量任务()

        with patch("tasks.限时限量任务.上报", new_callable=AsyncMock):
            with pytest.raises(ValueError, match="折扣不能为空"):
                await 任务.执行(
                    模拟页面,
                    {"shop_id": "shop-1", "task_param": {"新商品ID": "1001"}},
                )

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_正常流程_单商品创建成功(
        self,
        模拟回调,
        模拟页面,
        模拟限时限量页,
    ):
        from tasks.限时限量任务 import 限时限量任务

        with patch("tasks.限时限量任务.上报", new_callable=AsyncMock), \
                patch("tasks.限时限量任务.限时限量页", return_value=模拟限时限量页):
            任务 = 限时限量任务()
            结果 = await 任务.执行(
                模拟页面,
                {"shop_id": "shop-1", "task_param": {"batch_id": "batch-1", "新商品ID": "1001", "折扣": "6"}},
            )

        assert 结果 == "成功"
        assert 任务._执行结果 == {
            "batch_id": "batch-1",
            "折扣": 6.0,
            "新商品ID": "1001",
        }
        模拟限时限量页.导航到创建页.assert_awaited_once()
        模拟限时限量页.点击展开更多设置.assert_awaited_once()
        模拟限时限量页.勾选自动创建.assert_awaited_once()
        模拟限时限量页.点击选择商品.assert_awaited_once()
        模拟限时限量页.弹窗输入商品ID.assert_awaited_once_with("1001")
        模拟限时限量页.弹窗勾选第一行.assert_awaited_once()
        模拟限时限量页.填写折扣.assert_awaited_once_with(6.0)
        模拟限时限量页.点击确认设置.assert_awaited_once()
        模拟限时限量页.点击创建.assert_awaited_once()
        模拟限时限量页.等待创建成功.assert_awaited_once()
        模拟限时限量页.截图.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_创建失败时返回失败(
        self,
        模拟回调,
        模拟页面,
        模拟限时限量页,
    ):
        from tasks.限时限量任务 import 限时限量任务

        模拟限时限量页.等待创建成功 = AsyncMock(return_value=False)

        with patch("tasks.限时限量任务.上报", new_callable=AsyncMock), \
                patch("tasks.限时限量任务.限时限量页", return_value=模拟限时限量页):
            任务 = 限时限量任务()
            结果 = await 任务.执行(
                模拟页面,
                {"shop_id": "shop-1", "task_param": {"batch_id": "batch-1", "new_product_id": "1001", "折扣": 6}},
            )

        assert 结果 == "失败"
        模拟限时限量页.截图.assert_awaited_once()
