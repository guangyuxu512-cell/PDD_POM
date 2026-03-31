"""
settings API 与工具模块测试
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.settings_api import 路由 as 设置路由
from backend.utils.crypto import decrypt_value, encrypt_value
from backend.utils.settings import ensure_settings_schema


def _创建客户端(tmp_path: Path) -> TestClient:
    app = FastAPI(redirect_slashes=False)
    app.include_router(设置路由)
    return TestClient(app)


class 测试_加密工具:
    def test_encrypt_and_decrypt_roundtrip(self):
        密文 = encrypt_value("hello")
        assert decrypt_value(密文) == "hello"


class 测试_settings_API:
    def test_GET_返回设置列表且敏感字段脱敏(self, tmp_path: Path):
        客户端 = _创建客户端(tmp_path)
        数据库路径 = tmp_path / "ecom.db"

        with patch("backend.utils.settings.DB_PATH", 数据库路径):
            ensure_settings_schema()
            from backend.utils.settings import update_setting

            update_setting("feishu_webhook_url", "https://open.feishu.cn/hook/test")
            响应 = 客户端.get("/api/settings")
        assert 响应.status_code == 200
        数据 = 响应.json()["data"]["list"]
        webhook配置 = next(item for item in 数据 if item["key"] == "feishu_webhook_url")

        assert webhook配置["encrypted"] == 1
        assert webhook配置["value"] is None
        assert webhook配置["has_value"] is True

    def test_PUT_更新敏感字段后数据库保存密文(self, tmp_path: Path):
        客户端 = _创建客户端(tmp_path)
        数据库路径 = tmp_path / "ecom.db"

        with patch("backend.utils.settings.DB_PATH", 数据库路径):
            ensure_settings_schema()
            响应 = 客户端.put(
                "/api/settings/feishu_webhook_url",
                json={"value": "https://open.feishu.cn/hook/test"},
            )
        assert 响应.status_code == 200
        assert 响应.json()["msg"] == "配置已更新"

        with sqlite3.connect(数据库路径) as 连接:
            密文 = 连接.execute(
                "SELECT value FROM settings WHERE key = ?",
                ("feishu_webhook_url",),
            ).fetchone()[0]

        assert 密文 != "https://open.feishu.cn/hook/test"
        assert decrypt_value(密文) == "https://open.feishu.cn/hook/test"

    def test_batch_更新时空白敏感字段不会覆盖旧值(self, tmp_path: Path):
        客户端 = _创建客户端(tmp_path)
        数据库路径 = tmp_path / "ecom.db"

        with patch("backend.utils.settings.DB_PATH", 数据库路径):
            ensure_settings_schema()
            客户端.put(
                "/api/settings/feishu_webhook_url",
                json={"value": "https://open.feishu.cn/hook/test"},
            )

            响应 = 客户端.post(
                "/api/settings/batch",
                json={
                    "items": [
                        {"key": "default_proxy", "value": "127.0.0.1:7890"},
                        {"key": "feishu_webhook_url", "value": ""},
                    ]
                },
            )
        assert 响应.status_code == 200
        assert 响应.json()["msg"] == "已更新 1 项配置"

        with sqlite3.connect(数据库路径) as 连接:
            默认代理 = 连接.execute(
                "SELECT value FROM settings WHERE key = ?",
                ("default_proxy",),
            ).fetchone()[0]
            密文 = 连接.execute(
                "SELECT value FROM settings WHERE key = ?",
                ("feishu_webhook_url",),
            ).fetchone()[0]

        assert 默认代理 == "127.0.0.1:7890"
        assert decrypt_value(密文) == "https://open.feishu.cn/hook/test"

    def test_PUT_未知配置返回_404(self, tmp_path: Path):
        客户端 = _创建客户端(tmp_path)
        with patch("backend.utils.settings.DB_PATH", tmp_path / "ecom.db"):
            ensure_settings_schema()
            响应 = 客户端.put("/api/settings/not-exists", json={"value": "x"})
        assert 响应.status_code == 404
