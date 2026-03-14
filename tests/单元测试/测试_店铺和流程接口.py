"""
店铺与流程接口单元测试
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


class 测试_店铺接口:
    """测试店铺 CRUD 接口。"""

    def test_店铺CRUD_支持无尾斜杠并遮蔽密码(self, 客户端: TestClient):
        """创建、查询、更新、删除店铺时都应返回脱敏密码。"""
        创建响应 = 客户端.post(
            "/api/shops",
            json={
                "name": "测试店铺",
                "username": "demo@example.com",
                "password": "secret",
            },
        )

        assert 创建响应.status_code == 200
        创建数据 = 创建响应.json()
        assert 创建数据["code"] == 0
        assert 创建数据["data"]["password"] == "***"
        店铺ID = 创建数据["data"]["id"]

        列表响应 = 客户端.get("/api/shops")
        assert 列表响应.status_code == 200
        列表数据 = 列表响应.json()["data"]
        assert 列表数据["total"] == 1
        assert 列表数据["list"][0]["password"] == "***"

        更新响应 = 客户端.put(
            f"/api/shops/{店铺ID}",
            json={
                "name": "更新后店铺",
                "password": "new-secret",
            },
        )
        assert 更新响应.status_code == 200
        更新数据 = 更新响应.json()
        assert 更新数据["code"] == 0
        assert 更新数据["data"]["name"] == "更新后店铺"
        assert 更新数据["data"]["password"] == "***"

        删除响应 = 客户端.delete(f"/api/shops/{店铺ID}")
        assert 删除响应.status_code == 200
        assert 删除响应.json()["code"] == 0

        删除后列表 = 客户端.get("/api/shops").json()["data"]
        assert 删除后列表["total"] == 0
        assert 删除后列表["list"] == []

    def test_创建店铺_空名称返回错误(self, 客户端: TestClient):
        """空店铺名称应返回业务错误。"""
        响应 = 客户端.post(
            "/api/shops",
            json={
                "name": "   ",
            },
        )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "店铺名称不能为空" in 响应.json()["msg"]


class 测试_流程接口:
    """测试流程 CRUD 与校验逻辑。"""

    def test_流程CRUD_支持任务校验与列表返回(self, 客户端: TestClient):
        """流程创建、查询、更新、删除应正常工作。"""
        创建响应 = 客户端.post(
            "/api/flows",
            json={
                "name": "日常售后",
                "steps": [
                    {
                        "task": "登录",
                        "on_fail": "continue",
                    }
                ],
                "description": "基础流程",
            },
        )

        assert 创建响应.status_code == 200
        创建数据 = 创建响应.json()
        assert 创建数据["code"] == 0
        assert 创建数据["data"]["name"] == "日常售后"
        assert 创建数据["data"]["steps"] == [
            {"task": "登录", "on_fail": "continue", "barrier": False, "merge": False}
        ]
        流程ID = 创建数据["data"]["id"]

        列表响应 = 客户端.get("/api/flows")
        assert 列表响应.status_code == 200
        列表数据 = 列表响应.json()["data"]
        assert 列表数据["total"] == 1
        assert 列表数据["list"][0]["id"] == 流程ID

        更新响应 = 客户端.put(
            f"/api/flows/{流程ID}",
            json={
                "description": "更新后的描述",
                "steps": [
                    {
                        "task": "登录",
                        "on_fail": "retry:2",
                    }
                ],
            },
        )
        assert 更新响应.status_code == 200
        更新数据 = 更新响应.json()
        assert 更新数据["code"] == 0
        assert 更新数据["data"]["description"] == "更新后的描述"
        assert 更新数据["data"]["steps"] == [
            {"task": "登录", "on_fail": "retry:2", "barrier": False, "merge": False}
        ]

        删除响应 = 客户端.delete(f"/api/flows/{流程ID}")
        assert 删除响应.status_code == 200
        assert 删除响应.json()["code"] == 0

        删除后列表 = 客户端.get("/api/flows").json()["data"]
        assert 删除后列表["total"] == 0
        assert 删除后列表["list"] == []

    def test_创建流程_未知任务返回错误(self, 客户端: TestClient):
        """steps 中 task 未注册时应返回业务错误。"""
        响应 = 客户端.post(
            "/api/flows",
            json={
                "name": "坏流程",
                "steps": [
                    {
                        "task": "不存在任务",
                        "on_fail": "continue",
                    }
                ],
            },
        )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "步骤任务未注册" in 响应.json()["msg"]

    def test_创建流程_steps非法JSON返回错误(self, 客户端: TestClient):
        """steps 为非法 JSON 字符串时应返回业务错误。"""
        响应 = 客户端.post(
            "/api/flows",
            json={
                "name": "坏流程",
                "steps": "{not-json}",
            },
        )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "steps JSON 格式错误" in 响应.json()["msg"]
