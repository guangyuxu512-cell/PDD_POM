"""
系统接口单元测试
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.api.system_api import 测试Redis连接, 健康检查, 获取运行指标
from backend.config import 配置实例
from backend.models.data_structure import Redis连接测试请求


class 测试_系统接口:
    """测试系统接口新增能力"""

    @pytest.mark.asyncio
    async def test_Redis连接测试_成功(self):
        """显式传入 Redis 地址时返回延迟并关闭连接"""
        模拟客户端 = AsyncMock()
        模拟客户端.ping = AsyncMock(return_value=True)
        模拟客户端.aclose = AsyncMock()

        with patch("backend.api.system_api.aioredis.from_url", return_value=模拟客户端) as 模拟创建客户端:
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

        with patch("backend.api.system_api.aioredis.from_url", return_value=模拟客户端) as 模拟创建客户端, \
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

        with patch("backend.api.system_api.aioredis.from_url", return_value=模拟客户端):
            响应 = await 测试Redis连接(Redis连接测试请求(redis_url="redis://127.0.0.1:6379/0"))

        assert 响应.code == 0
        assert 响应.msg == "Redis 连接成功"
        模拟客户端.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_健康检查_返回结构化信息(self):
        with patch(
            "backend.api.system_api.系统服务实例.健康检查",
            new=AsyncMock(
                return_value={
                    "status": "healthy",
                    "version": "0.1.0",
                    "uptime_seconds": 12,
                    "checks": {"redis": {"status": "ok"}},
                    "timestamp": "2026-03-31T10:00:00+08:00",
                }
            ),
        ):
            响应 = await 健康检查()

        assert 响应.code == 0
        assert 响应.data["status"] == "healthy"
        assert "checks" in 响应.data

    @pytest.mark.asyncio
    async def test_获取运行指标_返回统一响应(self):
        with patch(
            "backend.api.system_api.系统服务实例.获取指标",
            new=AsyncMock(
                return_value={
                    "tasks_total": 10,
                    "tasks_success": 8,
                    "tasks_failed": 2,
                    "tasks_running": 1,
                    "avg_task_duration_ms": 500.0,
                    "browser_instances_active": 1,
                    "browser_instances_max": 5,
                    "redis_memory_used_mb": 12.3,
                    "uptime_seconds": 30,
                }
            ),
        ):
            响应 = await 获取运行指标()

        assert 响应.code == 0
        assert 响应.data["tasks_total"] == 10
        assert 响应.data["browser_instances_max"] == 5
