"""
任务回调模块测试
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import browser.任务回调 as 任务回调模块


class 测试_任务回调:
    """验证 Worker 到 Agent 的任务回调协议。"""

    @pytest.mark.asyncio
    async def test__回调_携带_X_RPA_KEY_并校验业务响应(self):
        """任务回调应携带 X-RPA-KEY，并校验统一业务响应。"""
        模拟响应 = MagicMock()
        模拟响应.json.return_value = {"code": 0, "msg": "ok", "data": {"ok": True}}

        class 假客户端:
            def __init__(self):
                self.post = AsyncMock(return_value=模拟响应)

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        客户端实例 = 假客户端()
        原回调地址 = 任务回调模块.回调地址
        任务回调模块.回调地址 = "http://agent-host:8001/api/task-callback"

        try:
            with patch.object(任务回调模块.配置实例, "X_RPA_KEY", "test-rpa-key"), \
                    patch("browser.任务回调.httpx.AsyncClient", return_value=客户端实例):
                await 任务回调模块._回调({"task": "登录", "status": "running"})
        finally:
            任务回调模块.回调地址 = 原回调地址

        客户端实例.post.assert_awaited_once_with(
            "http://agent-host:8001/api/task-callback",
            json={"task": "登录", "status": "running"},
            headers={"X-RPA-KEY": "test-rpa-key"},
        )
        模拟响应.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test__回调_业务失败时静默忽略(self):
        """Agent 返回业务失败时不应向外抛异常。"""
        模拟响应 = MagicMock()
        模拟响应.json.return_value = {"code": 1, "msg": "denied"}

        class 假客户端:
            def __init__(self):
                self.post = AsyncMock(return_value=模拟响应)

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        原回调地址 = 任务回调模块.回调地址
        任务回调模块.回调地址 = "http://agent-host:8001/api/task-callback"

        try:
            with patch.object(任务回调模块.配置实例, "X_RPA_KEY", "test-rpa-key"), \
                    patch("browser.任务回调.httpx.AsyncClient", return_value=假客户端()):
                await 任务回调模块._回调({"task": "登录", "status": "failed"})
        finally:
            任务回调模块.回调地址 = 原回调地址
