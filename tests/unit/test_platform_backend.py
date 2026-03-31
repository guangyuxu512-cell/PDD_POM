"""
单平台模式后端回归测试
"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.router import 注册所有路由
from backend.models import database as 数据库模块


仓库根目录 = Path(__file__).resolve().parents[2]


@pytest.fixture
def 单平台客户端(tmp_path: Path):
    """构造使用临时数据库和数据目录的测试客户端。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.shop_service.配置实例.DATA_DIR", str(数据目录)):
        asyncio.run(数据库模块.初始化数据库())

        app = FastAPI(redirect_slashes=False)
        注册所有路由(app)

        with TestClient(app) as client:
            yield client, 数据库文件


class 测试_单平台后端:
    def test_创建店铺时忽略传入platform并固定为_pdd(self, 单平台客户端):
        客户端, 数据库文件 = 单平台客户端

        响应 = 客户端.post(
            "/api/shops",
            json={
                "name": "单平台店铺",
                "platform": "taobao",
            },
        )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 0
        assert 响应.json()["data"]["platform"] == "pdd"

        with sqlite3.connect(数据库文件) as 连接:
            数据库平台 = 连接.execute(
                "SELECT platform FROM shops WHERE name = ?",
                ("单平台店铺",),
            ).fetchone()[0]

        assert 数据库平台 == "pdd"

    def test_平台抽象入口已删除且_platforms_接口不存在(self, 单平台客户端):
        客户端, _ = 单平台客户端
        路由文件 = (仓库根目录 / "backend/api/router.py").read_text(encoding="utf-8")

        assert not (仓库根目录 / "backend/api/platform_api.py").exists()
        assert not (仓库根目录 / "platforms").exists()
        assert "platform_api" not in 路由文件
        assert "平台路由" not in 路由文件

        响应 = 客户端.get("/api/platforms")
        assert 响应.status_code == 404
