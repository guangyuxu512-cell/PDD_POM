"""
任务参数服务批次成功记录测试
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.models import 数据库 as 数据库模块
from backend.services.任务参数服务 import 任务参数服务实例
from backend.services.店铺服务 import 店铺服务实例


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


class 测试_任务参数批次成功记录:
    """验证按批次查询成功记录。"""

    @pytest.mark.asyncio
    async def test_查询批次成功记录_只返回成功结果JSON(self, 临时环境: Path):
        店铺 = await 店铺服务实例.创建({"name": "批次成功店铺", "username": "svc-limit", "password": "pwd"})
        店铺ID = 店铺["id"]

        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "9001"},
                "status": "success",
                "result": {"new_product_id": "new-1"},
                "batch_id": "batch-limit",
            }
        )
        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "9002"},
                "status": "failed",
                "result": {"new_product_id": "new-2"},
                "batch_id": "batch-limit",
            }
        )
        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布换图商品",
                "params": {"parent_product_id": "9003"},
                "status": "success",
                "result": {"new_product_id": "new-3"},
                "batch_id": "batch-limit",
            }
        )

        结果列表 = await 任务参数服务实例.查询批次成功记录(
            店铺ID,
            "batch-limit",
            "发布相似商品",
        )

        assert 结果列表 == [{"new_product_id": "new-1"}]

    @pytest.mark.asyncio
    async def test_查询批次成功记录_无记录时返回空列表(self, 临时环境: Path):
        店铺 = await 店铺服务实例.创建({"name": "空批次店铺", "username": "svc-empty", "password": "pwd"})

        结果列表 = await 任务参数服务实例.查询批次成功记录(
            店铺["id"],
            "missing-batch",
            "发布相似商品",
        )

        assert 结果列表 == []
