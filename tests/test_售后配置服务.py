"""售后配置服务单元测试。"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.models import 数据库 as 数据库模块
from backend.services.售后配置服务 import 售后配置服务


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


async def 插入店铺(shop_id: str, 名称: str = "测试店铺") -> None:
    async with 数据库模块.获取连接() as 连接:
        await 连接.execute(
            """
            INSERT INTO shops (id, name, status)
            VALUES (?, ?, 'offline')
            """,
            (shop_id, 名称),
        )
        await 连接.commit()


class 测试_售后配置服务:
    @pytest.mark.asyncio
    async def test_初始化数据库_创建售后配置表(self, 临时环境: Path):
        with sqlite3.connect(临时环境) as 连接:
            表名集合 = {
                行[0]
                for 行 in 连接.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            assert "aftersale_config" in 表名集合

            字段集合 = {
                行[1] for 行 in 连接.execute("PRAGMA table_info(aftersale_config)")
            }
            assert {
                "shop_id",
                "启用自动售后",
                "不支持自动处理类型",
                "退货物流白名单",
                "仅退款_启用",
                "飞书通知_webhook",
                "每批最大处理数",
                "飞书多维表_写入场景",
            }.issubset(字段集合)

    @pytest.mark.asyncio
    async def test_获取配置_不存在时自动创建默认配置(self, 临时环境: Path):
        服务 = 售后配置服务()
        await 插入店铺("shop-1")

        配置 = await 服务.获取配置("shop-1")

        assert 配置["shop_id"] == "shop-1"
        assert 配置["启用自动售后"] is True
        assert 配置["仅退款_启用"] is False
        assert 配置["退货物流白名单"] == []
        assert 配置["优先处理类型"] == ["退货退款", "仅退款"]

    @pytest.mark.asyncio
    async def test_获取配置_已存在时返回现有配置(self, 临时环境: Path):
        服务 = 售后配置服务()
        await 插入店铺("shop-2")
        await 服务.更新配置("shop-2", {"启用自动售后": False, "每批最大处理数": 12})

        配置 = await 服务.获取配置("shop-2")

        assert 配置["启用自动售后"] is False
        assert 配置["每批最大处理数"] == 12

    @pytest.mark.asyncio
    async def test_更新配置_只更新白名单且保留其他默认值(self, 临时环境: Path):
        服务 = 售后配置服务()
        await 插入店铺("shop-3")

        更新后 = await 服务.更新配置(
            "shop-3",
            {
                "退货物流白名单": [
                    {
                        "名称": "杭州仓",
                        "快递公司": "韵达",
                        "地区关键词": ["杭州"],
                        "派件人": ["张三"],
                        "启用": True,
                    }
                ]
            },
        )

        assert 更新后["退货物流白名单"][0]["快递公司"] == "韵达"
        assert 更新后["自动退款金额上限"] == 50.0
        assert 更新后["仅退款_最大拒绝次数"] == 3

    @pytest.mark.asyncio
    async def test_更新配置_JSON字段序列化与反序列化正确(self, 临时环境: Path):
        服务 = 售后配置服务()
        await 插入店铺("shop-4")

        await 服务.更新配置(
            "shop-4",
            {
                "通知场景": ["人工审核", "入库校验"],
                "弹窗偏好": {"输入内容": "系统自动处理"},
                "备注模板": {"人工": "人工复核"},
            },
        )
        配置 = await 服务.获取配置("shop-4")

        assert 配置["通知场景"] == ["人工审核", "入库校验"]
        assert 配置["弹窗偏好"]["输入内容"] == "系统自动处理"
        assert 配置["备注模板"]["人工"] == "人工复核"

    def test_校验白名单_格式正确通过(self, 临时环境: Path):
        del 临时环境
        服务 = 售后配置服务()

        结果 = 服务._校验白名单(
            [
                {
                    "名称": "杭州仓",
                    "快递公司": "韵达",
                    "地区关键词": ["杭州", "余杭"],
                    "派件人": ["张三", "李四"],
                    "启用": 1,
                }
            ]
        )

        assert 结果[0]["快递公司"] == "韵达"
        assert 结果[0]["启用"] is True

    def test_校验白名单_缺少必填字段报错(self, 临时环境: Path):
        del 临时环境
        服务 = 售后配置服务()

        with pytest.raises(ValueError, match="缺少字段"):
            服务._校验白名单(
                [
                    {
                        "名称": "杭州仓",
                        "地区关键词": ["杭州"],
                        "派件人": ["张三"],
                    }
                ]
            )

    @pytest.mark.asyncio
    async def test_删除配置(self, 临时环境: Path):
        服务 = 售后配置服务()
        await 插入店铺("shop-5")
        await 服务.获取配置("shop-5")

        删除结果 = await 服务.删除配置("shop-5")
        全部配置 = await 服务.获取所有配置()

        assert 删除结果 is True
        assert all(配置["shop_id"] != "shop-5" for 配置 in 全部配置)

    @pytest.mark.asyncio
    async def test_从规则服务迁移_迁移到新配置并禁用规则(self, 临时环境: Path):
        服务 = 售后配置服务()
        await 插入店铺("shop-6")

        async with 数据库模块.获取连接() as 连接:
            await 连接.execute(
                """
                INSERT INTO rules (name, platform, business, shop_id, priority, conditions, actions, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    "旧售后规则",
                    "pdd",
                    "售后",
                    "shop-6",
                    10,
                    '{"operator":"and","rules":[]}',
                    (
                        '[{"自动同意金额上限": 15, "自动退款金额上限": 88, '
                        '"退货等待时间":{"刚发出":1,"中途运输":2,"到达目的市":0.5}, '
                        '"弹窗偏好":{"输入内容":"旧规则"}, "action":"拒绝"}]'
                    ),
                ),
            )
            await 连接.commit()

        迁移数量 = await 服务.从规则服务迁移()
        配置 = await 服务.获取配置("shop-6")

        assert 迁移数量 == 1
        assert 配置["仅退款_启用"] is True
        assert 配置["仅退款_需要拒绝"] is True
        assert 配置["仅退款_自动同意金额上限"] == 15.0
        assert 配置["自动退款金额上限"] == 88.0
        assert 配置["弹窗偏好"]["输入内容"] == "旧规则"

        async with 数据库模块.获取连接() as 连接:
            async with 连接.execute("SELECT enabled FROM rules WHERE name = '旧售后规则'") as 游标:
                行 = await 游标.fetchone()
        assert 行[0] == 0
