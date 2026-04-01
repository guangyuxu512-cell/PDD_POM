"""
settings API 补丁测试
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.settings_api import 路由 as 设置路由
from backend.utils.settings import ensure_settings_schema


def 创建客户端() -> TestClient:
    app = FastAPI(redirect_slashes=False)
    app.include_router(设置路由)
    return TestClient(app)


class 测试_settings_API补丁:
    def test_PUT_更新Celery地址时会规范化并刷新配置(self, tmp_path: Path):
        客户端 = 创建客户端()
        数据库路径 = tmp_path / "ecom.db"

        with patch("backend.utils.settings.DB_PATH", 数据库路径), \
                patch("backend.api.settings_api.刷新Celery配置") as 模拟刷新:
            ensure_settings_schema()
            响应 = 客户端.put(
                "/api/settings/celery_broker_url",
                json={"value": " redis://127.0.0.1/:6380/0 "},
            )

        assert 响应.status_code == 200
        模拟刷新.assert_called_once()

        with sqlite3.connect(数据库路径) as 连接:
            值 = 连接.execute(
                "SELECT value FROM settings WHERE key = ?",
                ("celery_broker_url",),
            ).fetchone()[0]

        assert 值 == "redis://127.0.0.1:6380/0"

    def test_batch_更新Celery地址时会规范化并刷新配置(self, tmp_path: Path):
        客户端 = 创建客户端()
        数据库路径 = tmp_path / "ecom.db"

        with patch("backend.utils.settings.DB_PATH", 数据库路径), \
                patch("backend.api.settings_api.刷新Celery配置") as 模拟刷新:
            ensure_settings_schema()
            响应 = 客户端.post(
                "/api/settings/batch",
                json={
                    "items": [
                        {"key": "celery_result_backend", "value": " redis://127.0.0.1/:6381/1 "},
                    ]
                },
            )

        assert 响应.status_code == 200
        模拟刷新.assert_called_once()

        with sqlite3.connect(数据库路径) as 连接:
            值 = 连接.execute(
                "SELECT value FROM settings WHERE key = ?",
                ("celery_result_backend",),
            ).fetchone()[0]

        assert 值 == "redis://127.0.0.1:6381/1"
