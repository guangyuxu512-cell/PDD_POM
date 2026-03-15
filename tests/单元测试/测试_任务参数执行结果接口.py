"""
任务参数执行结果接口测试
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
from backend.services.任务参数服务 import 任务参数服务实例
from backend.services.流程参数服务 import 流程参数服务实例


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


def 创建店铺(client: TestClient, 名称: str = "结果店铺") -> str:
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


def 创建流程(client: TestClient, 名称: str = "结果流程") -> str:
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


class 测试_任务参数执行结果接口:
    """验证执行结果接口能返回 flow_params 数据。"""

    def test_执行结果接口_合并返回_task_params_和_flow_params(self, 客户端: TestClient):
        店铺ID = 创建店铺(客户端)
        flow_id = 创建流程(客户端)

        运行协程(
            任务参数服务实例.创建(
                {
                    "shop_id": 店铺ID,
                    "task_name": "发布相似商品",
                    "params": {"parent_product_id": "9001", "discount": 6},
                    "status": "success",
                    "result": {"new_product_id": "task-new-1"},
                    "batch_id": "batch-task",
                }
            )
        )

        运行协程(
            流程参数服务实例.创建(
                {
                    "shop_id": 店铺ID,
                    "flow_id": flow_id,
                    "params": {"parent_product_id": "9002", "discount": 7, "roi": 5.5},
                    "step_results": {
                        "发布相似商品": {
                            "status": "completed",
                            "new_product_id": "flow-new-1",
                        },
                        "限时限量": {
                            "status": "completed",
                            "discount": 7,
                        },
                    },
                    "current_step": 2,
                    "status": "success",
                    "batch_id": "batch-flow",
                }
            )
        )

        响应 = 客户端.get(
            "/api/task-params/results",
            params={"shop_id": 店铺ID, "status": "success"},
        )

        assert 响应.status_code == 200
        数据 = 响应.json()["data"]
        assert 数据["total"] == 2

        任务结果 = next(记录 for 记录 in 数据["list"] if 记录["batch_id"] == "batch-task")
        流程结果 = next(记录 for 记录 in 数据["list"] if 记录["batch_id"] == "batch-flow")

        assert 任务结果["task_name"] == "发布相似商品"
        assert 任务结果["result"]["new_product_id"] == "task-new-1"

        assert 流程结果["task_name"] == "限时限量"
        assert 流程结果["params"]["parent_product_id"] == "9002"
        assert 流程结果["params"]["discount"] == 7
        assert 流程结果["params"]["roi"] == 5.5
        assert 流程结果["result"]["new_product_id"] == "flow-new-1"

    def test_执行结果接口_支持按任务类型筛选_flow_results(self, 客户端: TestClient):
        店铺ID = 创建店铺(客户端, 名称="筛选店铺")
        flow_id = 创建流程(客户端, 名称="筛选流程")

        运行协程(
            流程参数服务实例.创建(
                {
                    "shop_id": 店铺ID,
                    "flow_id": flow_id,
                    "params": {"parent_product_id": "9003", "discount": 8},
                    "step_results": {
                        "发布相似商品": {
                            "status": "completed",
                            "new_product_id": "flow-new-2",
                        },
                        "限时限量": {
                            "status": "running",
                        },
                    },
                    "current_step": 2,
                    "status": "running",
                    "batch_id": "batch-running",
                }
            )
        )

        响应 = 客户端.get(
            "/api/task-params/results",
            params={"shop_id": 店铺ID, "task_name": "限时限量", "status": "running"},
        )

        assert 响应.status_code == 200
        数据 = 响应.json()["data"]
        assert 数据["total"] == 1
        assert 数据["list"][0]["task_name"] == "限时限量"
