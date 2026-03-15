"""
任务服务健壮性测试
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.任务服务 import 任务服务实例


class 假管理器:
    """用于任务服务测试的假浏览器管理器"""

    def __init__(self):
        self.实例集 = {"shop-1": {"page": object()}}

    def 获取页面(self, 店铺ID: str):
        return object()


class 测试_任务服务:
    """测试统一执行任务的超时兜底"""

    @pytest.mark.asyncio
    async def test_执行任务_发布相似商品自动注入首条待执行参数并回填成功(self):
        """发布相似商品任务应读取首条 pending 参数，并在成功后回填 success。"""
        假任务实例 = SimpleNamespace(
            _执行结果={"new_product_id": "new-1001", "parent_product_id": "916453776556"},
            执行=AsyncMock(return_value="成功"),
        )
        店铺配置 = {"shop_id": "8eec98e4-89b9-49d5-ab1f-c72be3c405f6", "username": "demo", "password": "pwd"}

        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[
                {"id": 11, "params": {"parent_product_id": "916453776556", "new_title": "测试标题"}},
                {"id": 12, "params": {"parent_product_id": "916453776557"}},
            ]),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ) as 模拟回填, patch(
            "tasks.任务注册表.获取任务",
            return_value=假任务实例,
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="8eec98e4-89b9-49d5-ab1f-c72be3c405f6",
                task_name="发布相似商品",
                页面=object(),
                店铺配置=店铺配置,
            )

        assert 结果["result"] == "成功"
        假任务实例.执行.assert_awaited_once()
        assert 店铺配置["task_param"] == {
            "parent_product_id": "916453776556",
            "new_title": "测试标题",
            "task_param_id": 11,
        }
        assert 模拟回填.await_count == 2
        assert 模拟回填.await_args_list[0].args[:2] == (11, "running")
        assert 模拟回填.await_args_list[1].args[:2] == (11, "success")
        assert 模拟回填.await_args_list[1].kwargs["结果"]["new_product_id"] == "new-1001"

    @pytest.mark.asyncio
    async def test_执行任务_发布换图商品无待执行参数时跳过(self):
        """没有 pending 任务参数时，应上报并跳过，不实例化任务。"""
        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[]),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ) as 模拟回填, patch(
            "browser.任务回调.上报",
            new=AsyncMock(),
        ) as 模拟上报, patch(
            "tasks.任务注册表.获取任务",
            new=MagicMock(),
        ) as 模拟获取任务:
            结果 = await 任务服务实例.执行任务(
                shop_id="8eec98e4-89b9-49d5-ab1f-c72be3c405f6",
                task_name="发布换图商品",
                页面=object(),
                店铺配置={"shop_id": "8eec98e4-89b9-49d5-ab1f-c72be3c405f6"},
            )

        assert 结果["result"] == "跳过"
        模拟上报.assert_awaited_once_with("没有待执行的任务参数", "8eec98e4-89b9-49d5-ab1f-c72be3c405f6")
        模拟获取任务.assert_not_called()
        模拟回填.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_执行任务_发布相似商品失败时回填失败信息(self):
        """发布任务返回失败时，应将 task_params 回填为 failed。"""
        假任务实例 = SimpleNamespace(
            _执行结果={"parent_product_id": "916453776556"},
            执行=AsyncMock(return_value="失败"),
        )

        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[
                {"id": 21, "params": {"parent_product_id": "916453776556"}},
            ]),
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ) as 模拟回填, patch(
            "tasks.任务注册表.获取任务",
            return_value=假任务实例,
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="8eec98e4-89b9-49d5-ab1f-c72be3c405f6",
                task_name="发布相似商品",
                页面=object(),
                店铺配置={"shop_id": "8eec98e4-89b9-49d5-ab1f-c72be3c405f6"},
            )

        assert 结果["result"] == "失败"
        assert 模拟回填.await_count == 2
        assert 模拟回填.await_args_list[1].args[:2] == (21, "failed")
        assert 模拟回填.await_args_list[1].kwargs["错误信息"] == "失败"

    @pytest.mark.asyncio
    async def test_执行任务_flow_context存在时直接透传不读取task_params(self):
        """flow_context 已注入时，应直接作为 task_param 使用而不再查询 task_params。"""
        假任务实例 = SimpleNamespace(
            _执行结果={"new_product_id": "new-2001"},
            执行=AsyncMock(return_value="成功"),
        )
        店铺配置 = {
            "shop_id": "shop-1",
            "username": "demo",
            "password": "pwd",
            "flow_context": {"parent_product_id": "9001", "discount": 6},
        }

        with patch(
            "backend.services.任务服务.任务参数服务实例.获取待执行列表",
            new=AsyncMock(return_value=[]),
        ) as 模拟获取待执行, patch(
            "tasks.任务注册表.获取任务",
            return_value=假任务实例,
        ), patch(
            "backend.services.任务服务.任务参数服务实例.更新执行结果",
            new=AsyncMock(),
        ) as 模拟回填:
            结果 = await 任务服务实例.执行任务(
                shop_id="shop-1",
                task_name="发布相似商品",
                页面=object(),
                店铺配置=店铺配置,
            )

        assert 结果["result"] == "成功"
        assert 店铺配置["task_param"] == {"parent_product_id": "9001", "discount": 6}
        模拟获取待执行.assert_not_awaited()
        模拟回填.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_执行任务_收到取消信号时直接返回_cancelled(self):
        假任务实例 = SimpleNamespace(
            _执行结果={},
            执行=AsyncMock(return_value="成功"),
        )

        with patch(
            "backend.services.执行服务.检查取消标记",
            new=AsyncMock(return_value=True),
        ), patch(
            "tasks.任务注册表.获取任务",
            return_value=假任务实例,
        ) as 模拟获取任务:
            结果 = await 任务服务实例.执行任务(
                shop_id="shop-1",
                task_name="登录",
                页面=object(),
                店铺配置={"shop_id": "shop-1", "batch_id": "batch-cancel"},
            )

        assert 结果["status"] == "cancelled"
        assert 结果["error"] == "用户手动停止"
        模拟获取任务.assert_not_called()

    @pytest.mark.asyncio
    async def test_执行任务_flow_param_ids_barrier模式复用同一页面循环执行(self):
        """多条 flow_params 的 barrier-only 模式应在同一页面内循环执行。"""
        任务一 = SimpleNamespace(
            _执行结果={"新商品ID": "new-1001"},
            执行=AsyncMock(return_value="成功"),
        )
        任务二 = SimpleNamespace(
            _执行结果={"新商品ID": "new-1002"},
            执行=AsyncMock(return_value="成功"),
        )
        页面对象 = object()
        店铺配置 = {
            "shop_id": "shop-1",
            "username": "demo",
            "password": "pwd",
            "flow_param_ids": [101, 102],
            "step_index": 2,
            "total_steps": 3,
            "on_fail": "continue",
            "batch_id": "batch-1",
        }

        with patch(
            "backend.services.流程参数服务.流程参数服务实例.更新",
            new=AsyncMock(return_value={}),
        ), patch(
            "backend.services.流程参数服务.流程参数服务实例.更新步骤结果",
            new=AsyncMock(return_value={}),
        ), patch(
            "backend.services.流程参数服务.流程参数服务实例.获取步骤上下文",
            new=AsyncMock(side_effect=[
                {"parent_product_id": "9001", "discount": 6},
                {"parent_product_id": "9002", "discount": 7},
            ]),
        ) as 模拟获取上下文, patch(
            "backend.services.任务服务.任务服务实例.处理流程步骤执行完成",
            new=AsyncMock(),
        ) as 模拟处理流程, patch(
            "backend.services.任务服务.asyncio.sleep",
            new=AsyncMock(),
        ) as 模拟睡眠, patch(
            "tasks.任务注册表.获取任务",
            side_effect=[任务一, 任务二],
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="shop-1",
                task_name="发布相似商品",
                页面=页面对象,
                店铺配置=店铺配置,
            )

        assert 结果["result"] == "成功"
        assert 任务一.执行.await_args.args[0] is 页面对象
        assert 任务二.执行.await_args.args[0] is 页面对象
        assert 模拟获取上下文.await_args_list[0].args == (101, "发布相似商品")
        assert 模拟获取上下文.await_args_list[1].args == (102, "发布相似商品")
        assert 模拟处理流程.await_count == 2
        模拟睡眠.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_执行任务_flow_param_ids_收到取消后不再继续下一条(self):
        任务一 = SimpleNamespace(
            _执行结果={"新商品ID": "new-1001"},
            执行=AsyncMock(return_value="成功"),
        )
        页面对象 = object()
        店铺配置 = {
            "shop_id": "shop-1",
            "username": "demo",
            "password": "pwd",
            "flow_param_ids": [101, 102],
            "step_index": 2,
            "total_steps": 3,
            "on_fail": "continue",
            "batch_id": "batch-1",
        }

        with patch(
            "backend.services.执行服务.检查取消标记",
            new=AsyncMock(side_effect=[False, False, False, True]),
        ), patch(
            "backend.services.流程参数服务.流程参数服务实例.更新",
            new=AsyncMock(return_value={}),
        ), patch(
            "backend.services.流程参数服务.流程参数服务实例.更新步骤结果",
            new=AsyncMock(return_value={}),
        ), patch(
            "backend.services.流程参数服务.流程参数服务实例.获取步骤上下文",
            new=AsyncMock(return_value={"parent_product_id": "9001", "discount": 6}),
        ), patch(
            "backend.services.任务服务.任务服务实例.处理流程步骤执行完成",
            new=AsyncMock(),
        ) as 模拟处理流程, patch(
            "backend.services.任务服务.asyncio.sleep",
            new=AsyncMock(),
        ) as 模拟睡眠, patch(
            "tasks.任务注册表.获取任务",
            return_value=任务一,
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="shop-1",
                task_name="发布相似商品",
                页面=页面对象,
                店铺配置=店铺配置,
            )

        assert 结果["status"] == "cancelled"
        任务一.执行.assert_awaited_once()
        模拟处理流程.assert_awaited_once()
        模拟睡眠.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_执行任务_flow_param_ids_merge模式只执行一次(self):
        """merge 模式应合并参数后只调用一次任务执行。"""
        合并任务 = SimpleNamespace(
            _执行结果={"成功列表": ["1001", "1002"]},
            执行=AsyncMock(return_value="成功"),
        )
        店铺配置 = {
            "shop_id": "shop-1",
            "username": "demo",
            "password": "pwd",
            "flow_param_ids": [201, 202],
            "merge": True,
            "step_index": 3,
            "total_steps": 4,
            "on_fail": "continue",
            "batch_id": "batch-merge",
        }

        with patch(
            "backend.services.流程参数服务.流程参数服务实例.根据ID获取",
            new=AsyncMock(side_effect=[
                {"id": 201, "step_results": {}, "shop_id": "shop-1"},
                {"id": 202, "step_results": {}, "shop_id": "shop-1"},
            ]),
        ), patch(
            "backend.services.流程参数服务.流程参数服务实例.更新",
            new=AsyncMock(return_value={}),
        ), patch(
            "backend.services.流程参数服务.流程参数服务实例.更新步骤结果",
            new=AsyncMock(return_value={}),
        ), patch(
            "backend.services.任务服务.任务服务实例._构建合并参数",
            new=AsyncMock(return_value={
                "商品ID列表": ["1001", "1002"],
                "商品参数映射": {
                    "1001": {"flow_param_id": 201, "投产比": 5.0},
                    "1002": {"flow_param_id": 202, "投产比": 6.0},
                },
            }),
        ) as 模拟构建合并参数, patch(
            "backend.services.任务服务.任务服务实例._标记合并跳过",
            new=AsyncMock(),
        ) as 模拟标记跳过, patch(
            "backend.services.任务服务.任务服务实例.处理流程步骤执行完成",
            new=AsyncMock(),
        ) as 模拟处理流程, patch(
            "tasks.任务注册表.获取任务",
            return_value=合并任务,
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="shop-1",
                task_name="设置推广",
                页面=object(),
                店铺配置=店铺配置,
            )

        assert 结果["result"] == "成功"
        合并任务.执行.assert_awaited_once()
        模拟构建合并参数.assert_awaited_once()
        模拟标记跳过.assert_awaited_once_with(202, "设置推广", 3, 201)
        assert 模拟处理流程.await_args.kwargs["flow_param_id"] == 201

    @pytest.mark.asyncio
    async def test_执行任务_flow_param_ids_abort时后续记录标记失败(self):
        """barrier-only 模式下首条失败且 on_fail=abort 时，后续记录不再执行。"""
        失败任务 = SimpleNamespace(
            _执行结果={"error": "boom"},
            执行=AsyncMock(return_value="失败"),
        )
        店铺配置 = {
            "shop_id": "shop-1",
            "username": "demo",
            "password": "pwd",
            "flow_param_ids": [301, 302],
            "step_index": 2,
            "total_steps": 3,
            "on_fail": "abort",
            "batch_id": "batch-stop",
        }

        with patch(
            "backend.services.流程参数服务.流程参数服务实例.更新",
            new=AsyncMock(return_value={}),
        ) as 模拟更新, patch(
            "backend.services.流程参数服务.流程参数服务实例.更新步骤结果",
            new=AsyncMock(return_value={}),
        ) as 模拟更新步骤结果, patch(
            "backend.services.流程参数服务.流程参数服务实例.更新执行状态",
            new=AsyncMock(return_value={}),
        ) as 模拟更新执行状态, patch(
            "backend.services.流程参数服务.流程参数服务实例.获取步骤上下文",
            new=AsyncMock(return_value={"parent_product_id": "9001"}),
        ), patch(
            "backend.services.任务服务.任务服务实例.处理流程步骤执行完成",
            new=AsyncMock(),
        ) as 模拟处理流程, patch(
            "backend.services.任务服务.asyncio.sleep",
            new=AsyncMock(),
        ) as 模拟睡眠, patch(
            "tasks.任务注册表.获取任务",
            return_value=失败任务,
        ):
            结果 = await 任务服务实例.执行任务(
                shop_id="shop-1",
                task_name="发布相似商品",
                页面=object(),
                店铺配置=店铺配置,
            )

        assert 结果["result"] == "失败"
        失败任务.执行.assert_awaited_once()
        assert 模拟处理流程.await_count == 1
        模拟更新执行状态.assert_awaited_once()
        assert any("前序记录失败，按 on_fail 终止" in str(调用.kwargs.get("错误信息", "")) for 调用 in 模拟更新步骤结果.await_args_list)
        模拟睡眠.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_统一执行任务_浏览器初始化超时返回失败(self):
        """浏览器初始化超时时，应返回 failed 而不是抛出异常给上层"""
        with patch("backend.services.任务服务.任务服务实例.更新任务状态", new=AsyncMock()) as 模拟更新任务状态, \
                patch("backend.services.店铺服务.店铺服务实例.更新", new=AsyncMock()) as 模拟更新店铺状态, \
                patch("backend.services.浏览器服务.确保已初始化", new=AsyncMock(side_effect=asyncio.TimeoutError())), \
                patch("backend.services.浏览器服务.管理器实例", None):
            结果 = await 任务服务实例.统一执行任务(
                task_id="task-1",
                shop_id="shop-1",
                task_name="登录",
                params=None,
                来源="test"
            )

        assert 结果["status"] == "failed"
        assert "浏览器初始化超时" in 结果["error"]
        assert 模拟更新任务状态.await_count >= 2
        模拟更新店铺状态.assert_awaited()

    @pytest.mark.asyncio
    async def test_统一执行任务_执行前检测到取消则写为_cancelled(self):
        with patch("backend.services.任务服务.任务服务实例.更新任务状态", new=AsyncMock()) as 模拟更新任务状态, \
                patch("backend.services.店铺服务.店铺服务实例.根据ID获取完整信息", new=AsyncMock(return_value={
                    "id": "shop-1",
                    "name": "测试店铺",
                    "username": "demo",
                    "password": "pwd",
                })), \
                patch("backend.services.浏览器服务.确保已初始化", new=AsyncMock()), \
                patch("backend.services.浏览器服务.获取当前管理器实例", return_value=假管理器()), \
                patch("backend.services.执行服务.检查取消标记", new=AsyncMock(return_value=True)), \
                patch("backend.services.任务服务.任务服务实例._确保页面可用", new=AsyncMock(return_value=object())), \
                patch("backend.services.任务服务.任务服务实例.执行任务", new=AsyncMock(return_value={"result": "成功", "result_data": {}})) as 模拟执行任务:
            结果 = await 任务服务实例.统一执行任务(
                task_id="task-1",
                shop_id="shop-1",
                task_name="发布相似商品",
                params={"batch_id": "batch-1"},
                来源="test",
            )

        assert 结果["status"] == "cancelled"
        assert 结果["error"] == "用户手动停止"
        assert 模拟更新任务状态.await_args_list[-1].args[1] == "cancelled"
        模拟执行任务.assert_not_awaited()
