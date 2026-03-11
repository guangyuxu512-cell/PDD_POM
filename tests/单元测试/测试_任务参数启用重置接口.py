"""
任务参数启用/禁用/重置接口测试
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.api.路由注册 import 注册所有路由
from backend.models import 数据库 as 数据库模块


def 运行协程(协程对象):
    """使用独立事件循环执行协程，避免测试相互影响。"""
    事件循环 = asyncio.new_event_loop()
    try:
        return 事件循环.run_until_complete(协程对象)
    finally:
        事件循环.close()


@pytest.fixture
def 客户端(tmp_path: Path):
    """构造临时数据库对应的 FastAPI 客户端。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        运行协程(数据库模块.初始化数据库())

        app = FastAPI(redirect_slashes=False)
        注册所有路由(app)

        with TestClient(app) as client:
            yield client


def 创建店铺(client: TestClient, 名称: str = "接口店铺") -> str:
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


class 测试_任务参数启用重置接口:
    """验证单条和批量接口行为。"""

    def test_单条启用禁用重置接口_保持统一响应(self, 客户端: TestClient):
        """单条禁用、重置、启用接口应直接返回更新后的记录。"""
        店铺ID = 创建店铺(客户端, "单条接口店铺")
        创建响应 = 客户端.post(
            "/api/task-params",
            json={
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "5001"},
                "status": "success",
                "result": {"goods_id": "sku-5001"},
                "error": "历史错误",
            },
        )
        记录ID = 创建响应.json()["data"]["id"]

        禁用响应 = 客户端.put(f"/api/task-params/{记录ID}/disable")
        assert 禁用响应.status_code == 200
        assert 禁用响应.json()["code"] == 0
        assert 禁用响应.json()["data"]["enabled"] is False

        重置响应 = 客户端.put(f"/api/task-params/{记录ID}/reset")
        assert 重置响应.status_code == 200
        assert 重置响应.json()["code"] == 0
        assert 重置响应.json()["data"]["status"] == "pending"
        assert 重置响应.json()["data"]["result"] == {}
        assert 重置响应.json()["data"]["error"] is None
        assert 重置响应.json()["data"]["enabled"] is False

        启用响应 = 客户端.put(f"/api/task-params/{记录ID}/enable")
        assert 启用响应.status_code == 200
        assert 启用响应.json()["code"] == 0
        assert 启用响应.json()["data"]["enabled"] is True

    def test_批量接口与发布次数导入_按筛选条件生效(self, 客户端: TestClient):
        """批量启用禁用需带筛选条件，发布次数导入和批量重置应正确生效。"""
        店铺ID = 创建店铺(客户端, "批量接口店铺")

        无筛选批量启用 = 客户端.put("/api/task-params/batch-enable", json={})
        assert 无筛选批量启用.status_code == 200
        assert 无筛选批量启用.json()["code"] == 1
        assert "至少提供一个筛选条件" in 无筛选批量启用.json()["msg"]

        CSV内容 = (
            "店铺ID,父商品ID,新标题,发布次数\n"
            f"{店铺ID},6001,接口展开标题,2\n"
        ).encode("utf-8-sig")
        导入响应 = 客户端.post(
            "/api/task-params/import-csv",
            data={"task_name": "发布相似商品"},
            files={"file": ("task-params.csv", CSV内容, "text/csv")},
        )

        assert 导入响应.status_code == 200
        assert 导入响应.json()["code"] == 0
        assert 导入响应.json()["data"]["success_count"] == 2

        列表响应 = 客户端.get("/api/task-params", params={"shop_id": 店铺ID, "task_name": "发布相似商品"})
        列表数据 = 列表响应.json()["data"]["list"]
        记录ID列表 = [记录["id"] for 记录 in 列表数据]
        assert sorted(记录["params"]["batch_index"] for 记录 in 列表数据) == [1, 2]

        批量禁用响应 = 客户端.put(
            "/api/task-params/batch-disable",
            json={"shop_id": 店铺ID, "task_name": "发布相似商品", "status": "pending"},
        )
        assert 批量禁用响应.status_code == 200
        assert 批量禁用响应.json()["code"] == 0
        assert 批量禁用响应.json()["data"]["updated_count"] == 2

        禁用后列表 = 客户端.get("/api/task-params", params={"shop_id": 店铺ID, "task_name": "发布相似商品"})
        assert all(记录["enabled"] is False for 记录 in 禁用后列表.json()["data"]["list"])

        客户端.put(
            f"/api/task-params/{记录ID列表[0]}",
            json={"status": "success", "result": {"goods_id": "sku-6001"}},
        )
        客户端.put(
            f"/api/task-params/{记录ID列表[1]}",
            json={"status": "failed", "error": "上传失败"},
        )

        批量重置响应 = 客户端.put(
            "/api/task-params/batch-reset",
            json={"shop_id": 店铺ID, "task_name": "发布相似商品"},
        )
        assert 批量重置响应.status_code == 200
        assert 批量重置响应.json()["code"] == 0
        assert 批量重置响应.json()["data"]["updated_count"] == 2

        重置后列表 = 客户端.get("/api/task-params", params={"shop_id": 店铺ID, "task_name": "发布相似商品"})
        for 记录 in 重置后列表.json()["data"]["list"]:
            assert 记录["status"] == "pending"
            assert 记录["result"] == {}
            assert 记录["error"] is None
            assert 记录["enabled"] is False
