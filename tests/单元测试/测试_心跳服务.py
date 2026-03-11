"""
心跳服务健壮性测试
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.心跳服务 import 心跳服务


class 测试_心跳服务:
    """测试心跳服务异常不会影响主流程"""

    @pytest.mark.asyncio
    async def test_发送心跳_按Agent约定发送请求头和shadowbot_running(self):
        """心跳请求应携带 X-RPA-KEY，并使用 shadowbot_running 字段。"""
        服务 = 心跳服务()
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

        with patch("backend.services.心跳服务.配置实例.AGENT_MACHINE_ID", "machine-a"), \
                patch("backend.services.心跳服务.配置实例.AGENT_HEARTBEAT_URL", "http://agent/heartbeat"), \
                patch("backend.services.心跳服务.配置实例.X_RPA_KEY", "test-rpa-key"), \
                patch("backend.services.心跳服务.httpx.AsyncClient", return_value=客户端实例):
            await 服务._发送心跳()

        客户端实例.post.assert_awaited_once_with(
            "http://agent/heartbeat",
            json={"machine_id": "machine-a", "shadowbot_running": False},
            headers={"X-RPA-KEY": "test-rpa-key"},
        )
        模拟响应.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_发送心跳_HTTP异常时静默忽略(self):
        """发送心跳失败时不向外抛异常"""
        服务 = 心跳服务()

        class 假客户端:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, *args, **kwargs):
                raise RuntimeError("network failed")

        with patch("backend.services.心跳服务.配置实例.AGENT_MACHINE_ID", "machine-a"), \
                patch("backend.services.心跳服务.配置实例.AGENT_HEARTBEAT_URL", "http://agent/heartbeat"), \
                patch("backend.services.心跳服务.配置实例.X_RPA_KEY", "test-rpa-key"), \
                patch("backend.services.心跳服务.httpx.AsyncClient", return_value=假客户端()):
            await 服务._发送心跳()

    @pytest.mark.asyncio
    async def test_循环发送心跳_单次失败不终止循环(self):
        """循环中的单次异常只记录，不让后台任务退出"""
        服务 = 心跳服务()

        class 假停止事件:
            def __init__(self):
                self._次数 = 0

            def is_set(self):
                self._次数 += 1
                return self._次数 > 1

            async def wait(self):
                return None

        服务._停止事件 = 假停止事件()

        async def 假发送():
            raise RuntimeError("heartbeat failed")

        with patch.object(服务, "_发送心跳", new=AsyncMock(side_effect=假发送)):
            await 服务._循环发送心跳()
