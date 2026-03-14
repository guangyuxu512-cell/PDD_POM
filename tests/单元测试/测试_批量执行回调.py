"""
批量执行完成回调测试
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.api.执行接口 import 路由
from backend.services import 执行服务 as 执行服务模块


class 假Redis客户端:
    """用于回调测试的简化 Redis 客户端。"""

    def __init__(self, 首次标记成功: bool = True):
        self.首次标记成功 = 首次标记成功
        self.set调用列表 = []
        self.publish调用列表 = []
        self.closed = False

    def set(self, *args, **kwargs):
        self.set调用列表.append((args, kwargs))
        if kwargs.get("nx"):
            return self.首次标记成功
        return True

    def publish(self, *args, **kwargs):
        self.publish调用列表.append((args, kwargs))
        return 1

    def close(self):
        self.closed = True


@pytest.fixture
def 客户端():
    """构造仅注册执行接口的测试客户端。"""
    应用 = FastAPI(redirect_slashes=False)
    应用.include_router(路由)

    with TestClient(应用) as 测试客户端:
        yield 测试客户端


class 测试_批量执行回调:
    """验证批量执行完成回调。"""

    def test_构建批次回调载荷_失败时返回_partial_failed(self):
        """只要存在失败店铺，回调状态就应为 partial_failed。"""
        批次数据 = {
            "batch_id": "batch-1",
            "total": 2,
            "completed": 1,
            "failed": 1,
            "shops": {
                "shop-1": {
                    "shop_id": "shop-1",
                    "shop_name": "店铺一",
                    "status": "completed",
                    "last_error": None,
                },
                "shop-2": {
                    "shop_id": "shop-2",
                    "shop_name": "店铺二",
                    "status": "failed",
                    "last_error": "boom",
                },
            },
        }

        载荷 = 执行服务模块.构建批次回调载荷(批次数据)

        assert 载荷 == {
            "batch_id": "batch-1",
            "status": "partial_failed",
            "total": 2,
            "completed": 1,
            "failed": 1,
            "results": [
                {"shop_id": "shop-1", "shop_name": "店铺一", "status": "success", "error": None},
                {"shop_id": "shop-2", "shop_name": "店铺二", "status": "failed", "error": "boom"},
            ],
        }

    def test_同步写入批次状态_回调失败不影响主流程(self):
        """回调异常时仍应正常写入批次状态。"""
        假客户端 = 假Redis客户端()
        批次数据 = {
            "batch_id": "batch-1",
            "status": "completed",
            "stopped": False,
            "total": 1,
            "completed": 1,
            "failed": 0,
            "shops": {
                "shop-1": {
                    "shop_id": "shop-1",
                    "shop_name": "店铺一",
                    "status": "completed",
                    "last_error": None,
                }
            },
        }

        with patch("backend.services.执行服务.同步获取Redis客户端", return_value=假客户端), \
                patch("backend.services.执行服务.发送批次完成回调", side_effect=RuntimeError("callback failed")):
            结果 = 执行服务模块.同步写入批次状态(批次数据)

        assert 结果 is 批次数据
        assert len(假客户端.set调用列表) >= 3
        assert 假客户端.publish调用列表
        assert 假客户端.closed is True

    def test_发送批次完成回调_默认地址取Agent根地址并携带鉴权头(self):
        """默认回调应从 Agent 根地址拼出固定路径并带 X-RPA-KEY。"""
        批次数据 = {
            "batch_id": "batch-1",
            "total": 1,
            "completed": 1,
            "failed": 0,
            "shops": {
                "shop-1": {
                    "shop_id": "shop-1",
                    "shop_name": "店铺一",
                    "status": "completed",
                    "last_error": None,
                }
            },
        }
        模拟响应 = MagicMock()
        模拟响应.json.return_value = {"code": 0, "msg": "ok", "data": {"ok": True}}

        with patch.object(执行服务模块.配置实例, "AGENT_CALLBACK_URL", "http://agent-host:8001/api/task-callback"), \
                patch.object(执行服务模块.配置实例, "X_RPA_KEY", "test-rpa-key"), \
                patch("backend.services.执行服务.httpx.Client") as 模拟客户端类:
            模拟客户端 = 模拟客户端类.return_value.__enter__.return_value
            模拟客户端.post.return_value = 模拟响应

            结果 = 执行服务模块.发送批次完成回调(批次数据)

        assert 结果 is True
        模拟客户端.post.assert_called_once_with(
            "http://agent-host:8001/api/batch-callback",
            json=执行服务模块.构建批次回调载荷(批次数据),
            headers={"X-RPA-KEY": "test-rpa-key"},
        )
        模拟响应.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_创建批次_记录自定义回调地址(self):
        """创建批次时应将 callback_url 记入批次元数据。"""
        服务 = 执行服务模块.执行服务()
        已写入批次 = {}

        async def 假写入批次状态(批次数据):
            已写入批次.clear()
            已写入批次.update(批次数据)
            return 批次数据

        async def 假投递单步任务(**kwargs):
            kwargs["批次数据"]["shops"][kwargs["shop_id"]]["task_ids"].append("task-1")
            kwargs["批次数据"]["task_ids"].append("task-1")
            return {
                "task_id": "task-1",
                "signature": MagicMock(apply_async=MagicMock()),
                "batch": kwargs["批次数据"],
            }

        with patch("backend.services.执行服务.初始化任务注册表"), \
                patch("backend.services.执行服务.获取任务类", side_effect=lambda 名称: object()), \
                patch("backend.services.执行服务.店铺服务实例.根据ID获取", new=AsyncMock(return_value={"id": "shop-1", "name": "店铺一"})), \
                patch.object(服务, "投递单步任务", new=AsyncMock(side_effect=假投递单步任务)), \
                patch.object(服务, "_写入批次状态", new=AsyncMock(side_effect=假写入批次状态)):
            await 服务.创建批次(
                flow_id=None,
                task_name="登录",
                shop_ids=["shop-1"],
                concurrency=1,
                callback_url="http://agent.custom/api/batch-callback",
            )

        assert 已写入批次["callback_url"] == "http://agent.custom/api/batch-callback"

    def test_批量执行接口_透传_callback_url(self, 客户端: TestClient):
        """POST /api/execute/batch 应透传 callback_url 给服务层。"""
        with patch(
            "backend.api.执行接口.执行服务实例.创建批次",
            new=AsyncMock(return_value={"batch_id": "batch-1", "total": 1, "status": "running"}),
        ) as 模拟创建批次:
            响应 = 客户端.post(
                "/api/execute/batch",
                json={
                    "task_name": "登录",
                    "shop_ids": ["shop-1"],
                    "concurrency": 1,
                    "callback_url": "http://agent.custom/api/batch-callback",
                },
            )

        assert 响应.status_code == 200
        模拟创建批次.assert_awaited_once_with(
            flow_id=None,
            task_name="登录",
            shop_ids=["shop-1"],
            concurrency=1,
            callback_url="http://agent.custom/api/batch-callback",
        )
