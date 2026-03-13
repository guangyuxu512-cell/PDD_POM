"""
任务内部执行接口单元测试
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


class 测试_任务接口内部执行:
    """验证 Worker 调用的内部执行接口。"""

    def test_execute_internal_成功返回统一响应并回写流程结果(self, 客户端: TestClient):
        with patch(
            "backend.api.任务接口.任务服务.创建任务记录",
            new=AsyncMock(return_value={"task_id": "task-1"}),
        ), patch(
            "backend.api.任务接口.任务服务.统一执行任务",
            new=AsyncMock(return_value={
                "task_id": "task-1",
                "shop_id": "shop-1",
                "task_name": "登录",
                "status": "completed",
                "result": "成功",
                "error": None,
                "result_data": {"token": "ok"},
            }),
        ), patch(
            "backend.api.任务接口.流程参数服务实例.更新",
            new=AsyncMock(return_value={}),
        ) as 模拟更新, patch(
            "backend.api.任务接口.流程参数服务实例.获取步骤上下文",
            new=AsyncMock(return_value={"discount": 6}),
        ) as 模拟获取上下文, patch(
            "backend.api.任务接口.流程参数服务实例.回写步骤结果",
            new=AsyncMock(return_value={}),
        ) as 模拟回写, patch(
            "backend.api.任务接口.流程参数服务实例.更新执行状态",
            new=AsyncMock(return_value={}),
        ) as 模拟更新状态:
            响应 = 客户端.post(
                "/api/tasks/execute-internal",
                json={
                    "shop_id": "shop-1",
                    "task_name": "登录",
                    "params": {
                        "batch_id": "batch-1",
                        "step_index": 2,
                        "total_steps": 2,
                        "on_fail": "abort",
                    },
                    "flow_param_id": 99,
                },
            )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 0
        assert 响应.json()["data"]["task_id"] == "task-1"
        assert 模拟更新.await_count >= 1
        assert 模拟获取上下文.await_args.args == (99, "登录")
        assert 模拟回写.await_args.args == (99, "登录", {"token": "ok"}, 2)
        assert 模拟更新状态.await_args.args == (99, "success", None)

    def test_execute_internal_异常时返回业务错误(self, 客户端: TestClient):
        with patch(
            "backend.api.任务接口.任务服务.创建任务记录",
            new=AsyncMock(side_effect=RuntimeError("写入失败")),
        ):
            响应 = 客户端.post(
                "/api/tasks/execute-internal",
                json={
                    "shop_id": "shop-1",
                    "task_name": "登录",
                    "params": {},
                },
            )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 1
        assert "内部执行任务失败" in 响应.json()["msg"]
