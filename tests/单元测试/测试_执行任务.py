"""
执行任务单元测试
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tasks.执行任务 import 执行任务 as 执行任务对象


执行任务函数 = 执行任务对象.run.__func__


class 测试_执行任务:
    """验证批次子任务的失败策略。"""

    def test_continue策略_失败后继续后续步骤(self):
        """continue 应吞掉异常，返回 continued，并保持店铺链路继续。"""
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-1", retries=0),
            retry=MagicMock(),
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务._运行异步任务", side_effect=lambda 值: 值), \
                patch("tasks.执行任务.任务服务实例.创建任务记录", new=MagicMock(return_value={"task_id": "task-log-1"})), \
                patch(
                    "tasks.执行任务.任务服务实例.统一执行任务",
                    new=MagicMock(return_value={
                        "task_id": "task-log-1",
                        "status": "failed",
                        "error": "boom",
                    }),
                ), \
                patch("tasks.执行任务.同步更新批次店铺状态") as 模拟更新批次状态:
            结果 = 执行任务函数(
                假任务对象,
                batch_id="batch-1",
                shop_id="shop-1",
                task_name="登录",
                on_fail="continue",
                step_index=1,
                total_steps=2,
            )

        assert 结果 == {
            "task_id": "task-log-1",
            "shop_id": "shop-1",
            "task_name": "登录",
            "status": "continued",
            "result": None,
            "error": "boom",
        }
        assert 模拟更新批次状态.call_args_list[0].kwargs["shop_status"] == "running"
        assert 模拟更新批次状态.call_args_list[-1].kwargs["step_status"] == "failed"
        assert 模拟更新批次状态.call_args_list[-1].kwargs["shop_status"] == "running"

    def test_abort策略_失败后抛出异常并标记失败(self):
        """abort 应标记批次失败并终止链路。"""
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-1", retries=0),
            retry=MagicMock(),
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务._运行异步任务", side_effect=lambda 值: 值), \
                patch("tasks.执行任务.任务服务实例.创建任务记录", new=MagicMock(return_value={"task_id": "task-log-2"})), \
                patch(
                    "tasks.执行任务.任务服务实例.统一执行任务",
                    new=MagicMock(return_value={
                        "task_id": "task-log-2",
                        "status": "failed",
                        "error": "boom",
                    }),
                ), \
                patch("tasks.执行任务.同步更新批次店铺状态") as 模拟更新批次状态:
            with pytest.raises(RuntimeError, match="boom"):
                执行任务函数(
                    假任务对象,
                    batch_id="batch-1",
                    shop_id="shop-1",
                    task_name="登录",
                    on_fail="abort",
                    step_index=2,
                    total_steps=2,
                )

        assert 模拟更新批次状态.call_args_list[-1].kwargs["step_status"] == "failed"
        assert 模拟更新批次状态.call_args_list[-1].kwargs["shop_status"] == "failed"

    def test_retry策略_额度内触发重试(self):
        """retry:N 在剩余次数内应调用 self.retry。"""

        class 重试信号(Exception):
            """用于中断测试流程。"""

        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-1", retries=1),
            retry=MagicMock(side_effect=重试信号("retry-called")),
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务._运行异步任务", side_effect=lambda 值: 值), \
                patch("tasks.执行任务.任务服务实例.创建任务记录", new=MagicMock(return_value={"task_id": "task-log-3"})), \
                patch(
                    "tasks.执行任务.任务服务实例.统一执行任务",
                    new=MagicMock(return_value={
                        "task_id": "task-log-3",
                        "status": "failed",
                        "error": "boom",
                    }),
                ), \
                patch("tasks.执行任务.同步更新批次店铺状态") as 模拟更新批次状态:
            with pytest.raises(重试信号, match="retry-called"):
                执行任务函数(
                    假任务对象,
                    batch_id="batch-1",
                    shop_id="shop-1",
                    task_name="登录",
                    on_fail="retry:2",
                    step_index=1,
                    total_steps=3,
                )

        假任务对象.retry.assert_called_once()
        重试参数 = 假任务对象.retry.call_args.kwargs
        assert isinstance(重试参数["exc"], RuntimeError)
        assert str(重试参数["exc"]) == "boom"
        assert 重试参数["countdown"] == 0
        assert 模拟更新批次状态.call_args_list[-1].kwargs["step_status"] == "running"
        assert 模拟更新批次状态.call_args_list[-1].kwargs["shop_status"] == "running"
        assert "boom" in 模拟更新批次状态.call_args_list[-1].kwargs["error"]

    def test_flow_param成功时回写步骤结果并更新最终状态(self):
        """flow_param_id 存在且业务成功时，应回写步骤结果并在最后一步标记 success。"""
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-2", retries=0),
            retry=MagicMock(),
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务._运行异步任务", side_effect=lambda 值: 值), \
                patch("tasks.执行任务.任务服务实例.创建任务记录", new=MagicMock(return_value={"task_id": "task-log-4"})), \
                patch(
                    "tasks.执行任务.任务服务实例.统一执行任务",
                    new=MagicMock(return_value={
                        "task_id": "task-log-4",
                        "status": "completed",
                        "result": "成功",
                        "result_data": {"新商品ID": "new-1"},
                    }),
                ) as 模拟统一执行, \
                patch("tasks.执行任务.流程参数服务实例.更新", new=MagicMock(return_value={})) as 模拟更新, \
                patch("tasks.执行任务.流程参数服务实例.获取步骤上下文", new=MagicMock(return_value={"discount": 6})) as 模拟上下文, \
                patch("tasks.执行任务.流程参数服务实例.回写步骤结果", new=MagicMock(return_value={})) as 模拟回写步骤结果, \
                patch("tasks.执行任务.流程参数服务实例.更新执行状态", new=MagicMock(return_value={})) as 模拟更新流程状态, \
                patch("tasks.执行任务.同步更新批次店铺状态") as 模拟更新批次状态:
            结果 = 执行任务函数(
                假任务对象,
                batch_id="batch-1",
                shop_id="shop-1",
                task_name="发布相似商品",
                on_fail="abort",
                step_index=2,
                total_steps=2,
                flow_param_id=88,
            )

        assert 结果["result"] == "成功"
        assert 模拟更新.call_args_list[0].args[0] == 88
        assert 模拟上下文.call_args.args == (88, "发布相似商品")
        assert 模拟统一执行.call_args.kwargs["params"]["flow_param_id"] == 88
        assert 模拟统一执行.call_args.kwargs["params"]["flow_context"] == {"discount": 6}
        assert 模拟回写步骤结果.call_args.args == (88, "发布相似商品", {"新商品ID": "new-1"}, 2)
        assert 模拟更新流程状态.call_args.args == (88, "success", None)
        模拟更新批次状态.assert_called()

    def test_flow_param失败时按策略更新流程参数状态(self):
        """flow_param_id 存在且业务失败时，应将流程参数标记为 failed。"""
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-3", retries=0),
            retry=MagicMock(),
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务._运行异步任务", side_effect=lambda 值: 值), \
                patch("tasks.执行任务.任务服务实例.创建任务记录", new=MagicMock(return_value={"task_id": "task-log-5"})), \
                patch(
                    "tasks.执行任务.任务服务实例.统一执行任务",
                    new=MagicMock(return_value={
                        "task_id": "task-log-5",
                        "status": "completed",
                        "result": "失败",
                        "error": None,
                    }),
                ), \
                patch("tasks.执行任务.流程参数服务实例.更新", new=MagicMock(return_value={})), \
                patch("tasks.执行任务.流程参数服务实例.获取步骤上下文", new=MagicMock(return_value={"discount": 6})), \
                patch("tasks.执行任务.流程参数服务实例.更新执行状态", new=MagicMock(return_value={})) as 模拟更新流程状态, \
                patch("tasks.执行任务.同步更新批次店铺状态"):
            with pytest.raises(RuntimeError, match="失败"):
                执行任务函数(
                    假任务对象,
                    batch_id="batch-1",
                    shop_id="shop-1",
                    task_name="发布相似商品",
                    on_fail="abort",
                    step_index=1,
                    total_steps=2,
                    flow_param_id=89,
                )

        assert 模拟更新流程状态.call_args_list[-1].args[:2] == (89, "failed")
