"""
流程参数接口单元测试
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.路由注册 import 注册所有路由
from backend.models import 数据库 as 数据库模块


def 运行协程(协程对象):
    事件循环 = asyncio.new_event_loop()
    try:
        return 事件循环.run_until_complete(协程对象)
    finally:
        事件循环.close()


@pytest.fixture
def 客户端(tmp_path: Path):
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        运行协程(数据库模块.初始化数据库())

        app = FastAPI(redirect_slashes=False)
        注册所有路由(app)

        with TestClient(app) as client:
            yield client


def 创建店铺(client: TestClient, 名称: str = "流程参数店铺") -> str:
    响应 = client.post(
        "/api/shops",
        json={
            "name": 名称,
            "username": f"{名称}@example.com",
            "password": "secret",
        },
    )
    assert 响应.status_code == 200
    assert 响应.json()["code"] == 0
    return 响应.json()["data"]["id"]


def 创建流程(client: TestClient, 名称: str = "流程参数流程") -> str:
    响应 = client.post(
        "/api/flows",
        json={
            "name": 名称,
            "steps": [
                {"task": "发布相似商品", "on_fail": "abort"},
                {"task": "限时限量", "on_fail": "abort"},
            ],
        },
    )
    assert 响应.status_code == 200
    assert 响应.json()["code"] == 0
    return 响应.json()["data"]["id"]


class 测试_流程参数接口:
    """验证 flow_params CRUD 与导入接口。"""

    def test_CRUD与导入_正常工作(self, 客户端: TestClient):
        店铺ID = 创建店铺(客户端)
        flow_id = 创建流程(客户端)

        导入内容 = (
            "店铺ID,父商品ID,折扣\n"
            f"{店铺ID},9001,6\n"
        ).encode("utf-8-sig")
        导入响应 = 客户端.post(
            "/api/flow-params/import",
            data={"flow_id": flow_id},
            files={"file": ("flow-params.csv", 导入内容, "text/csv")},
        )

        assert 导入响应.status_code == 200
        assert 导入响应.json()["code"] == 0
        assert 导入响应.json()["data"]["success_count"] == 1

        列表响应 = 客户端.get("/api/flow-params", params={"flow_id": flow_id})
        列表数据 = 列表响应.json()["data"]
        assert 列表数据["total"] == 1
        记录ID = 列表数据["list"][0]["id"]

        详情响应 = 客户端.get(f"/api/flow-params/{记录ID}")
        assert 详情响应.status_code == 200
        assert 详情响应.json()["data"]["params"]["parent_product_id"] == "9001"

        更新响应 = 客户端.put(
            f"/api/flow-params/{记录ID}",
            json={"status": "running", "current_step": 1},
        )
        assert 更新响应.status_code == 200
        assert 更新响应.json()["data"]["current_step"] == 1

        清空响应 = 客户端.delete(
            "/api/flow-params/batch-clear",
            params={"flow_id": flow_id, "status": "running"},
        )
        assert 清空响应.status_code == 200
        assert 清空响应.json()["data"]["deleted_count"] == 1

    def test_导入流程参数_flow不存在返回业务错误(self, 客户端: TestClient):
        店铺ID = 创建店铺(客户端, 名称="流程参数异常店铺")
        导入内容 = (
            "店铺ID,父商品ID\n"
            f"{店铺ID},9001\n"
        ).encode("utf-8-sig")

        响应 = 客户端.post(
            "/api/flow-params/import",
            data={"flow_id": "missing-flow"},
            files={"file": ("flow-params.csv", 导入内容, "text/csv")},
        )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "流程不存在" in 响应.json()["msg"]
