"""
定时执行接口单元测试
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.路由注册 import 注册所有路由
from backend.models import 数据库 as 数据库模块


@pytest.fixture
def 客户端(tmp_path: Path):
    """构造使用临时数据库和数据目录的测试客户端。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        asyncio.run(数据库模块.初始化数据库())

        app = FastAPI(redirect_slashes=False)
        注册所有路由(app)

        with TestClient(app) as client:
            yield client


def 创建基础数据(客户端: TestClient) -> tuple[str, str]:
    """通过真实接口创建店铺和流程。"""
    店铺响应 = 客户端.post("/api/shops", json={"name": "接口店铺"})
    店铺ID = 店铺响应.json()["data"]["id"]

    流程响应 = 客户端.post(
        "/api/flows",
        json={
            "name": "接口流程",
            "steps": [{"task": "登录", "on_fail": "continue"}],
        },
    )
    流程ID = 流程响应.json()["data"]["id"]
    return 店铺ID, 流程ID


class 测试_定时执行接口:
    """验证 schedules 路由的统一响应与基本闭环。"""

    def test_定时计划CRUD与暂停恢复接口可用(self, 客户端: TestClient):
        """创建、列表、暂停、恢复、删除都应返回统一成功响应。"""
        店铺ID, 流程ID = 创建基础数据(客户端)
        下次运行时间 = datetime(2026, 3, 10, 12, 30, 0)

        with patch(
            "backend.api.定时执行接口.定时执行服务实例._同步RedBeat计划",
            new=AsyncMock(return_value=下次运行时间),
        ), patch(
            "backend.api.定时执行接口.定时执行服务实例._移除RedBeat计划",
            new=AsyncMock(return_value=None),
        ):
            创建响应 = 客户端.post(
                "/api/schedules",
                json={
                    "name": "接口计划",
                    "flow_id": 流程ID,
                    "shop_ids": [店铺ID],
                    "concurrency": 2,
                    "interval_seconds": 60,
                    "overlap_policy": "wait",
                },
            )

            assert 创建响应.status_code == 200
            创建数据 = 创建响应.json()
            assert 创建数据["code"] == 0
            assert 创建数据["data"]["name"] == "接口计划"
            assert 创建数据["data"]["next_run_at"] == "2026-03-10 12:30:00"
            计划ID = 创建数据["data"]["id"]

            列表响应 = 客户端.get("/api/schedules")
            assert 列表响应.status_code == 200
            列表数据 = 列表响应.json()["data"]
            assert 列表数据["total"] == 1
            assert 列表数据["list"][0]["id"] == 计划ID

            暂停响应 = 客户端.post(f"/api/schedules/{计划ID}/pause")
            assert 暂停响应.status_code == 200
            assert 暂停响应.json()["code"] == 0
            assert 暂停响应.json()["data"]["enabled"] is False

            恢复响应 = 客户端.post(f"/api/schedules/{计划ID}/resume")
            assert 恢复响应.status_code == 200
            assert 恢复响应.json()["code"] == 0
            assert 恢复响应.json()["data"]["enabled"] is True

            删除响应 = 客户端.delete(f"/api/schedules/{计划ID}")
            assert 删除响应.status_code == 200
            assert 删除响应.json()["code"] == 0

        删除后列表 = 客户端.get("/api/schedules").json()["data"]
        assert 删除后列表["total"] == 0
        assert 删除后列表["list"] == []

    def test_创建定时计划_流程不存在返回业务错误(self, 客户端: TestClient):
        """流程不存在时应返回统一业务错误。"""
        响应 = 客户端.post(
            "/api/schedules",
            json={
                "name": "坏计划",
                "flow_id": "missing-flow",
                "shop_ids": ["shop-1"],
                "interval_seconds": 60,
            },
        )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "流程不存在" in 响应.json()["msg"]
