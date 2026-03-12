"""
发布相似商品任务单元测试
"""
import importlib
import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


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


class 测试_发布相似商品任务:
    """测试发布相似商品任务的关键分支。"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        return 页面

    @pytest.fixture
    def 模拟发布页面(self):
        页面 = MagicMock()
        页面.wait_for_load_state = AsyncMock()
        return 页面

    @pytest.fixture
    def 模拟商品列表页(self):
        商品列表对象 = MagicMock()
        商品列表对象.导航到商品列表 = AsyncMock()
        商品列表对象.输入商品ID = AsyncMock()
        商品列表对象.点击查询 = AsyncMock()
        商品列表对象.等待搜索结果 = AsyncMock()
        商品列表对象.点击发布相似 = AsyncMock()
        商品列表对象.确认发布相似弹窗 = AsyncMock()
        商品列表对象.切回前台 = AsyncMock()
        return 商品列表对象

    @pytest.fixture
    def 模拟发布页(self):
        发布页对象 = MagicMock()
        发布页对象.关闭所有弹窗 = AsyncMock()
        发布页对象.提取商品ID = AsyncMock(side_effect=["init-1001", "new-2002"])
        发布页对象.获取主图列表 = AsyncMock(return_value=[MagicMock() for _ in range(5)])
        发布页对象.拖拽主图 = AsyncMock()
        发布页对象.输入商品标题 = AsyncMock()
        发布页对象.获取商品标题 = AsyncMock(return_value="原标题")
        发布页对象.点击提交并上架 = AsyncMock()
        发布页对象.等待发布成功 = AsyncMock(return_value=True)
        发布页对象.截图当前状态 = AsyncMock(return_value="publish.png")
        发布页对象.关闭当前标签页 = AsyncMock()
        return 发布页对象

    def test_注册名为_发布相似商品(self):
        """任务应以发布相似商品名称注册。"""
        from tasks import 注册表 as 注册表模块
        import tasks.发布相似商品任务 as 发布相似商品任务模块

        原注册表 = deepcopy(注册表模块.任务注册表)

        try:
            注册表模块.清空任务注册表()
            发布相似商品任务模块 = importlib.reload(发布相似商品任务模块)
            发布相似商品任务 = 发布相似商品任务模块.发布相似商品任务
            assert 注册表模块.获取任务类("发布相似商品") is 发布相似商品任务
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_缺少_父商品ID_抛ValueError(self, 模拟回调, 模拟页面):
        """缺少父商品ID时应抛出 ValueError。"""
        from tasks.发布相似商品任务 import 发布相似商品任务

        任务 = 发布相似商品任务()

        with patch("tasks.发布相似商品任务.上报", new_callable=AsyncMock), \
                patch("tasks.发布相似商品任务.任务参数服务实例.更新执行结果", new_callable=AsyncMock):
            with pytest.raises(ValueError, match="父商品ID"):
                await 任务.执行(
                    模拟页面,
                    {"shop_id": "shop-1", "task_param": {}},
                )

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_正常流程_英文参数成功并写入中文结果(
        self,
        模拟回调,
        模拟页面,
        模拟发布页面,
        模拟商品列表页,
        模拟发布页,
    ):
        """正常流程应返回成功并写入中文结果结构。"""
        from tasks.发布相似商品任务 import 发布相似商品任务

        模拟页面.expect_popup.return_value = 模拟弹窗上下文(模拟发布页面)
        with patch("tasks.发布相似商品任务.上报", new_callable=AsyncMock), \
                patch("tasks.发布相似商品任务.商品列表页", return_value=模拟商品列表页), \
                patch("tasks.发布相似商品任务.发布商品页", return_value=模拟发布页), \
                patch("tasks.发布相似商品任务.random.randint", return_value=2), \
                patch("tasks.发布相似商品任务.任务参数服务实例.更新执行结果", new_callable=AsyncMock) as 模拟回填:
            任务 = 发布相似商品任务()
            任务._步骤间延迟 = AsyncMock()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "parent_product_id": "1001",
                        "new_title": "新的标题",
                        "task_param_id": 11,
                    },
                },
            )

        assert 结果 == "成功"
        assert 任务._执行结果 == {
            "新商品ID": "new-2002",
            "父商品ID": "1001",
            "标题": "新的标题",
        }
        任务._步骤间延迟.assert_awaited()
        assert 任务._步骤间延迟.await_count == 7
        模拟商品列表页.导航到商品列表.assert_awaited_once()
        模拟商品列表页.输入商品ID.assert_awaited_once_with("1001")
        模拟商品列表页.点击查询.assert_awaited_once()
        模拟商品列表页.等待搜索结果.assert_awaited_once()
        模拟商品列表页.点击发布相似.assert_awaited_once()
        模拟商品列表页.确认发布相似弹窗.assert_awaited_once()
        模拟商品列表页.切回前台.assert_awaited_once()
        模拟发布页.拖拽主图.assert_awaited_once_with(2, 0)
        模拟发布页.输入商品标题.assert_awaited_once_with("新的标题")
        模拟发布页.关闭当前标签页.assert_awaited_once()
        assert 模拟回填.await_count == 2
        assert 模拟回填.await_args_list[0].kwargs["结果"] == {"父商品ID": "1001"}
        assert 模拟回填.await_args_list[1].kwargs["结果"] == 任务._执行结果

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_中文参数键名_也能成功执行(
        self,
        模拟回调,
        模拟页面,
        模拟发布页面,
        模拟商品列表页,
        模拟发布页,
    ):
        """兼容直接传入中文键名的任务参数。"""
        from tasks.发布相似商品任务 import 发布相似商品任务

        模拟页面.expect_popup.return_value = 模拟弹窗上下文(模拟发布页面)
        with patch("tasks.发布相似商品任务.上报", new_callable=AsyncMock), \
                patch("tasks.发布相似商品任务.商品列表页", return_value=模拟商品列表页), \
                patch("tasks.发布相似商品任务.发布商品页", return_value=模拟发布页), \
                patch("tasks.发布相似商品任务.random.randint", return_value=2), \
                patch("tasks.发布相似商品任务.任务参数服务实例.更新执行结果", new_callable=AsyncMock):
            任务 = 发布相似商品任务()
            任务._步骤间延迟 = AsyncMock()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "父商品ID": "1002",
                        "新标题": "中文标题",
                    },
                },
            )

        assert 结果 == "成功"
        模拟商品列表页.输入商品ID.assert_awaited_once_with("1002")
        模拟发布页.输入商品标题.assert_awaited_once_with("中文标题")

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_new_title为空时不调用_修改标题_并回填原标题(
        self,
        模拟回调,
        模拟页面,
        模拟发布页面,
        模拟商品列表页,
        模拟发布页,
    ):
        """标题为空时应跳过修改标题，并读取当前页面标题。"""
        from tasks.发布相似商品任务 import 发布相似商品任务

        模拟页面.expect_popup.return_value = 模拟弹窗上下文(模拟发布页面)
        with patch("tasks.发布相似商品任务.上报", new_callable=AsyncMock), \
                patch("tasks.发布相似商品任务.商品列表页", return_value=模拟商品列表页), \
                patch("tasks.发布相似商品任务.发布商品页", return_value=模拟发布页), \
                patch("tasks.发布相似商品任务.random.randint", return_value=2), \
                patch("tasks.发布相似商品任务.任务参数服务实例.更新执行结果", new_callable=AsyncMock):
            任务 = 发布相似商品任务()
            任务._步骤间延迟 = AsyncMock()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "parent_product_id": "1001",
                        "new_title": "",
                    },
                },
            )

        assert 结果 == "成功"
        assert 任务._执行结果["标题"] == "原标题"
        assert 任务._步骤间延迟.await_count == 7
        模拟发布页.输入商品标题.assert_not_called()
        模拟发布页.获取商品标题.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_发布失败时回填failed和error(
        self,
        模拟回调,
        模拟页面,
        模拟发布页面,
        模拟商品列表页,
        模拟发布页,
    ):
        """发布失败时应回填 failed 和错误信息。"""
        from tasks.发布相似商品任务 import 发布相似商品任务

        模拟发布页.等待发布成功 = AsyncMock(return_value=False)

        模拟页面.expect_popup.return_value = 模拟弹窗上下文(模拟发布页面)
        with patch("tasks.发布相似商品任务.上报", new_callable=AsyncMock), \
                patch("tasks.发布相似商品任务.商品列表页", return_value=模拟商品列表页), \
                patch("tasks.发布相似商品任务.发布商品页", return_value=模拟发布页), \
                patch("tasks.发布相似商品任务.random.randint", return_value=2), \
                patch("tasks.发布相似商品任务.任务参数服务实例.更新执行结果", new_callable=AsyncMock) as 模拟回填:
            任务 = 发布相似商品任务()
            任务._步骤间延迟 = AsyncMock()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "parent_product_id": "1001",
                        "task_param_id": 11,
                    },
                },
            )

        assert 结果 == "失败"
        assert 任务._步骤间延迟.await_count == 7
        assert 模拟回填.await_count == 2
        assert 模拟回填.await_args_list[1].args[:2] == (11, "failed")
        assert 模拟回填.await_args_list[1].kwargs["错误信息"] == "发布失败"
        模拟商品列表页.切回前台.assert_awaited_once()
        模拟发布页.关闭当前标签页.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_只有一张主图时跳过拖拽(
        self,
        模拟回调,
        模拟页面,
        模拟发布页面,
        模拟商品列表页,
        模拟发布页,
    ):
        from tasks.发布相似商品任务 import 发布相似商品任务

        模拟发布页.获取主图列表 = AsyncMock(return_value=[MagicMock()])
        模拟页面.expect_popup.return_value = 模拟弹窗上下文(模拟发布页面)
        with patch("tasks.发布相似商品任务.上报", new_callable=AsyncMock) as 模拟上报, \
                patch("tasks.发布相似商品任务.商品列表页", return_value=模拟商品列表页), \
                patch("tasks.发布相似商品任务.发布商品页", return_value=模拟发布页), \
                patch("tasks.发布相似商品任务.任务参数服务实例.更新执行结果", new_callable=AsyncMock):
            任务 = 发布相似商品任务()
            任务._步骤间延迟 = AsyncMock()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-1",
                    "task_param": {
                        "parent_product_id": "1001",
                    },
                },
            )

        assert 结果 == "成功"
        模拟发布页.拖拽主图.assert_not_called()
        模拟上报.assert_any_await("只有1张主图，跳过拖拽", "shop-1")
