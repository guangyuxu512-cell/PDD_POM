"""
数据库模型单元测试
"""
import json
import sqlite3
from unittest.mock import patch

import pytest

from backend.models.定时任务模型 import 定时任务模型
from backend.models.店铺模型 import 店铺模型
from backend.models.流程模型 import 流程步骤, 流程模型


class 测试_数据库模型:
    """验证新增数据表模型与建表逻辑。"""

    def test_店铺模型_转数据库记录使用英文列名(self):
        """店铺模型应输出英文列名，保持中文属性到数据库列的映射。"""
        模型 = 店铺模型(
            店铺ID="shop-1",
            名称="演示店铺",
            账号="demo",
            状态="online",
        )

        记录 = 模型.转数据库记录()

        assert 记录["id"] == "shop-1"
        assert 记录["name"] == "演示店铺"
        assert 记录["username"] == "demo"
        assert 记录["status"] == "online"

    def test_流程模型_步骤序列化为JSON(self):
        """流程模型应将步骤序列化为 task/on_fail/barrier/merge 结构。"""
        模型 = 流程模型(
            流程ID="flow-1",
            名称="基础流程",
            步骤=[
                流程步骤(任务="登录", 失败策略="continue"),
                {"task": "采集商品", "on_fail": "retry:3"},
            ],
            描述="日常巡检流程",
        )

        记录 = 模型.转数据库记录()
        步骤列表 = json.loads(记录["steps"])

        assert 记录["id"] == "flow-1"
        assert 步骤列表 == [
            {"task": "登录", "on_fail": "continue", "barrier": False, "merge": False},
            {"task": "采集商品", "on_fail": "retry:3", "barrier": False, "merge": False},
        ]

    def test_流程步骤_非法失败策略抛出异常(self):
        """非法 on_fail 配置应被立即拒绝。"""
        with pytest.raises(ValueError, match="on_fail"):
            流程步骤(任务="登录", 失败策略="retry:abc")

    def test_定时任务模型_缺少调度规则抛出异常(self):
        """定时任务至少需要 interval_seconds 或 cron_expr 之一。"""
        with pytest.raises(ValueError, match="至少要提供一个"):
            定时任务模型(
                计划ID="schedule-1",
                名称="空计划",
                流程ID="flow-1",
                店铺ID列表=["shop-1"],
            )

    @pytest.mark.asyncio
    async def test_初始化数据库_创建流程与定时任务表(self, tmp_path):
        """数据库初始化后应创建新增数据表。"""
        from backend.models import 数据库 as 数据库模块

        临时数据库路径 = tmp_path / "ecom.db"

        with patch.object(数据库模块, "数据库路径", 临时数据库路径):
            await 数据库模块.初始化数据库()

        with sqlite3.connect(临时数据库路径) as 连接:
            表名集合 = {
                行[0]
                for 行 in 连接.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            assert {
                "shops",
                "flows",
                "execution_schedules",
                "execution_runs",
                "execution_run_items",
                "execution_run_steps",
                "task_logs",
                "operation_logs",
            }.issubset(表名集合)

            流程字段集合 = {
                行[1] for 行 in 连接.execute("PRAGMA table_info(flows)")
            }
            assert {
                "id",
                "name",
                "steps",
                "description",
                "created_at",
                "updated_at",
            }.issubset(流程字段集合)

            运行实例字段集合 = {
                行[1] for 行 in 连接.execute("PRAGMA table_info(execution_runs)")
            }
            assert {
                "id",
                "mode",
                "flow_id",
                "task_name",
                "flow_snapshot",
                "shop_ids",
                "requested_concurrency",
                "actual_concurrency",
                "status",
                "total_items",
                "created_at",
                "updated_at",
            }.issubset(运行实例字段集合)

            运行项字段集合 = {
                行[1] for 行 in 连接.execute("PRAGMA table_info(execution_run_items)")
            }
            assert {
                "id",
                "run_id",
                "shop_id",
                "context_data",
                "current_step",
                "total_steps",
                "status",
                "created_at",
                "updated_at",
            }.issubset(运行项字段集合)

            运行步骤字段集合 = {
                行[1] for 行 in 连接.execute("PRAGMA table_info(execution_run_steps)")
            }
            assert {
                "id",
                "run_item_id",
                "step_index",
                "task_name",
                "on_fail",
                "status",
                "created_at",
                "updated_at",
            }.issubset(运行步骤字段集合)

            定时任务字段集合 = {
                行[1]
                for 行 in 连接.execute("PRAGMA table_info(execution_schedules)")
            }
            assert {
                "id",
                "name",
                "flow_id",
                "shop_ids",
                "concurrency",
                "interval_seconds",
                "cron_expr",
                "overlap_policy",
                "enabled",
                "last_run_at",
                "next_run_at",
                "created_at",
                "updated_at",
            }.issubset(定时任务字段集合)
