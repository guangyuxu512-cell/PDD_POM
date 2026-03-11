"""
系统接口单元测试
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.api.系统接口 import 测试Redis连接
from backend.配置 import 配置实例
from backend.models.数据结构 import Redis连接测试请求


class 测试_系统接口:
    """测试系统接口新增能力"""

    @pytest.mark.asyncio
    async def test_Redis连接测试_成功(self):
        """显式传入 Redis 地址时返回延迟并关闭连接"""
        模拟客户端 = AsyncMock()
        模拟客户端.ping = AsyncMock(return_value=True)
        模拟客户端.aclose = AsyncMock()

        with patch("backend.api.系统接口.aioredis.from_url", return_value=模拟客户端) as 模拟创建客户端:
            响应 = await 测试Redis连接(Redis连接测试请求(redis_url="redis://127.0.0.1:6379/0"))

        assert 响应.code == 0
        assert 响应.msg == "Redis 连接成功"
        assert 响应.data["latency_ms"] >= 0
        模拟创建客户端.assert_called_once_with("redis://127.0.0.1:6379/0")
        模拟客户端.ping.assert_awaited_once()
        模拟客户端.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_Redis连接测试_失败时回退配置并返回错误(self):
        """请求体为空时回退配置，并在失败时返回统一错误响应"""
        模拟客户端 = AsyncMock()
        模拟客户端.ping = AsyncMock(side_effect=asyncio.TimeoutError())
        模拟客户端.aclose = AsyncMock()

        with patch("backend.api.系统接口.aioredis.from_url", return_value=模拟客户端) as 模拟创建客户端, \
                patch.object(配置实例, "REDIS_URL", "redis://config-host:6379/0"):
            响应 = await 测试Redis连接(None)

        assert 响应.code == 1
        assert 响应.data is None
        assert 响应.msg == "Redis 连接失败: 连接超时（5秒）"
        模拟创建客户端.assert_called_once_with("redis://config-host:6379/0")
        模拟客户端.ping.assert_awaited_once()
        模拟客户端.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_Redis连接测试_关闭连接失败不覆盖主响应(self):
        """关闭 Redis 连接失败时，仍然返回原本的业务响应"""
        模拟客户端 = AsyncMock()
        模拟客户端.ping = AsyncMock(return_value=True)
        模拟客户端.aclose = AsyncMock(side_effect=RuntimeError("close failed"))

        with patch("backend.api.系统接口.aioredis.from_url", return_value=模拟客户端):
            响应 = await 测试Redis连接(Redis连接测试请求(redis_url="redis://127.0.0.1:6379/0"))

        assert 响应.code == 0
        assert 响应.msg == "Redis 连接成功"
        模拟客户端.aclose.assert_awaited_once()
