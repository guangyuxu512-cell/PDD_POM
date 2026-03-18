"""售后任务单元测试。"""
from __future__ import annotations

import importlib
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def 构造队列服务(*, 写入结果序列: list[int] | None = None):
    服务 = MagicMock()
    服务.创建批次 = AsyncMock(return_value="AS-shop-1-001")
    服务.批量写入队列 = AsyncMock(side_effect=写入结果序列 or [1])
    return 服务


def 构造售后页(
    *,
    导航拦截结果: list[dict] | None = None,
    翻页拦截序列: list[list[dict] | None] | None = None,
    DOM摘要序列: list[dict] | None = None,
):
    页面对象 = MagicMock()
    页面对象.导航并拦截售后列表 = AsyncMock(return_value=导航拦截结果 if 导航拦截结果 is not None else [])
    页面对象.翻页并拦截 = AsyncMock(side_effect=翻页拦截序列 or [None])

    DOM摘要列表 = DOM摘要序列 or []
    页面对象.获取售后单数量 = AsyncMock(return_value=len(DOM摘要列表))
    页面对象.获取第N行信息 = AsyncMock(side_effect=DOM摘要列表)
    return 页面对象


class 测试_售后任务:
    @pytest.fixture
    def 模拟页面(self):
        return MagicMock()

    def test_注册名为_售后处理(self):
        from tasks import 注册表 as 注册表模块

        原注册表 = deepcopy(注册表模块.任务注册表)
        if len(原注册表) <= 1:
            注册表模块.清空任务注册表()
            注册表模块.初始化任务注册表()
            原注册表 = deepcopy(注册表模块.任务注册表)

        import tasks.售后任务 as 售后任务模块

        try:
            注册表模块.清空任务注册表()
            售后任务模块 = importlib.reload(售后任务模块)
            assert 注册表模块.获取任务类("售后处理") is 售后任务模块.售后任务
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)

    @pytest.mark.parametrize(
        ("原始类型", "期望类型"),
        [
            ("我要退货退款", "退货退款"),
            ("仅退款", "退款"),
            ("补寄配件", "补寄"),
            ("换货处理", "换货"),
            ("返厂维修", "维修"),
            ("其他问题", "其他问题"),
            ("", ""),
        ],
    )
    def test_判断售后类型_标准化归类(self, 原始类型: str, 期望类型: str):
        from tasks.售后任务 import 售后任务

        assert 售后任务._判断售后类型(原始类型) == 期望类型

    def test_构建队列记录_包含原始类型和人工标记(self):
        from tasks.售后任务 import 售后任务

        任务 = 售后任务()

        记录 = 任务._构建队列记录(
            {
                "订单号": "ORDER-1",
                "售后类型": "补寄配件",
                "售后状态": "待商家处理",
                "退款金额": "¥18.60",
                "商品名称": "测试商品",
            },
            "AS-shop-1-001",
            "shop-1",
            "店铺A",
        )

        assert 记录 == {
            "batch_id": "AS-shop-1-001",
            "shop_id": "shop-1",
            "shop_name": "店铺A",
            "订单号": "ORDER-1",
            "售后类型": "补寄",
            "售后类型_原始": "补寄配件",
            "售后状态": "待商家处理",
            "退款金额": 18.6,
            "商品名称": "测试商品",
            "需要人工": True,
        }

    @pytest.mark.asyncio
    async def test_执行_API多页扫描并写入队列(self, 模拟页面):
        模拟售后页 = 构造售后页(
            导航拦截结果=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "我要退货退款",
                    "售后状态": "待商家处理",
                    "退款金额": 8,
                    "商品名称": "商品1",
                }
            ],
            翻页拦截序列=[
                [
                    {
                        "订单号": "ORDER-2",
                        "售后类型": "补寄配件",
                        "售后状态": "待商家处理",
                        "退款金额": "¥9.50",
                        "商品名称": "商品2",
                    }
                ],
                None,
            ],
        )
        模拟队列服务 = 构造队列服务(写入结果序列=[1, 1])

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
                "tasks.售后任务.售后页",
                return_value=模拟售后页,
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "扫描2单, 写入2单"
        模拟售后页.导航并拦截售后列表.assert_awaited_once()
        assert 模拟售后页.翻页并拦截.await_count == 2
        模拟售后页.获取售后单数量.assert_not_awaited()
        模拟售后页.获取第N行信息.assert_not_awaited()

        第一页写入 = 模拟队列服务.批量写入队列.await_args_list[0].args[0]
        第二页写入 = 模拟队列服务.批量写入队列.await_args_list[1].args[0]
        assert 第一页写入[0]["售后类型"] == "退货退款"
        assert 第一页写入[0]["售后类型_原始"] == "我要退货退款"
        assert 第一页写入[0]["需要人工"] is False
        assert 第二页写入[0]["售后类型"] == "补寄"
        assert 第二页写入[0]["需要人工"] is True

    @pytest.mark.asyncio
    async def test_执行_重复页全部已扫描时停止翻页(self, 模拟页面):
        模拟售后页 = 构造售后页(
            导航拦截结果=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "仅退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥8.80",
                    "商品名称": "商品1",
                }
            ],
            翻页拦截序列=[
                [
                    {
                        "订单号": "ORDER-1",
                        "售后类型": "仅退款",
                        "售后状态": "待商家处理",
                        "退款金额": "¥8.80",
                        "商品名称": "商品1",
                    }
                ],
                [
                    {
                        "订单号": "ORDER-2",
                        "售后类型": "仅退款",
                        "售后状态": "待商家处理",
                        "退款金额": "¥9.80",
                        "商品名称": "商品2",
                    }
                ],
            ],
        )
        模拟队列服务 = 构造队列服务(写入结果序列=[1])

        with patch("tasks.售后任务.上报", new_callable=AsyncMock) as 模拟上报, patch(
            "tasks.售后任务.售后页",
            return_value=模拟售后页,
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "扫描1单, 写入1单"
        模拟队列服务.批量写入队列.assert_awaited_once()
        assert 模拟售后页.翻页并拦截.await_count == 1
        assert any(
            调用.args == ("[扫描] 第1页 扫描1单(新1单)，写入1单", "shop-1")
            for 调用 in 模拟上报.await_args_list
        )
        assert any(
            调用.args == ("[扫描] 第2页全部为已扫描订单，停止翻页", "shop-1")
            for 调用 in 模拟上报.await_args_list
        )

    @pytest.mark.asyncio
    async def test_执行_第一页为空时返回无待处理售后单(self, 模拟页面):
        模拟售后页 = 构造售后页(
            导航拦截结果=[],
            DOM摘要序列=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "仅退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥8.80",
                    "商品名称": "商品1",
                }
            ],
        )
        模拟队列服务 = 构造队列服务(写入结果序列=[1])

        with patch("tasks.售后任务.上报", new_callable=AsyncMock) as 模拟上报, patch(
            "tasks.售后任务.售后页",
            return_value=模拟售后页,
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "无待处理售后单"
        模拟队列服务.批量写入队列.assert_not_awaited()
        模拟售后页.获取售后单数量.assert_not_awaited()
        模拟售后页.获取第N行信息.assert_not_awaited()
        assert any(调用.args == ("[完成] 无待处理售后单", "shop-1") for 调用 in 模拟上报.await_args_list)

    @pytest.mark.asyncio
    async def test_执行_下一页空列表时结束并返回已扫描汇总(self, 模拟页面):
        模拟售后页 = 构造售后页(
            导航拦截结果=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "仅退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥8.80",
                    "商品名称": "商品1",
                }
            ],
            翻页拦截序列=[[], None],
        )
        模拟队列服务 = 构造队列服务(写入结果序列=[1])

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
            "tasks.售后任务.售后页",
            return_value=模拟售后页,
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "扫描1单, 写入1单"
        模拟队列服务.批量写入队列.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_执行_当前页重复订单只保留最后一条(self, 模拟页面):
        模拟售后页 = 构造售后页(
            导航拦截结果=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "仅退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥1.00",
                    "商品名称": "旧商品",
                },
                {
                    "订单号": "ORDER-1",
                    "售后类型": "换货申请",
                    "售后状态": "待商家处理",
                    "退款金额": "¥2.00",
                    "商品名称": "新商品",
                },
            ]
        )
        模拟队列服务 = 构造队列服务(写入结果序列=[1])

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
            "tasks.售后任务.售后页",
            return_value=模拟售后页,
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "扫描1单, 写入1单"
        写入记录列表 = 模拟队列服务.批量写入队列.await_args.args[0]
        assert len(写入记录列表) == 1
        assert 写入记录列表[0]["订单号"] == "ORDER-1"
        assert 写入记录列表[0]["商品名称"] == "新商品"
        assert 写入记录列表[0]["售后类型"] == "换货"
        assert 写入记录列表[0]["售后类型_原始"] == "换货申请"
        assert 写入记录列表[0]["需要人工"] is True

    @pytest.mark.asyncio
    async def test_执行_写队列异常时返回失败(self, 模拟页面):
        模拟售后页 = 构造售后页(
            导航拦截结果=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "仅退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥6.00",
                    "商品名称": "商品1",
                }
            ]
        )
        模拟队列服务 = 构造队列服务()
        模拟队列服务.批量写入队列 = AsyncMock(side_effect=RuntimeError("写队列失败"))

        with patch("tasks.售后任务.上报", new_callable=AsyncMock) as 模拟上报, patch(
            "tasks.售后任务.售后页",
            return_value=模拟售后页,
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "失败: 写队列失败"
        assert any(
            调用.args == ("[失败] 售后任务异常: 写队列失败", "shop-1")
            for 调用 in 模拟上报.await_args_list
        )
