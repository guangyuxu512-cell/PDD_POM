"""
执行服务单元测试
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from backend.services import 执行服务 as 执行服务模块


class 假签名:
    """用于记录单步任务的 apply_async 调用。"""

    def __init__(self, task_id: str, 调用顺序: list[object]):
        self.task_id = task_id
        self._调用顺序 = 调用顺序

    def apply_async(self):
        self._调用顺序.append(("apply", self.task_id))
        return self


class 测试_执行服务:
    """验证批次创建、校验与停止逻辑。"""

    @pytest.mark.asyncio
    async def test_创建批次_流程模式先写入状态再投递首步任务(self):
        """批次元数据应先落 Redis，再投递首步任务，且同店铺全部 flow_params 都会纳入批次。"""
        服务 = 执行服务模块.执行服务()
        调用顺序: list[object] = []
        已写入批次 = {}
        投递调用列表: list[dict[str, object]] = []

        async def 假投递单步任务(**kwargs):
            投递调用列表.append(kwargs)
            记录标识 = kwargs.get("flow_param_ids") or [kwargs.get("flow_param_id") or kwargs["task_name"]]
            task_id = f"{kwargs['shop_id']}-{'-'.join(str(标识) for 标识 in 记录标识)}"
            kwargs["批次数据"]["shops"][kwargs["shop_id"]]["task_ids"].append(task_id)
            kwargs["批次数据"]["task_ids"].append(task_id)
            return {
                "task_id": task_id,
                "signature": 假签名(task_id, 调用顺序),
                "batch": kwargs["批次数据"],
            }

        async def 假写入批次状态(批次数据):
            调用顺序.append("write")
            已写入批次.clear()
            已写入批次.update(批次数据)
            return 批次数据

        with patch.object(执行服务模块.配置实例, "AGENT_MACHINE_ID", "machine-1"), \
                patch("backend.services.执行服务.初始化任务注册表"), \
                patch("backend.services.执行服务.获取任务类", side_effect=lambda 名称: object()), \
                patch("backend.services.执行服务.店铺服务实例.根据ID获取", new=AsyncMock(side_effect=lambda 店铺ID: {"id": 店铺ID})), \
                patch(
                    "backend.services.执行服务.流程服务实例.根据ID获取",
                    new=AsyncMock(
                        return_value={
                            "id": "flow-1",
                            "steps": [
                                {"task": "发布相似商品", "on_fail": "continue", "barrier": True, "merge": False},
                                {"task": "限时限量", "on_fail": "abort", "barrier": True, "merge": False},
                            ],
                        }
                    ),
                ), \
                patch(
                    "backend.services.执行服务.流程参数服务实例.获取待执行列表",
                    new=AsyncMock(
                        side_effect=[
                            [{"id": 101}, {"id": 102}],
                            [{"id": 201}],
                        ]
                    ),
                ), \
                patch("backend.services.执行服务.流程参数服务实例.更新", new=AsyncMock()) as 模拟更新流程参数, \
                patch.object(服务, "_写入运行实例快照", new=AsyncMock()), \
                patch.object(服务, "投递单步任务", new=AsyncMock(side_effect=假投递单步任务)), \
                patch.object(服务, "_写入批次状态", new=AsyncMock(side_effect=假写入批次状态)):
            结果 = await 服务.创建批次(
                flow_id="flow-1",
                task_name=None,
                shop_ids=["shop-1", "shop-2"],
                concurrency=2,
            )

        assert 结果["total"] == 2
        assert 结果["status"] == "running"
        assert 调用顺序 == [
            "write",
            ("apply", "shop-1-101-102"),
            ("apply", "shop-2-201"),
        ]
        assert 已写入批次["queue_name"] == "worker.machine-1"
        assert 已写入批次["requested_concurrency"] == 2
        assert 已写入批次["shops"]["shop-1"]["task_ids"] == ["shop-1-101-102"]
        assert 已写入批次["shops"]["shop-2"]["task_ids"] == ["shop-2-201"]
        assert 投递调用列表[0]["flow_param_ids"] == [101, 102]
        assert 投递调用列表[0]["flow_mode"] is True
        assert 投递调用列表[0]["merge"] is False
        assert 投递调用列表[1]["flow_param_ids"] == [201]
        assert 投递调用列表[1]["flow_mode"] is True
        assert 模拟更新流程参数.await_count == 3

    @pytest.mark.asyncio
    async def test_创建批次_流程模式无待执行流程参数时仍创建空上下文任务(self):
        """flow 模式下，即使某店铺没有 flow_params，也应创建批次并投递首步任务。"""
        服务 = 执行服务模块.执行服务()
        已写入批次 = {}
        投递调用列表 = []

        async def 假投递单步任务(**kwargs):
            投递调用列表.append(kwargs)
            kwargs["批次数据"]["shops"][kwargs["shop_id"]]["task_ids"].append("task-1")
            kwargs["批次数据"]["task_ids"].append("task-1")
            return {
                "task_id": "task-1",
                "signature": 假签名("task-1", []),
                "batch": kwargs["批次数据"],
            }

        async def 假写入批次状态(批次数据):
            已写入批次.clear()
            已写入批次.update(批次数据)
            return 批次数据

        with patch.object(执行服务模块.配置实例, "AGENT_MACHINE_ID", "machine-1"), \
                patch("backend.services.执行服务.初始化任务注册表"), \
                patch("backend.services.执行服务.获取任务类", side_effect=lambda 名称: object()), \
                patch("backend.services.执行服务.店铺服务实例.根据ID获取", new=AsyncMock(side_effect=lambda 店铺ID: {"id": 店铺ID})), \
                patch(
                    "backend.services.执行服务.流程服务实例.根据ID获取",
                    new=AsyncMock(return_value={"id": "flow-1", "steps": [{"task": "登录", "on_fail": "abort"}]}),
                ), \
                patch(
                    "backend.services.执行服务.流程参数服务实例.获取待执行列表",
                    new=AsyncMock(side_effect=[[{"id": 201}], []]),
                ), \
                patch("backend.services.执行服务.流程参数服务实例.更新", new=AsyncMock()), \
                patch.object(服务, "_写入运行实例快照", new=AsyncMock()), \
                patch.object(服务, "投递单步任务", new=AsyncMock(side_effect=假投递单步任务)), \
                patch.object(服务, "_写入批次状态", new=AsyncMock(side_effect=假写入批次状态)):
            结果 = await 服务.创建批次(
                flow_id="flow-1",
                task_name=None,
                shop_ids=["shop-1", "shop-2"],
                concurrency=1,
            )

        assert 结果["total"] == 2
        assert list(已写入批次["shops"].keys()) == ["shop-1", "shop-2"]
        assert 投递调用列表[0]["flow_param_id"] == 201
        assert 投递调用列表[0]["flow_mode"] is True
        assert "flow_param_id" not in 投递调用列表[1]
        assert 投递调用列表[1]["flow_mode"] is True

    @pytest.mark.asyncio
    async def test_创建批次_输入集模式会透传_input_set_id_并创建兼容流程参数(self):
        """指定 input_set_id 时，应写入运行快照并基于输入行生成兼容 flow_params。"""
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
                "signature": 假签名("task-1", []),
                "batch": kwargs["批次数据"],
            }

        with patch.object(执行服务模块.配置实例, "AGENT_MACHINE_ID", "machine-1"), \
                patch("backend.services.执行服务.店铺服务实例.根据ID获取", new=AsyncMock(return_value={"id": "shop-1", "name": "店铺一"})), \
                patch.object(
                    服务,
                    "_构建步骤列表",
                    new=AsyncMock(return_value=[{"task": "发布相似商品", "on_fail": "abort", "barrier": False, "merge": False}]),
                ), \
                patch.object(
                    服务,
                    "_获取流程输入行映射",
                    new=AsyncMock(return_value={
                        "shop-1": [
                            {
                                "id": 11,
                                "shop_id": "shop-1",
                                "input_data": {"parent_product_id": "9001"},
                            }
                        ]
                    }),
                ), \
                patch.object(
                    服务,
                    "_创建输入集兼容流程参数",
                    new=AsyncMock(return_value={"shop-1": [{"id": 301, "input_row_id": 11}]}),
                ), \
                patch("backend.services.执行服务.流程参数服务实例.更新", new=AsyncMock()), \
                patch.object(服务, "_写入运行实例快照", new=AsyncMock()) as 模拟写入快照, \
                patch.object(服务, "投递单步任务", new=AsyncMock(side_effect=假投递单步任务)), \
                patch.object(服务, "_写入批次状态", new=AsyncMock(side_effect=假写入批次状态)):
            结果 = await 服务.创建批次(
                flow_id="flow-1",
                task_name=None,
                shop_ids=["shop-1"],
                concurrency=1,
                input_set_id="input-set-1",
            )

        assert 结果["status"] == "running"
        assert 已写入批次["input_set_id"] == "input-set-1"
        assert 模拟写入快照.await_args.kwargs["input_set_id"] == "input-set-1"
        assert 模拟写入快照.await_args.kwargs["运行项上下文映射"]["shop-1"]["input_row_id"] == 11
        assert 模拟写入快照.await_args.kwargs["运行项上下文映射"]["shop-1"]["flow_param_ids"] == [301]

    @pytest.mark.asyncio
    async def test_创建批次_require_input缺少输入时直接报错(self):
        """当空运行策略为 require_input 且店铺没有输入数据时，应拒绝启动。"""
        服务 = 执行服务模块.执行服务()

        with patch("backend.services.执行服务.店铺服务实例.根据ID获取", new=AsyncMock(return_value={"id": "shop-1"})), \
                patch.object(
                    服务,
                    "_构建步骤列表",
                    new=AsyncMock(return_value=[{"task": "发布相似商品", "on_fail": "abort", "barrier": False, "merge": False}]),
                ), \
                patch.object(服务, "_获取流程输入行映射", new=AsyncMock(return_value={"shop-1": []})), \
                patch.object(服务, "_创建输入集兼容流程参数", new=AsyncMock(return_value={"shop-1": []})), \
                patch(
                    "backend.services.执行服务.获取任务元数据",
                    side_effect=lambda 名称: {
                        "requires_input": 名称 == "发布相似商品",
                        "required_fields": ["parent_product_id"] if 名称 == "发布相似商品" else [],
                        "supports_empty_context": 名称 != "发布相似商品",
                    },
                ):
            with pytest.raises(ValueError, match="缺少输入数据"):
                await 服务.创建批次(
                    flow_id="flow-1",
                    task_name=None,
                    shop_ids=["shop-1"],
                    concurrency=1,
                    input_set_id="input-set-1",
                    empty_run_policy="require_input",
                )

    @pytest.mark.asyncio
    async def test_预检流程_输入缺字段时返回失败项(self):
        """预检应明确指出缺少的必填字段。"""
        服务 = 执行服务模块.执行服务()

        with patch("backend.services.执行服务.店铺服务实例.根据ID获取", new=AsyncMock(return_value={"id": "shop-1"})), \
                patch.object(
                    服务,
                    "_构建步骤列表",
                    new=AsyncMock(return_value=[{"task": "发布相似商品", "on_fail": "abort", "barrier": False, "merge": False}]),
                ), \
                patch.object(
                    服务,
                    "_获取流程输入行映射",
                    new=AsyncMock(return_value={"shop-1": [{"id": 11, "shop_id": "shop-1", "input_data": {}}]}),
                ), \
                patch(
                    "backend.services.执行服务.获取任务元数据",
                    return_value={
                        "requires_input": True,
                        "required_fields": ["parent_product_id"],
                        "supports_empty_context": False,
                    },
                ):
            结果 = await 服务.预检流程(
                flow_id="flow-1",
                shop_ids=["shop-1"],
                input_set_id="input-set-1",
            )

        assert 结果["ok"] is False
        assert 结果["summary"]["failed_items"] == 1
        assert 结果["items"][0]["input_row_id"] == 11
        assert "parent_product_id" in str(结果["items"][0]["error"])

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
                patch("backend.services.执行服务.设置取消标记", new=AsyncMock(return_value=True)) as 模拟设置取消标记, \
                patch("backend.services.执行服务.celery应用.control.revoke") as 模拟撤销:
            结果 = await 服务.停止批次()

        assert 结果 == {"batch_id": "batch-1", "total": 3, "status": "stopped"}
        assert 已写入批次["stopped"] is True
        assert 已写入批次["shops"]["shop-1"]["status"] == "stopped"
        assert 已写入批次["shops"]["shop-2"]["status"] == "stopped"
        assert 已写入批次["shops"]["shop-3"]["status"] == "completed"
        模拟设置取消标记.assert_awaited_once_with("batch-1")
        模拟撤销.assert_has_calls(
            [
                call("task-1", terminate=False),
                call("task-2", terminate=False),
            ]
        )
