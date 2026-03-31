"""
平台支持相关后端测试
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
from platforms.base.base_platform import get_platform, list_platforms


@pytest.fixture
def 平台客户端(tmp_path: Path):
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


class 测试_平台迁移:
    """验证平台字段迁移和回填。"""

    @pytest.mark.asyncio
    async def test_初始化数据库_补齐platform字段并回填默认值(self, tmp_path: Path):
        """旧库升级后，shops/flows/task_logs 都应带上 platform 并回填 pdd。"""
        数据库文件 = tmp_path / "legacy.db"

        with sqlite3.connect(数据库文件) as 连接:
            连接.executescript(
                """
                CREATE TABLE shops (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    username TEXT,
                    password TEXT,
                    proxy TEXT,
                    user_agent TEXT,
                    profile_dir TEXT,
                    cookie_path TEXT,
                    status TEXT DEFAULT 'offline',
                    last_login DATETIME,
                    smtp_host TEXT,
                    smtp_port INTEGER DEFAULT 993,
                    smtp_user TEXT,
                    smtp_pass TEXT,
                    smtp_protocol TEXT DEFAULT 'imap',
                    remark TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO shops (id, name, status) VALUES ('shop-1', '旧店铺', 'offline');

                CREATE TABLE flows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO flows (id, name, steps) VALUES ('flow-1', '旧流程', '[{"task":"登录","on_fail":"abort"}]');

                CREATE TABLE task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    shop_id TEXT,
                    task_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    params TEXT,
                    result TEXT,
                    error TEXT,
                    screenshot TEXT,
                    started_at DATETIME,
                    finished_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO task_logs (task_id, shop_id, task_name, status)
                VALUES ('task-1', 'shop-1', '登录', 'completed');
                """
            )

        with patch.object(数据库模块, "数据库路径", 数据库文件):
            await 数据库模块.初始化数据库()

        with sqlite3.connect(数据库文件) as 连接:
            店铺字段 = {行[1] for 行 in 连接.execute("PRAGMA table_info(shops)")}
            流程字段 = {行[1] for 行 in 连接.execute("PRAGMA table_info(flows)")}
            任务字段 = {行[1] for 行 in 连接.execute("PRAGMA table_info(task_logs)")}

            assert "platform" in 店铺字段
            assert "platform" in 流程字段
            assert "platform" in 任务字段

            assert 连接.execute(
                "SELECT platform FROM shops WHERE id = 'shop-1'"
            ).fetchone()[0] == "pdd"
            assert 连接.execute(
                "SELECT platform FROM flows WHERE id = 'flow-1'"
            ).fetchone()[0] == "pdd"
            assert 连接.execute(
                "SELECT platform FROM task_logs WHERE task_id = 'task-1'"
            ).fetchone()[0] == "pdd"


class 测试_平台接口:
    """验证平台接口与过滤行为。"""

    def test_店铺与流程接口_支持platform过滤(self, 平台客户端):
        """店铺和流程列表应按 platform 过滤，创建时默认绑定 pdd。"""
        客户端, 数据库文件 = 平台客户端

        店铺响应 = 客户端.post("/api/shops", json={"name": "默认平台店铺"})
        assert 店铺响应.status_code == 200
        assert 店铺响应.json()["code"] == 0
        assert 店铺响应.json()["data"]["platform"] == "pdd"

        流程响应 = 客户端.post(
            "/api/flows",
            json={
                "name": "默认平台流程",
                "steps": [{"task": "登录", "on_fail": "abort"}],
            },
        )
        assert 流程响应.status_code == 200
        assert 流程响应.json()["code"] == 0
        assert 流程响应.json()["data"]["platform"] == "pdd"

        with sqlite3.connect(数据库文件) as 连接:
            连接.execute(
                """
                INSERT INTO shops (id, name, platform, status)
                VALUES (?, ?, ?, ?)
                """,
                ("shop-taobao", "淘宝店铺", "taobao", "offline"),
            )
            连接.execute(
                """
                INSERT INTO flows (id, name, platform, steps)
                VALUES (?, ?, ?, ?)
                """,
                ("flow-taobao", "淘宝流程", "taobao", '[{"task":"登录","on_fail":"abort"}]'),
            )
            连接.commit()

        店铺列表响应 = 客户端.get("/api/shops?platform=pdd")
        assert 店铺列表响应.status_code == 200
        assert 店铺列表响应.json()["code"] == 0
        assert 店铺列表响应.json()["data"]["total"] == 1
        assert [店铺["platform"] for 店铺 in 店铺列表响应.json()["data"]["list"]] == ["pdd"]

        流程列表响应 = 客户端.get("/api/flows?platform=pdd")
        assert 流程列表响应.status_code == 200
        assert 流程列表响应.json()["code"] == 0
        assert 流程列表响应.json()["data"]["total"] == 1
        assert [流程["platform"] for 流程 in 流程列表响应.json()["data"]["list"]] == ["pdd"]

        平台列表响应 = 客户端.get("/api/platforms")
        assert 平台列表响应.status_code == 200
        assert 平台列表响应.json() == {
            "code": 0,
            "msg": "ok",
            "data": {
                "list": [
                    {"id": "pdd", "name": "拼多多", "icon": "🟠"},
                    {"id": "douyin", "name": "抖音", "icon": "🎵"},
                    {"id": "taobao", "name": "淘宝", "icon": "🟧"},
                ]
            },
        }


class 测试_平台注册表:
    """验证平台注册表行为。"""

    def test_获取平台与列出平台(self):
        """已注册平台应可读取，未注册平台应抛出异常。"""
        拼多多平台 = get_platform("pdd")
        抖音平台 = get_platform("douyin")
        淘宝平台 = get_platform("taobao")

        assert 拼多多平台.display_name == "拼多多"
        assert 拼多多平台.login_url == "https://mms.pinduoduo.com/login"
        assert 拼多多平台.get_available_tasks() == [
            "登录",
            "售后处理",
            "发布相似商品",
            "发布换图商品",
            "限时限量",
            "设置推广",
        ]
        assert 抖音平台.display_name == "抖音"
        assert 抖音平台.login_url == "https://fxg.jinritemai.com/login/common"
        assert 抖音平台.get_available_tasks() == []
        assert 淘宝平台.display_name == "淘宝"
        assert 淘宝平台.login_url == "https://myseller.taobao.com/"
        assert 淘宝平台.get_available_tasks() == []
        assert list_platforms() == [
            {"id": "pdd", "name": "拼多多", "icon": "🟠"},
            {"id": "douyin", "name": "抖音", "icon": "🎵"},
            {"id": "taobao", "name": "淘宝", "icon": "🟧"},
        ]

        with pytest.raises(ValueError, match="未注册的平台: jd"):
            get_platform("jd")
