"""
执行任务单元测试
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tasks.执行任务 import 执行任务 as 执行任务对象


执行任务函数 = 执行任务对象.run.__func__


class 假HTTP响应:
    """用于模拟 httpx 响应。"""

    def __init__(self, 数据: dict):
        self._数据 = 数据

    def raise_for_status(self):
        return None

    def json(self):
        return self._数据


def 构造HTTP客户端上下文(响应数据: dict):
    客户端 = MagicMock()
    客户端.post.return_value = 假HTTP响应(响应数据)
    上下文 = MagicMock()
    上下文.__enter__.return_value = 客户端
    上下文.__exit__.return_value = False
    return 客户端, 上下文


class 测试_执行任务:
    """验证批次子任务的失败策略。"""

    def test_continue策略_失败后继续后续步骤(self):
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-1", retries=0),
            retry=MagicMock(),
        )
        客户端, 客户端上下文 = 构造HTTP客户端上下文(
            {
                "code": 0,
                "data": {
                    "task_id": "task-log-1",
                    "status": "failed",
                    "error": "boom",
                },
            }
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
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
        assert 客户端.post.call_args.kwargs["json"]["params"]["on_fail"] == "continue"
        assert 模拟更新批次状态.call_args_list[0].kwargs["shop_status"] == "running"
        assert 模拟更新批次状态.call_args_list[-1].kwargs["step_status"] == "failed"
        assert 模拟更新批次状态.call_args_list[-1].kwargs["shop_status"] == "running"

    def test_abort策略_失败后抛出异常并标记失败(self):
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-1", retries=0),
            retry=MagicMock(),
        )
        _, 客户端上下文 = 构造HTTP客户端上下文(
            {
                "code": 0,
                "data": {
                    "task_id": "task-log-2",
                    "status": "failed",
                    "error": "boom",
                },
            }
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
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
        class 重试信号(Exception):
            """用于中断测试流程。"""

        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-1", retries=1),
            retry=MagicMock(side_effect=重试信号("retry-called")),
        )
        _, 客户端上下文 = 构造HTTP客户端上下文(
            {
                "code": 0,
                "data": {
                    "task_id": "task-log-3",
                    "status": "failed",
                    "error": "boom",
                },
            }
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
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

    def test_flow_param会透传给内部执行接口(self):
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-2", retries=0),
            retry=MagicMock(),
        )
        客户端, 客户端上下文 = 构造HTTP客户端上下文(
            {
                "code": 0,
                "data": {
                    "task_id": "task-log-4",
                    "status": "completed",
                    "result": "成功",
                    "result_data": {"新商品ID": "new-1"},
                },
            }
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
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
        请求体 = 客户端.post.call_args.kwargs["json"]
        assert 请求体["flow_param_id"] == 88
        assert 请求体["params"]["step_index"] == 2
        assert 请求体["params"]["total_steps"] == 2
        assert 请求体["params"]["on_fail"] == "abort"
        模拟更新批次状态.assert_called()

    def test_内部接口返回业务失败时直接抛错(self):
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-3", retries=0),
            retry=MagicMock(),
        )
        _, 客户端上下文 = 构造HTTP客户端上下文(
            {
                "code": 1,
                "msg": "内部执行任务失败: boom",
                "data": None,
            }
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
                patch("tasks.执行任务.同步更新批次店铺状态"):
            with pytest.raises(RuntimeError, match="内部执行任务失败: boom"):
                执行任务函数(
                    假任务对象,
                    batch_id="batch-1",
                    shop_id="shop-1",
                    task_name="登录",
                    on_fail="abort",
                    step_index=1,
                    total_steps=1,
                )
