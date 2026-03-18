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


def 构造Celery签名():
    签名 = MagicMock()
    签名.set.return_value = 签名
    return 签名


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
        下一步签名 = 构造Celery签名()
        批次状态 = {
            "queue_name": "worker.machine-1",
            "shops": {
                "shop-1": {
                    "steps": [
                        {"task": "登录", "on_fail": "continue", "merge": False},
                        {"task": "采集商品", "on_fail": "abort", "merge": True},
                    ]
                }
            },
        }

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
                patch("tasks.执行任务.同步更新批次店铺状态") as 模拟更新批次状态, \
                patch("tasks.执行任务.同步读取批次状态", return_value=批次状态), \
                patch("tasks.执行任务.同步检查取消标记", return_value=False), \
                patch.object(执行任务对象, "si", return_value=下一步签名) as 模拟投递下一步:
            结果 = 执行任务函数(
                假任务对象,
                batch_id="batch-1",
                shop_id="shop-1",
                shop_name="店铺A",
                task_name="登录",
                on_fail="continue",
                step_index=1,
                total_steps=2,
            )

        assert 结果 == {
            "task_id": "task-log-1",
            "shop_id": "shop-1",
            "shop_name": "店铺A",
            "task_name": "登录",
            "status": "continued",
            "result": None,
            "error": "boom",
        }
        assert 客户端.post.call_args.kwargs["json"]["params"]["on_fail"] == "continue"
        assert 模拟更新批次状态.call_args_list[0].kwargs["shop_status"] == "running"
        assert 模拟更新批次状态.call_args_list[-1].kwargs["step_status"] == "failed"
        assert 模拟更新批次状态.call_args_list[-1].kwargs["shop_status"] == "running"
        assert 模拟投递下一步.call_args.kwargs == {
            "batch_id": "batch-1",
            "shop_id": "shop-1",
            "shop_name": "店铺A",
            "task_name": "采集商品",
            "on_fail": "abort",
            "step_index": 2,
            "total_steps": 2,
            "merge": True,
        }
        下一步签名.set.assert_called_once_with(queue="worker.machine-1", routing_key="worker.machine-1")
        下一步签名.apply_async.assert_called_once()

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
        assert 请求体["params"]["flow_param_ids"] == [88]
        assert 请求体["params"]["merge"] is False
        assert 请求体["params"]["step_index"] == 2
        assert 请求体["params"]["total_steps"] == 2
        assert 请求体["params"]["on_fail"] == "abort"
        模拟更新批次状态.assert_called()

    def test_flow_param_ids会透传给内部执行接口(self):
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-4", retries=0),
            retry=MagicMock(),
        )
        客户端, 客户端上下文 = 构造HTTP客户端上下文(
            {
                "code": 0,
                "data": {
                    "task_id": "task-log-5",
                    "status": "completed",
                    "result": "成功",
                    "result_data": {"处理数量": 2},
                },
            }
        )
        下一步签名 = 构造Celery签名()
        批次状态 = {
            "queue_name": "worker.machine-2",
            "shops": {
                "shop-1": {
                    "steps": [
                        {"task": "登录", "on_fail": "abort", "merge": False},
                        {"task": "限时限量", "on_fail": "continue", "merge": False},
                        {"task": "设置推广", "on_fail": "abort", "merge": True},
                    ]
                }
            },
        }

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
                patch("tasks.执行任务.同步更新批次店铺状态"), \
                patch("tasks.执行任务.同步读取批次状态", return_value=批次状态), \
                patch("tasks.执行任务.同步检查取消标记", return_value=False), \
                patch.object(执行任务对象, "si", return_value=下一步签名) as 模拟投递下一步:
            执行任务函数(
                假任务对象,
                batch_id="batch-1",
                shop_id="shop-1",
                task_name="限时限量",
                on_fail="continue",
                step_index=2,
                total_steps=3,
                flow_param_ids=[11, 12],
                merge=False,
            )

        请求体 = 客户端.post.call_args.kwargs["json"]
        assert "flow_param_id" not in 请求体
        assert 请求体["params"]["flow_param_ids"] == [11, 12]
        assert 请求体["params"]["merge"] is False
        assert 模拟投递下一步.call_args.kwargs == {
            "batch_id": "batch-1",
            "shop_id": "shop-1",
            "shop_name": None,
            "task_name": "设置推广",
            "on_fail": "abort",
            "step_index": 3,
            "total_steps": 3,
            "merge": True,
            "flow_param_ids": [11, 12],
        }
        下一步签名.set.assert_called_once_with(queue="worker.machine-2", routing_key="worker.machine-2")
        下一步签名.apply_async.assert_called_once()

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

    def test_HTTP返回后检测到取消标记则返回cancelled(self):
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-5", retries=0),
            retry=MagicMock(),
        )
        _, 客户端上下文 = 构造HTTP客户端上下文(
            {
                "code": 0,
                "data": {
                    "task_id": "task-log-6",
                    "status": "completed",
                    "result": "成功",
                },
            }
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
                patch("tasks.执行任务.同步检查取消标记", return_value=True), \
                patch("tasks.执行任务.同步更新批次店铺状态") as 模拟更新批次状态:
            结果 = 执行任务函数(
                假任务对象,
                batch_id="batch-1",
                shop_id="shop-1",
                task_name="登录",
                on_fail="abort",
                step_index=1,
                total_steps=1,
            )

        assert 结果 == {
            "status": "cancelled",
            "shop_id": "shop-1",
            "task_name": "登录",
            "error": "用户手动停止",
        }
        assert 模拟更新批次状态.call_args.kwargs["shop_status"] == "stopped"

    def test_批次已停止时不投递下一步(self):
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-6", retries=0),
            retry=MagicMock(),
        )
        _, 客户端上下文 = 构造HTTP客户端上下文(
            {
                "code": 0,
                "data": {
                    "task_id": "task-log-7",
                    "status": "completed",
                    "result": "成功",
                },
            }
        )

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
                patch("tasks.执行任务.同步读取批次状态", return_value={"stopped": True, "shops": {"shop-1": {"steps": [{"task": "登录"}, {"task": "采集商品"}]}}}), \
                patch("tasks.执行任务.同步检查取消标记", return_value=False), \
                patch("tasks.执行任务.同步更新批次店铺状态"), \
                patch.object(执行任务对象, "si") as 模拟投递下一步:
            结果 = 执行任务函数(
                假任务对象,
                batch_id="batch-1",
                shop_id="shop-1",
                task_name="登录",
                on_fail="abort",
                step_index=1,
                total_steps=2,
            )

        assert 结果["status"] == "completed"
        模拟投递下一步.assert_not_called()
