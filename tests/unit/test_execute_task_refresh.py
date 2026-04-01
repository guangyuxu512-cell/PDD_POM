"""
执行任务前刷新 Celery 配置测试
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tasks.execute_task import 执行任务 as 执行任务对象


执行任务函数 = 执行任务对象.run.__func__


class 测试_执行任务刷新配置:
    def test_执行任务_初始化后先刷新Celery配置(self):
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-refresh-1", retries=0),
            retry=MagicMock(),
        )
        调用顺序: list[str] = []

        with patch(
            "tasks.execute_task.初始化Worker环境",
            side_effect=lambda: 调用顺序.append("初始化Worker环境"),
        ), patch(
            "tasks.execute_task.刷新Celery配置",
            side_effect=lambda: 调用顺序.append("刷新Celery配置"),
        ), patch(
            "tasks.execute_task.获取任务类",
            side_effect=lambda _: 调用顺序.append("获取任务类"),
        ), patch(
            "tasks.execute_task._调用主进程执行",
            return_value={"task_id": "task-1", "status": "completed", "result": "成功"},
        ):
            返回结果 = 执行任务函数(
                假任务对象,
                batch_id="",
                shop_id="shop-1",
                task_name="登录",
                on_fail="abort",
                step_index=1,
                total_steps=1,
            )

        assert 返回结果["status"] == "completed"
        assert 调用顺序[:3] == ["初始化Worker环境", "刷新Celery配置", "获取任务类"]
