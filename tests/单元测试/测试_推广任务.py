"""
推广任务单元测试
"""
import importlib
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class 测试_推广任务:
    """测试推广任务编排。"""

    @pytest.fixture
    def 模拟页面(self):
        return MagicMock()

    @pytest.fixture
    def 模拟推广页(self):
        页面对象 = MagicMock()
        页面对象.导航到全站推广页 = AsyncMock()
        页面对象.返回商品列表页 = AsyncMock()
        页面对象.关闭广告弹窗 = AsyncMock(return_value=True)
        页面对象.点击添加推广商品 = AsyncMock(return_value=True)
        页面对象.获取全局优先起量状态 = AsyncMock(return_value="true")
        页面对象.点击全局优先起量开关 = AsyncMock(return_value=True)
        页面对象.确认关闭优先起量 = AsyncMock(return_value=True)
        页面对象.输入商品ID = AsyncMock(return_value=True)
        页面对象.点击查询 = AsyncMock(return_value=True)
        页面对象.获取列表商品ID = AsyncMock(return_value=["123456789012", "987654321098"])
        页面对象.点击全选 = AsyncMock(return_value=True)
        页面对象.点击投产设置按钮 = AsyncMock(return_value=True)
        页面对象.获取极速起量状态 = AsyncMock(return_value="true")
        页面对象.点击极速起量开关 = AsyncMock(return_value=True)
        页面对象.确认关闭极速起量 = AsyncMock(return_value=True)
        页面对象.填写一阶段投产比 = AsyncMock(return_value=True)
        页面对象.检测投产比限制 = AsyncMock(return_value=False)
        页面对象.点击编辑二阶段 = AsyncMock(return_value=True)
        页面对象.填写二阶段投产比 = AsyncMock(return_value=True)
        页面对象.确认二阶段 = AsyncMock(return_value=True)
        页面对象.确认投产设置 = AsyncMock(return_value=True)
        页面对象.取消投产设置 = AsyncMock(return_value=True)
        页面对象.取消勾选商品 = AsyncMock(return_value=True)
        页面对象.点击开启推广 = AsyncMock(return_value=True)
        页面对象.等待推广成功 = AsyncMock(return_value=True)
        页面对象.截图 = AsyncMock(return_value="promo.png")
        return 页面对象

    def test_注册名为_设置推广(self):
        from tasks import 注册表 as 注册表模块
        import tasks.推广任务 as 推广任务模块

        原注册表 = deepcopy(注册表模块.任务注册表)

        try:
            注册表模块.清空任务注册表()
            推广任务模块 = importlib.reload(推广任务模块)
            推广任务 = 推广任务模块.推广任务
            assert 注册表模块.获取任务类("设置推广") is 推广任务
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_缺少商品ID列表_抛出_ValueError(self, 模拟回调, 模拟页面):
        from tasks.推广任务 import 推广任务

        任务 = 推广任务()

        with patch("tasks.推广任务.上报", new_callable=AsyncMock):
            with pytest.raises(ValueError, match="商品ID列表不能为空"):
                await 任务.执行(模拟页面, {"shop_id": "shop-1", "task_param": {}})

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_正常流程_返回成功并记录结果(self, 模拟回调, 模拟页面, 模拟推广页):
        from tasks.推广任务 import 推广任务

        with patch("tasks.推广任务.上报", new_callable=AsyncMock), \
                patch("tasks.推广任务.推广页", return_value=模拟推广页):
            任务 = 推广任务()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "商品ID列表": "123456789012,987654321098",
                        "一阶段投产比": 5.5,
                        "二阶段投产比": 6.5,
                    },
                },
            )

        assert 结果 == "成功"
        assert 任务._执行结果 == {
            "推广商品数": 2,
            "成功列表": ["123456789012", "987654321098"],
            "失败列表": [],
            "一阶段投产比": 5.5,
            "二阶段投产比": 6.5,
        }
        模拟推广页.关闭广告弹窗.assert_awaited()
        模拟推广页.输入商品ID.assert_awaited_once_with("123456789012,987654321098")
        assert 模拟推广页.点击投产设置按钮.await_count == 2
        模拟推广页.点击开启推广.assert_awaited_once()
        模拟推广页.等待推广成功.assert_awaited_once()
        模拟推广页.返回商品列表页.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_投产限制时跳过并返回无可推广商品(self, 模拟回调, 模拟页面, 模拟推广页):
        from tasks.推广任务 import 推广任务

        模拟推广页.检测投产比限制 = AsyncMock(return_value=True)

        with patch("tasks.推广任务.上报", new_callable=AsyncMock) as 模拟上报, \
                patch("tasks.推广任务.推广页", return_value=模拟推广页):
            任务 = 推广任务()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "商品ID列表": ["123456789012"],
                    },
                },
            )

        assert 结果 == "跳过：无可推广商品"
        assert 任务._执行结果["成功列表"] == []
        assert 任务._执行结果["失败列表"] == ["123456789012"]
        模拟推广页.取消投产设置.assert_awaited_once()
        模拟推广页.取消勾选商品.assert_awaited_once()
        模拟推广页.点击开启推广.assert_not_awaited()
        模拟上报.assert_any_await("商品受投产比限制，跳过: 123456789012", "shop-1")

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_点击添加推广商品失败时返回失败(self, 模拟回调, 模拟页面, 模拟推广页):
        from tasks.推广任务 import 推广任务

        模拟推广页.点击添加推广商品 = AsyncMock(return_value=False)

        with patch("tasks.推广任务.上报", new_callable=AsyncMock), \
                patch("tasks.推广任务.推广页", return_value=模拟推广页):
            任务 = 推广任务()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "商品ID列表": ["123456789012"],
                    },
                },
            )

        assert 结果 == "失败"
        模拟推广页.截图.assert_awaited_once()
