"""
流程参数服务单元测试
"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.models import 数据库 as 数据库模块
from backend.services.店铺服务 import 店铺服务实例
from backend.services.流程参数服务 import 流程参数服务实例
from backend.services.流程服务 import 流程服务实例


def 运行协程(协程对象):
    事件循环 = asyncio.new_event_loop()
    try:
        return 事件循环.run_until_complete(协程对象)
    finally:
        事件循环.close()


@pytest.fixture
def 临时环境(tmp_path: Path):
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        运行协程(数据库模块.初始化数据库())
        yield 数据库文件


class 测试_流程参数服务:
    """验证 flow_params 服务层逻辑。"""

    @pytest.mark.asyncio
    async def test_初始化数据库_创建流程参数表(self, 临时环境: Path):
        with sqlite3.connect(临时环境) as 连接:
            表名集合 = {
                行[0]
                for 行 in 连接.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            assert "flow_params" in 表名集合

            字段集合 = {
                行[1]
                for 行 in 连接.execute("PRAGMA table_info(flow_params)")
            }
            assert {
                "id",
                "shop_id",
                "flow_id",
                "params",
                "step_results",
                "current_step",
                "status",
                "batch_id",
                "enabled",
                "run_count",
            }.issubset(字段集合)

    @pytest.mark.asyncio
    async def test_批量导入_获取步骤上下文_回写步骤结果(self, 临时环境: Path):
        店铺 = await 店铺服务实例.创建({"name": "流程参数店铺", "username": "flow-user", "password": "pwd"})
        流程 = await 流程服务实例.创建(
            {
                "name": "新商品链路",
                "steps": [
                    {"task": "发布相似商品", "on_fail": "abort"},
                    {"task": "限时限量", "on_fail": "abort"},
                ],
            }
        )

        CSV内容 = (
            "店铺ID,父商品ID,折扣\n"
            f"{店铺['id']},9001,6\n"
        ).encode("utf-8-sig")

        导入结果 = await 流程参数服务实例.批量导入(CSV内容, 流程["id"], file_name="flow-params.csv")
        assert 导入结果["success_count"] == 1
        assert 导入结果["failed_count"] == 0

        待执行列表 = await 流程参数服务实例.获取待执行列表(店铺["id"], 流程["id"])
        assert len(待执行列表) == 1
        记录 = 待执行列表[0]
        assert 记录["params"]["parent_product_id"] == "9001"

        await 流程参数服务实例.回写步骤结果(
            记录["id"],
            "发布相似商品",
            {"新商品ID": "new-1001", "标题": "测试标题"},
            1,
        )

        已回写记录 = await 流程参数服务实例.根据ID获取(记录["id"])
        assert 已回写记录["step_results"]["发布相似商品"]["status"] == "completed"

        上下文 = await 流程参数服务实例.获取步骤上下文(记录["id"], "限时限量")
        assert 上下文["parent_product_id"] == "9001"
        assert 上下文["discount"] == 6
        assert 上下文["新商品ID"] == "new-1001"
        assert 上下文["标题"] == "测试标题"

    @pytest.mark.asyncio
    async def test_查询同批次步骤状态与批量推进到下一步(self, 临时环境: Path):
        店铺 = await 店铺服务实例.创建({"name": "屏障店铺", "username": "barrier-user", "password": "pwd"})
        流程 = await 流程服务实例.创建(
            {
                "name": "屏障流程",
                "steps": [
                    {"task": "发布相似商品", "on_fail": "continue", "barrier": True, "merge": False},
                    {"task": "设置推广", "on_fail": "abort", "barrier": True, "merge": True},
                ],
            }
        )

        记录1 = await 流程参数服务实例.创建(
            {
                "shop_id": 店铺["id"],
                "flow_id": 流程["id"],
                "params": {"新商品ID": "1001"},
                "batch_id": "batch-1",
            }
        )
        记录2 = await 流程参数服务实例.创建(
            {
                "shop_id": 店铺["id"],
                "flow_id": 流程["id"],
                "params": {"新商品ID": "1002"},
                "batch_id": "batch-1",
            }
        )

        await 流程参数服务实例.更新步骤结果(
            记录1["id"],
            "发布相似商品",
            步骤状态="completed",
            step_index=1,
            结果字典={"新商品ID": "1001"},
        )
        await 流程参数服务实例.更新步骤结果(
            记录2["id"],
            "发布相似商品",
            步骤状态="waiting_barrier",
            step_index=0,
            当前步骤=0,
        )

        状态 = await 流程参数服务实例.查询同批次步骤状态(
            店铺["id"],
            "batch-1",
            流程["id"],
            "发布相似商品",
        )
        assert len(状态["records"]) == 2
        assert len(状态["completed_records"]) == 1
        assert len(状态["unfinished_records"]) == 1

        推进数量 = await 流程参数服务实例.批量推进到下一步([记录1["id"], 记录2["id"]])
        assert 推进数量 == 2
        推进后记录1 = await 流程参数服务实例.根据ID获取(记录1["id"])
        推进后记录2 = await 流程参数服务实例.根据ID获取(记录2["id"])
        assert 推进后记录1["current_step"] == 2
        assert 推进后记录2["current_step"] == 1

    @pytest.mark.asyncio
    async def test_获取步骤上下文_记录不存在时报错(self, 临时环境: Path):
        with pytest.raises(ValueError, match="流程参数记录不存在"):
            await 流程参数服务实例.获取步骤上下文(999, "发布相似商品")
