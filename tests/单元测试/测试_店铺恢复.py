"""
店铺字段与页面布局恢复回归测试
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.路由注册 import 注册所有路由
import backend.models.数据库 as 数据库模块


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


@pytest.fixture
def 客户端(tmp_path: Path):
    """构造使用临时数据库的测试客户端。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), patch(
        "backend.services.店铺服务.配置实例.DATA_DIR",
        str(数据目录),
    ):
        asyncio.run(数据库模块.初始化数据库())

        app = FastAPI(redirect_slashes=False)
        注册所有路由(app)

        with TestClient(app) as client:
            yield client


class 测试_店铺字段恢复:
    """验证 `/api/shops` 仍返回改造前的核心字段。"""

    def test_店铺CRUD_保留邮箱与浏览器相关字段(self, 客户端: TestClient):
        """创建和更新店铺后，列表接口仍应返回原有字段。"""
        创建响应 = 客户端.post(
            "/api/shops",
            json={
                "name": "恢复测试店铺",
                "username": "demo@example.com",
                "password": "secret",
                "proxy": "127.0.0.1:7890",
                "user_agent": "Mozilla/5.0 Test",
                "smtp_host": "imap.qq.com",
                "smtp_port": 993,
                "smtp_user": "mail@example.com",
                "smtp_pass": "mail-secret",
                "smtp_protocol": "imap",
                "remark": "恢复字段验证",
            },
        )

        assert 创建响应.status_code == 200
        创建数据 = 创建响应.json()
        assert 创建数据["code"] == 0
        店铺 = 创建数据["data"]
        店铺ID = 店铺["id"]

        for 字段 in [
            "id",
            "name",
            "username",
            "password",
            "proxy",
            "user_agent",
            "profile_dir",
            "cookie_path",
            "status",
            "last_login",
            "smtp_host",
            "smtp_port",
            "smtp_user",
            "smtp_pass",
            "smtp_protocol",
            "remark",
            "created_at",
            "updated_at",
        ]:
            assert 字段 in 店铺

        assert 店铺["password"] == "***"
        assert 店铺["smtp_pass"] == "***"
        assert 店铺["user_agent"] == "Mozilla/5.0 Test"
        assert 店铺["smtp_host"] == "imap.qq.com"
        assert 店铺["smtp_user"] == "mail@example.com"
        assert 店铺["smtp_protocol"] == "imap"
        assert 店铺["remark"] == "恢复字段验证"
        assert 店铺["status"] == "offline"
        assert 店铺["profile_dir"]
        assert 店铺["cookie_path"] is None

        更新响应 = 客户端.put(
            f"/api/shops/{店铺ID}",
            json={
                "smtp_host": "smtp.qq.com",
                "smtp_port": 465,
                "smtp_user": "updated@example.com",
                "smtp_pass": "updated-secret",
                "remark": "已更新",
            },
        )

        assert 更新响应.status_code == 200
        更新数据 = 更新响应.json()
        assert 更新数据["code"] == 0
        assert 更新数据["data"]["smtp_host"] == "smtp.qq.com"
        assert 更新数据["data"]["smtp_port"] == 465
        assert 更新数据["data"]["smtp_user"] == "updated@example.com"
        assert 更新数据["data"]["smtp_pass"] == "***"
        assert 更新数据["data"]["remark"] == "已更新"

        列表响应 = 客户端.get("/api/shops")
        assert 列表响应.status_code == 200
        列表数据 = 列表响应.json()["data"]
        assert 列表数据["total"] == 1

        列表项 = 列表数据["list"][0]
        assert 列表项["id"] == 店铺ID
        assert 列表项["user_agent"] == "Mozilla/5.0 Test"
        assert 列表项["smtp_host"] == "smtp.qq.com"
        assert 列表项["smtp_port"] == 465
        assert 列表项["smtp_user"] == "updated@example.com"
        assert 列表项["smtp_pass"] == "***"
        assert 列表项["cookie_path"] is None


class 测试_店铺页布局恢复:
    """验证店铺页已恢复为旧版卡片布局。"""

    def test_店铺页_恢复旧版卡片和邮箱表单(self):
        """店铺页应重新使用 ShopCard、小卡片网格和邮箱配置表单。"""
        店铺页 = 读取文件("frontend/src/views/ShopManage.vue")
        店铺卡片 = 读取文件("frontend/src/components/ShopCard.vue")
        店铺接口 = 读取文件("frontend/src/api/shops.ts")

        assert "ShopCard" in 店铺页
        assert 'class="shops-grid"' in 店铺页
        assert "邮箱配置" in 店铺页
        assert "smtp_host" in 店铺页
        assert "smtp_user" in 店铺页
        assert "smtp_pass" in 店铺页
        assert "测试连接" in 店铺页
        assert "openShopBrowser" in 店铺页
        assert "checkShopStatus" in 店铺页
        assert "summary-grid" not in 店铺页
        assert "Resource Workspace" not in 店铺页
        assert "总数" not in 店铺页

        assert "邮箱：" in 店铺卡片
        assert "smtp_user" in 店铺卡片

        assert "openShopBrowser" in 店铺接口
        assert "checkShopStatus" in 店铺接口
        assert "testShopEmailConnection" in 店铺接口
