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
            "backend.api.任务接口.流程参数服务实例.更新步骤结果",
            new=AsyncMock(return_value={}),
        ) as 模拟更新步骤结果, patch(
            "backend.api.任务接口.流程参数服务实例.获取步骤上下文",
            new=AsyncMock(return_value={"discount": 6}),
        ) as 模拟获取上下文, patch(
            "backend.api.任务接口.任务服务.处理流程步骤执行完成",
            new=AsyncMock(return_value={}),
        ) as 模拟处理流程:
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
        assert 模拟更新步骤结果.await_count >= 1
        assert 模拟获取上下文.await_args.args == (99, "登录")
        assert 模拟处理流程.await_args.kwargs["flow_param_id"] == 99
        assert 模拟处理流程.await_args.kwargs["task_name"] == "登录"

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

    def test_execute_internal_flow_mode会读取运行上下文并在abort失败时不续投递(self, 客户端: TestClient):
        with patch(
            "backend.api.任务接口.任务服务.创建任务记录",
            new=AsyncMock(return_value={"task_id": "task-2"}),
        ), patch(
            "backend.api.任务接口.任务服务.统一执行任务",
            new=AsyncMock(return_value={
                "task_id": "task-2",
                "shop_id": "shop-1",
                "task_name": "限时限量",
                "status": "completed",
                "result": "跳过：无新商品ID",
                "error": None,
                "result_data": {},
            }),
        ) as 模拟统一执行任务, patch(
            "backend.api.任务接口.运行服务实例.获取运行项流程上下文",
            new=AsyncMock(return_value={"parent_product_id": "9001"}),
        ), patch(
            "backend.api.任务接口.运行服务实例.回写无流程参数步骤结果",
            new=AsyncMock(return_value={
                "next_step": {"task": "推广", "on_fail": "abort", "merge": False},
                "total_steps": 2,
            }),
        ) as 模拟回写步骤结果, patch(
            "backend.api.任务接口.执行服务实例.投递单步任务",
            new=AsyncMock(),
        ) as 模拟投递下一步:
            响应 = 客户端.post(
                "/api/tasks/execute-internal",
                json={
                    "shop_id": "shop-1",
                    "task_name": "限时限量",
                    "params": {
                        "batch_id": "batch-2",
                        "step_index": 1,
                        "total_steps": 2,
                        "on_fail": "abort",
                        "flow_mode": True,
                    },
                },
            )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 0
        assert 响应.json()["data"]["status"] == "failed"
        assert "跳过：无新商品ID" in 响应.json()["data"]["error"]
        assert 模拟统一执行任务.await_args.kwargs["params"]["flow_context"] == {"parent_product_id": "9001"}
        assert 模拟回写步骤结果.await_args.kwargs["run_id"] == "batch-2"
        模拟投递下一步.assert_not_called()

    def test_execute_internal_flow_mode成功后由主进程投递下一步(self, 客户端: TestClient):
        with patch(
            "backend.api.任务接口.任务服务.创建任务记录",
            new=AsyncMock(return_value={"task_id": "task-3"}),
        ), patch(
            "backend.api.任务接口.任务服务.统一执行任务",
            new=AsyncMock(return_value={
                "task_id": "task-3",
                "shop_id": "shop-1",
                "task_name": "发布相似商品",
                "status": "completed",
                "result": "成功",
                "error": None,
                "result_data": {"新商品ID": "new-1001"},
            }),
        ), patch(
            "backend.api.任务接口.运行服务实例.获取运行项流程上下文",
            new=AsyncMock(return_value={"parent_product_id": "9001"}),
        ), patch(
            "backend.api.任务接口.运行服务实例.回写无流程参数步骤结果",
            new=AsyncMock(return_value={
                "next_step": {"task": "限时限量", "on_fail": "continue", "merge": False},
                "total_steps": 2,
            }),
        ), patch(
            "backend.api.任务接口.执行服务实例.获取最新批次状态",
            new=AsyncMock(return_value={
                "batch_id": "batch-3",
                "queue_name": "worker.machine-1",
                "stopped": False,
                "shops": {
                    "shop-1": {
                        "shop_id": "shop-1",
                        "shop_name": "店铺一",
                    }
                },
            }),
        ), patch(
            "backend.api.任务接口.执行服务实例.投递单步任务",
            new=AsyncMock(return_value={"task_id": "celery-2"}),
        ) as 模拟投递下一步:
            响应 = 客户端.post(
                "/api/tasks/execute-internal",
                json={
                    "shop_id": "shop-1",
                    "task_name": "发布相似商品",
                    "params": {
                        "batch_id": "batch-3",
                        "step_index": 1,
                        "total_steps": 2,
                        "on_fail": "abort",
                        "flow_mode": True,
                    },
                },
            )

        assert 响应.status_code == 200
        assert 响应.json()["code"] == 0
        assert 响应.json()["data"]["status"] == "completed"
        assert 模拟投递下一步.await_args.kwargs == {
            "batch_id": "batch-3",
            "shop_id": "shop-1",
            "shop_name": "店铺一",
            "task_name": "限时限量",
            "on_fail": "continue",
            "step_index": 2,
            "total_steps": 2,
            "flow_mode": True,
            "merge": False,
            "queue_name": "worker.machine-1",
        }
