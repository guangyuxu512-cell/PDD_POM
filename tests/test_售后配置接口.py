"""售后配置接口测试。"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.售后配置接口 import 路由 as 售后配置路由
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


@pytest.fixture
def 配置客户端(临时环境: Path):
    del 临时环境
    应用 = FastAPI(redirect_slashes=False)
    应用.include_router(售后配置路由)
    with TestClient(应用) as 客户端:
        yield 客户端


class 测试_售后配置接口:
    def test_GET配置_新店返回默认值(self, 配置客户端: TestClient):
        运行协程(插入店铺("shop-api-1"))

        响应 = 配置客户端.get("/api/aftersale-config/shop-api-1")

        assert 响应.status_code == 200
        数据 = 响应.json()
        assert 数据["code"] == 0
        assert 数据["data"]["shop_id"] == "shop-api-1"
        assert 数据["data"]["启用自动售后"] is True

    def test_PUT配置_部分更新并返回结果(self, 配置客户端: TestClient):
        运行协程(插入店铺("shop-api-2"))

        响应 = 配置客户端.put(
            "/api/aftersale-config/shop-api-2",
            json={
                "启用自动售后": False,
                "每批最大处理数": 18,
                "退货物流白名单": [
                    {
                        "名称": "杭州仓",
                        "快递公司": "韵达",
                        "地区关键词": ["杭州"],
                        "派件人": ["张三"],
                        "启用": True,
                    }
                ],
            },
        )

        assert 响应.status_code == 200
        数据 = 响应.json()["data"]
        assert 数据["启用自动售后"] is False
        assert 数据["每批最大处理数"] == 18
        assert 数据["退货物流白名单"][0]["名称"] == "杭州仓"

    def test_获取所有配置_支持多店铺(self, 配置客户端: TestClient):
        服务 = 售后配置服务()
        运行协程(插入店铺("shop-api-3"))
        运行协程(插入店铺("shop-api-4"))
        运行协程(服务.获取配置("shop-api-3"))
        运行协程(服务.更新配置("shop-api-4", {"启用自动售后": False}))

        响应 = 配置客户端.get("/api/aftersale-config")

        assert 响应.status_code == 200
        数据列表 = 响应.json()["data"]
        店铺ID列表 = {项["shop_id"] for 项 in 数据列表}
        assert {"shop-api-3", "shop-api-4"}.issubset(店铺ID列表)

    def test_删除配置(self, 配置客户端: TestClient):
        服务 = 售后配置服务()
        运行协程(插入店铺("shop-api-5"))
        运行协程(服务.获取配置("shop-api-5"))

        删除响应 = 配置客户端.delete("/api/aftersale-config/shop-api-5")

        assert 删除响应.status_code == 200
        assert 删除响应.json()["code"] == 0
        全部配置 = 运行协程(服务.获取所有配置())
        assert all(项["shop_id"] != "shop-api-5" for 项 in 全部配置)
