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
        页面对象.输入商品ID = AsyncMock(return_value=True)
        页面对象.点击查询 = AsyncMock(return_value=True)
        页面对象.商品行是否存在 = AsyncMock(return_value=True)
        页面对象.获取全局优先起量状态 = AsyncMock(return_value="true")
        页面对象.点击全局优先起量开关 = AsyncMock(return_value=True)
        页面对象.确认关闭全局起量 = AsyncMock(return_value=True)
        页面对象.点击更多设置 = AsyncMock(return_value=True)
        页面对象.点击预算日限额 = AsyncMock(return_value=True)
        页面对象.输入日限额 = AsyncMock(return_value=True)
        页面对象.确认日限额 = AsyncMock(return_value=True)
        页面对象.点击修改投产铅笔按钮 = AsyncMock(return_value=True)
        页面对象.等待投产弹窗 = AsyncMock(return_value=True)
        页面对象.获取极速起量高级版状态 = AsyncMock(return_value="true")
        页面对象.点击极速起量高级版开关 = AsyncMock(return_value=True)
        页面对象.确认关闭极速起量 = AsyncMock(return_value=True)
        页面对象.输入投产比 = AsyncMock(return_value=True)
        页面对象.确认投产比设置 = AsyncMock(return_value=True)
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
                        "投产比": 5.5,
                        "日限额": 100,
                        "关闭极速起量": True,
                    },
                },
            )

        assert 结果 == "成功"
        assert 任务._执行结果 == {
            "推广商品数": 2,
            "成功列表": ["123456789012", "987654321098"],
            "失败列表": [],
            "投产比": 5.5,
            "日限额": 100.0,
        }
        模拟推广页.关闭广告弹窗.assert_awaited()
        模拟推广页.输入商品ID.assert_awaited_once_with("123456789012,987654321098")
        assert 模拟推广页.商品行是否存在.await_count == 2
        模拟推广页.点击全局优先起量开关.assert_awaited_once()
        模拟推广页.确认关闭全局起量.assert_awaited_once()
        assert 模拟推广页.点击更多设置.await_count == 2
        assert 模拟推广页.点击修改投产铅笔按钮.await_count == 2
        assert 模拟推广页.点击极速起量高级版开关.await_count == 2
        模拟推广页.确认关闭极速起量.assert_any_await("123456789012")
        模拟推广页.确认关闭极速起量.assert_any_await("987654321098")
        模拟推广页.确认投产比设置.assert_any_await("123456789012")
        模拟推广页.确认投产比设置.assert_any_await("987654321098")
        模拟推广页.点击开启推广.assert_awaited_once()
        模拟推广页.等待推广成功.assert_awaited_once()
        模拟推广页.返回商品列表页.assert_awaited_once()
        模拟推广页.截图.assert_awaited_once_with("推广成功")

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_商品行不存在时返回失败(self, 模拟回调, 模拟页面, 模拟推广页):
        from tasks.推广任务 import 推广任务

        模拟推广页.商品行是否存在 = AsyncMock(return_value=False)

        with patch("tasks.推广任务.上报", new_callable=AsyncMock), \
                patch("tasks.推广任务.推广页", return_value=模拟推广页):
            任务 = 推广任务()
            结果 = await 任务.执行(
                模拟页面,
                {"shop_id": "shop-1", "task_param": {"商品ID列表": ["123456789012"]}},
            )

        assert 结果 == "失败"
        模拟推广页.截图.assert_awaited_once_with("推广任务异常")

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_不关闭极速起量且无日限额时跳过对应步骤(self, 模拟回调, 模拟页面, 模拟推广页):
        from tasks.推广任务 import 推广任务

        with patch("tasks.推广任务.上报", new_callable=AsyncMock), \
                patch("tasks.推广任务.推广页", return_value=模拟推广页):
            任务 = 推广任务()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "商品ID": "123456789012",
                        "phase1_roi": 6.0,
                        "关闭极速起量": False,
                    },
                },
            )

        assert 结果 == "成功"
        模拟推广页.点击更多设置.assert_not_awaited()
        模拟推广页.点击预算日限额.assert_not_awaited()
        模拟推广页.点击极速起量高级版开关.assert_not_awaited()
        模拟推广页.确认关闭极速起量.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_合并参数映射_按商品读取投产比和日限额(self, 模拟回调, 模拟页面, 模拟推广页):
        from tasks.推广任务 import 推广任务

        with patch("tasks.推广任务.上报", new_callable=AsyncMock), \
                patch("tasks.推广任务.推广页", return_value=模拟推广页):
            任务 = 推广任务()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "商品ID列表": ["123456789012", "987654321098"],
                        "投产比": 5.0,
                        "日限额": 80,
                        "商品参数映射": {
                            "123456789012": {"投产比": 6.2, "日限额": 120},
                            "987654321098": {"投产比": 4.5},
                        },
                    },
                },
            )

        assert 结果 == "成功"
        assert 模拟推广页.输入日限额.await_args_list[0].args == (120.0,)
        assert 模拟推广页.输入日限额.await_args_list[1].args == (80.0,)
        assert 模拟推广页.输入投产比.await_args_list[0].args == (6.2,)
        assert 模拟推广页.输入投产比.await_args_list[1].args == (4.5,)

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_关闭全局起量确认失败时返回失败(self, 模拟回调, 模拟页面, 模拟推广页):
        from tasks.推广任务 import 推广任务

        模拟推广页.确认关闭全局起量 = AsyncMock(return_value=False)

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
        模拟推广页.截图.assert_awaited_once_with("推广任务异常")

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_close_fast_boost参数为false时会开启极速起量(self, 模拟回调, 模拟页面, 模拟推广页):
        from tasks.推广任务 import 推广任务

        模拟推广页.获取全局优先起量状态 = AsyncMock(return_value="false")
        模拟推广页.获取极速起量高级版状态 = AsyncMock(return_value="false")

        with patch("tasks.推广任务.上报", new_callable=AsyncMock), \
                patch("tasks.推广任务.推广页", return_value=模拟推广页):
            任务 = 推广任务()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "商品ID列表": ["123456789012"],
                        "close_fast_boost": False,
                    },
                },
            )

        assert 结果 == "成功"
        模拟推广页.点击全局优先起量开关.assert_not_awaited()
        模拟推广页.点击极速起量高级版开关.assert_awaited_once_with("123456789012")
        模拟推广页.确认关闭极速起量.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_关闭极速起量发生在填写投产比之前(self, 模拟回调, 模拟页面, 模拟推广页):
        from tasks.推广任务 import 推广任务

        调用顺序: list[str] = []

        async def 记录点击铅笔(_商品ID):
            调用顺序.append("铅笔")
            return True

        async def 记录点击开关(_商品ID):
            调用顺序.append("点击极速")
            return True

        async def 记录确认关闭(_商品ID):
            调用顺序.append("确认关闭极速")
            return True

        async def 记录输入投产比(_投产比):
            调用顺序.append("输入投产比")
            return True

        模拟推广页.点击修改投产铅笔按钮.side_effect = 记录点击铅笔
        模拟推广页.点击极速起量高级版开关.side_effect = 记录点击开关
        模拟推广页.确认关闭极速起量.side_effect = 记录确认关闭
        模拟推广页.输入投产比.side_effect = 记录输入投产比

        with patch("tasks.推广任务.上报", new_callable=AsyncMock), \
                patch("tasks.推广任务.推广页", return_value=模拟推广页):
            任务 = 推广任务()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "商品ID列表": ["123456789012"],
                        "关闭极速起量": True,
                    },
                },
            )

        assert 结果 == "成功"
        assert 调用顺序 == ["铅笔", "点击极速", "确认关闭极速", "输入投产比"]
