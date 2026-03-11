"""
任务参数服务单元测试
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
    """使用独立事件循环执行协程，避免与全局 loop 状态冲突。"""
    事件循环 = asyncio.new_event_loop()
    try:
        return 事件循环.run_until_complete(协程对象)
    finally:
        事件循环.close()


@pytest.fixture
def 临时环境(tmp_path: Path):
    """构造任务参数服务测试所需的临时数据库和数据目录。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        运行协程(数据库模块.初始化数据库())
        yield 数据库文件


class 测试_任务参数服务:
    """验证 task_params 服务层逻辑。"""

    @pytest.mark.asyncio
    async def test_初始化数据库_创建任务参数表(self, 临时环境: Path):
        """数据库初始化后应创建 task_params 表及核心字段。"""
        with sqlite3.connect(临时环境) as 连接:
            表名集合 = {
                行[0]
                for 行 in 连接.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            assert "task_params" in 表名集合

            字段集合 = {
                行[1]
                for 行 in 连接.execute("PRAGMA table_info(task_params)")
            }
            assert {
                "id",
                "shop_id",
                "task_name",
                "params",
                "status",
                "result",
                "error",
                "batch_id",
                "created_at",
                "updated_at",
            }.issubset(字段集合)

    @pytest.mark.asyncio
    async def test_获取待执行列表与更新执行结果(self, 临时环境: Path):
        """待执行查询和结果回填应按状态生效。"""
        店铺 = await 店铺服务实例.创建({"name": "服务店铺", "username": "svc", "password": "pwd"})
        店铺ID = 店铺["id"]

        记录1 = await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "5001"},
            }
        )
        await 任务参数服务实例.创建(
            {
                "shop_id": 店铺ID,
                "task_name": "发布相似商品",
                "params": {"parent_product_id": "5002"},
                "status": "running",
            }
        )

        待执行列表 = await 任务参数服务实例.获取待执行列表(店铺ID, "发布相似商品")
        assert len(待执行列表) == 1
        assert 待执行列表[0]["id"] == 记录1["id"]

        更新后 = await 任务参数服务实例.更新执行结果(
            记录1["id"],
            "failed",
            结果={"step": "upload"},
            错误信息="上传失败",
        )
        assert 更新后 is not None
        assert 更新后["status"] == "failed"
        assert 更新后["result"]["step"] == "upload"
        assert 更新后["error"] == "上传失败"

        再次待执行列表 = await 任务参数服务实例.获取待执行列表(店铺ID, "发布相似商品")
        assert 再次待执行列表 == []

    @pytest.mark.asyncio
    async def test_批量导入_发布换图商品支持可选字段(self, 临时环境: Path):
        """发布换图商品 CSV 导入应正确映射 image_path，并允许 new_title 留空。"""
        店铺 = await 店铺服务实例.创建({"name": "换图店铺", "username": "svc2", "password": "pwd"})
        店铺ID = 店铺["id"]
        CSV内容 = (
            "店铺ID,父商品ID,新标题,图片路径\n"
            f"{店铺ID},7001,,E:/images/demo.png\n"
        ).encode("utf-8-sig")

        结果 = await 任务参数服务实例.批量导入(CSV内容, "发布换图商品")

        assert 结果["success_count"] == 1
        assert 结果["failed_count"] == 0

        列表 = await 任务参数服务实例.分页查询(task_name="发布换图商品")
        assert 列表["total"] == 1
        参数 = 列表["list"][0]["params"]
        assert 参数["parent_product_id"] == "7001"
        assert 参数["image_path"] == "E:/images/demo.png"
        assert "new_title" not in 参数

    @pytest.mark.asyncio
    async def test_批量导入_支持按店铺名称匹配(self, 临时环境: Path):
        """CSV 中填写店铺名称时，应自动匹配到对应店铺 ID。"""
        店铺 = await 店铺服务实例.创建({"name": "名称匹配店铺", "username": "svc3", "password": "pwd"})
        店铺ID = 店铺["id"]
        CSV内容 = (
            "店铺ID,父商品ID,新标题\n"
            "名称匹配店铺,8001,按名称导入\n"
        ).encode("utf-8-sig")

        结果 = await 任务参数服务实例.批量导入(CSV内容, "发布相似商品")

        assert 结果["success_count"] == 1
        assert 结果["failed_count"] == 0

        列表 = await 任务参数服务实例.分页查询(task_name="发布相似商品")
        assert 列表["total"] == 1
        assert 列表["list"][0]["shop_id"] == 店铺ID
        assert 列表["list"][0]["shop_name"] == "名称匹配店铺"

    @pytest.mark.asyncio
    async def test_批量导入_店铺名称不存在时跳过并记录原因(self, 临时环境: Path):
        """未知店铺名称不应中断导入，应记录错误并跳过该行。"""
        CSV内容 = (
            "店铺ID,父商品ID,新标题\n"
            "不存在的店铺,9001,坏数据\n"
        ).encode("utf-8-sig")

        结果 = await 任务参数服务实例.批量导入(CSV内容, "发布相似商品")

        assert 结果["success_count"] == 0
        assert 结果["failed_count"] == 1
        assert "店铺名称未找到" in 结果["errors"][0]

    @pytest.mark.asyncio
    async def test_批量导入_支持utf8无BOM编码(self, 临时环境: Path):
        """UTF-8 无 BOM 的 CSV 仍应正常导入。"""
        店铺 = await 店铺服务实例.创建({"name": "UTF8店铺", "username": "svc4", "password": "pwd"})
        店铺ID = 店铺["id"]
        CSV内容 = (
            "店铺ID,父商品ID,新标题\n"
            f"{店铺ID},8101,UTF8标题\n"
        ).encode("utf-8")

        结果 = await 任务参数服务实例.批量导入(CSV内容, "发布相似商品")

        assert 结果["success_count"] == 1
        assert 结果["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_批量导入_支持GBK编码(self, 临时环境: Path):
        """GBK 编码的 CSV 应能正常解析并导入。"""
        店铺 = await 店铺服务实例.创建({"name": "GBK店铺", "username": "svc5", "password": "pwd"})
        店铺ID = 店铺["id"]
        CSV内容 = (
            "店铺ID,父商品ID,新标题\n"
            f"{店铺ID},8201,国标编码标题\n"
        ).encode("gbk")

        结果 = await 任务参数服务实例.批量导入(CSV内容, "发布相似商品")

        assert 结果["success_count"] == 1
        assert 结果["failed_count"] == 0

        列表 = await 任务参数服务实例.分页查询(task_name="发布相似商品")
        标题集合 = {记录["params"].get("new_title") for 记录 in 列表["list"]}
        assert "国标编码标题" in 标题集合

    @pytest.mark.asyncio
    async def test_批量导入_科学计数法商品ID自动还原(self, 临时环境: Path):
        """父商品ID为科学计数法时，应自动转换为完整数字字符串。"""
        店铺 = await 店铺服务实例.创建({"name": "科学计数店铺", "username": "svc6", "password": "pwd"})
        店铺ID = 店铺["id"]
        CSV内容 = (
            "店铺ID,父商品ID,新标题\n"
            f"{店铺ID},9.16454E+11,科学计数标题\n"
        ).encode("utf-8-sig")

        结果 = await 任务参数服务实例.批量导入(CSV内容, "发布相似商品")

        assert 结果["success_count"] == 1
        assert 结果["failed_count"] == 0

        列表 = await 任务参数服务实例.分页查询(task_name="发布相似商品")
        assert any(
            记录["params"].get("parent_product_id") == "916454000000"
            for 记录 in 列表["list"]
        )

    def test_预处理CSV行_普通数字ID不受影响(self):
        """普通数字字符串不应被科学计数法修复逻辑改写。"""
        行数据 = {
            "店铺ID": "12345",
            "父商品ID": "916453776556",
            "新标题": "普通标题",
        }

        结果 = 任务参数服务实例._预处理CSV行(行数据)

        assert 结果["店铺ID"] == "12345"
        assert 结果["父商品ID"] == "916453776556"
        assert 结果["新标题"] == "普通标题"

    def test_解析CSV内容_不支持编码时报错(self):
        """所有候选编码都无法解码时应返回明确提示。"""
        with pytest.raises(ValueError, match="CSV 文件编码不支持，请另存为 UTF-8 格式"):
            任务参数服务实例._解析CSV内容(b"\xff\xff\xff")
