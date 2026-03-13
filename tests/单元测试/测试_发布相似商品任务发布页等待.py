"""
发布相似商品任务发布页等待测试
"""
import asyncio
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


class 测试_发布相似商品任务发布页等待:
    """验证发布页关键表单等待逻辑。"""

    @pytest.fixture
    def 模拟页面(self):
        return MagicMock()

    @pytest.fixture
    def 模拟发布页面(self):
        页面 = MagicMock()
        页面.wait_for_load_state = AsyncMock()
        页面.wait_for_selector = AsyncMock(return_value=None)
        return 页面

    @pytest.fixture
    def 模拟商品列表页(self):
        对象 = MagicMock()
        对象.导航到商品列表 = AsyncMock()
        对象.输入商品ID = AsyncMock()
        对象.点击查询 = AsyncMock()
        对象.等待搜索结果 = AsyncMock()
        对象.点击发布相似 = AsyncMock()
        对象.确认发布相似弹窗 = AsyncMock()
        对象.切回前台 = AsyncMock()
        return 对象

    @pytest.fixture
    def 模拟发布页(self):
        对象 = MagicMock()
        对象.关闭所有弹窗 = AsyncMock()
        对象.提取商品ID = AsyncMock(side_effect=["init-1001", "new-2002"])
        对象.获取主图列表 = AsyncMock(return_value=[MagicMock()])
        对象.拖拽主图 = AsyncMock()
        对象.输入商品标题 = AsyncMock()
        对象.获取商品标题 = AsyncMock(return_value="原标题")
        对象.点击提交并上架 = AsyncMock()
        对象.等待发布成功 = AsyncMock(return_value=True)
        对象.截图当前状态 = AsyncMock(return_value="publish.png")
        对象.关闭当前标签页 = AsyncMock()
        return 对象

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_发布页表单渲染_等待标题输入框出现(
        self,
        模拟回调,
        模拟页面,
        模拟发布页面,
        模拟商品列表页,
        模拟发布页,
    ):
        from tasks.发布相似商品任务 import 发布相似商品任务
        from selectors.发布商品页选择器 import 发布商品页选择器

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
                        "new_title": "新标题",
                    },
                },
            )

        assert 结果 == "成功"
        模拟上报.assert_any_await("等待发布页表单渲染", "shop-1")
        首个选择器 = 发布商品页选择器.商品标题输入框.所有选择器()[0]
        模拟发布页面.wait_for_selector.assert_awaited_with(首个选择器, state="visible", timeout=30000)
        模拟发布页.关闭所有弹窗.assert_not_called()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_发布页表单渲染超时_上报后继续执行(
        self,
        模拟回调,
        模拟页面,
        模拟发布页面,
        模拟商品列表页,
        模拟发布页,
    ):
        from tasks.发布相似商品任务 import 发布相似商品任务

        模拟发布页面.wait_for_selector = AsyncMock(side_effect=Exception("timeout"))
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
        模拟上报.assert_any_await("发布页表单渲染超时，继续尝试", "shop-1")
        模拟发布页.关闭所有弹窗.assert_not_called()
