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
