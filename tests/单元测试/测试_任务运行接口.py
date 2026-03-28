"""
任务运行接口单元测试
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.任务接口 import 路由


@pytest.fixture
def 客户端():
    应用 = FastAPI(redirect_slashes=False)
    应用.include_router(路由)

    with TestClient(应用) as 测试客户端:
        yield 测试客户端


class 测试_任务运行接口:
    """验证单任务运行接口。"""

    def test_创建单任务运行会转发到执行服务(self, 客户端: TestClient):
        with patch(
            "backend.api.任务接口.执行服务实例.创建批次",
            new=AsyncMock(return_value={"batch_id": "run-task-1", "status": "running", "total": 2}),
        ) as 模拟创建批次:
            响应 = 客户端.post(
                "/api/tasks/登录/runs",
                json={
                    "shop_ids": ["shop-1", "shop-2"],
                    "requested_concurrency": 2,
                    "callback_url": "http://agent.local/callback",
                },
            )

        assert 响应.status_code == 200
        assert 响应.json() == {
            "code": 0,
            "msg": "任务已启动",
            "data": {
                "run_id": "run-task-1",
                "status": "running",
                "total_items": 2,
            },
        }
        模拟创建批次.assert_awaited_once_with(
            flow_id=None,
            task_name="登录",
            shop_ids=["shop-1", "shop-2"],
            concurrency=2,
            callback_url="http://agent.local/callback",
        )

    def test_创建单任务运行失败时返回业务错误(self, 客户端: TestClient):
        with patch(
            "backend.api.任务接口.执行服务实例.创建批次",
            new=AsyncMock(side_effect=ValueError("任务未注册")),
        ):
            响应 = 客户端.post(
                "/api/tasks/不存在任务/runs",
                json={"shop_ids": ["shop-1"], "requested_concurrency": 1},
            )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "创建任务运行失败" in 响应.json()["msg"]
