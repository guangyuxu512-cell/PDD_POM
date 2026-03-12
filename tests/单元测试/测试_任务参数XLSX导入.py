"""
任务参数 XLSX 导入测试
"""
from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import Workbook

from backend.api.路由注册 import 注册所有路由
from backend.models import 数据库 as 数据库模块
from backend.services.任务参数服务 import 任务参数服务实例
from backend.services.店铺服务 import 店铺服务实例


def 运行协程(协程对象):
    """使用独立事件循环执行协程，避免测试间 loop 相互影响。"""
    事件循环 = asyncio.new_event_loop()
    try:
        return 事件循环.run_until_complete(协程对象)
    finally:
        事件循环.close()


def 构造XLSX字节(表头: list[str], 行列表: list[list[object]]) -> bytes:
    """构造内存中的 xlsx 文件字节。"""
    工作簿 = Workbook()
    工作表 = 工作簿.active
    工作表.append(表头)
    for 行数据 in 行列表:
        工作表.append(行数据)

    缓冲区 = BytesIO()
    工作簿.save(缓冲区)
    工作簿.close()
    return 缓冲区.getvalue()


@pytest.fixture
def 临时环境(tmp_path: Path):
    """构造任务参数服务测试所需的临时数据库环境。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        运行协程(数据库模块.初始化数据库())
        yield 数据库文件


@pytest.fixture
def 客户端(tmp_path: Path):
    """构造任务参数接口测试客户端。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), \
            patch("backend.services.店铺服务.配置实例.DATA_DIR", str(数据目录)):
        运行协程(数据库模块.初始化数据库())

        app = FastAPI(redirect_slashes=False)
        注册所有路由(app)

        with TestClient(app) as client:
            yield client


def 创建店铺(client: TestClient, 名称: str = "XLSX任务参数店铺") -> str:
    响应 = client.post(
        "/api/shops",
        json={
            "name": 名称,
            "username": f"{名称}@example.com",
            "password": "secret",
        },
    )
    assert 响应.status_code == 200
    assert 响应.json()["code"] == 0
    return 响应.json()["data"]["id"]


class 测试_任务参数XLSX导入:
    """验证 xlsx 导入和 csv 兼容逻辑。"""

    @pytest.mark.asyncio
    async def test_批量导入_支持读取XLSX并保留大整数精度(self, 临时环境: Path):
        """xlsx 导入应直接从 Excel 原始值读取商品 ID，避免科学计数法精度问题。"""
        店铺 = await 店铺服务实例.创建({"name": "XLSX店铺", "username": "xlsx-user", "password": "pwd"})
        店铺ID = 店铺["id"]
        XLSX内容 = 构造XLSX字节(
            ["店铺ID", "父商品ID", "新标题"],
            [[店铺ID, 916453776556, "Excel标题"]],
        )

        解析结果 = 任务参数服务实例._解析XLSX内容(XLSX内容)
        assert 解析结果 == [
            {
                "店铺ID": 店铺ID,
                "父商品ID": "916453776556",
                "新标题": "Excel标题",
            }
        ]

        导入结果 = await 任务参数服务实例.批量导入(
            XLSX内容,
            "发布相似商品",
            file_name="task-params.xlsx",
        )

        assert 导入结果["success_count"] == 1
        assert 导入结果["failed_count"] == 0

        列表 = await 任务参数服务实例.分页查询(task_name="发布相似商品")
        assert 列表["total"] == 1
        assert 列表["list"][0]["params"]["parent_product_id"] == "916453776556"

    @pytest.mark.asyncio
    async def test_批量导入_非XLSX扩展名仍按CSV解析(self, 临时环境: Path):
        """服务层在非 xlsx 扩展名下应继续沿用 CSV 解析逻辑。"""
        店铺 = await 店铺服务实例.创建({"name": "CSV回退店铺", "username": "csv-user", "password": "pwd"})
        店铺ID = 店铺["id"]
        CSV内容 = (
            "店铺ID,父商品ID,新标题\n"
            f"{店铺ID},8101,CSV回退标题\n"
        ).encode("utf-8-sig")

        导入结果 = await 任务参数服务实例.批量导入(
            CSV内容,
            "发布相似商品",
            file_name="task-params.txt",
        )

        assert 导入结果["success_count"] == 1
        assert 导入结果["failed_count"] == 0

    def test_导入接口_支持XLSX并拒绝不支持的扩展名(self, 客户端: TestClient):
        """接口应支持 xlsx 文件并对不支持的扩展名返回业务错误。"""
        店铺ID = 创建店铺(客户端, "XLSX接口店铺")
        XLSX内容 = 构造XLSX字节(
            ["店铺ID", "父商品ID", "新标题"],
            [[店铺ID, 916453776556, "接口Excel标题"]],
        )

        导入响应 = 客户端.post(
            "/api/task-params/import-csv",
            data={"task_name": "发布相似商品"},
            files={
                "file": (
                    "task-params.xlsx",
                    XLSX内容,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        assert 导入响应.status_code == 200
        assert 导入响应.json()["code"] == 0
        assert 导入响应.json()["data"]["success_count"] == 1

        列表响应 = 客户端.get("/api/task-params", params={"task_name": "发布相似商品"})
        列表数据 = 列表响应.json()["data"]["list"]
        assert len(列表数据) == 1
        assert 列表数据[0]["params"]["parent_product_id"] == "916453776556"

        错误响应 = 客户端.post(
            "/api/task-params/import-csv",
            data={"task_name": "发布相似商品"},
            files={"file": ("task-params.txt", b"hello", "text/plain")},
        )

        assert 错误响应.status_code == 200
        assert 错误响应.json()["code"] == 1
        assert "仅支持 .csv 或 .xlsx 文件" in 错误响应.json()["msg"]
