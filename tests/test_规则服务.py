"""规则服务单元测试。"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.规则接口 import 路由 as 规则路由
from backend.models import 数据库 as 数据库模块
from backend.services.规则服务 import 规则服务


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


async def 清空规则表():
    async with 数据库模块.获取连接() as 连接:
        await 连接.execute("DELETE FROM rules")
        await 连接.commit()


@pytest.fixture
def 规则客户端(临时环境: Path):
    应用 = FastAPI(redirect_slashes=False)
    应用.include_router(规则路由)

    with TestClient(应用) as 客户端:
        yield 客户端


class 测试_规则服务:
    @pytest.mark.asyncio
    async def test_评估单条_支持各类操作符(self, 临时环境: Path):
        服务 = 规则服务()
        用例列表 = [
            ({"field": "售后类型", "op": "==", "value": "仅退款"}, {"售后类型": "仅退款"}, True),
            ({"field": "售后类型", "op": "!=", "value": "退货退款"}, {"售后类型": "仅退款"}, True),
            ({"field": "退款金额", "op": ">", "value": 10}, {"退款金额": "¥12.50"}, True),
            ({"field": "退款金额", "op": "<", "value": 20}, {"退款金额": "12.50"}, True),
            ({"field": "退款金额", "op": ">=", "value": 12.5}, {"退款金额": "12.50"}, True),
            ({"field": "退款金额", "op": "<=", "value": 12.5}, {"退款金额": "¥12.50"}, True),
            ({"field": "售后类型", "op": "in", "value": ["仅退款", "换货"]}, {"售后类型": "仅退款"}, True),
            ({"field": "售后类型", "op": "not_in", "value": ["退货退款", "换货"]}, {"售后类型": "仅退款"}, True),
            ({"field": "商品名称", "op": "contains", "value": "测试"}, {"商品名称": "售后测试商品"}, True),
        ]

        for 规则, 数据, 预期值 in 用例列表:
            assert 服务._评估单条(规则, 数据) is 预期值

    @pytest.mark.asyncio
    async def test_评估条件_支持_and_or_与嵌套(self, 临时环境: Path):
        服务 = 规则服务()
        数据 = {"售后类型": "仅退款", "退款金额": 8, "发货状态": "未发货"}

        and条件 = {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "仅退款"},
                {"field": "退款金额", "op": "<=", "value": 10},
            ],
        }
        or条件 = {
            "operator": "or",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "退货退款"},
                {"field": "退款金额", "op": "<=", "value": 10},
            ],
        }
        嵌套条件 = {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "仅退款"},
                {
                    "operator": "or",
                    "rules": [
                        {"field": "发货状态", "op": "==", "value": "已发货"},
                        {"field": "退款金额", "op": "<", "value": 10},
                    ],
                },
            ],
        }

        assert 服务._评估条件(and条件, 数据) is True
        assert 服务._评估条件(or条件, 数据) is True
        assert 服务._评估条件(嵌套条件, 数据) is True

    @pytest.mark.asyncio
    async def test_匹配规则_精确店铺优先于通配规则(self, 临时环境: Path):
        服务 = 规则服务()
        await 清空规则表()

        await 服务.创建规则(
            {
                "name": "通用规则",
                "platform": "pdd",
                "business": "售后",
                "shop_id": "*",
                "priority": 999,
                "conditions": {"operator": "and", "rules": [{"field": "售后类型", "op": "==", "value": "仅退款"}]},
                "actions": [{"type": "标记", "action": "人工审核"}],
            }
        )
        await 服务.创建规则(
            {
                "name": "店铺专属规则",
                "platform": "pdd",
                "business": "售后",
                "shop_id": "shop-1",
                "priority": 1,
                "conditions": {"operator": "and", "rules": [{"field": "售后类型", "op": "==", "value": "仅退款"}]},
                "actions": [{"type": "页面操作", "action": "同意退款"}],
            }
        )

        动作列表 = await 服务.匹配规则("pdd", "售后", "shop-1", {"售后类型": "仅退款"})
        assert 动作列表 == [{"type": "页面操作", "action": "同意退款"}]

    @pytest.mark.asyncio
    async def test_匹配规则_同店铺按优先级降序命中(self, 临时环境: Path):
        服务 = 规则服务()
        await 清空规则表()

        await 服务.创建规则(
            {
                "name": "低优先级",
                "platform": "pdd",
                "business": "售后",
                "shop_id": "shop-1",
                "priority": 10,
                "conditions": {"operator": "and", "rules": [{"field": "退款金额", "op": "<=", "value": 50}]},
                "actions": [{"type": "页面操作", "action": "同意退款"}],
            }
        )
        await 服务.创建规则(
            {
                "name": "高优先级",
                "platform": "pdd",
                "business": "售后",
                "shop_id": "shop-1",
                "priority": 100,
                "conditions": {"operator": "and", "rules": [{"field": "退款金额", "op": "<=", "value": 50}]},
                "actions": [{"type": "飞书通知", "action": "发工单"}],
            }
        )

        动作列表 = await 服务.匹配规则("pdd", "售后", "shop-1", {"退款金额": 8})
        assert 动作列表 == [{"type": "飞书通知", "action": "发工单"}]

    @pytest.mark.asyncio
    async def test_匹配规则_无命中时返回默认动作(self, 临时环境: Path):
        服务 = 规则服务()
        await 清空规则表()

        动作列表 = await 服务.匹配规则("pdd", "售后", "shop-1", {"售后类型": "换货"})
        assert 动作列表 == [{"type": "默认", "action": "人工处理"}]

    @pytest.mark.asyncio
    async def test_CRUD_创建读取更新删除切换启用(self, 临时环境: Path):
        服务 = 规则服务()
        await 清空规则表()

        创建结果 = await 服务.创建规则(
            {
                "name": "测试规则",
                "platform": "pdd",
                "business": "售后",
                "shop_id": "shop-1",
                "priority": 10,
                "conditions": {"operator": "and", "rules": [{"field": "售后类型", "op": "==", "value": "仅退款"}]},
                "actions": [{"type": "页面操作", "action": "同意退款"}],
            }
        )
        规则ID = 创建结果["id"]

        详情 = await 服务.获取规则(规则ID)
        assert 详情["name"] == "测试规则"

        更新结果 = await 服务.更新规则(
            规则ID,
            {
                "priority": 20,
                "actions": [{"type": "飞书通知", "action": "发工单"}],
            },
        )
        assert 更新结果["priority"] == 20
        assert 更新结果["actions"] == [{"type": "飞书通知", "action": "发工单"}]

        assert await 服务.切换启用(规则ID, False) is True
        assert (await 服务.获取规则(规则ID))["enabled"] is False

        assert await 服务.删除规则(规则ID) is True
        assert await 服务.获取规则(规则ID) is None

    @pytest.mark.asyncio
    async def test_初始化默认售后规则_现已为空实现(self, 临时环境: Path):
        服务 = 规则服务()
        await 清空规则表()

        await 服务.初始化默认售后规则()
        第一次列表 = await 服务.获取规则列表(platform="pdd", business="售后")
        assert 第一次列表 == []

        await 服务.初始化默认售后规则()
        第二次列表 = await 服务.获取规则列表(platform="pdd", business="售后")
        assert 第二次列表 == []

    @pytest.mark.asyncio
    async def test_初始化数据库_创建_rules_表(self, 临时环境: Path):
        with sqlite3.connect(临时环境) as 连接:
            表名集合 = {行[0] for 行 in 连接.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            assert "rules" in 表名集合

            字段集合 = {行[1] for 行 in 连接.execute("PRAGMA table_info(rules)")}
            assert {
                "id",
                "name",
                "platform",
                "business",
                "shop_id",
                "priority",
                "conditions",
                "actions",
                "enabled",
                "created_at",
                "updated_at",
            }.issubset(字段集合)

    def test_规则接口_CRUD与匹配可用(self, 规则客户端: TestClient):
        运行协程(清空规则表())

        创建响应 = 规则客户端.post(
            "/api/rules",
            json={
                "name": "接口规则",
                "platform": "pdd",
                "business": "售后",
                "shop_id": "shop-1",
                "priority": 10,
                "conditions": {"operator": "and", "rules": [{"field": "售后类型", "op": "==", "value": "仅退款"}]},
                "actions": [{"type": "页面操作", "action": "同意退款"}],
            },
        )

        assert 创建响应.status_code == 200
        assert 创建响应.json()["code"] == 0
        规则ID = 创建响应.json()["data"]["id"]

        详情响应 = 规则客户端.get(f"/api/rules/{规则ID}")
        assert 详情响应.status_code == 200
        assert 详情响应.json()["data"]["name"] == "接口规则"

        匹配响应 = 规则客户端.post(
            "/api/rules/match",
            json={
                "platform": "pdd",
                "business": "售后",
                "shop_id": "shop-1",
                "data": {"售后类型": "仅退款"},
            },
        )
        assert 匹配响应.status_code == 200
        assert 匹配响应.json()["code"] == 0
        assert 匹配响应.json()["data"]["rule_name"] == "接口规则"
