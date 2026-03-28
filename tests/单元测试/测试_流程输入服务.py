"""
流程输入服务单元测试
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.models import 数据库 as 数据库模块
from backend.services.店铺服务 import 店铺服务实例
from backend.services.流程服务 import 流程服务实例
from backend.services.流程输入服务 import 流程输入服务实例


@pytest.fixture
def 临时环境(tmp_path: Path):
    """构造临时数据库测试环境。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        asyncio.run(数据库模块.初始化数据库())
        yield


async def 创建基础数据() -> tuple[str, str]:
    """创建流程和店铺。"""
    店铺 = await 店铺服务实例.创建({"name": "输入服务店铺"})
    流程 = await 流程服务实例.创建(
        {
            "name": "输入服务流程",
            "steps": [{"task": "登录", "on_fail": "abort"}],
        }
    )
    return 店铺["id"], 流程["id"]


class 测试_流程输入服务:
    """验证输入集与输入行服务。"""

    @pytest.mark.asyncio
    async def test_输入集与输入行CRUD正常工作(self, 临时环境):
        店铺ID, 流程ID = await 创建基础数据()

        输入集 = await 流程输入服务实例.创建输入集(
            {
                "flow_id": 流程ID,
                "name": "手工输入集",
                "description": "测试用",
                "source_type": "manual",
                "enabled": True,
            }
        )
        assert 输入集["flow_id"] == 流程ID
        assert 输入集["enabled"] is True

        输入行 = await 流程输入服务实例.创建输入行(
            {
                "input_set_id": 输入集["id"],
                "shop_id": 店铺ID,
                "input_data": {"parent_product_id": "9001"},
                "enabled": True,
                "sort_order": 10,
                "source_key": "row-1",
            }
        )
        assert 输入行["shop_id"] == 店铺ID
        assert 输入行["input_data"]["parent_product_id"] == "9001"

        输入集列表 = await 流程输入服务实例.获取输入集列表(流程ID)
        assert 输入集列表["total"] == 1
        assert 输入集列表["list"][0]["id"] == 输入集["id"]

        输入行列表 = await 流程输入服务实例.获取输入行列表(输入集["id"])
        assert 输入行列表["total"] == 1
        assert 输入行列表["list"][0]["id"] == 输入行["id"]

        更新后输入集 = await 流程输入服务实例.更新输入集(
            输入集["id"],
            {"name": "更新后输入集"},
        )
        assert 更新后输入集 is not None
        assert 更新后输入集["name"] == "更新后输入集"

        更新后输入行 = await 流程输入服务实例.更新输入行(
            输入行["id"],
            {"input_data": {"parent_product_id": "9002"}, "sort_order": 20, "enabled": False},
        )
        assert 更新后输入行 is not None
        assert 更新后输入行["input_data"]["parent_product_id"] == "9002"
        assert 更新后输入行["sort_order"] == 20

        启用输入行 = await 流程输入服务实例.获取启用输入行(输入集["id"], shop_ids=[店铺ID])
        assert 启用输入行 == []

        await 流程输入服务实例.更新输入行(输入行["id"], {"enabled": True})
        启用输入行 = await 流程输入服务实例.获取启用输入行(输入集["id"], shop_ids=[店铺ID])
        assert len(启用输入行) == 1
        assert 启用输入行[0]["id"] == 输入行["id"]

        assert await 流程输入服务实例.删除输入行(输入行["id"]) is True
        assert await 流程输入服务实例.删除输入集(输入集["id"]) is True

    @pytest.mark.asyncio
    async def test_批量导入输入行会返回成功与失败统计(self, 临时环境):
        店铺ID, 流程ID = await 创建基础数据()
        输入集 = await 流程输入服务实例.创建输入集(
            {
                "flow_id": 流程ID,
                "name": "CSV输入集",
                "source_type": "csv",
                "enabled": True,
            }
        )

        文件内容 = (
            "店铺ID,parent_product_id,source_key\n"
            f"{店铺ID},9001,row-1\n"
            ",9002,row-2\n"
        ).encode("utf-8")

        导入结果 = await 流程输入服务实例.批量导入输入行(
            输入集["id"],
            文件内容,
            file_name="demo.csv",
        )

        assert 导入结果["success_count"] == 1
        assert 导入结果["failed_count"] == 1
        assert 导入结果["errors"]

    @pytest.mark.asyncio
    async def test_创建输入集_非法来源类型抛出异常(self, 临时环境):
        _, 流程ID = await 创建基础数据()

        with pytest.raises(ValueError, match="source_type"):
            await 流程输入服务实例.创建输入集(
                {
                    "flow_id": 流程ID,
                    "name": "非法来源",
                    "source_type": "json",
                }
            )
