"""售后队列服务单元测试。"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.models import 数据库 as 数据库模块
from backend.services.售后队列服务 import 售后队列服务


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

    with patch.object(数据库模块, "数据库路径", 数据库文件):
        运行协程(数据库模块.初始化数据库())
        yield 数据库文件


async def 根据ID查询记录(记录ID: int) -> dict | None:
    async with 数据库模块.获取连接() as 连接:
        async with 连接.execute(
            "SELECT * FROM aftersale_queue WHERE id = ?",
            (记录ID,),
        ) as 游标:
            行 = await 游标.fetchone()
    return dict(行) if 行 else None


class 测试_售后队列服务:
    @pytest.mark.asyncio
    async def test_初始化数据库_创建售后队列表(self, 临时环境: Path):
        with sqlite3.connect(临时环境) as 连接:
            表名集合 = {行[0] for 行 in 连接.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            assert "aftersale_queue" in 表名集合

            字段集合 = {行[1] for 行 in 连接.execute("PRAGMA table_info(aftersale_queue)")}
            assert {
                "id",
                "batch_id",
                "shop_id",
                "订单号",
                "售后类型",
                "售后状态",
                "退款金额",
                "商品名称",
                "详情数据",
                "可用按钮列表",
                "当前阶段",
            }.issubset(字段集合)

            索引集合 = {
                行[0]
                for 行 in 连接.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'aftersale_queue'"
                )
            }
            assert "idx_aftersale_queue_shop_order" in 索引集合

    @pytest.mark.asyncio
    async def test_创建批次_格式正确(self, 临时环境: Path):
        服务 = 售后队列服务()

        批次ID = await 服务.创建批次("shop-001")

        assert 批次ID.startswith("AS-shop-001-")
        assert 批次ID.split("AS-shop-001-")[1].isdigit()

    @pytest.mark.asyncio
    async def test_写入队列并获取待处理列表(self, 临时环境: Path):
        服务 = 售后队列服务()
        批次ID = await 服务.创建批次("shop-1")

        记录ID = await 服务.写入队列(
            {
                "batch_id": 批次ID,
                "shop_id": "shop-1",
                "订单号": "ORDER-1001",
                "售后类型": "仅退款",
                "售后状态": "待商家处理",
                "退款金额": "¥6.08",
                "商品名称": "测试商品A",
            }
        )

        assert 记录ID > 0
        列表 = await 服务.获取待处理列表(batch_id=批次ID, shop_id="shop-1")
        assert len(列表) == 1
        assert 列表[0]["订单号"] == "ORDER-1001"
        assert 列表[0]["退款金额"] == 6.08
        assert 列表[0]["当前阶段"] == "待处理"

    @pytest.mark.asyncio
    async def test_写入队列_缺少订单号时报错(self, 临时环境: Path):
        服务 = 售后队列服务()

        with pytest.raises(ValueError, match="订单号不能为空"):
            await 服务.写入队列(
                {
                    "batch_id": "AS-shop-1-20260316010101000",
                    "shop_id": "shop-1",
                    "订单号": "",
                }
            )

    @pytest.mark.asyncio
    async def test_写入队列_订单已存在时直接跳过(self, 临时环境: Path):
        服务 = 售后队列服务()

        首次写入ID = await 服务.写入队列(
            {
                "batch_id": "AS-shop-1-old",
                "shop_id": "shop-1",
                "订单号": "ORDER-1002",
                "售后类型": "仅退款",
            }
        )
        再次写入ID = await 服务.写入队列(
            {
                "batch_id": "AS-shop-1-new",
                "shop_id": "shop-1",
                "订单号": "ORDER-1002",
                "售后类型": "退货退款",
            }
        )

        assert 首次写入ID > 0
        assert 再次写入ID == 0
        列表 = await 服务.获取待处理列表(shop_id="shop-1")
        assert len(列表) == 1
        assert 列表[0]["batch_id"] == "AS-shop-1-old"
        assert 列表[0]["售后类型"] == "仅退款"

    @pytest.mark.asyncio
    async def test_批量写入队列_同批次同订单去重(self, 临时环境: Path):
        服务 = 售后队列服务()
        批次ID = "AS-shop-2-20260316010101001"

        写入数量 = await 服务.批量写入队列(
            [
                {
                    "batch_id": 批次ID,
                    "shop_id": "shop-2",
                    "订单号": "ORDER-2001",
                    "售后类型": "仅退款",
                },
                {
                    "batch_id": 批次ID,
                    "shop_id": "shop-2",
                    "订单号": "ORDER-2001",
                    "售后类型": "仅退款",
                },
                {
                    "batch_id": 批次ID,
                    "shop_id": "shop-2",
                    "订单号": "ORDER-2002",
                    "售后类型": "退货退款",
                },
            ]
        )

        assert 写入数量 == 2
        列表 = await 服务.获取待处理列表(batch_id=批次ID, shop_id="shop-2")
        assert [记录["订单号"] for 记录 in 列表] == ["ORDER-2001", "ORDER-2002"]

    @pytest.mark.asyncio
    async def test_批量写入队列_已有订单时跨批次跳过(self, 临时环境: Path):
        服务 = 售后队列服务()

        旧记录ID = await 服务.写入队列(
            {
                "batch_id": "AS-shop-2-old",
                "shop_id": "shop-2",
                "订单号": "ORDER-2003",
                "售后类型": "退货退款",
            }
        )
        await 服务.标记已完成(旧记录ID, "已处理")

        写入数量 = await 服务.批量写入队列(
            [
                {
                    "batch_id": "AS-shop-2-new",
                    "shop_id": "shop-2",
                    "订单号": "ORDER-2003",
                    "售后类型": "退货退款",
                },
                {
                    "batch_id": "AS-shop-2-new",
                    "shop_id": "shop-2",
                    "订单号": "ORDER-2004",
                    "售后类型": "退货退款",
                },
            ]
        )

        assert 写入数量 == 1
        列表 = await 服务.获取待处理列表(batch_id="AS-shop-2-new", shop_id="shop-2")
        assert [记录["订单号"] for 记录 in 列表] == ["ORDER-2004"]

    @pytest.mark.asyncio
    async def test_更新详情_JSON写入和关键字段提取(self, 临时环境: Path):
        服务 = 售后队列服务()
        记录ID = await 服务.写入队列(
            {
                "batch_id": "AS-shop-3-20260316010101002",
                "shop_id": "shop-3",
                "订单号": "ORDER-3001",
                "售后类型": "仅退款",
                "商品名称": "测试商品C",
            }
        )

        更新成功 = await 服务.更新详情(
            记录ID,
            {
                "售后类型": "仅退款",
                "售后状态": "待商家处理",
                "退款金额": 12.5,
                "商品名称": "测试商品C",
                "申请原因": "尺寸不合适",
                "售后申请说明": "买家申请退款",
                "发货物流公司": "顺丰",
                "发货快递单号": "SF123456",
                "有售后图片": True,
                "物流最新状态": "包裹已签收",
                "物流最新时间": "2026-03-16 10:00:00",
                "收货城市": "合肥",
                "剩余处理时间": "12时30分",
                "平台建议": "建议优先协商",
                "可用按钮列表": ["同意退款", "拒绝"],
                "协商轮次": 2,
                "商家已回复": True,
            },
        )

        assert 更新成功 is True
        记录 = await 根据ID查询记录(记录ID)
        assert 记录 is not None
        assert 记录["申请原因"] == "尺寸不合适"
        assert 记录["发货物流公司"] == "顺丰"
        assert 记录["物流最新时间"] == "2026-03-16 10:00:00"
        assert 记录["有售后图片"] == 1

        列表 = await 服务.获取待处理列表(batch_id="AS-shop-3-20260316010101002", shop_id="shop-3")
        assert 列表[0]["详情数据"]["平台建议"] == "建议优先协商"
        assert 列表[0]["可用按钮列表"] == ["同意退款", "拒绝"]
        assert 列表[0]["商家已回复"] is True

    @pytest.mark.asyncio
    async def test_更新阶段_阶段拒绝次数和下次处理时间正确更新(self, 临时环境: Path):
        服务 = 售后队列服务()
        记录ID = await 服务.写入队列(
            {
                "batch_id": "AS-shop-4-20260316010101003",
                "shop_id": "shop-4",
                "订单号": "ORDER-4001",
            }
        )

        更新成功 = await 服务.更新阶段(
            记录ID,
            "等待退回",
            下次处理时间="2026-03-20 08:00:00",
            拒绝次数=2,
            处理结果="等待买家退回",
            错误信息="需核验货物状态",
        )

        assert 更新成功 is True
        记录 = await 根据ID查询记录(记录ID)
        assert 记录["当前阶段"] == "等待退回"
        assert 记录["下次处理时间"] == "2026-03-20 08:00:00"
        assert 记录["拒绝次数"] == 2
        assert 记录["处理结果"] == "等待买家退回"
        assert 记录["错误信息"] == "需核验货物状态"
        assert 记录["处理次数"] == 1
        assert 记录["上次拒绝时间"] is not None

    @pytest.mark.asyncio
    async def test_获取到期记录_只返回到期且未完成的(self, 临时环境: Path):
        服务 = 售后队列服务()
        待处理ID = await 服务.写入队列(
            {"batch_id": "AS-shop-5-1", "shop_id": "shop-5", "订单号": "ORDER-5001"}
        )
        等待退回ID = await 服务.写入队列(
            {"batch_id": "AS-shop-5-1", "shop_id": "shop-5", "订单号": "ORDER-5002"}
        )
        已完成ID = await 服务.写入队列(
            {"batch_id": "AS-shop-5-1", "shop_id": "shop-5", "订单号": "ORDER-5003"}
        )
        未来待退款ID = await 服务.写入队列(
            {"batch_id": "AS-shop-5-1", "shop_id": "shop-5", "订单号": "ORDER-5004"}
        )

        await 服务.更新阶段(待处理ID, "待处理", 下次处理时间="2000-01-01 00:00:00")
        await 服务.更新阶段(等待退回ID, "等待退回", 下次处理时间="2000-01-01 00:00:01")
        await 服务.更新阶段(已完成ID, "已完成", 下次处理时间="2000-01-01 00:00:02")
        await 服务.更新阶段(未来待退款ID, "待退款", 下次处理时间="2999-01-01 00:00:00")

        到期列表 = await 服务.获取到期记录()

        assert [记录["订单号"] for 记录 in 到期列表] == ["ORDER-5001", "ORDER-5002"]

    @pytest.mark.asyncio
    async def test_查询拒绝次数_返回当前订单拒绝次数(self, 临时环境: Path):
        服务 = 售后队列服务()
        记录ID = await 服务.写入队列(
            {"batch_id": "AS-shop-6-1", "shop_id": "shop-6", "订单号": "ORDER-6001"}
        )

        await 服务.更新阶段(记录ID, "等待验货", 拒绝次数=3)

        assert await 服务.查询拒绝次数("ORDER-6001") == 3

    @pytest.mark.asyncio
    async def test_获取批次统计_返回各阶段计数(self, 临时环境: Path):
        服务 = 售后队列服务()
        批次ID = "AS-shop-7-20260316010101007"
        记录ID列表 = [
            await 服务.写入队列({"batch_id": 批次ID, "shop_id": "shop-7", "订单号": "ORDER-7001"}),
            await 服务.写入队列({"batch_id": 批次ID, "shop_id": "shop-7", "订单号": "ORDER-7002"}),
            await 服务.写入队列({"batch_id": 批次ID, "shop_id": "shop-7", "订单号": "ORDER-7003"}),
            await 服务.写入队列({"batch_id": 批次ID, "shop_id": "shop-7", "订单号": "ORDER-7004"}),
            await 服务.写入队列({"batch_id": 批次ID, "shop_id": "shop-7", "订单号": "ORDER-7005"}),
        ]

        await 服务.标记已完成(记录ID列表[0], "自动退款成功")
        await 服务.更新阶段(记录ID列表[1], "失败", 错误信息="页面异常")
        await 服务.标记人工(记录ID列表[2], "需人工判断")
        await 服务.更新阶段(记录ID列表[4], "等待退回", 下次处理时间="2000-01-01 00:00:00")

        统计 = await 服务.获取批次统计(批次ID)

        assert 统计 == {
            "总数": 5,
            "已完成": 1,
            "失败": 1,
            "人工": 1,
            "待处理": 1,
        }
