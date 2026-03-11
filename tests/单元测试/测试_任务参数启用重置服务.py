"""
任务参数启用/禁用/重置服务测试
"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.models import 数据库 as 数据库模块
from backend.services.任务参数服务 import 任务参数服务实例
from backend.services.店铺服务 import 店铺服务实例


def 运行协程(协程对象):
    """使用独立事件循环执行协程，避免测试间 loop 污染。"""
    事件循环 = asyncio.new_event_loop()
    try:
        return 事件循环.run_until_complete(协程对象)
    finally:
        事件循环.close()


@pytest.fixture
def 临时环境(tmp_path: Path):
    """创建独立数据库环境。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        运行协程(数据库模块.初始化数据库())
        yield 数据库文件


class 测试_任务参数启用重置服务:
    """验证 enabled、run_count、批量操作与发布次数展开。"""

    @pytest.mark.asyncio
    async def test_初始化数据库_旧版task_params补齐新字段(self, tmp_path: Path):
        """旧表结构升级后应自动补齐 enabled 与 run_count 字段。"""
        数据库文件 = tmp_path / "legacy.db"

        with sqlite3.connect(数据库文件) as 连接:
            连接.execute(
                """
                CREATE TABLE task_params (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    params TEXT DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'pending',
                    result TEXT DEFAULT '{}',
                    error TEXT,
                    batch_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            连接.commit()

        with patch.object(数据库模块, "数据库路径", 数据库文件):
            await 数据库模块.初始化数据库()

        with sqlite3.connect(数据库文件) as 连接:
            字段集合 = {
                行[1]
                for 行 in 连接.execute("PRAGMA table_info(task_params)")
            }

        assert "enabled" in 字段集合
        assert "run_count" in 字段集合

    @pytest.mark.asyncio
    async def test_获取待执行列表_跳过禁用记录并累计执行次数(self, 临时环境: Path):
        """待执行查询只返回启用记录，执行成功后 run_count 增加。"""
        店铺 = await 店铺服务实例.创建({"name": "启用店铺", "username": "svc-enabled", "password": "pwd"})
        店铺ID = 店铺["id"]

        可执行记录 = await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "1001"},
                "enabled": True,
            }
        )
        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "1002"},
                "enabled": False,
            }
        )
        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "1003"},
                "status": "running",
            }
        )

        待执行列表 = await 任务参数服务实例.获取待执行列表(店铺ID, "发布相似商品")
        assert [记录["id"] for 记录 in 待执行列表] == [可执行记录["id"]]

        运行中记录 = await 任务参数服务实例.更新执行结果(可执行记录["id"], "running")
        assert 运行中记录 is not None
        assert 运行中记录["run_count"] == 0

        成功记录 = await 任务参数服务实例.更新执行结果(
            可执行记录["id"],
            "success",
            结果={"goods_id": "new-1001"},
        )
        assert 成功记录 is not None
        assert 成功记录["status"] == "success"
        assert 成功记录["run_count"] == 1
        assert 成功记录["result"]["goods_id"] == "new-1001"

    @pytest.mark.asyncio
    async def test_单条与批量操作_保留参数并按条件处理(self, 临时环境: Path):
        """重置不应修改 params/enabled，批量启用禁用和批量重置应按条件生效。"""
        店铺 = await 店铺服务实例.创建({"name": "批量店铺", "username": "svc-batch", "password": "pwd"})
        店铺ID = 店铺["id"]

        成功记录 = await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "2001"},
                "status": "success",
                "result": {"goods_id": "sku-1"},
                "enabled": False,
                "run_count": 3,
            }
        )
        失败记录 = await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "2002"},
                "status": "failed",
                "error": "上传失败",
                "enabled": False,
            }
        )
        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "2003"},
                "status": "pending",
                "enabled": False,
            }
        )

        重置后 = await 任务参数服务实例.重置(失败记录["id"])
        assert 重置后 is not None
        assert 重置后["status"] == "pending"
        assert 重置后["result"] == {}
        assert 重置后["error"] is None
        assert 重置后["enabled"] is False
        assert 重置后["params"]["parent_product_id"] == "2002"

        批量启用数量 = await 任务参数服务实例.批量启用(
            shop_id=店铺ID,
            task_name="发布相似商品",
            status="pending",
        )
        assert 批量启用数量 == 2

        批量禁用数量 = await 任务参数服务实例.批量禁用(
            shop_id=店铺ID,
            task_name="发布相似商品",
            status="pending",
        )
        assert 批量禁用数量 == 2

        批量重置数量 = await 任务参数服务实例.批量重置(
            shop_id=店铺ID,
            task_name="发布相似商品",
        )
        assert 批量重置数量 == 1

        重置成功记录 = await 任务参数服务实例.根据ID获取(成功记录["id"])
        assert 重置成功记录 is not None
        assert 重置成功记录["status"] == "pending"
        assert 重置成功记录["enabled"] is False
        assert 重置成功记录["run_count"] == 3
        assert 重置成功记录["params"]["parent_product_id"] == "2001"

    @pytest.mark.asyncio
    async def test_批量导入_发布次数展开为多条记录(self, 临时环境: Path):
        """发布次数列应把单行展开为多条记录，并写入 batch_index。"""
        店铺 = await 店铺服务实例.创建({"name": "展开店铺", "username": "svc-expand", "password": "pwd"})
        店铺ID = 店铺["id"]
        CSV内容 = (
            "店铺ID,父商品ID,新标题,发布次数\n"
            f"{店铺ID},3001,展开标题,3\n"
            f"{店铺ID},3002,单条标题,\n"
        ).encode("utf-8-sig")

        结果 = await 任务参数服务实例.批量导入(CSV内容, "发布相似商品")

        assert 结果["success_count"] == 4
        assert 结果["failed_count"] == 0

        列表 = await 任务参数服务实例.分页查询(task_name="发布相似商品", shop_id=店铺ID)
        assert 列表["total"] == 4

        展开批次 = sorted(
            记录["params"].get("batch_index")
            for 记录 in 列表["list"]
            if 记录["params"].get("parent_product_id") == "3001"
        )
        assert 展开批次 == [1, 2, 3]
        assert any(
            记录["params"].get("parent_product_id") == "3002" and "batch_index" not in 记录["params"]
            for 记录 in 列表["list"]
        )

    @pytest.mark.asyncio
    async def test_批量导入_非法发布次数应记录失败(self, 临时环境: Path):
        """发布次数非法时不应中断导入，且应返回明确错误。"""
        店铺 = await 店铺服务实例.创建({"name": "错误店铺", "username": "svc-error", "password": "pwd"})
        店铺ID = 店铺["id"]
        CSV内容 = (
            "店铺ID,父商品ID,新标题,发布次数\n"
            f"{店铺ID},4001,坏数据,0\n"
        ).encode("utf-8-sig")

        结果 = await 任务参数服务实例.批量导入(CSV内容, "发布相似商品")

        assert 结果["success_count"] == 0
        assert 结果["failed_count"] == 1
        assert "发布次数必须大于 0" in 结果["errors"][0]
