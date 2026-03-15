"""
飞书服务测试
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.飞书接口 import 路由 as 飞书路由
from backend.services import 系统服务 as 系统服务模块
from backend.services.飞书服务 import 飞书服务


def 构造异步客户端上下文(响应列表: list[MagicMock]):
    客户端 = AsyncMock()
    客户端.post = AsyncMock(side_effect=响应列表)
    上下文 = AsyncMock()
    上下文.__aenter__.return_value = 客户端
    上下文.__aexit__.return_value = False
    return 客户端, 上下文


def 构造响应(数据: dict):
    响应 = MagicMock()
    响应.json.return_value = 数据
    响应.raise_for_status.return_value = None
    return 响应


class 测试_飞书服务:
    @pytest.mark.asyncio
    async def test_发送文本通知_正确组装_body(self):
        响应 = 构造响应({"StatusCode": 0})
        客户端, 上下文 = 构造异步客户端上下文([响应])

        with patch("backend.services.飞书服务.httpx.AsyncClient", return_value=上下文):
            服务 = 飞书服务(webhook_url="https://open.feishu.cn/hook/test")
            结果 = await 服务.发送文本通知("测试通知")

        assert 结果["success"] is True
        客户端.post.assert_awaited_once_with(
            "https://open.feishu.cn/hook/test",
            json={
                "msg_type": "text",
                "content": {"text": "测试通知"},
            },
        )

    @pytest.mark.asyncio
    async def test_发送卡片通知_正确组装交互卡片(self):
        响应 = 构造响应({"StatusCode": 0})
        客户端, 上下文 = 构造异步客户端上下文([响应])

        with patch("backend.services.飞书服务.httpx.AsyncClient", return_value=上下文):
            服务 = 飞书服务(webhook_url="https://open.feishu.cn/hook/test")
            结果 = await 服务.发送卡片通知(
                "售后通知",
                [{"订单号": "A001", "金额": "99.00", "处理方式": "自动同意"}],
            )

        assert 结果["success"] is True
        请求体 = 客户端.post.await_args.kwargs["json"]
        assert 请求体["msg_type"] == "interactive"
        assert 请求体["card"]["header"]["title"]["content"] == "售后通知"
        assert "订单号" in 请求体["card"]["elements"][0]["text"]["content"]

    @pytest.mark.asyncio
    async def test_发送售后通知_从订单数据生成卡片(self):
        响应 = 构造响应({"StatusCode": 0})
        客户端, 上下文 = 构造异步客户端上下文([响应])

        with patch("backend.services.飞书服务.httpx.AsyncClient", return_value=上下文):
            服务 = 飞书服务(webhook_url="https://open.feishu.cn/hook/test")
            结果 = await 服务.发送售后通知(
                {"order_no": "SO-1", "amount": "58.8", "type": "退款", "shop_name": "测试店铺"},
                "人工审核",
            )

        assert 结果["success"] is True
        内容 = 客户端.post.await_args.kwargs["json"]["card"]["elements"][0]["text"]["content"]
        assert "SO-1" in 内容
        assert "人工审核" in 内容

    @pytest.mark.asyncio
    async def test_获取tenant_access_token_解析并缓存(self):
        token响应 = 构造响应({"tenant_access_token": "token-1", "expire": 7200})
        客户端, 上下文 = 构造异步客户端上下文([token响应])

        with patch("backend.services.飞书服务.httpx.AsyncClient", return_value=上下文), \
                patch("backend.services.飞书服务.time.time", side_effect=[1000.0, 1001.0]):
            服务 = 飞书服务(app_id="app-id", app_secret="app-secret")
            token1 = await 服务._获取tenant_access_token()
            token2 = await 服务._获取tenant_access_token()

        assert token1 == "token-1"
        assert token2 == "token-1"
        客户端.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_写入多维表格_正确调用路径和_headers(self):
        token响应 = 构造响应({"tenant_access_token": "token-2", "expire": 7200})
        写入响应 = 构造响应({"code": 0, "data": {"record_id": "rec-1"}})
        客户端, 上下文 = 构造异步客户端上下文([token响应, 写入响应])

        with patch("backend.services.飞书服务.httpx.AsyncClient", return_value=上下文):
            服务 = 飞书服务(app_id="app-id", app_secret="app-secret")
            结果 = await 服务.写入多维表格("app-token", "table-id", {"订单号": "A001"})

        assert 结果["success"] is True
        assert 客户端.post.await_args_list[1].args[0].endswith("/apps/app-token/tables/table-id/records")
        assert 客户端.post.await_args_list[1].kwargs["headers"]["Authorization"] == "Bearer token-2"

    @pytest.mark.asyncio
    async def test_测试webhook_成功与失败(self):
        成功响应 = 构造响应({"StatusCode": 0})
        成功客户端, 成功上下文 = 构造异步客户端上下文([成功响应])
        with patch("backend.services.飞书服务.httpx.AsyncClient", return_value=成功上下文):
            服务 = 飞书服务(webhook_url="https://open.feishu.cn/hook/test")
            assert await 服务.测试webhook() is True

        失败上下文 = AsyncMock()
        失败上下文.__aenter__.side_effect = RuntimeError("network error")
        失败上下文.__aexit__.return_value = False
        with patch("backend.services.飞书服务.httpx.AsyncClient", return_value=失败上下文):
            服务 = 飞书服务(webhook_url="https://open.feishu.cn/hook/test")
            assert await 服务.测试webhook() is False


class 测试_飞书接口:
    def test_test_webhook_成功返回统一响应(self):
        app = FastAPI(redirect_slashes=False)
        app.include_router(飞书路由)

        with patch("backend.api.飞书接口.飞书服务.测试webhook", new=AsyncMock(return_value=True)):
            响应 = TestClient(app).post(
                "/api/feishu/test-webhook",
                json={"webhook_url": "https://open.feishu.cn/hook/test"},
            )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 0
        assert 响应.json()["data"]["success"] is True

    def test_test_webhook_缺少_url_返回业务错误(self):
        app = FastAPI(redirect_slashes=False)
        app.include_router(飞书路由)

        响应 = TestClient(app).post("/api/feishu/test-webhook", json={})

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "webhook_url 不能为空" in 响应.json()["msg"]


class 测试_系统服务飞书白名单:
    @pytest.mark.asyncio
    async def test_更新配置_接受飞书相关字段(self, tmp_path: Path):
        服务 = 系统服务模块.系统服务()
        服务._env文件路径 = tmp_path / ".env"
        服务._env文件路径.write_text("", encoding="utf-8")

        with patch.object(系统服务模块.配置实例, "REDIS_URL", "redis://localhost:6379/0"), \
                patch.object(系统服务模块.配置实例, "AGENT_MACHINE_ID", "machine-old"), \
                patch.object(系统服务模块.配置实例, "CAPTCHA_PROVIDER", "yescaptcha"), \
                patch.object(系统服务模块.配置实例, "CAPTCHA_API_KEY", None), \
                patch.object(系统服务模块.配置实例, "DEFAULT_PROXY", None), \
                patch.object(系统服务模块.配置实例, "MAX_BROWSER_INSTANCES", 5), \
                patch.object(系统服务模块.配置实例, "CHROME_PATH", None), \
                patch.object(系统服务模块.配置实例, "LOG_LEVEL", "INFO"):
            await 服务.更新配置(
                {
                    "feishu_webhook_url": "https://open.feishu.cn/hook/test",
                    "feishu_app_id": "cli_xxx",
                    "feishu_app_secret": "sec_xxx",
                    "feishu_bitable_app_token": "app_token",
                    "feishu_bitable_table_id": "tbl_xxx",
                }
            )

        文本 = 服务._env文件路径.read_text(encoding="utf-8")
        assert "FEISHU_WEBHOOK_URL=https://open.feishu.cn/hook/test" in 文本
        assert "FEISHU_APP_ID=cli_xxx" in 文本
        assert "FEISHU_APP_SECRET=sec_xxx" in 文本
        assert "FEISHU_BITABLE_APP_TOKEN=app_token" in 文本
        assert "FEISHU_BITABLE_TABLE_ID=tbl_xxx" in 文本
