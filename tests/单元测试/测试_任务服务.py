"""
任务服务健壮性测试
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.任务服务 import 任务服务实例


class 假管理器:
    """用于任务服务测试的假浏览器管理器"""

    def __init__(self):
        self.实例集 = {"shop-1": {"page": object()}}

    def 获取页面(self, 店铺ID: str):
        return object()


class 测试_任务服务:
    """测试统一执行任务的超时兜底"""

    @pytest.mark.asyncio
    async def test_执行任务_发布相似商品自动注入首条待执行参数并回填成功(self):
        """发布相似商品任务应读取首条 pending 参数，并在成功后回填 success。"""
        假任务实例 = SimpleNamespace(
            _执行结果={"new_product_id": "new-1001", "parent_product_id": "916453776556"},
            执行=AsyncMock(return_value="成功"),
        )
        店铺配置 = {"shop_id": "8eec98e4-89b9-49d5-ab1f-c72be3c405f6", "username": "demo", "password": "pwd"}

        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[
                {"id": 11, "params": {"parent_product_id": "916453776556", "new_title": "测试标题"}},
                {"id": 12, "params": {"parent_product_id": "916453776557"}},
            ]),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ) as 模拟回填, patch(
            "tasks.任务注册表.获取任务",
            return_value=假任务实例,
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="8eec98e4-89b9-49d5-ab1f-c72be3c405f6",
                task_name="发布相似商品",
                页面=object(),
                店铺配置=店铺配置,
            )

        assert 结果["result"] == "成功"
        假任务实例.执行.assert_awaited_once()
        assert 店铺配置["task_param"] == {
            "parent_product_id": "916453776556",
            "new_title": "测试标题",
            "task_param_id": 11,
        }
        assert 模拟回填.await_count == 2
        assert 模拟回填.await_args_list[0].args[:2] == (11, "running")
        assert 模拟回填.await_args_list[1].args[:2] == (11, "success")
        assert 模拟回填.await_args_list[1].kwargs["结果"]["new_product_id"] == "new-1001"

    @pytest.mark.asyncio
    async def test_执行任务_发布换图商品无待执行参数时跳过(self):
        """没有 pending 任务参数时，应上报并跳过，不实例化任务。"""
        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[]),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ) as 模拟回填, patch(
            "browser.任务回调.上报",
            new=AsyncMock(),
        ) as 模拟上报, patch(
            "tasks.任务注册表.获取任务",
            new=MagicMock(),
        ) as 模拟获取任务:
            结果 = await 任务服务实例.执行任务(
                shop_id="8eec98e4-89b9-49d5-ab1f-c72be3c405f6",
                task_name="发布换图商品",
                页面=object(),
                店铺配置={"shop_id": "8eec98e4-89b9-49d5-ab1f-c72be3c405f6"},
            )

        assert 结果["result"] == "跳过"
        模拟上报.assert_awaited_once_with("没有待执行的任务参数", "8eec98e4-89b9-49d5-ab1f-c72be3c405f6")
        模拟获取任务.assert_not_called()
        模拟回填.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_执行任务_发布相似商品失败时回填失败信息(self):
        """发布任务返回失败时，应将 task_params 回填为 failed。"""
        假任务实例 = SimpleNamespace(
            _执行结果={"parent_product_id": "916453776556"},
            执行=AsyncMock(return_value="失败"),
        )

        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[
                {"id": 21, "params": {"parent_product_id": "916453776556"}},
            ]),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ) as 模拟回填, patch(
            "tasks.任务注册表.获取任务",
            return_value=假任务实例,
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="8eec98e4-89b9-49d5-ab1f-c72be3c405f6",
                task_name="发布相似商品",
                页面=object(),
                店铺配置={"shop_id": "8eec98e4-89b9-49d5-ab1f-c72be3c405f6"},
            )

        assert 结果["result"] == "失败"
        assert 模拟回填.await_count == 2
        assert 模拟回填.await_args_list[1].args[:2] == (21, "failed")
        assert 模拟回填.await_args_list[1].kwargs["错误信息"] == "失败"

    @pytest.mark.asyncio
    async def test_执行任务_flow_context存在时直接透传不读取task_params(self):
        """flow_context 已注入时，应直接作为 task_param 使用而不再查询 task_params。"""
        假任务实例 = SimpleNamespace(
            _执行结果={"new_product_id": "new-2001"},
            执行=AsyncMock(return_value="成功"),
        )
        店铺配置 = {
            "shop_id": "shop-1",
            "username": "demo",
            "password": "pwd",
            "flow_context": {"parent_product_id": "9001", "discount": 6},
        }

        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[]),
        ) as 模拟获取待执行, patch(
            "tasks.任务注册表.获取任务",
            return_value=假任务实例,
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ) as 模拟回填:
            结果 = await 任务服务实例.执行任务(
                shop_id="shop-1",
                task_name="发布相似商品",
                页面=object(),
                店铺配置=店铺配置,
            )

        assert 结果["result"] == "成功"
        assert 店铺配置["task_param"] == {"parent_product_id": "9001", "discount": 6}
        模拟获取待执行.assert_not_awaited()
        模拟回填.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_统一执行任务_浏览器初始化超时返回失败(self):
        """浏览器初始化超时时，应返回 failed 而不是抛出异常给上层"""
        with patch("backend.services.任务服务.任务服务实例.更新任务状态", new=AsyncMock()) as 模拟更新任务状态, \
                patch("backend.services.店铺服务.店铺服务实例.更新", new=AsyncMock()) as 模拟更新店铺状态, \
                patch("backend.services.浏览器服务.确保已初始化", new=AsyncMock(side_effect=asyncio.TimeoutError())), \
                patch("backend.services.浏览器服务.管理器实例", None):
            结果 = await 任务服务实例.统一执行任务(
                task_id="task-1",
                shop_id="shop-1",
                task_name="登录",
                params=None,
                来源="test"
            )

        assert 结果["status"] == "failed"
        assert "浏览器初始化超时" in 结果["error"]
        assert 模拟更新任务状态.await_count >= 2
        模拟更新店铺状态.assert_awaited()
