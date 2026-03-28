"""
流程输入接口单元测试
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
from backend.services.店铺服务 import 店铺服务实例
from backend.services.流程服务 import 流程服务实例


@pytest.fixture
def 客户端(tmp_path: Path):
    """构造临时数据库客户端。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        asyncio.run(数据库模块.初始化数据库())

        app = FastAPI(redirect_slashes=False)
        注册所有路由(app)

        with TestClient(app) as client:
            yield client


async def 创建基础数据() -> tuple[str, str]:
    """创建流程与店铺。"""
    店铺 = await 店铺服务实例.创建({"name": "输入接口店铺"})
    流程 = await 流程服务实例.创建(
        {
            "name": "输入接口流程",
            "steps": [{"task": "登录", "on_fail": "abort"}],
        }
    )
    return 店铺["id"], 流程["id"]


class 测试_流程输入接口:
    """验证输入层接口。"""

    def test_输入集与输入行接口可完成CRUD(self, 客户端: TestClient):
        店铺ID, 流程ID = asyncio.run(创建基础数据())

        创建输入集响应 = 客户端.post(
            f"/api/flows/{流程ID}/input-sets",
            json={
                "name": "接口输入集",
                "description": "测试",
                "source_type": "manual",
                "enabled": True,
            },
        )
        assert 创建输入集响应.status_code == 200
        输入集数据 = 创建输入集响应.json()["data"]
        输入集ID = 输入集数据["id"]
        assert 输入集数据["flow_id"] == 流程ID

        列表响应 = 客户端.get(f"/api/flows/{流程ID}/input-sets")
        assert 列表响应.status_code == 200
        assert 列表响应.json()["data"]["total"] == 1

        创建输入行响应 = 客户端.post(
            f"/api/input-sets/{输入集ID}/rows",
            json={
                "shop_id": 店铺ID,
                "input_data": {"parent_product_id": "9001"},
                "enabled": True,
                "sort_order": 1,
            },
        )
        assert 创建输入行响应.status_code == 200
        输入行数据 = 创建输入行响应.json()["data"]
        输入行ID = 输入行数据["id"]
        assert 输入行数据["shop_id"] == 店铺ID

        输入行列表响应 = 客户端.get(f"/api/input-sets/{输入集ID}/rows")
        assert 输入行列表响应.status_code == 200
        assert 输入行列表响应.json()["data"]["total"] == 1

        更新输入行响应 = 客户端.put(
            f"/api/input-sets/{输入集ID}/rows/{输入行ID}",
            json={"input_data": {"parent_product_id": "9002"}},
        )
        assert 更新输入行响应.status_code == 200
        assert 更新输入行响应.json()["data"]["input_data"]["parent_product_id"] == "9002"

        更新输入集响应 = 客户端.put(
            f"/api/flows/{流程ID}/input-sets/{输入集ID}",
            json={"name": "更新后输入集"},
        )
        assert 更新输入集响应.status_code == 200
        assert 更新输入集响应.json()["data"]["name"] == "更新后输入集"

        删除输入行响应 = 客户端.delete(f"/api/input-sets/{输入集ID}/rows/{输入行ID}")
        assert 删除输入行响应.status_code == 200
        assert 删除输入行响应.json()["code"] == 0

        删除输入集响应 = 客户端.delete(f"/api/flows/{流程ID}/input-sets/{输入集ID}")
        assert 删除输入集响应.status_code == 200
        assert 删除输入集响应.json()["code"] == 0

    def test_导入输入行接口会校验文件后缀(self, 客户端: TestClient):
        _, 流程ID = asyncio.run(创建基础数据())

        创建输入集响应 = 客户端.post(
            f"/api/flows/{流程ID}/input-sets",
            json={
                "name": "导入输入集",
                "source_type": "csv",
                "enabled": True,
            },
        )
        输入集ID = 创建输入集响应.json()["data"]["id"]

        响应 = 客户端.post(
            f"/api/input-sets/{输入集ID}/rows/import",
            files={"file": ("demo.txt", b"bad", "text/plain")},
        )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "仅支持" in 响应.json()["msg"]
