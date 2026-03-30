"""
登录态监控回归测试
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import backend.config as 配置模块
from backend.models import database as 数据库模块
from browser.session_monitor import 登录态监控实例


@pytest.fixture
def 临时日志环境(tmp_path):
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), patch.object(
        配置模块.配置实例,
        "DATA_DIR",
        str(数据目录),
    ):
        asyncio.run(数据库模块.初始化数据库())
        yield 数据库文件


class 测试_登录态监控:
    @pytest.mark.asyncio
    async def test_检查登录态_登录页URL返回False(self):
        页面 = MagicMock()
        页面.url = "https://mms.pinduoduo.com/login?redirect=home"

        assert await 登录态监控实例.检查登录态(页面, "shop-1") is False

    @pytest.mark.asyncio
    async def test_触发失效告警_写入操作日志(self, 临时日志环境):
        模拟Redis客户端 = AsyncMock()
        模拟Redis客户端.publish = AsyncMock()
        模拟Redis客户端.aclose = AsyncMock()

        with patch(
            "browser.session_monitor.aioredis.from_url",
            return_value=模拟Redis客户端,
        ), patch.object(配置模块.配置实例, "FEISHU_WEBHOOK_URL", ""):
            await 登录态监控实例.触发失效告警("shop-1", "店铺A", "Cookie 已过期")

        async with 数据库模块.获取连接() as db:
            async with db.execute(
                """
                SELECT shop_id, shop_name, level, source, message, detail
                FROM operation_logs
                ORDER BY id DESC
                LIMIT 1
                """
            ) as cursor:
                记录 = await cursor.fetchone()

        assert 记录["shop_id"] == "shop-1"
        assert 记录["shop_name"] == "店铺A"
        assert 记录["level"] == "ERROR"
        assert 记录["source"] == "session_monitor"
        assert "登录态已失效" in 记录["message"]
        assert 记录["detail"] == "Cookie 已过期"
        模拟Redis客户端.publish.assert_awaited_once()

