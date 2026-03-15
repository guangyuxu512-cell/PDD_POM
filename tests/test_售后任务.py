"""售后任务单元测试。"""
from __future__ import annotations

import importlib
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class 测试_售后任务:
    @pytest.fixture
    def 模拟页面(self):
        return MagicMock()

    @pytest.fixture
    def 模拟售后页(self):
        页面对象 = MagicMock()
        页面对象.导航到售后列表 = AsyncMock()
        页面对象.切换待处理 = AsyncMock()
        页面对象.获取售后单数量 = AsyncMock(return_value=1)
        页面对象.获取第N行信息 = AsyncMock(
            return_value={
                "订单号": "A001",
                "售后类型": "仅退款",
                "退款金额": "8",
                "商品名称": "测试商品",
            }
        )
        页面对象.点击第N行操作 = AsyncMock()
        页面对象.处理确认弹窗 = AsyncMock(return_value=True)
        页面对象.截图 = AsyncMock(return_value="aftersale.png")
        return 页面对象

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
    async def test_状态机正常流转(self, 模拟回调, 模拟页面, 模拟售后页):
        规则服务实例 = MagicMock()
        规则服务实例.匹配规则 = AsyncMock(return_value=[{"type": "页面操作", "action": "同意退款"}])
        飞书服务实例 = MagicMock()
        飞书服务实例.发送售后通知 = AsyncMock(return_value={"success": True})

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), \
                patch("tasks.售后任务.售后页", return_value=模拟售后页), \
                patch("tasks.售后任务.规则服务", return_value=规则服务实例), \
                patch("tasks.售后任务.飞书服务", return_value=飞书服务实例):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1"})

        assert 结果 == "成功处理 1 单"
        模拟售后页.导航到售后列表.assert_awaited_once()
        模拟售后页.切换待处理.assert_awaited_once()
        模拟售后页.获取第N行信息.assert_awaited_once_with(1)
        模拟售后页.点击第N行操作.assert_awaited_once_with(1, "同意退款")
        模拟售后页.处理确认弹窗.assert_awaited_once()
        assert 任务._执行结果["处理数量"] == 1

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_售后单数量为0时直接完成(self, 模拟回调, 模拟页面, 模拟售后页):
        规则服务实例 = MagicMock()
        规则服务实例.匹配规则 = AsyncMock(return_value=[])
        模拟售后页.获取售后单数量 = AsyncMock(return_value=0)

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), \
                patch("tasks.售后任务.售后页", return_value=模拟售后页), \
                patch("tasks.售后任务.规则服务", return_value=规则服务实例):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1"})

        assert 结果 == "成功处理 0 单"
        模拟售后页.获取第N行信息.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_人工审核时跳过页面操作直接飞书通知(self, 模拟回调, 模拟页面, 模拟售后页):
        规则服务实例 = MagicMock()
        规则服务实例.匹配规则 = AsyncMock(
            return_value=[
                {"type": "标记", "action": "人工审核"},
                {"type": "飞书通知", "action": "发工单"},
            ]
        )
        飞书服务实例 = MagicMock()
        飞书服务实例.发送售后通知 = AsyncMock(return_value={"success": True})

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), \
                patch("tasks.售后任务.售后页", return_value=模拟售后页), \
                patch("tasks.售后任务.规则服务", return_value=规则服务实例), \
                patch("tasks.售后任务.飞书服务", return_value=飞书服务实例):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1"})

        assert 结果 == "成功处理 1 单"
        模拟售后页.点击第N行操作.assert_not_awaited()
        飞书服务实例.发送售后通知.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_微信通知分支(self, 模拟回调, 模拟页面, 模拟售后页):
        规则服务实例 = MagicMock()
        规则服务实例.匹配规则 = AsyncMock(
            return_value=[
                {"type": "微信通知", "action": "发消息", "template": "亲，您的退款 {退款金额} 元已处理~"},
            ]
        )
        微信实例 = MagicMock()
        微信实例.发送消息 = MagicMock(return_value=True)

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), \
                patch("tasks.售后任务.售后页", return_value=模拟售后页), \
                patch("tasks.售后任务.规则服务", return_value=规则服务实例), \
                patch("tasks.售后任务.微信页", return_value=微信实例), \
                patch("tasks.售后任务.asyncio.to_thread", new=AsyncMock(return_value=True)) as 模拟线程调用:
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            结果 = await 任务.执行(
                模拟页面,
                {"shop_id": "shop-1", "task_param": {"客户微信": "张三"}},
            )

        assert 结果 == "成功处理 1 单"
        assert 模拟线程调用.await_args.args[1] == "张三"
        assert "8" in 模拟线程调用.await_args.args[2]

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_飞书通知分支(self, 模拟回调, 模拟页面, 模拟售后页):
        规则服务实例 = MagicMock()
        规则服务实例.匹配规则 = AsyncMock(
            return_value=[{"type": "飞书通知", "action": "发工单"}]
        )
        飞书服务实例 = MagicMock()
        飞书服务实例.发送售后通知 = AsyncMock(return_value={"success": True})

        with patch("tasks.售后任务.上报", new_callable=AsyncMock), \
                patch("tasks.售后任务.售后页", return_value=模拟售后页), \
                patch("tasks.售后任务.规则服务", return_value=规则服务实例), \
                patch("tasks.售后任务.飞书服务", return_value=飞书服务实例):
            from tasks.售后任务 import 售后任务

            任务 = 售后任务()
            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1"})

        assert 结果 == "成功处理 1 单"
        飞书服务实例.发送售后通知.assert_awaited_once()

    def test_渲染模板_正确替换占位符(self):
        from tasks.售后任务 import 售后任务

        任务 = 售后任务()
        assert 任务._渲染模板("退款 {退款金额} 元，订单 {订单号}", {"退款金额": "8", "订单号": "A001"}) == "退款 8 元，订单 A001"

    @pytest.mark.asyncio
    @patch("browser.任务回调._回调", new_callable=AsyncMock)
    async def test_最大迭代安全限制(self, 模拟回调, 模拟页面):
        with patch("tasks.售后任务.上报", new_callable=AsyncMock) as 模拟上报:
            from tasks.售后任务 import 售后任务, 售后状态

            任务 = 售后任务()
            任务._执行状态 = AsyncMock(return_value=售后状态.初始化)
            结果 = await 任务.执行(模拟页面, {"shop_id": "shop-1"})

        assert 结果 == "失败"
        模拟上报.assert_any_await("[失败] 状态机迭代超限", "shop-1")
