"""售后任务单元测试。"""
from __future__ import annotations

import importlib
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest


def 构造队列服务(待处理列表: list[dict] | None = None):
    服务 = MagicMock()
    服务.创建批次 = AsyncMock(return_value="AS-shop-1-001")
    服务.批量写入队列 = AsyncMock(return_value=1)
    服务.获取待处理列表 = AsyncMock(
        return_value=待处理列表 or [{"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}]
    )
    服务.更新详情 = AsyncMock(return_value=True)
    服务.更新退货物流 = AsyncMock(return_value=True)
    服务.更新阶段 = AsyncMock(return_value=True)
    服务.标记已被处理 = AsyncMock(return_value=True)
    服务.标记人工 = AsyncMock(return_value=True)
    服务.标记已完成 = AsyncMock(return_value=True)
    服务.获取批次统计 = AsyncMock(
        return_value={"总数": 1, "已完成": 1, "失败": 0, "人工": 0, "待处理": 0}
    )
    return 服务


def 构造售后页(
    *,
    摘要列表: list[dict] | None = None,
    详情: dict | None = None,
    退货物流: dict | None = None,
):
    页面对象 = MagicMock()
    页面对象.导航到售后列表 = AsyncMock()
    页面对象.确保待商家处理已选中 = AsyncMock()
    页面对象.扫描所有待处理 = AsyncMock(
        return_value=摘要列表
        or [{"订单号": "ORDER-1", "售后类型": "仅退款", "退款金额": "¥8.00", "商品名称": "测试商品"}]
    )
    页面对象.列表页添加备注 = AsyncMock(return_value=True)
    页面对象.搜索订单 = AsyncMock()
    页面对象.随机延迟 = AsyncMock()
    页面对象.点击订单详情并切换标签 = AsyncMock()
    页面对象.抓取详情页完整信息 = AsyncMock(
        return_value=详情
        or {"订单编号": "ORDER-1", "售后类型": "仅退款", "可用按钮列表": ["同意退款", "拒绝"]}
    )
    页面对象.抓取退货物流信息 = AsyncMock(return_value=退货物流 or {"有退货物流": False})
    页面对象.检查是否需要处理 = AsyncMock(return_value=True)
    页面对象.点击指定按钮 = AsyncMock(return_value=True)
    页面对象.弹窗扫描循环 = AsyncMock(return_value="成功")
    页面对象.详情页添加备注 = AsyncMock(return_value=True)
    页面对象.关闭详情标签 = AsyncMock()
    页面对象.详情页截图 = AsyncMock(return_value="detail.png")
    页面对象._详情页 = MagicMock()
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

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_执行_列表页分流_补寄直接转人工(self, 模拟回调, 模拟页面):
        模拟售后页 = 构造售后页(
            摘要列表=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "补寄",
                    "售后状态": "待商家处理",
                    "退款金额": "¥8.00",
                    "商品名称": "测试商品",
                }
            ]
        )
        模拟队列服务 = 构造队列服务(
            [{"id": 1, "订单号": "ORDER-1", "售后类型": "补寄", "售后状态": "待商家处理"}]
        )
        模拟飞书服务 = MagicMock()
        模拟飞书服务.发送售后通知 = AsyncMock(return_value={"success": True})

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
            "tasks.售后任务.售后页", return_value=模拟售后页
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务
            任务._飞书服务 = 模拟飞书服务

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "处理0单, 人工1单, 跳过0单"
        模拟售后页.列表页添加备注.assert_awaited_once_with("ORDER-1", "【系统】补寄暂不支持自动处理，转人工")
        模拟队列服务.标记人工.assert_awaited_once_with(1, "补寄不支持自动处理")
        模拟飞书服务.发送售后通知.assert_awaited_once()
        模拟售后页.点击订单详情并切换标签.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_执行_退货退款不分流而是进入详情处理(self, 模拟回调, 模拟页面):
        模拟售后页 = 构造售后页(
            摘要列表=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "退货退款",
                    "售后状态": "待商家确认收货",
                    "退款金额": "¥8.00",
                    "商品名称": "测试商品",
                }
            ],
            详情={"订单编号": "ORDER-1", "售后类型": "退货退款", "可用按钮列表": ["同意退款", "拒绝"]},
            退货物流={"有退货物流": False},
        )
        模拟队列服务 = 构造队列服务(
            [{"id": 1, "订单号": "ORDER-1", "售后类型": "退货退款", "拒绝次数": 0}]
        )
        模拟规则服务 = MagicMock()
        模拟规则服务.匹配规则 = AsyncMock(return_value=[])
        模拟决策引擎 = MagicMock()
        模拟决策引擎.决策 = AsyncMock(
            return_value={
                "操作": "同意退款",
                "目标按钮": "同意退款",
                "备选按钮": [],
                "弹窗偏好": {},
                "需要备注": False,
                "备注内容": "",
                "需要飞书通知": False,
                "飞书通知内容": "",
                "人工原因": "",
                "下次处理天数": None,
            }
        )

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
            "tasks.售后任务.售后页", return_value=模拟售后页
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务
            任务._规则服务 = 模拟规则服务
            任务._决策引擎 = 模拟决策引擎

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "处理1单, 人工0单, 跳过0单"
        模拟售后页.列表页添加备注.assert_not_awaited()
        模拟售后页.点击订单详情并切换标签.assert_awaited_once_with("ORDER-1")
        模拟队列服务.标记已完成.assert_awaited_once_with(1, "同意退款成功")

    @pytest.mark.asyncio
    async def test_处理单条_不再调用搜索订单(self, 模拟页面):
        模拟售后页 = 构造售后页()
        模拟队列服务 = 构造队列服务()
        模拟规则服务 = MagicMock()
        模拟规则服务.匹配规则 = AsyncMock(return_value=[])
        模拟决策引擎 = MagicMock()
        模拟决策引擎.决策 = AsyncMock(
            return_value={
                "操作": "跳过",
                "目标按钮": "",
                "备选按钮": [],
                "弹窗偏好": {},
                "需要备注": False,
                "备注内容": "",
                "需要飞书通知": False,
                "飞书通知内容": "",
                "人工原因": "已处理",
                "下次处理天数": None,
            }
        )

        with patch("tasks.售后任务.上报", new_callable=AsyncMock):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._售后页 = 模拟售后页
            任务._队列服务 = 模拟队列服务
            任务._规则服务 = 模拟规则服务
            任务._决策引擎 = 模拟决策引擎

            结果 = await 任务._处理单条({"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}, {"shop_id": "shop-1"})

        assert 结果 == "跳过"
        模拟售后页.搜索订单.assert_not_awaited()
        模拟售后页.点击订单详情并切换标签.assert_awaited_once_with("ORDER-1")
        模拟队列服务.标记已被处理.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_处理单条_退货物流等待时写入下次处理时间(self, 模拟页面):
        模拟售后页 = 构造售后页(
            详情={"订单编号": "ORDER-1", "售后类型": "退货退款", "可用按钮列表": ["同意退款", "拒绝"]},
            退货物流={
                "有退货物流": True,
                "退货快递公司": "极兔速递",
                "退货快递单号": "JT123456",
                "轨迹全文": "2026-03-16 10:00 已揽收",
                "退货物流状态": "已揽收",
            },
        )
        模拟队列服务 = 构造队列服务()
        模拟规则服务 = MagicMock()
        模拟规则服务.匹配规则 = AsyncMock(return_value=[])
        模拟决策引擎 = MagicMock()
        模拟决策引擎.决策 = AsyncMock(
            return_value={
                "操作": "等待",
                "目标按钮": "",
                "备选按钮": [],
                "弹窗偏好": {},
                "需要备注": False,
                "备注内容": "",
                "需要飞书通知": False,
                "飞书通知内容": "",
                "人工原因": "等待买家寄回",
                "下次处理天数": 3,
            }
        )

        with patch("tasks.售后任务.上报", new_callable=AsyncMock):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._售后页 = 模拟售后页
            任务._队列服务 = 模拟队列服务
            任务._规则服务 = 模拟规则服务
            任务._决策引擎 = 模拟决策引擎

            结果 = await 任务._处理单条({"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}, {"shop_id": "shop-1"})

        assert 结果 == "跳过"
        模拟队列服务.更新退货物流.assert_awaited_once_with(
            1,
            "极兔速递",
            "JT123456",
            "2026-03-16 10:00 已揽收",
            "已揽收",
        )
        末次调用 = 模拟队列服务.更新阶段.await_args_list[-1]
        assert 末次调用.args == (1, "等待退回")
        assert 末次调用.kwargs["处理结果"] == "等待3天后复查"
        assert 末次调用.kwargs["下次处理时间"]

    @pytest.mark.asyncio
    async def test_处理单条_退货物流匹配时自动退款(self, 模拟页面):
        模拟售后页 = 构造售后页(
            详情={"订单编号": "ORDER-1", "售后类型": "退货退款", "可用按钮列表": ["同意退款", "拒绝"]},
            退货物流={
                "有退货物流": True,
                "退货快递公司": "极兔速递",
                "退货快递单号": "JT123456",
                "轨迹全文": "2026-03-16 10:00 快递员陈喜德正在派件",
                "退货物流状态": "快递员陈喜德正在派件",
            },
        )
        模拟队列服务 = 构造队列服务()
        模拟规则服务 = MagicMock()
        模拟规则服务.匹配规则 = AsyncMock(return_value=[])
        模拟决策引擎 = MagicMock()
        模拟决策引擎.决策 = AsyncMock(
            return_value={
                "操作": "同意退款",
                "目标按钮": "同意退款",
                "备选按钮": [],
                "弹窗偏好": {},
                "需要备注": True,
                "备注内容": "退回物流匹配，自动退款",
                "需要飞书通知": False,
                "飞书通知内容": "",
                "人工原因": "",
                "下次处理天数": None,
            }
        )

        with patch("tasks.售后任务.上报", new_callable=AsyncMock):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._售后页 = 模拟售后页
            任务._队列服务 = 模拟队列服务
            任务._规则服务 = 模拟规则服务
            任务._决策引擎 = 模拟决策引擎

            结果 = await 任务._处理单条({"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}, {"shop_id": "shop-1"})

        assert 结果 == "已处理"
        模拟售后页.点击指定按钮.assert_awaited_once_with("同意退款")
        模拟队列服务.标记已完成.assert_awaited_once_with(1, "同意退款成功")
        模拟售后页.详情页添加备注.assert_awaited_once_with("退回物流匹配，自动退款")
        模拟队列服务.更新退货物流.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_处理单条_等待验货时写备注发飞书并回写阶段(self, 模拟页面):
        模拟售后页 = 构造售后页(
            详情={"订单编号": "ORDER-1", "售后类型": "退货退款", "可用按钮列表": ["同意退款", "拒绝"]},
            退货物流={"有退货物流": True, "退货快递公司": "极兔速递", "退货快递单号": "JT123456", "轨迹全文": "已签收"},
        )
        模拟队列服务 = 构造队列服务()
        模拟规则服务 = MagicMock()
        模拟规则服务.匹配规则 = AsyncMock(return_value=[])
        模拟决策引擎 = MagicMock()
        模拟决策引擎.决策 = AsyncMock(
            return_value={
                "操作": "等待验货",
                "目标按钮": "",
                "备选按钮": [],
                "弹窗偏好": {},
                "需要备注": True,
                "备注内容": "退回件已到，待入库校验",
                "需要飞书通知": True,
                "飞书通知内容": "订单ORDER-1 退回件到达，请入库校验后在前端确认",
                "人工原因": "",
                "下次处理天数": None,
            }
        )
        模拟飞书服务 = MagicMock()
        模拟飞书服务.发送售后通知 = AsyncMock(return_value={"success": True})

        with patch("tasks.售后任务.上报", new_callable=AsyncMock):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._售后页 = 模拟售后页
            任务._队列服务 = 模拟队列服务
            任务._规则服务 = 模拟规则服务
            任务._决策引擎 = 模拟决策引擎
            任务._飞书服务 = 模拟飞书服务

            结果 = await 任务._处理单条({"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "人工"
        模拟队列服务.更新阶段.assert_any_await(1, "等待验货", 处理结果="待入库校验")
        模拟售后页.详情页添加备注.assert_awaited_once_with("退回件已到，待入库校验")
        模拟飞书服务.发送售后通知.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_处理单条_按钮点击失败时尝试备选按钮(self, 模拟页面):
        模拟售后页 = 构造售后页()
        模拟售后页.点击指定按钮 = AsyncMock(side_effect=[False, True])
        模拟队列服务 = 构造队列服务()
        模拟规则服务 = MagicMock()
        模拟规则服务.匹配规则 = AsyncMock(return_value=[])
        模拟决策引擎 = MagicMock()
        模拟决策引擎.决策 = AsyncMock(
            return_value={
                "操作": "同意退款",
                "目标按钮": "同意退款",
                "备选按钮": ["同意拒收后退款"],
                "弹窗偏好": {},
                "需要备注": False,
                "备注内容": "",
                "需要飞书通知": False,
                "飞书通知内容": "",
                "人工原因": "",
                "下次处理天数": None,
            }
        )

        with patch("tasks.售后任务.上报", new_callable=AsyncMock):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._售后页 = 模拟售后页
            任务._队列服务 = 模拟队列服务
            任务._规则服务 = 模拟规则服务
            任务._决策引擎 = 模拟决策引擎

            结果 = await 任务._处理单条({"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}, {"shop_id": "shop-1"})

        assert 结果 == "已处理"
        assert 模拟售后页.点击指定按钮.await_args_list == [call("同意退款"), call("同意拒收后退款")]
