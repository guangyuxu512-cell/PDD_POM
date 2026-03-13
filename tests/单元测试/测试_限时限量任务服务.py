"""
限时限量任务执行入口测试
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.任务服务 import 任务服务实例


class 测试_限时限量任务服务:
    """测试任务服务对限时限量任务的注入逻辑。"""

    @pytest.mark.asyncio
    async def test_执行任务_限时限量自动注入待执行参数(self):
        假任务实例 = SimpleNamespace(
            _执行结果={"batch_id": "batch-1", "商品数量": 2},
            执行=AsyncMock(return_value="成功"),
        )
        店铺配置 = {"shop_id": "shop-1", "username": "demo", "password": "pwd"}

        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[
                {"id": 31, "params": {"batch_id": "batch-1", "折扣": 6}},
            ]),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ) as 模拟回填, patch(
            "tasks.任务注册表.获取任务",
            return_value=假任务实例,
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="shop-1",
                task_name="限时限量",
                页面=object(),
                店铺配置=店铺配置,
            )

        assert 结果["result"] == "成功"
        假任务实例.执行.assert_awaited_once()
        assert 店铺配置["task_param"] == {
            "batch_id": "batch-1",
            "折扣": 6,
            "task_param_id": 31,
        }
        assert 模拟回填.await_count == 2
        assert 模拟回填.await_args_list[0].args[:2] == (31, "running")
        assert 模拟回填.await_args_list[1].args[:2] == (31, "success")

    @pytest.mark.asyncio
    async def test_执行任务_限时限量无待执行参数时跳过(self):
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
                shop_id="shop-1",
                task_name="限时限量",
                页面=object(),
                店铺配置={"shop_id": "shop-1"},
            )

        assert 结果["result"] == "跳过"
        模拟上报.assert_awaited_once_with("没有待执行的任务参数", "shop-1")
        模拟获取任务.assert_not_called()
        模拟回填.assert_not_awaited()
