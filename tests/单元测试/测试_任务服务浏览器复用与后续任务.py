"""
任务服务浏览器复用与后续任务测试
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.任务服务 import 任务服务实例


class 假页面:
    """用于页面刷新测试的轻量页面替身。"""

    def __init__(self, 已关闭: bool):
        self._已关闭 = 已关闭

    def is_closed(self) -> bool:
        return self._已关闭

    def __repr__(self) -> str:
        return f"<假页面 已关闭={self._已关闭}>"


class 假管理器:
    """用于统一执行任务测试的假浏览器管理器。"""

    def __init__(self, 页面, 浏览器上下文):
        self.实例集 = {
            "shop-1": {
                "浏览器": 浏览器上下文,
                "页面": 页面,
                "page": 页面,
            }
        }

    def 获取页面(self, 店铺ID: str):
        return self.实例集[店铺ID]["页面"]


class 测试_任务服务浏览器复用与后续任务:
    """验证统一执行任务的页面刷新与后续任务触发。"""

    @pytest.mark.asyncio
    async def test_统一执行任务_主页面已关闭时自动创建新页面(self):
        旧页面 = 假页面(True)
        新页面 = 假页面(False)
        浏览器上下文 = MagicMock()
        浏览器上下文.pages = []
        浏览器上下文.new_page = AsyncMock(return_value=新页面)
        管理器 = 假管理器(旧页面, 浏览器上下文)

        with patch(
            "backend.services.任务服务.任务服务实例.更新任务状态",
            new=AsyncMock(),
        ), patch(
            "backend.services.浏览器服务.确保已初始化",
            new=AsyncMock(),
        ), patch(
            "backend.services.浏览器服务.获取当前管理器实例",
            return_value=管理器,
        ), patch(
            "backend.services.店铺服务.店铺服务实例.根据ID获取完整信息",
            new=AsyncMock(return_value={
                "id": "shop-1",
                "name": "测试店铺",
                "username": "demo",
                "password": "pwd",
            }),
        ), patch(
            "backend.services.任务服务.任务服务实例.执行任务",
            new=AsyncMock(return_value={"result": "成功"}),
        ) as 模拟执行任务:
            结果 = await 任务服务实例.统一执行任务(
                task_id="task-1",
                shop_id="shop-1",
                task_name="发布相似商品",
                来源="test",
            )

        assert 结果["status"] == "completed"
        浏览器上下文.new_page.assert_awaited_once()
        assert 管理器.实例集["shop-1"]["页面"] is 新页面
        assert 管理器.实例集["shop-1"]["page"] is 新页面
        assert 模拟执行任务.await_args.kwargs["页面"] is 新页面

    @pytest.mark.asyncio
    async def test_执行任务_发布相似商品成功后创建下一步任务(self):
        假任务实例 = SimpleNamespace(
            _执行结果={"新商品ID": "new-1001", "标题": "测试标题"},
            执行=AsyncMock(return_value="成功"),
        )

        源记录 = {
            "id": 41,
            "shop_id": "shop-1",
            "batch_id": "batch-1",
            "params": {"parent_product_id": "9001", "discount": 6},
        }
        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[
                源记录
            ]),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.创建后续任务",
            new=AsyncMock(return_value={"id": 99}),
        ) as 模拟创建后续任务, patch(
            "tasks.任务注册表.获取任务",
            return_value=假任务实例,
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="shop-1",
                task_name="发布相似商品",
                页面=object(),
                店铺配置={"shop_id": "shop-1", "username": "demo", "password": "pwd"},
            )

        assert 结果["result"] == "成功"
        模拟创建后续任务.assert_awaited_once()
        assert 模拟创建后续任务.await_args.kwargs["源记录"] == 源记录
        assert 模拟创建后续任务.await_args.kwargs["执行结果"] == {"新商品ID": "new-1001", "标题": "测试标题"}
        assert 模拟创建后续任务.await_args.kwargs["下一步任务名"] == "限时限量"

    @pytest.mark.asyncio
    async def test_执行任务_失败时不触发批次后续任务(self):
        假任务实例 = SimpleNamespace(
            _执行结果={"parent_product_id": "9001"},
            执行=AsyncMock(return_value="失败"),
        )

        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[
                {
                    "id": 42,
                    "batch_id": "batch-1",
                    "params": {"parent_product_id": "9001", "discount": 6},
                }
            ]),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.创建后续任务",
            new=AsyncMock(return_value={"id": 99}),
        ) as 模拟创建后续任务, patch(
            "tasks.任务注册表.获取任务",
            return_value=假任务实例,
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="shop-1",
                task_name="发布相似商品",
                页面=object(),
                店铺配置={"shop_id": "shop-1", "username": "demo", "password": "pwd"},
            )

        assert 结果["result"] == "失败"
        模拟创建后续任务.assert_not_awaited()
