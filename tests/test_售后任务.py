"""售后任务单元测试。"""
from __future__ import annotations

import importlib
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest


def 构造队列服务():
    服务 = MagicMock()
    服务.创建批次 = AsyncMock(return_value="AS-shop-1-001")
    服务.批量写入队列 = AsyncMock(return_value=1)
    服务.获取待处理列表 = AsyncMock(
        return_value=[{"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}]
    )
    服务.更新详情 = AsyncMock(return_value=True)
    服务.更新阶段 = AsyncMock(return_value=True)
    服务.标记已被处理 = AsyncMock(return_value=True)
    服务.标记人工 = AsyncMock(return_value=True)
    服务.标记已完成 = AsyncMock(return_value=True)
    服务.获取批次统计 = AsyncMock(
        return_value={"总数": 1, "已完成": 1, "失败": 0, "人工": 0, "待处理": 0}
    )
    return 服务


def 构造售后页():
    页面对象 = MagicMock()
    页面对象.导航到售后列表 = AsyncMock()
    页面对象.确保待商家处理已选中 = AsyncMock()
    页面对象.扫描所有待处理 = AsyncMock(
        return_value=[
            {"订单号": "ORDER-1", "售后类型": "仅退款", "退款金额": "¥8.00", "商品名称": "测试商品"}
        ]
    )
    页面对象.搜索订单 = AsyncMock()
    页面对象.随机延迟 = AsyncMock()
    页面对象.点击订单详情并切换标签 = AsyncMock()
    页面对象.抓取详情页完整信息 = AsyncMock(
        return_value={"订单编号": "ORDER-1", "售后类型": "仅退款", "可用按钮列表": ["同意退款", "拒绝"]}
    )
    页面对象.检查是否需要处理 = AsyncMock(return_value=True)
    页面对象.点击指定按钮 = AsyncMock(return_value=True)
    页面对象.弹窗扫描循环 = AsyncMock(return_value="成功")
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
    async def test_执行_完整流程_扫描写队列并自动处理(self, 模拟回调, 模拟页面):
        模拟售后页 = 构造售后页()
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
                "需要备注": False,
                "备注内容": "",
                "需要飞书通知": False,
                "飞书通知内容": "",
                "人工原因": "",
            }
        )
        模拟飞书服务 = MagicMock()
        模拟飞书服务.发送售后通知 = AsyncMock(return_value={"success": True})

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), \
                patch("tasks.售后任务.售后页", return_value=模拟售后页):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._队列服务 = 模拟队列服务
            任务._规则服务 = 模拟规则服务
            任务._决策引擎 = 模拟决策引擎
            任务._飞书服务 = 模拟飞书服务

            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1", "shop_name": "店铺A"})

        assert 结果 == "处理1单, 人工0单, 跳过0单"
        模拟队列服务.创建批次.assert_awaited_once_with("shop-1")
        模拟队列服务.批量写入队列.assert_awaited_once()
        模拟售后页.点击指定按钮.assert_awaited_once_with("同意退款")
        模拟队列服务.标记已完成.assert_awaited_once_with(1, "同意退款成功")
        assert 任务._执行结果["总数"] == 1

    @pytest.mark.asyncio
    async def test_处理单条_详情页无操作按钮时跳过(self, 模拟页面):
        模拟售后页 = 构造售后页()
        模拟售后页.检查是否需要处理 = AsyncMock(return_value=False)
        模拟队列服务 = 构造队列服务()

        with patch("tasks.售后任务.上报", new_callable=AsyncMock):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._售后页 = 模拟售后页
            任务._队列服务 = 模拟队列服务
            结果 = await 任务._处理单条({"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}, {"shop_id": "shop-1"})

        assert 结果 == "跳过"
        模拟队列服务.标记已被处理.assert_awaited_once_with(1)
        模拟售后页.关闭详情标签.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_处理单条_弹窗返回人工时标记人工(self, 模拟页面):
        模拟售后页 = 构造售后页()
        模拟售后页.弹窗扫描循环 = AsyncMock(return_value="人工处理")
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
                "需要备注": False,
                "备注内容": "",
                "需要飞书通知": False,
                "飞书通知内容": "",
                "人工原因": "",
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

        assert 结果 == "人工"
        模拟队列服务.标记人工.assert_awaited_once_with(1, "弹窗无法自动处理")

    @pytest.mark.asyncio
    async def test_处理单条_拒绝场景回写拒绝次数和下次时间(self, 模拟页面):
        模拟售后页 = 构造售后页()
        模拟队列服务 = 构造队列服务()
        模拟规则服务 = MagicMock()
        模拟规则服务.匹配规则 = AsyncMock(return_value=[{"action": "拒绝"}])
        模拟决策引擎 = MagicMock()
        模拟决策引擎.决策 = AsyncMock(
            return_value={
                "操作": "拒绝",
                "目标按钮": "拒绝",
                "备选按钮": [],
                "弹窗偏好": {"选项偏好": ["无货"]},
                "需要备注": False,
                "备注内容": "",
                "需要飞书通知": False,
                "飞书通知内容": "",
                "人工原因": "",
            }
        )

        with patch("tasks.售后任务.上报", new_callable=AsyncMock):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._售后页 = 模拟售后页
            任务._队列服务 = 模拟队列服务
            任务._规则服务 = 模拟规则服务
            任务._决策引擎 = 模拟决策引擎

            结果 = await 任务._处理单条({"id": 1, "订单号": "ORDER-1", "拒绝次数": 1}, {"shop_id": "shop-1"})

        assert 结果 == "已处理"
        末次调用 = 模拟队列服务.更新阶段.await_args_list[-1]
        assert 末次调用.args == (1, "待处理")
        assert 末次调用.kwargs["拒绝次数"] == 2
        assert 末次调用.kwargs["处理结果"] == "拒绝第2次"
        assert 末次调用.kwargs["下次处理时间"]

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

    @pytest.mark.asyncio
    async def test_处理单条_搜不到订单时跳过(self, 模拟页面):
        模拟售后页 = 构造售后页()
        模拟售后页.点击订单详情并切换标签 = AsyncMock(side_effect=RuntimeError("not found"))
        模拟队列服务 = 构造队列服务()

        with patch("tasks.售后任务.上报", new_callable=AsyncMock):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            任务._售后页 = 模拟售后页
            任务._队列服务 = 模拟队列服务

            结果 = await 任务._处理单条({"id": 1, "订单号": "ORDER-1", "拒绝次数": 0}, {"shop_id": "shop-1"})

        assert 结果 == "跳过"
        模拟队列服务.标记已被处理.assert_awaited_once_with(1)
