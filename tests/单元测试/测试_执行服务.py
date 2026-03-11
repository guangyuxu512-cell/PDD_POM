"""
执行服务单元测试
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch, call

import pytest

from backend.services import 执行服务 as 执行服务模块


class 假签名:
    """用于模拟 Celery signature。"""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.options = {}

    def set(self, **options):
        self.options.update(options)
        return self


class 假Celery任务:
    """用于构造批次链路中的假任务签名。"""

    @staticmethod
    def si(**kwargs):
        return 假签名(**kwargs)


class 假任务链:
    """用于记录 freeze 和 apply_async 调用顺序。"""

    def __init__(self, *任务, 调用顺序):
        self.tasks = list(任务)
        self._调用顺序 = 调用顺序

    def freeze(self):
        for 索引, 任务 in enumerate(self.tasks, start=1):
            任务.options.setdefault("task_id", f"{任务.kwargs['shop_id']}-step-{索引}")
        return self

    def apply_async(self):
        self._调用顺序.append(("apply", self.tasks[0].kwargs["shop_id"]))
        return self


class 测试_执行服务:
    """验证批次创建、校验与停止逻辑。"""

    @pytest.mark.asyncio
    async def test_创建批次_流程模式先写入状态再投递链路(self):
        """批次元数据应先落 Redis，再投递 Celery，避免 Worker 抢跑。"""
        服务 = 执行服务模块.执行服务()
        调用顺序 = []
        已写入批次 = {}
        任务链列表 = []
        步骤列表 = [
            {"task": "登录", "on_fail": "continue"},
            {"task": "采集商品", "on_fail": "abort"},
        ]

        def 假任务链工厂(*任务):
            任务链 = 假任务链(*任务, 调用顺序=调用顺序)
            任务链列表.append(任务链)
            return 任务链

        async def 假写入批次状态(批次数据):
            调用顺序.append("write")
            已写入批次.clear()
            已写入批次.update(批次数据)
            return 批次数据

        with patch.object(执行服务模块.配置实例, "AGENT_MACHINE_ID", "machine-1"), \
                patch("backend.services.执行服务.初始化任务注册表"), \
                patch("backend.services.执行服务.获取任务类", side_effect=lambda 名称: object()), \
                patch("backend.services.执行服务.店铺服务实例.根据ID获取", new=AsyncMock(side_effect=lambda 店铺ID: {"id": 店铺ID})), \
                patch("backend.services.执行服务.流程服务实例.根据ID获取", new=AsyncMock(return_value={"id": "flow-1", "steps": 步骤列表})), \
                patch("backend.services.执行服务.celery_chain", side_effect=假任务链工厂), \
                patch("tasks.执行任务.执行任务", new=假Celery任务), \
                patch.object(服务, "_写入批次状态", new=AsyncMock(side_effect=假写入批次状态)):
            结果 = await 服务.创建批次(
                flow_id="flow-1",
                task_name=None,
                shop_ids=["shop-1", "shop-2"],
                concurrency=2,
            )

        assert 结果["total"] == 2
        assert 结果["status"] == "running"
        assert 调用顺序 == ["write", ("apply", "shop-1"), ("apply", "shop-2")]
        assert len(任务链列表) == 2
        assert 已写入批次["queue_name"] == "worker.machine-1"
        assert 已写入批次["requested_concurrency"] == 2
        assert 已写入批次["shops"]["shop-1"]["task_ids"] == ["shop-1-step-1", "shop-1-step-2"]
        assert 已写入批次["shops"]["shop-2"]["task_ids"] == ["shop-2-step-1", "shop-2-step-2"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("flow_id", "task_name"),
        [
            ("flow-1", "登录"),
            (None, None),
        ],
    )
    async def test_构建步骤列表_flow_id与task_name必须二选一(self, flow_id, task_name):
        """flow_id 与 task_name 同传或都不传时应直接失败。"""
        服务 = 执行服务模块.执行服务()

        with pytest.raises(ValueError, match="二选一"):
            await 服务._构建步骤列表(flow_id=flow_id, task_name=task_name)

    @pytest.mark.asyncio
    async def test_创建批次_未注册任务返回错误(self):
        """单任务模式应在投递前拦截未注册任务。"""
        服务 = 执行服务模块.执行服务()

        with patch("backend.services.执行服务.初始化任务注册表"), \
                patch("backend.services.执行服务.获取任务类", side_effect=KeyError("missing")), \
                patch("backend.services.执行服务.店铺服务实例.根据ID获取", new=AsyncMock(return_value={"id": "shop-1"})):
            with pytest.raises(ValueError, match="任务未注册"):
                await 服务.创建批次(
                    flow_id=None,
                    task_name="不存在任务",
                    shop_ids=["shop-1"],
                    concurrency=1,
                )

    @pytest.mark.asyncio
    async def test_停止批次_撤销任务并更新批次状态(self):
        """停止批次时应撤销所有子任务，并将待运行店铺改为 stopped。"""
        服务 = 执行服务模块.执行服务()
        原始批次 = {
            "batch_id": "batch-1",
            "total": 3,
            "task_ids": ["task-1", "task-2"],
            "stopped": False,
            "shops": {
                "shop-1": {"status": "waiting", "current_task": "登录"},
                "shop-2": {"status": "running", "current_task": "采集商品"},
                "shop-3": {"status": "completed", "current_task": None},
            },
        }
        已写入批次 = {}

        async def 假写入批次状态(批次数据):
            已写入批次.clear()
            已写入批次.update(批次数据)
            return 批次数据

        with patch.object(服务, "获取最新批次状态", new=AsyncMock(return_value=原始批次.copy())), \
                patch.object(服务, "_写入批次状态", new=AsyncMock(side_effect=假写入批次状态)), \
                patch("backend.services.执行服务.celery应用.control.revoke") as 模拟撤销:
            结果 = await 服务.停止批次()

        assert 结果 == {"batch_id": "batch-1", "total": 3, "status": "stopped"}
        assert 已写入批次["stopped"] is True
        assert 已写入批次["shops"]["shop-1"]["status"] == "stopped"
        assert 已写入批次["shops"]["shop-2"]["status"] == "stopped"
        assert 已写入批次["shops"]["shop-3"]["status"] == "completed"
        模拟撤销.assert_has_calls(
            [
                call("task-1", terminate=False),
                call("task-2", terminate=False),
            ]
        )
