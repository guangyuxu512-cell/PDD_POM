"""
批次完成后自动创建限时限量记录测试
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


class 测试_批次完成后自动创建限时限量:
    """验证发布相似商品批次完成后的后续任务创建逻辑。"""

    @pytest.mark.asyncio
    async def test_批次完成后创建后续任务_满足条件时创建一条限时限量(self, 临时环境: Path):
        店铺 = await 店铺服务实例.创建({"name": "后续任务店铺", "username": "follow-up", "password": "pwd"})
        店铺ID = 店铺["id"]

        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "9001", "discount": 6},
                "status": "success",
                "result": {"new_product_id": "new-1"},
                "batch_id": "batch-auto",
            }
        )
        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "9002", "discount": 6},
                "status": "failed",
                "result": {},
                "batch_id": "batch-auto",
            }
        )

        创建数量 = await 任务参数服务实例.批次完成后创建后续任务("batch-auto")

        assert 创建数量 == 1
        列表 = await 任务参数服务实例.分页查询(task_name="限时限量", batch_id="batch-auto")
        assert 列表["total"] == 1
        记录 = 列表["list"][0]
        assert 记录["shop_id"] == 店铺ID
        assert 记录["status"] == "pending"
        assert 记录["params"] == {"batch_id": "batch-auto", "折扣": 6}

    @pytest.mark.asyncio
    async def test_批次完成后创建后续任务_存在未完成记录时跳过(self, 临时环境: Path):
        店铺 = await 店铺服务实例.创建({"name": "未完成批次店铺", "username": "pending-shop", "password": "pwd"})
        店铺ID = 店铺["id"]

        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "9001", "discount": 6},
                "status": "success",
                "result": {"new_product_id": "new-1"},
                "batch_id": "batch-pending",
            }
        )
        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "9002", "discount": 6},
                "status": "pending",
                "result": {},
                "batch_id": "batch-pending",
            }
        )

        创建数量 = await 任务参数服务实例.批次完成后创建后续任务("batch-pending")

        assert 创建数量 == 0
        列表 = await 任务参数服务实例.分页查询(task_name="限时限量", batch_id="batch-pending")
        assert 列表["total"] == 0

    @pytest.mark.asyncio
    async def test_批次完成后创建后续任务_重复调用保持幂等(self, 临时环境: Path):
        店铺 = await 店铺服务实例.创建({"name": "幂等批次店铺", "username": "idem-shop", "password": "pwd"})
        店铺ID = 店铺["id"]

        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "9001", "折扣": 7},
                "status": "success",
                "result": {"new_product_id": "new-1"},
                "batch_id": "batch-idem",
            }
        )

        第一次 = await 任务参数服务实例.批次完成后创建后续任务("batch-idem")
        第二次 = await 任务参数服务实例.批次完成后创建后续任务("batch-idem")

        assert 第一次 == 1
        assert 第二次 == 0
        列表 = await 任务参数服务实例.分页查询(task_name="限时限量", batch_id="batch-idem")
        assert 列表["total"] == 1
