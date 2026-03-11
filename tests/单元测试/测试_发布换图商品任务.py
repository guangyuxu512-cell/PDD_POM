"""
发布换图商品任务单元测试
"""
import importlib
from copy import deepcopy
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class 测试_发布换图商品任务:
    """测试发布换图商品任务的关键分支。"""

    @pytest.fixture
    def 模拟页面(self):
        return MagicMock()

    @pytest.fixture
    def 模拟发布页面(self):
        return MagicMock()

    @pytest.fixture
    def 模拟商品列表页(self, 模拟发布页面):
        商品列表对象 = MagicMock()
        商品列表对象.导航 = AsyncMock()
        商品列表对象.搜索商品 = AsyncMock()
        商品列表对象.点击发布相似品 = AsyncMock(return_value=模拟发布页面)
        return 商品列表对象

    @pytest.fixture
    def 模拟发布页(self):
        发布页对象 = MagicMock()
        发布页对象.初始化页面 = AsyncMock()
        发布页对象.从URL提取新商品ID = MagicMock(return_value="init-3001")
        发布页对象.上传主图 = AsyncMock()
        发布页对象.随机调整主图到第一位 = AsyncMock(return_value="跳过")
        发布页对象.修改标题 = AsyncMock()
        发布页对象.点击提交并上架 = AsyncMock()
        发布页对象.检测滑块验证码 = AsyncMock(return_value=False)
        发布页对象.是否发布成功 = AsyncMock(return_value=True)
        发布页对象.从成功页提取商品ID = MagicMock(return_value="new-4002")
        发布页对象.截图当前状态 = AsyncMock(return_value="publish-change.png")
        发布页对象.关闭页面 = AsyncMock()
        return 发布页对象

    def test_注册名为_发布换图商品(self):
        """任务应以发布换图商品名称注册。"""
        from tasks import 注册表 as 注册表模块
        import tasks.发布换图商品任务 as 发布换图商品任务模块

        原注册表 = deepcopy(注册表模块.任务注册表)

        try:
            注册表模块.清空任务注册表()
            发布换图商品任务模块 = importlib.reload(发布换图商品任务模块)
            发布换图商品任务 = 发布换图商品任务模块.发布换图商品任务
            assert 注册表模块.获取任务类("发布换图商品") is 发布换图商品任务
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_image_path和new_title为空时跳过上传与改标题(
        self,
        模拟回调,
        模拟页面,
        模拟商品列表页,
        模拟发布页,
    ):
        """图片路径和标题为空时应跳过上传与修改标题。"""
        from tasks.发布换图商品任务 import 发布换图商品任务

        with patch("tasks.发布换图商品任务.上报", new_callable=AsyncMock), \
                patch("tasks.发布换图商品任务.商品列表页", return_value=模拟商品列表页), \
                patch("tasks.发布换图商品任务.发布商品页", return_value=模拟发布页), \
                patch("tasks.发布换图商品任务.任务参数服务实例.更新执行结果", new_callable=AsyncMock):
            任务 = 发布换图商品任务()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-2",
                    "task_param": {
                        "parent_product_id": "3001",
                        "image_path": "",
                        "new_title": "",
                    },
                },
            )

        assert 结果 == "成功"
        模拟发布页.上传主图.assert_not_called()
        模拟发布页.修改标题.assert_not_called()
        模拟发布页.随机调整主图到第一位.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_正常流程_返回成功(
        self,
        模拟回调,
        模拟页面,
        模拟商品列表页,
        模拟发布页,
    ):
        """正常换图流程应返回成功并保存执行结果。"""
        from tasks.发布换图商品任务 import 发布换图商品任务

        模拟发布页.随机调整主图到第一位.return_value = "第3张调到第1位（共5张）"

        with patch("tasks.发布换图商品任务.上报", new_callable=AsyncMock), \
                patch("tasks.发布换图商品任务.商品列表页", return_value=模拟商品列表页), \
                patch("tasks.发布换图商品任务.发布商品页", return_value=模拟发布页), \
                patch("tasks.发布换图商品任务.任务参数服务实例.更新执行结果", new_callable=AsyncMock) as 模拟回填:
            任务 = 发布换图商品任务()
            结果 = await 任务.执行(
                模拟页面,
                {
                    "shop_id": "shop-2",
                    "task_param": {
                        "parent_product_id": "3001",
                        "image_path": "E:/images/demo.png",
                        "new_title": "换图新标题",
                        "task_param_id": 22,
                    },
                },
            )

        assert 结果 == "成功"
        assert 任务._执行结果["new_product_id"] == "new-4002"
        assert 任务._执行结果["parent_product_id"] == "3001"
        模拟发布页.上传主图.assert_awaited_once_with("E:/images/demo.png")
        模拟发布页.修改标题.assert_awaited_once_with("换图新标题")
        模拟发布页.关闭页面.assert_awaited_once()
        assert 模拟回填.await_count == 2
