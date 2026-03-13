"""
创建后续任务测试
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


class 测试_创建后续任务:
    """验证按单条成功记录创建下一步任务。"""

    @pytest.mark.asyncio
    async def test_创建后续任务_继承源参数并合并执行结果(self, 临时环境: Path):
        店铺 = await 店铺服务实例.创建({"name": "链路店铺", "username": "chain-user", "password": "pwd"})
        源记录 = await 任务参数服务实例.创建(
            {
                "shop_id": 店铺["id"],
                "task_name": "发布相似商品",
                "params": {
                    "discount": 6,
                    "roi": 2.5,
                    "parent_product_id": "9001",
                },
                "status": "success",
                "batch_id": "batch-chain",
            }
        )

        新记录 = await 任务参数服务实例.创建后续任务(
            源记录=源记录,
            执行结果={"新商品ID": "new-1001", "标题": "测试标题"},
            下一步任务名="限时限量",
        )

        assert 新记录 is not None
        assert 新记录["task_name"] == "限时限量"
        assert 新记录["status"] == "pending"
        assert 新记录["batch_id"] == "batch-chain"
        assert 新记录["params"] == {
            "discount": 6,
            "roi": 2.5,
            "parent_product_id": "9001",
            "新商品ID": "new-1001",
            "标题": "测试标题",
            "source_task_param_id": 源记录["id"],
            "batch_id": "batch-chain",
        }

    @pytest.mark.asyncio
    async def test_创建后续任务_同一源记录保持幂等(self, 临时环境: Path):
        店铺 = await 店铺服务实例.创建({"name": "幂等链路店铺", "username": "idem-chain", "password": "pwd"})
        源记录 = await 任务参数服务实例.创建(
            {
                "shop_id": 店铺["id"],
                "task_name": "发布相似商品",
                "params": {"discount": 7},
                "status": "success",
            }
        )

        第一次 = await 任务参数服务实例.创建后续任务(
            源记录=源记录,
            执行结果={"新商品ID": "new-1002"},
            下一步任务名="限时限量",
        )
        第二次 = await 任务参数服务实例.创建后续任务(
            源记录=源记录,
            执行结果={"新商品ID": "new-1002"},
            下一步任务名="限时限量",
        )

        assert 第一次 is not None
        assert 第二次 is not None
        assert 第一次["id"] == 第二次["id"]
        列表 = await 任务参数服务实例.分页查询(task_name="限时限量", shop_id=店铺["id"])
        assert 列表["total"] == 1

    @pytest.mark.asyncio
    async def test_创建后续任务_缺少源记录ID时报错(self, 临时环境: Path):
        店铺 = await 店铺服务实例.创建({"name": "异常链路店铺", "username": "bad-chain", "password": "pwd"})

        with pytest.raises(ValueError, match="源记录缺少 id"):
            await 任务参数服务实例.创建后续任务(
                源记录={"shop_id": 店铺["id"], "params": {"discount": 6}},
                执行结果={"新商品ID": "new-1003"},
                下一步任务名="限时限量",
            )
