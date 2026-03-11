"""
任务服务健壮性测试
"""
import asyncio
from unittest.mock import AsyncMock, patch

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
