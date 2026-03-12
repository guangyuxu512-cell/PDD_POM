"""
任务参数接口单元测试
"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.路由注册 import 注册所有路由
from backend.models import 数据库 as 数据库模块


def 运行协程(协程对象):
    """使用独立事件循环执行协程，避免受全局 loop 状态影响。"""
    事件循环 = asyncio.new_event_loop()
    try:
        return 事件循环.run_until_complete(协程对象)
    finally:
        事件循环.close()


@pytest.fixture
def 客户端(tmp_path: Path):
    """构造带临时数据库的测试客户端。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        运行协程(数据库模块.初始化数据库())

        app = FastAPI(redirect_slashes=False)
        注册所有路由(app)

        with TestClient(app) as client:
            yield client


def 创建店铺(client: TestClient, 名称: str = "任务参数店铺") -> str:
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


class 测试_任务参数接口:
    """验证 task_params CRUD 与 CSV 导入接口。"""

    def test_CRUD与筛选分页_正常工作(self, 客户端: TestClient):
        """创建、查询、更新、删除任务参数应全部正常。"""
        店铺ID = 创建店铺(客户端)

        创建响应 = 客户端.post(
            "/api/task-params",
            json={
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "1001", "new_title": "新标题"},
            },
        )

        assert 创建响应.status_code == 200
        创建数据 = 创建响应.json()
        assert 创建数据["code"] == 0
        assert 创建数据["data"]["shop_id"] == 店铺ID
        assert 创建数据["data"]["params"]["parent_product_id"] == "1001"
        记录ID = 创建数据["data"]["id"]

        列表响应 = 客户端.get(
            "/api/task-params",
            params={"shop_id": 店铺ID, "task_name": "发布相似商品", "status": "pending"},
        )
        assert 列表响应.status_code == 200
        列表数据 = 列表响应.json()["data"]
        assert 列表数据["total"] == 1
        assert 列表数据["list"][0]["shop_name"] == "任务参数店铺"

        更新响应 = 客户端.put(
            f"/api/task-params/{记录ID}",
            json={
                "status": "success",
                "result": {"new_product_id": "9001"},
            },
        )
        assert 更新响应.status_code == 200
        更新数据 = 更新响应.json()
        assert 更新数据["code"] == 0
        assert 更新数据["data"]["status"] == "success"
        assert 更新数据["data"]["result"]["new_product_id"] == "9001"

        删除响应 = 客户端.delete(f"/api/task-params/{记录ID}")
        assert 删除响应.status_code == 200
        assert 删除响应.json()["code"] == 0

        删除后列表 = 客户端.get("/api/task-params").json()["data"]
        assert 删除后列表["total"] == 0
        assert 删除后列表["list"] == []

    def test_CSV导入与按条件清空_支持店铺ID和店铺名称(self, 客户端: TestClient):
        """CSV 导入应支持店铺 ID、店铺名称，并在名称不存在时跳过。"""
        店铺ID = 创建店铺(客户端, 名称="CSV店铺")
        创建店铺(客户端, 名称="名称映射店铺")
        CSV内容 = (
            "店铺ID,父商品ID,新标题\n"
            f"{店铺ID},2001,导入标题\n"
            "名称映射店铺,2002,按名称导入\n"
            "不存在的店铺名称,2003,坏数据\n"
        ).encode("utf-8-sig")

        导入响应 = 客户端.post(
            "/api/task-params/import-csv",
            data={"task_name": "发布相似商品"},
            files={"file": ("task-params.csv", CSV内容, "text/csv")},
        )

        assert 导入响应.status_code == 200
        导入数据 = 导入响应.json()
        assert 导入数据["code"] == 0
        assert 导入数据["data"]["success_count"] == 2
        assert 导入数据["data"]["failed_count"] == 1
        assert "店铺名称未找到" in 导入数据["data"]["errors"][0]

        列表响应 = 客户端.get("/api/task-params", params={"task_name": "发布相似商品"})
        assert 列表响应.status_code == 200
        列表数据 = 列表响应.json()["data"]
        assert 列表数据["total"] == 2
        标题集合 = {记录["params"]["new_title"] for 记录 in 列表数据["list"]}
        assert 标题集合 == {"导入标题", "按名称导入"}

        清空响应 = 客户端.delete(
            "/api/task-params/clear",
            params={"task_name": "发布相似商品", "status": "pending"},
        )
        assert 清空响应.status_code == 200
        清空数据 = 清空响应.json()
        assert 清空数据["code"] == 0
        assert 清空数据["data"]["deleted_count"] == 2

        清空后列表 = 客户端.get("/api/task-params").json()["data"]
        assert 清空后列表["total"] == 0

    def test_创建任务参数_店铺不存在返回业务错误(self, 客户端: TestClient):
        """非法店铺 ID 应返回统一错误响应。"""
        响应 = 客户端.post(
            "/api/task-params",
            json={
                "shop_id": "missing-shop",
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "3001"},
            },
        )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "店铺不存在" in 响应.json()["msg"]

    def test_列表查询_支持批次筛选日期范围和批次选项(self, 客户端: TestClient):
        """列表接口应支持 batch_id、更新时间范围和批次聚合查询。"""
        店铺ID = 创建店铺(客户端, 名称="筛选接口店铺")

        创建1 = 客户端.post(
            "/api/task-params",
            json={
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "1001"},
                "status": "success",
                "result": {"new_product_id": "new-1"},
                "batch_id": "batch-api",
            },
        ).json()["data"]
        创建2 = 客户端.post(
            "/api/task-params",
            json={
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "1002"},
                "status": "failed",
                "result": {},
                "batch_id": "batch-api",
            },
        ).json()["data"]
        客户端.post(
            "/api/task-params",
            json={
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "1003"},
                "status": "success",
                "result": {"new_product_id": "new-3"},
                "batch_id": "batch-other",
            },
        )

        数据库文件 = 数据库模块.数据库路径
        with sqlite3.connect(数据库文件) as 连接:
            连接.execute("UPDATE task_params SET updated_at = ? WHERE id = ?", ("2026-03-11 08:00:00", 创建1["id"]))
            连接.execute("UPDATE task_params SET updated_at = ? WHERE id = ?", ("2026-03-12 10:00:00", 创建2["id"]))
            连接.commit()

        列表响应 = 客户端.get(
            "/api/task-params",
            params={
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "status": "success,failed",
                "batch_id": "batch-api",
                "updated_from": "2026-03-11",
                "updated_to": "2026-03-12",
                "sort_by": "updated_at",
                "sort_order": "desc",
            },
        )

        assert 列表响应.status_code == 200
        列表数据 = 列表响应.json()["data"]
        assert [记录["id"] for 记录 in 列表数据["list"]] == [创建2["id"], 创建1["id"]]

        批次响应 = 客户端.get(
            "/api/task-params/batch-options",
            params={
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "status": "success,failed",
            },
        )

        assert 批次响应.status_code == 200
        批次数据 = 批次响应.json()["data"]
        assert 批次数据[0]["batch_id"] == "batch-api"
        assert 批次数据[0]["record_count"] == 2
