"""
运行接口单元测试
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.路由注册 import 注册所有路由
from backend.models import 数据库 as 数据库模块
from backend.services.店铺服务 import 店铺服务实例
from backend.services.流程服务 import 流程服务实例
from backend.services.执行服务 import 执行服务, 同步写入运行实例状态


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


async def 创建运行样本() -> tuple[str, str, str]:
    """创建运行实例基础数据。"""
    店铺 = await 店铺服务实例.创建({"name": "接口运行店铺"})
    流程 = await 流程服务实例.创建(
        {
            "name": "接口运行流程",
            "steps": [{"task": "登录", "on_fail": "abort"}],
        }
    )
    run_id = "run-api-1"
    服务 = 执行服务()
    await 服务._写入运行实例快照(
        run_id=run_id,
        flow_id=流程["id"],
        task_name=None,
        shop_ids=[店铺["id"]],
        步骤模板=[{"task": "登录", "on_fail": "abort", "barrier": False, "merge": False}],
        concurrency=1,
        callback_url=None,
        流程参数记录映射={店铺["id"]: []},
    )
    同步写入运行实例状态(
        {
            "batch_id": run_id,
            "status": "running",
            "stopped": False,
            "total": 1,
            "waiting": 0,
            "running": 1,
            "completed": 0,
            "failed": 0,
            "shops": {
                店铺["id"]: {
                    "shop_id": 店铺["id"],
                    "shop_name": "接口运行店铺",
                    "status": "running",
                    "current_task": "登录",
                    "current_step": 1,
                    "total_steps": 1,
                    "last_error": None,
                    "last_result": None,
                    "steps": [
                        {
                            "task": "登录",
                            "on_fail": "abort",
                            "barrier": False,
                            "merge": False,
                            "status": "running",
                            "error": None,
                            "result": None,
                        }
                    ],
                }
            },
        }
    )
    return run_id, 店铺["id"], 流程["id"]


class 测试_运行接口:
    """验证运行中心接口。"""

    def test_运行列表详情运行项和步骤接口可用(self, 客户端: TestClient):
        run_id, 店铺ID, _ = asyncio.run(创建运行样本())

        列表响应 = 客户端.get("/api/runs")
        assert 列表响应.status_code == 200
        列表数据 = 列表响应.json()
        assert 列表数据["code"] == 0
        assert 列表数据["data"]["total"] == 1
        assert 列表数据["data"]["list"][0]["id"] == run_id

        详情响应 = 客户端.get(f"/api/runs/{run_id}")
        assert 详情响应.status_code == 200
        assert 详情响应.json()["data"]["status"] == "running"

        运行项响应 = 客户端.get(f"/api/runs/{run_id}/items")
        assert 运行项响应.status_code == 200
        assert 运行项响应.json()["data"]["total"] == 1
        assert 运行项响应.json()["data"]["list"][0]["shop_id"] == 店铺ID

        步骤响应 = 客户端.get(f"/api/runs/{run_id}/steps")
        assert 步骤响应.status_code == 200
        assert 步骤响应.json()["data"]["total"] == 1
        assert 步骤响应.json()["data"]["list"][0]["task_name"] == "登录"

    def test_获取不存在的运行返回业务错误(self, 客户端: TestClient):
        响应 = 客户端.get("/api/runs/missing-run")

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "运行不存在" in 响应.json()["msg"]

    def test_取消运行接口_透传到执行服务(self, 客户端: TestClient):
        with patch(
            "backend.api.运行接口.执行服务实例.停止批次",
            new=AsyncMock(return_value={"batch_id": "run-api-cancel", "total": 1, "status": "stopped"}),
        ) as 模拟停止批次:
            响应 = 客户端.post("/api/runs/run-api-cancel/cancel")

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 0
        模拟停止批次.assert_awaited_once_with(batch_id="run-api-cancel")
