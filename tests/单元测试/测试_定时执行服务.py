"""
定时执行服务单元测试
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.models import 数据库 as 数据库模块
from backend.services.店铺服务 import 店铺服务实例
from backend.services.流程服务 import 流程服务实例
from backend.services import 定时执行服务 as 定时执行服务模块


@pytest.fixture
def 临时环境(tmp_path: Path):
    """使用临时数据库和数据目录构造测试环境。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        asyncio.run(数据库模块.初始化数据库())
        yield


async def 创建基础数据() -> tuple[str, str]:
    """创建测试用店铺与流程。"""
    店铺 = await 店铺服务实例.创建({"name": "计划店铺"})
    流程 = await 流程服务实例.创建(
        {
            "name": "计划流程",
            "steps": [{"task": "登录", "on_fail": "continue"}],
        }
    )
    return 店铺["id"], 流程["id"]


class 测试_定时执行服务:
    """验证定时计划服务的 CRUD 与触发逻辑。"""

    @pytest.mark.asyncio
    async def test_创建计划_写入数据库并同步RedBeat(self, 临时环境):
        """创建计划时应入库并记录同步后的下次运行时间。"""
        服务 = 定时执行服务模块.定时执行服务()
        店铺ID, 流程ID = await 创建基础数据()
        下次运行时间 = datetime(2026, 3, 10, 12, 0, 0)

        with patch.object(服务, "_同步RedBeat计划", new=AsyncMock(return_value=下次运行时间)):
            结果 = await 服务.创建(
                {
                    "name": "每分钟巡检",
                    "flow_id": 流程ID,
                    "shop_ids": [店铺ID],
                    "concurrency": 2,
                    "interval_seconds": 60,
                    "overlap_policy": "skip",
                }
            )

        assert 结果["name"] == "每分钟巡检"
        assert 结果["flow_id"] == 流程ID
        assert 结果["shop_ids"] == [店铺ID]
        assert 结果["concurrency"] == 2
        assert 结果["enabled"] is True
        assert 结果["next_run_at"] == "2026-03-10 12:00:00"

        列表结果 = await 服务.获取全部()
        assert 列表结果["total"] == 1
        assert 列表结果["list"][0]["id"] == 结果["id"]

    @pytest.mark.asyncio
    async def test_触发计划_复用批量执行服务创建批次(self, 临时环境):
        """到点触发时应调用批量执行服务，而不是重复实现批量执行逻辑。"""
        服务 = 定时执行服务模块.定时执行服务()
        店铺ID, 流程ID = await 创建基础数据()

        with patch.object(服务, "_同步RedBeat计划", new=AsyncMock(return_value=None)):
            计划 = await 服务.创建(
                {
                    "name": "整点执行",
                    "flow_id": 流程ID,
                    "shop_ids": [店铺ID],
                    "concurrency": 2,
                    "interval_seconds": 300,
                }
            )

        with patch.object(服务, "_读取计划批次ID", new=AsyncMock(return_value=None)), \
                patch.object(服务, "_写入计划批次ID", new=AsyncMock()) as 写入计划批次ID, \
                patch(
                    "backend.services.定时执行服务.执行服务实例.创建批次",
                    new=AsyncMock(return_value={"batch_id": "batch-1", "total": 1, "status": "running"}),
                ) as 创建批次:
            结果 = await 服务.触发计划(计划["id"])

        assert 结果 == {
            "schedule_id": 计划["id"],
            "batch_id": "batch-1",
            "total": 1,
            "status": "running",
        }
        创建批次.assert_awaited_once_with(
            flow_id=流程ID,
            task_name=None,
            shop_ids=[店铺ID],
            concurrency=2,
            callback_url=None,
            input_set_id=None,
            empty_run_policy="allow_empty",
        )
        写入计划批次ID.assert_awaited_once_with(计划["id"], "batch-1")

        最新计划 = await 服务.根据ID获取(计划["id"])
        assert 最新计划 is not None
        assert 最新计划["last_run_at"] is not None
        assert 最新计划["next_run_at"] is not None

    @pytest.mark.asyncio
    async def test_创建计划_同时提供间隔和Cron返回错误(self, 临时环境):
        """interval_seconds 与 cron_expr 同传时应直接拒绝。"""
        服务 = 定时执行服务模块.定时执行服务()

        with pytest.raises(ValueError, match="不能同时提供"):
            await 服务.创建(
                {
                    "name": "冲突计划",
                    "flow_id": "flow-1",
                    "shop_ids": ["shop-1"],
                    "interval_seconds": 60,
                    "cron_expr": "* * * * *",
                }
            )

    @pytest.mark.asyncio
    async def test_触发Cron计划_运行时间使用同一时区(self, 临时环境):
        """Cron 计划触发后，last_run_at 和 next_run_at 应保持同一时区语义。"""
        服务 = 定时执行服务模块.定时执行服务()
        店铺ID, 流程ID = await 创建基础数据()

        with patch.object(服务, "_同步RedBeat计划", new=AsyncMock(return_value=None)):
            计划 = await 服务.创建(
                {
                    "name": "Cron 计划",
                    "flow_id": 流程ID,
                    "shop_ids": [店铺ID],
                    "cron_expr": "*/5 * * * *",
                }
            )

        with patch.object(服务, "_读取计划批次ID", new=AsyncMock(return_value=None)), \
                patch.object(服务, "_写入计划批次ID", new=AsyncMock()), \
                patch(
                    "backend.services.定时执行服务.执行服务实例.创建批次",
                    new=AsyncMock(return_value={"batch_id": "batch-cron", "total": 1, "status": "running"}),
                ):
            await 服务.触发计划(计划["id"])

        最新计划 = await 服务.根据ID获取(计划["id"])
        assert 最新计划 is not None
        assert 最新计划["last_run_at"] is not None
        assert 最新计划["next_run_at"] is not None

        上次运行时间 = datetime.fromisoformat(最新计划["last_run_at"])
        下次运行时间 = datetime.fromisoformat(最新计划["next_run_at"])

        assert 上次运行时间.tzinfo is not None
        assert 下次运行时间.tzinfo is not None
        assert 下次运行时间 > 上次运行时间
        assert (下次运行时间 - 上次运行时间).total_seconds() <= 300
