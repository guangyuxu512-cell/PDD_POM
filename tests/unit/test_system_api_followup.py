"""
系统测试接口补丁测试
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.api.system_api import 测试验证码服务, 测试飞书Webhook, _生成飞书签名
from backend.config import 配置实例
from backend.models.data_structure import 验证码测试请求, 飞书Webhook测试请求


def 构造异步客户端上下文(响应):
    客户端 = AsyncMock()
    客户端.post = AsyncMock(return_value=响应)
    上下文 = AsyncMock()
    上下文.__aenter__.return_value = 客户端
    上下文.__aexit__.return_value = False
    return 客户端, 上下文


def 构造响应(数据: dict):
    响应 = MagicMock()
    响应.raise_for_status.return_value = None
    响应.json.return_value = 数据
    return 响应


class 测试_系统测试接口补丁:
    @pytest.mark.asyncio
    async def test_测试验证码服务_成功时返回余额(self):
        响应 = 构造响应({"errorId": 0, "balance": 12.34})
        客户端, 上下文 = 构造异步客户端上下文(响应)

        with patch("backend.api.system_api.httpx.AsyncClient", return_value=上下文):
            返回结果 = await 测试验证码服务(
                验证码测试请求.model_validate({"provider": "yescaptcha", "api_key": "key-1"})
            )

        assert 返回结果.code == 0
        assert 返回结果.msg == "验证码服务连接成功"
        assert 返回结果.data == {"balance": 12.34}
        客户端.post.assert_awaited_once_with(
            "https://api.yescaptcha.com/getBalance",
            json={"clientKey": "key-1"},
        )

    @pytest.mark.asyncio
    async def test_测试验证码服务_失败时回退系统配置(self):
        响应 = 构造响应({"errorId": 1, "errorDescription": "invalid key"})
        客户端, 上下文 = 构造异步客户端上下文(响应)

        with patch("backend.api.system_api.httpx.AsyncClient", return_value=上下文), \
                patch.object(配置实例, "CAPTCHA_PROVIDER", "yescaptcha"), \
                patch.object(配置实例, "CAPTCHA_API_KEY", "fallback-key"):
            返回结果 = await 测试验证码服务(None)

        assert 返回结果.code == 1
        assert 返回结果.msg == "验证码测试失败: invalid key"
        客户端.post.assert_awaited_once_with(
            "https://api.yescaptcha.com/getBalance",
            json={"clientKey": "fallback-key"},
        )

    @pytest.mark.asyncio
    async def test_测试飞书Webhook_成功时带签名发送(self):
        响应 = 构造响应({"code": 0})
        客户端, 上下文 = 构造异步客户端上下文(响应)

        with patch("backend.api.system_api.httpx.AsyncClient", return_value=上下文), \
                patch("backend.api.system_api.time.time", return_value=1000):
            返回结果 = await 测试飞书Webhook(
                飞书Webhook测试请求.model_validate(
                    {"webhook_url": "https://open.feishu.cn/hook/test", "secret": "sign-secret"}
                )
            )

        assert 返回结果.code == 0
        assert 返回结果.msg == "飞书 Webhook 测试成功"
        客户端.post.assert_awaited_once_with(
            "https://open.feishu.cn/hook/test",
            json={
                "msg_type": "text",
                "content": {"text": "RPA 系统连接测试，Webhook 配置正常。"},
                "timestamp": "1000",
                "sign": _生成飞书签名("1000", "sign-secret"),
            },
        )

    @pytest.mark.asyncio
    async def test_测试飞书Webhook_失败时回退系统配置(self):
        响应 = 构造响应({"code": 999, "msg": "invalid webhook"})
        客户端, 上下文 = 构造异步客户端上下文(响应)

        with patch("backend.api.system_api.httpx.AsyncClient", return_value=上下文), \
                patch.object(配置实例, "FEISHU_WEBHOOK_URL", "https://open.feishu.cn/hook/fallback"), \
                patch.object(配置实例, "FEISHU_SECRET", None):
            返回结果 = await 测试飞书Webhook(None)

        assert 返回结果.code == 1
        assert 返回结果.msg == "飞书 Webhook 测试失败: invalid webhook"
        客户端.post.assert_awaited_once_with(
            "https://open.feishu.cn/hook/fallback",
            json={
                "msg_type": "text",
                "content": {"text": "RPA 系统连接测试，Webhook 配置正常。"},
            },
        )
