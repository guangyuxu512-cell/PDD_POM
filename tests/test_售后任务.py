"""售后任务单元测试。"""
from __future__ import annotations

import importlib
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def 构造售后配置(**覆盖) -> dict:
    配置 = {
        "启用自动售后": True,
        "不支持自动处理类型": ["补寄", "维修", "换货"],
        "每批最大处理数": 50,
        "退货物流白名单": [],
        "退货等待时间": {"刚发出": 3, "中途运输": 1, "到达目的市": 0.25},
        "需要入库校验": False,
        "自动退款金额上限": 50,
        "仅退款_启用": True,
        "仅退款_自动同意金额上限": 10,
        "仅退款_需要拒绝": False,
        "仅退款_最大拒绝次数": 3,
        "仅退款_拒绝后等待分钟": 30,
        "仅退款_有图片转人工": True,
        "仅退款_拒收退回自动同意": True,
        "拒收退款_启用": True,
        "拒收退款_需要检查物流": True,
        "飞书通知_启用": True,
        "飞书通知_webhook": "",
        "弹窗偏好": {},
        "备注模板": {"人工": "转人工处理", "拒绝": "系统拒绝第{n}次"},
    }
    配置.update(覆盖)
    return 配置


def 构造队列服务(待处理列表序列: list | None = None):
    服务 = MagicMock()
    服务.创建批次 = AsyncMock(return_value="AS-shop-1-001")
    服务.批量写入队列 = AsyncMock(return_value=1)
    服务.获取待处理列表 = AsyncMock(
        side_effect=待处理列表序列
        or [[{"id": 1, "订单号": "ORDER-1", "售后类型": "退货退款", "拒绝次数": 0}]]
    )
    服务.获取到期记录 = AsyncMock(return_value=[])
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
    页面摘要序列: list[dict] | None = None,
    详情: dict | None = None,
    退货物流: dict | None = None,
    翻页序列: list[bool] | None = None,
    导航拦截结果: list[dict] | None = None,
    翻页拦截序列: list[list[dict] | None] | None = None,
):
    摘要序列 = 页面摘要序列 or [
        {
            "订单号": "ORDER-1",
            "售后类型": "退货退款",
            "售后状态": "待商家处理",
            "退款金额": "¥8.00",
            "商品名称": "测试商品",
        }
    ]
    页面对象 = MagicMock()
    页面对象.导航到售后列表 = AsyncMock()
    页面对象.确保待商家处理已选中 = AsyncMock()
    页面对象.导航并拦截售后列表 = AsyncMock(return_value=导航拦截结果 if 导航拦截结果 is not None else 摘要序列)
    页面对象.翻页并拦截 = AsyncMock(side_effect=翻页拦截序列 or [None])
    页面对象.获取售后单数量 = AsyncMock(side_effect=[len(摘要序列)])
    页面对象.获取第N行信息 = AsyncMock(side_effect=摘要序列)
    页面对象.翻页 = AsyncMock(side_effect=翻页序列 or [False])
    页面对象.列表页添加备注 = AsyncMock(return_value=True)
    页面对象.搜索订单 = AsyncMock()
    页面对象.随机延迟 = AsyncMock()
    页面对象.点击订单详情并切换标签 = AsyncMock()
    页面对象.抓取详情页完整信息 = AsyncMock(
        return_value=详情
        or {
            "订单编号": "ORDER-1",
            "售后类型": "退货退款",
            "可用按钮列表": ["同意退款", "拒绝"],
        }
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
    async def test_执行_启用自动售后关闭时直接返回(self, 模拟页面):
        模拟售后页 = 构造售后页()
        模拟队列服务 = 构造队列服务()
        模拟配置服务 = MagicMock()
        模拟配置服务.获取配置 = AsyncMock(return_value=构造售后配置(启用自动售后=False))

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
            "tasks.售后任务.售后页", return_value=模拟售后页
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务
            任务._配置服务 = 模拟配置服务

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "售后自动处理已关闭"
        模拟售后页.导航并拦截售后列表.assert_not_awaited()
        模拟售后页.导航到售后列表.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_执行_列表页分流使用配置中的不支持类型(self, 模拟页面):
        模拟售后页 = 构造售后页(
            页面摘要序列=[
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
            [[{"id": 1, "订单号": "ORDER-1", "售后类型": "补寄", "售后状态": "待商家处理"}]]
        )
        模拟配置服务 = MagicMock()
        模拟配置服务.获取配置 = AsyncMock(
            return_value=构造售后配置(不支持自动处理类型=["补寄"])
        )
        模拟飞书服务 = MagicMock()
        模拟飞书服务.发送售后通知 = AsyncMock(return_value={"success": True})

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
            "tasks.售后任务.售后页", return_value=模拟售后页
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务
            任务._配置服务 = 模拟配置服务
            任务._飞书服务 = 模拟飞书服务
            任务._处理单条 = AsyncMock()

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "处理0单, 人工1单, 跳过0单"
        模拟售后页.列表页添加备注.assert_awaited_once()
        模拟队列服务.标记人工.assert_awaited_once_with(1, "补寄不支持自动处理")
        任务._处理单条.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_执行_API拦截多页时不走逐行DOM扫描(self, 模拟页面):
        模拟售后页 = 构造售后页(
            页面摘要序列=[
                {
                    "订单号": "DOM-ONLY",
                    "售后类型": "退货退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥1.00",
                    "商品名称": "不应进入DOM路径",
                }
            ],
            导航拦截结果=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "退货退款",
                    "售后状态": "待商家处理",
                    "退款金额": 8.0,
                    "商品名称": "商品1",
                }
            ],
            翻页拦截序列=[
                [
                    {
                        "订单号": "ORDER-2",
                        "售后类型": "退货退款",
                        "售后状态": "待商家处理",
                        "退款金额": 9.0,
                        "商品名称": "商品2",
                    }
                ],
                None,
            ],
        )
        模拟队列服务 = 构造队列服务(
            [
                [{"id": 1, "订单号": "ORDER-1", "售后类型": "退货退款", "拒绝次数": 0}],
                [{"id": 2, "订单号": "ORDER-2", "售后类型": "退货退款", "拒绝次数": 0}],
            ]
        )
        模拟配置服务 = MagicMock()
        模拟配置服务.获取配置 = AsyncMock(return_value=构造售后配置())

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
            "tasks.售后任务.售后页", return_value=模拟售后页
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务
            任务._配置服务 = 模拟配置服务
            任务._处理单条 = AsyncMock(side_effect=["已处理", "跳过"])

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "处理1单, 人工0单, 跳过1单"
        模拟售后页.导航并拦截售后列表.assert_awaited_once()
        assert 模拟售后页.翻页并拦截.await_count == 2
        模拟售后页.获取售后单数量.assert_not_awaited()
        模拟售后页.获取第N行信息.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_执行_API拦截为空时回退JS扫描(self, 模拟页面):
        模拟售后页 = 构造售后页(
            页面摘要序列=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "退货退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥8.00",
                    "商品名称": "测试商品",
                }
            ],
            导航拦截结果=[],
        )
        模拟队列服务 = 构造队列服务()
        模拟配置服务 = MagicMock()
        模拟配置服务.获取配置 = AsyncMock(return_value=构造售后配置())

        with patch("tasks.售后任务.上报", new_callable=AsyncMock) as 模拟上报, patch(
            "tasks.售后任务.售后页", return_value=模拟售后页
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务
            任务._配置服务 = 模拟配置服务
            任务._处理单条 = AsyncMock(return_value="已处理")

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "处理1单, 人工0单, 跳过0单"
        assert any(
            调用.args == ("[扫描] 当前页未拦截到数据，尝试 JS fallback", "shop-1")
            for 调用 in 模拟上报.await_args_list
        )
        模拟售后页.获取售后单数量.assert_awaited()
        模拟售后页.获取第N行信息.assert_awaited()

    @pytest.mark.asyncio
    async def test_执行_每批最大处理数限制总处理量(self, 模拟页面):
        模拟售后页 = 构造售后页(
            页面摘要序列=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "退货退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥8.00",
                    "商品名称": "商品1",
                },
                {
                    "订单号": "ORDER-2",
                    "售后类型": "退货退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥9.00",
                    "商品名称": "商品2",
                },
            ]
        )
        模拟售后页.获取售后单数量 = AsyncMock(side_effect=[2])
        模拟售后页.获取第N行信息 = AsyncMock(
            side_effect=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "退货退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥8.00",
                    "商品名称": "商品1",
                },
                {
                    "订单号": "ORDER-2",
                    "售后类型": "退货退款",
                    "售后状态": "待商家处理",
                    "退款金额": "¥9.00",
                    "商品名称": "商品2",
                },
            ]
        )
        模拟队列服务 = 构造队列服务(
            [[
                {"id": 1, "订单号": "ORDER-1", "售后类型": "退货退款", "拒绝次数": 0},
                {"id": 2, "订单号": "ORDER-2", "售后类型": "退货退款", "拒绝次数": 0},
            ]]
        )
        模拟配置服务 = MagicMock()
        模拟配置服务.获取配置 = AsyncMock(return_value=构造售后配置(每批最大处理数=1))

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
            "tasks.售后任务.售后页", return_value=模拟售后页
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务
            任务._配置服务 = 模拟配置服务
            任务._处理单条 = AsyncMock(return_value="已处理")

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "处理1单, 人工0单, 跳过0单"
        任务._处理单条.assert_awaited_once()
        assert 任务._处理单条.await_args.args[0]["订单号"] == "ORDER-1"

    @pytest.mark.asyncio
    async def test_执行_API当前页重复订单写队列前会去重(self, 模拟页面):
        模拟售后页 = 构造售后页(
            导航拦截结果=[
                {
                    "订单号": "ORDER-1",
                    "售后类型": "退货退款",
                    "售后状态": "待商家处理",
                    "退款金额": 8.0,
                    "商品名称": "商品1-旧",
                },
                {
                    "订单号": "ORDER-1",
                    "售后类型": "退货退款",
                    "售后状态": "待商家处理",
                    "退款金额": 9.0,
                    "商品名称": "商品1-新",
                },
            ]
        )
        模拟队列服务 = 构造队列服务(
            [[{"id": 1, "订单号": "ORDER-1", "售后类型": "退货退款", "拒绝次数": 0}]]
        )
        模拟配置服务 = MagicMock()
        模拟配置服务.获取配置 = AsyncMock(return_value=构造售后配置())

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
            "tasks.售后任务.售后页", return_value=模拟售后页
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务
            任务._配置服务 = 模拟配置服务
            任务._处理单条 = AsyncMock(return_value="已处理")

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "处理1单, 人工0单, 跳过0单"
        写入记录列表 = 模拟队列服务.批量写入队列.await_args.args[0]
        assert len(写入记录列表) == 1
        assert 写入记录列表[0]["订单号"] == "ORDER-1"
        assert 写入记录列表[0]["退款金额"] == 9.0
        assert 写入记录列表[0]["商品名称"] == "商品1-新"

    @pytest.mark.asyncio
    async def test_处理单条_不再调用搜索订单且读取配置服务(self, 模拟页面):
        模拟售后页 = 构造售后页(
            详情={"订单编号": "ORDER-1", "售后类型": "仅退款", "可用按钮列表": ["查看物流"]}
        )
        模拟队列服务 = 构造队列服务()
        模拟配置服务 = MagicMock()
        模拟配置服务.获取配置 = AsyncMock(return_value=构造售后配置())
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
            任务._配置服务 = 模拟配置服务
            任务._决策引擎 = 模拟决策引擎

            结果 = await 任务._处理单条({"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}, {"shop_id": "shop-1"})

        assert 结果 == "跳过"
        模拟售后页.搜索订单.assert_not_awaited()
        模拟配置服务.获取配置.assert_awaited_once_with("shop-1")

    @pytest.mark.asyncio
    async def test_处理单条_等待场景写入下次处理时间(self, 模拟页面):
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
        模拟配置服务 = MagicMock()
        模拟配置服务.获取配置 = AsyncMock(return_value=构造售后配置())
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
            任务._配置服务 = 模拟配置服务
            任务._决策引擎 = 模拟决策引擎

            结果 = await 任务._处理单条({"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}, {"shop_id": "shop-1"})

        assert 结果 == "跳过"
        末次调用 = 模拟队列服务.更新阶段.await_args_list[-1]
        assert 末次调用.args == (1, "等待退回")
        assert 末次调用.kwargs["下次处理时间"]

    @pytest.mark.asyncio
    async def test_处理单条_人工处理时使用配置中的飞书webhook(self, 模拟页面):
        模拟售后页 = 构造售后页(
            详情={"订单编号": "ORDER-1", "订单号": "ORDER-1", "售后类型": "仅退款", "可用按钮列表": ["同意退款"]}
        )
        模拟队列服务 = 构造队列服务()
        模拟配置服务 = MagicMock()
        模拟配置服务.获取配置 = AsyncMock(
            return_value=构造售后配置(飞书通知_webhook="https://feishu.example")
        )
        模拟决策引擎 = MagicMock()
        模拟决策引擎.决策 = AsyncMock(
            return_value={
                "操作": "人工处理",
                "目标按钮": "",
                "备选按钮": [],
                "弹窗偏好": {},
                "需要备注": False,
                "备注内容": "",
                "需要飞书通知": True,
                "飞书通知内容": "需要人工处理",
                "人工原因": "人工审核",
                "下次处理天数": None,
            }
        )
        模拟飞书服务 = MagicMock()
        模拟飞书服务.发送售后通知 = AsyncMock(return_value={"success": True})

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), patch(
            "tasks.售后任务.飞书服务",
            return_value=模拟飞书服务,
        ):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._售后页 = 模拟售后页
            任务._队列服务 = 模拟队列服务
            任务._配置服务 = 模拟配置服务
            任务._决策引擎 = 模拟决策引擎

            结果 = await 任务._处理单条(
                {"id": 1, "订单号": "ORDER-1", "拒绝次数": 0},
                {"shop_id": "shop-1", "shop_name": "店铺A"},
            )

        assert 结果 == "人工"
        模拟飞书服务.发送售后通知.assert_awaited_once()
