"""
执行接口单元测试
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.执行接口 import 路由


@pytest.fixture
def 客户端():
    """构造仅注册执行接口的测试客户端。"""
    应用 = FastAPI(redirect_slashes=False)
    应用.include_router(路由)

    with TestClient(应用) as 测试客户端:
        yield 测试客户端


class 测试_执行接口:
    """验证批量执行 REST 与 SSE 行为。"""

    def test_批量执行接口_返回统一成功响应(self, 客户端: TestClient):
        """POST /api/execute/batch 应返回标准成功结构。"""
        with patch(
            "backend.api.执行接口.执行服务实例.创建批次",
            new=AsyncMock(return_value={"batch_id": "batch-1", "total": 2, "status": "running"}),
        ):
            响应 = 客户端.post(
                "/api/execute/batch",
                json={
                    "task_name": "登录",
                    "shop_ids": ["shop-1", "shop-2"],
                    "concurrency": 2,
                },
            )

        assert 响应.status_code == 200
        assert 响应.json() == {
            "code": 0,
            "msg": "ok",
            "data": {
                "batch_id": "batch-1",
                "total": 2,
                "status": "running",
            },
        }

    def test_执行状态流_输出SSE事件(self, 客户端: TestClient):
        """GET /api/execute/status 应输出可消费的 SSE 数据。"""

        async def 假订阅批次状态(batch_id=None):
            yield {
                "batch_id": batch_id or "batch-1",
                "total": 1,
                "completed": 0,
                "running": 1,
                "waiting": 0,
                "failed": 0,
                "shops": {
                    "shop-1": {
                        "status": "running",
                        "current_task": "登录",
                        "current_step": 1,
                    }
                },
            }

        with patch("backend.api.执行接口.执行服务实例.订阅批次状态", new=假订阅批次状态):
            with 客户端.stream("GET", "/api/execute/status?batch_id=batch-1") as 响应:
                片段列表 = list(响应.iter_text())

        assert 响应.status_code == 200
        assert 响应.headers["content-type"].startswith("text/event-stream")
        assert any("data:" in 片段 for 片段 in 片段列表)
        assert any('"batch_id": "batch-1"' in 片段 for 片段 in 片段列表)
