"""
运行服务单元测试
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.models import 数据库 as 数据库模块
from backend.services.店铺服务 import 店铺服务实例
from backend.services.流程服务 import 流程服务实例
from backend.services.执行服务 import 执行服务, 同步写入运行实例状态
from backend.services.运行服务 import 运行服务实例


@pytest.fixture
def 临时环境(tmp_path: Path):
    """使用临时数据库和数据目录构造测试环境。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        asyncio.run(数据库模块.初始化数据库())
        yield


async def 创建运行样本() -> tuple[str, str]:
    """创建店铺与流程基础数据。"""
    店铺 = await 店铺服务实例.创建({"name": "运行店铺"})
    流程 = await 流程服务实例.创建(
        {
            "name": "运行流程",
            "steps": [
                {"task": "登录", "on_fail": "abort"},
                {"task": "限时限量", "on_fail": "abort"},
            ],
        }
    )
    return 店铺["id"], 流程["id"]


class 测试_运行服务:
    """验证运行实例状态查询与同步。"""

    @pytest.mark.asyncio
    async def test_同步运行实例状态后可查询运行详情_运行项_步骤(self, 临时环境):
        店铺ID, 流程ID = await 创建运行样本()
        服务 = 执行服务()
        run_id = "run-sync-1"
        步骤模板 = [
            {"task": "登录", "on_fail": "abort", "barrier": False, "merge": False},
            {"task": "限时限量", "on_fail": "abort", "barrier": False, "merge": False},
        ]

        await 服务._写入运行实例快照(
            run_id=run_id,
            flow_id=流程ID,
            task_name=None,
            shop_ids=[店铺ID],
            步骤模板=步骤模板,
            concurrency=1,
            callback_url=None,
            流程参数记录映射={店铺ID: []},
        )

        已同步 = 同步写入运行实例状态(
            {
                "batch_id": run_id,
                "status": "completed",
                "stopped": False,
                "total": 1,
                "waiting": 0,
                "running": 0,
                "completed": 1,
                "failed": 0,
                "shops": {
                    店铺ID: {
                        "shop_id": 店铺ID,
                        "shop_name": "运行店铺",
                        "status": "completed",
                        "current_task": None,
                        "current_step": 2,
                        "total_steps": 2,
                        "last_error": None,
                        "last_result": "成功",
                        "steps": [
                            {
                                "task": "登录",
                                "on_fail": "abort",
                                "barrier": False,
                                "merge": False,
                                "status": "completed",
                                "error": None,
                                "result": "成功",
                            },
                            {
                                "task": "限时限量",
                                "on_fail": "abort",
                                "barrier": False,
                                "merge": False,
                                "status": "completed",
                                "error": None,
                                "result": "成功",
                            },
                        ],
                    }
                },
            }
        )

        assert 已同步 is True

        运行 = await 运行服务实例.根据ID获取(run_id)
        assert 运行 is not None
        assert 运行["status"] == "completed"
        assert 运行["success_items"] == 1
        assert 运行["shop_ids"] == [店铺ID]

        运行项列表 = await 运行服务实例.获取运行项列表(run_id)
        assert 运行项列表["total"] == 1
        assert 运行项列表["list"][0]["status"] == "success"
        assert 运行项列表["list"][0]["result_data"]["result"] == "成功"

        步骤列表 = await 运行服务实例.获取运行步骤列表(run_id)
        assert 步骤列表["total"] == 2
        assert 步骤列表["list"][0]["status"] == "success"
        assert 步骤列表["list"][0]["result_data"]["result"] == "成功"
        assert 步骤列表["list"][1]["status"] == "success"

    def test_同步运行实例状态_运行不存在时返回False(self, 临时环境):
        已同步 = 同步写入运行实例状态(
            {
                "batch_id": "missing-run",
                "status": "running",
                "shops": {},
            }
        )

        assert 已同步 is False

    @pytest.mark.asyncio
    async def test_回写无流程参数步骤结果会累积_flow_context_并返回下一步(self, 临时环境):
        店铺ID, 流程ID = await 创建运行样本()
        服务 = 执行服务()
        run_id = "run-flow-context-1"
        步骤模板 = [
            {"task": "发布相似商品", "on_fail": "abort", "barrier": False, "merge": False},
            {"task": "限时限量", "on_fail": "continue", "barrier": False, "merge": False},
        ]

        await 服务._写入运行实例快照(
            run_id=run_id,
            flow_id=流程ID,
            task_name=None,
            shop_ids=[店铺ID],
            步骤模板=步骤模板,
            concurrency=1,
            callback_url=None,
            流程参数记录映射={店铺ID: []},
        )

        推进结果 = await 运行服务实例.回写无流程参数步骤结果(
            run_id=run_id,
            shop_id=店铺ID,
            task_name="发布相似商品",
            step_index=1,
            请求参数={"flow_mode": True, "flow_context": {"parent_product_id": "9001"}},
            执行结果={
                "status": "completed",
                "result": "成功",
                "result_data": {"新商品ID": "new-1001"},
                "error": None,
            },
        )

        assert 推进结果 is not None
        assert 推进结果["flow_context"] == {
            "parent_product_id": "9001",
            "新商品ID": "new-1001",
        }
        assert 推进结果["next_step"] == {
            "task": "限时限量",
            "on_fail": "continue",
            "barrier": False,
            "merge": False,
        }

        运行项 = await 运行服务实例.获取运行项(run_id, 店铺ID)
        assert 运行项 is not None
        assert 运行项["current_step"] == 1
        assert 运行项["context_data"]["flow_context"] == {
            "parent_product_id": "9001",
            "新商品ID": "new-1001",
        }

        步骤列表 = await 运行服务实例.获取运行步骤列表(run_id)
        assert 步骤列表["list"][0]["params_snapshot"]["flow_context"] == {"parent_product_id": "9001"}
        assert 步骤列表["list"][0]["result_data"] == {"新商品ID": "new-1001"}

    @pytest.mark.asyncio
    async def test_回写无流程参数步骤结果_失败时不污染已有_flow_context(self, 临时环境):
        店铺ID, 流程ID = await 创建运行样本()
        服务 = 执行服务()
        run_id = "run-flow-context-2"
        步骤模板 = [
            {"task": "发布相似商品", "on_fail": "abort", "barrier": False, "merge": False},
            {"task": "限时限量", "on_fail": "continue", "barrier": False, "merge": False},
        ]

        await 服务._写入运行实例快照(
            run_id=run_id,
            flow_id=流程ID,
            task_name=None,
            shop_ids=[店铺ID],
            步骤模板=步骤模板,
            concurrency=1,
            callback_url=None,
            流程参数记录映射={店铺ID: []},
        )

        await 运行服务实例.回写无流程参数步骤结果(
            run_id=run_id,
            shop_id=店铺ID,
            task_name="发布相似商品",
            step_index=1,
            请求参数={"flow_mode": True, "flow_context": {"parent_product_id": "9001"}},
            执行结果={
                "status": "failed",
                "result": None,
                "result_data": {"新商品ID": "new-1001"},
                "error": "boom",
            },
        )

        运行项 = await 运行服务实例.获取运行项(run_id, 店铺ID)
        assert 运行项 is not None
        assert 运行项["context_data"]["flow_context"] == {"parent_product_id": "9001"}
