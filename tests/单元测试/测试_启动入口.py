"""
启动入口相关回归测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class 测试_启动入口:
    """测试 FastAPI lifespan 资源管理"""

    @pytest.mark.asyncio
    async def test_生命周期_启动并关闭心跳服务(self):
        """lifespan 启动时拉起心跳，关闭时正确清理资源"""
        from backend import 启动入口 as 启动入口模块

        with patch("tasks.任务注册表.初始化任务注册表") as 模拟初始化任务注册表, \
                patch("browser.任务回调.设置回调地址") as 模拟设置回调地址, \
                patch("backend.启动入口.初始化数据库", new=AsyncMock()) as 模拟初始化数据库, \
                patch("backend.启动入口.关闭数据库", new=AsyncMock()) as 模拟关闭数据库, \
                patch("backend.services.心跳服务.心跳服务实例.启动", new=AsyncMock()) as 模拟启动心跳, \
                patch("backend.services.心跳服务.心跳服务实例.停止", new=AsyncMock()) as 模拟停止心跳, \
                patch.object(启动入口模块.配置实例, "AGENT_CALLBACK_URL", "http://agent/callback"):
            async with 启动入口模块.生命周期(MagicMock()):
                pass

        模拟初始化数据库.assert_awaited_once()
        模拟关闭数据库.assert_awaited_once()
        模拟初始化任务注册表.assert_called_once()
        模拟设置回调地址.assert_called_once_with("http://agent/callback")
        模拟启动心跳.assert_awaited_once()
        模拟停止心跳.assert_awaited_once()
