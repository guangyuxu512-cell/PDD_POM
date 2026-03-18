"""售后页单元测试。"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class 测试_售后页:
    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        页面.goto = AsyncMock()
        页面.wait_for_selector = AsyncMock()
        页面.wait_for_load_state = AsyncMock()
        页面.query_selector_all = AsyncMock(return_value=[])
        页面.evaluate = AsyncMock()
        页面.screenshot = AsyncMock()
        页面.url = "https://mms.pinduoduo.com/aftersales/aftersale_list?msfrom=mms_sidenav"
        页面.context = MagicMock()
        页面.context.pages = [页面]
        页面.context.wait_for_event = AsyncMock()
        页面.locator = MagicMock()
        页面.mouse = MagicMock()
        页面.keyboard = MagicMock()
        页面.on = MagicMock()
        页面.remove_listener = MagicMock()
        页面.get_by_text = MagicMock()
        页面.get_by_placeholder = MagicMock()
        return 页面

    @pytest.mark.asyncio
    async def test_导航到售后列表_打开校准URL(self, 模拟页面):
        from pages.售后页 import 售后页

        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.页面加载延迟 = AsyncMock()

        await 页面对象.导航到售后列表()

        模拟页面.goto.assert_awaited_once_with(
            "https://mms.pinduoduo.com/aftersales/aftersale_list?msfrom=mms_sidenav",
            wait_until="domcontentloaded",
        )

    @pytest.mark.asyncio
    async def test_确保待商家处理已选中_已选中时不点击(self, 模拟页面):
        from pages.售后页 import 售后页

        模拟页面.evaluate = AsyncMock(return_value=True)
        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.页面加载延迟 = AsyncMock()
        页面对象.安全点击 = AsyncMock()

        await 页面对象.确保待商家处理已选中()

        页面对象.安全点击.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_确保待商家处理已选中_已选中但强制点击时再次点击(self, 模拟页面):
        from pages.售后页 import 售后页
        from selectors.售后页选择器 import 售后页选择器

        模拟页面.evaluate = AsyncMock(return_value=True)
        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.页面加载延迟 = AsyncMock()
        页面对象.安全点击 = AsyncMock()

        await 页面对象.确保待商家处理已选中(强制点击=True)

        页面对象.安全点击.assert_awaited_once_with(售后页选择器.待商家处理卡片.主选择器)
        页面对象.页面加载延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_确保待商家处理已选中_未选中时点击(self, 模拟页面):
        from pages.售后页 import 售后页
        from selectors.售后页选择器 import 售后页选择器

        模拟页面.evaluate = AsyncMock(return_value=False)
        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.页面加载延迟 = AsyncMock()
        页面对象.安全点击 = AsyncMock()

        await 页面对象.确保待商家处理已选中()

        页面对象.安全点击.assert_awaited_once_with(售后页选择器.待商家处理卡片.主选择器)
        页面对象.页面加载延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_批量抓取当前页_返回当前页所有售后单(self, 模拟页面):
        from pages.售后页 import 售后页

        模拟页面.evaluate = AsyncMock(
            return_value=[
                {"订单号": "ORDER-1", "售后类型": "退货退款"},
                {"订单号": "ORDER-2", "售后类型": "仅退款"},
            ]
        )
        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        结果 = await 页面对象.批量抓取当前页()

        assert 结果 == [
            {"订单号": "ORDER-1", "售后类型": "退货退款"},
            {"订单号": "ORDER-2", "售后类型": "仅退款"},
        ]
        模拟页面.wait_for_selector.assert_awaited_once_with(
            'div[class*="after-sales-table_order_item"]',
            timeout=8000,
        )
        模拟页面.evaluate.assert_awaited_once()
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_批量抓取当前页_空页时直接返回空列表(self, 模拟页面):
        from pages.售后页 import 售后页

        模拟页面.wait_for_selector = AsyncMock(side_effect=RuntimeError("empty"))
        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        结果 = await 页面对象.批量抓取当前页()

        assert 结果 == []
        模拟页面.evaluate.assert_not_awaited()
        页面对象.操作后延迟.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_拦截售后列表API_抓取并清洗接口响应(self, 模拟页面):
        from pages.售后页 import 售后页

        class 假响应:
            url = "https://mms.pinduoduo.com/mangkhut/afterSales/list"
            status = 200

            async def json(self):
                return {
                    "result": {
                        "list": [
                            {
                                "orderSn": "ORDER-1",
                                "id": 1001,
                                "refundAmount": 460,
                                "receiveAmount": 1299,
                                "afterSalesTypeName": "退货退款",
                                "afterSalesType": 2,
                                "afterSalesTitle": "待商家处理",
                                "afterSalesStatus": 10,
                                "afterSalesReasonDesc": "不想要了",
                                "goodsName": "测试商品",
                                "sellerAfterSalesShippingStatusDesc": "已发货",
                                "actions": ["agree_refund", "reject_refund"],
                                "expireRemainTime": 7200,
                            }
                        ]
                    }
                }

        def 注册监听(_事件, 回调):
            asyncio.get_running_loop().call_soon(回调, 假响应())

        模拟页面.on.side_effect = 注册监听
        页面对象 = 售后页(模拟页面)

        结果 = await 页面对象.拦截售后列表API(超时秒=1)

        assert 结果 == [
            {
                "订单号": "ORDER-1",
                "售后单ID": "1001",
                "退款金额": 4.6,
                "实收金额": 12.99,
                "售后类型": "退货退款",
                "售后类型码": 2,
                "售后状态": "待商家处理",
                "售后状态码": 10,
                "申请原因": "不想要了",
                "商品名称": "测试商品",
                "发货状态": "已发货",
                "操作码列表": ["agree_refund", "reject_refund"],
                "剩余处理秒数": 7200,
            }
        ]
        模拟页面.remove_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_拦截售后列表API_仅待商家处理时忽略默认列表响应(self, 模拟页面):
        from pages.售后页 import 售后页

        class 假响应:
            status = 200

            def __init__(self, url: str, 数据: dict):
                self.url = url
                self._数据 = 数据

            async def json(self):
                return self._数据

        响应列表 = [
            假响应(
                "https://mms.pinduoduo.com/mangkhut/afterSales/list?tab=all",
                {
                    "result": {
                        "list": [
                            {
                                "orderSn": "ORDER-ALL",
                                "id": 1,
                                "refundAmount": 100,
                                "receiveAmount": 200,
                                "afterSalesTitle": "已处理",
                            }
                        ]
                    }
                },
            ),
            假响应(
                "https://mms.pinduoduo.com/mangkhut/afterSales/list?afterSalesStatus=10",
                {
                    "result": {
                        "list": [
                            {
                                "orderSn": "ORDER-PENDING",
                                "id": 2,
                                "refundAmount": 300,
                                "receiveAmount": 400,
                                "afterSalesTitle": "待商家处理",
                            }
                        ]
                    }
                },
            ),
        ]

        def 注册监听(_事件, 回调):
            for 响应 in 响应列表:
                asyncio.get_running_loop().call_soon(回调, 响应)

        模拟页面.on.side_effect = 注册监听
        页面对象 = 售后页(模拟页面)

        结果 = await 页面对象.拦截售后列表API(超时秒=1, 仅待商家处理=True)

        assert 结果 == [
            {
                "订单号": "ORDER-PENDING",
                "售后单ID": "2",
                "退款金额": 3.0,
                "实收金额": 4.0,
                "售后类型": "",
                "售后类型码": 0,
                "售后状态": "待商家处理",
                "售后状态码": 0,
                "申请原因": "",
                "商品名称": "",
                "发货状态": "",
                "操作码列表": [],
                "剩余处理秒数": 0,
            }
        ]

    @pytest.mark.asyncio
    async def test_拦截售后列表API_只保留最后一次有效响应并按订单号去重(self, 模拟页面):
        from pages.售后页 import 售后页

        class 假响应:
            url = "https://mms.pinduoduo.com/mangkhut/afterSales/list"
            status = 200

            def __init__(self, 数据):
                self._数据 = 数据

            async def json(self):
                return self._数据

        响应列表 = [
            假响应(
                {
                    "result": {
                        "list": [
                            {
                                "orderSn": "ORDER-OLD",
                                "id": 1,
                                "refundAmount": 100,
                                "receiveAmount": 200,
                            }
                        ]
                    }
                }
            ),
            假响应(
                {
                    "result": {
                        "list": [
                            {
                                "orderSn": "ORDER-NEW",
                                "id": 2,
                                "refundAmount": 300,
                                "receiveAmount": 400,
                            },
                            {
                                "orderSn": "ORDER-NEW",
                                "id": 3,
                                "refundAmount": 500,
                                "receiveAmount": 600,
                            },
                        ]
                    }
                }
            ),
        ]

        def 注册监听(_事件, 回调):
            for 响应 in 响应列表:
                asyncio.get_running_loop().call_soon(回调, 响应)

        模拟页面.on.side_effect = 注册监听
        页面对象 = 售后页(模拟页面)

        结果 = await 页面对象.拦截售后列表API(超时秒=1)

        assert 结果 == [
            {
                "订单号": "ORDER-NEW",
                "售后单ID": "2",
                "退款金额": 3.0,
                "实收金额": 4.0,
                "售后类型": "",
                "售后类型码": 0,
                "售后状态": "",
                "售后状态码": 0,
                "申请原因": "",
                "商品名称": "",
                "发货状态": "",
                "操作码列表": [],
                "剩余处理秒数": 0,
            }
        ]

    @pytest.mark.asyncio
    async def test_导航并拦截售后列表_点击待处理后批量抓取第一页(self, 模拟页面):
        from pages.售后页 import 售后页

        页面对象 = 售后页(模拟页面)
        页面对象.导航到售后列表 = AsyncMock()
        页面对象.确保待商家处理已选中 = AsyncMock()
        页面对象.安全点击 = AsyncMock()
        页面对象.页面加载延迟 = AsyncMock()
        页面对象.批量抓取当前页 = AsyncMock(
            return_value=[{"订单号": "ORDER-2", "售后类型": "仅退款"}]
        )

        结果 = await 页面对象.导航并拦截售后列表()

        assert 结果 == [{"订单号": "ORDER-2", "售后类型": "仅退款"}]
        页面对象.导航到售后列表.assert_awaited_once()
        页面对象.确保待商家处理已选中.assert_awaited_once_with(强制点击=True)
        页面对象.批量抓取当前页.assert_awaited_once()
        页面对象.安全点击.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_导航并拦截售后列表_当前页为空时返回空列表(self, 模拟页面):
        from pages.售后页 import 售后页

        页面对象 = 售后页(模拟页面)
        页面对象.导航到售后列表 = AsyncMock()
        页面对象.确保待商家处理已选中 = AsyncMock()
        页面对象.批量抓取当前页 = AsyncMock(return_value=[])

        结果 = await 页面对象.导航并拦截售后列表()

        assert 结果 == []
        页面对象.确保待商家处理已选中.assert_awaited_once_with(强制点击=True)
        页面对象.批量抓取当前页.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_翻页并拦截_无下一页直接返回None(self, 模拟页面):
        from pages.售后页 import 售后页

        页面对象 = 售后页(模拟页面)
        页面对象._检查有下一页 = AsyncMock(return_value=False)
        页面对象.翻页 = AsyncMock()
        页面对象.拦截售后列表API = AsyncMock()

        结果 = await 页面对象.翻页并拦截()

        assert 结果 is None
        页面对象.翻页.assert_not_awaited()
        页面对象.拦截售后列表API.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_翻页并拦截_成功返回下一页数据(self, 模拟页面):
        from pages.售后页 import 售后页

        页面对象 = 售后页(模拟页面)
        页面对象._检查有下一页 = AsyncMock(return_value=True)
        页面对象.翻页 = AsyncMock(return_value=True)
        页面对象.批量抓取当前页 = AsyncMock(
            return_value=[{"订单号": "ORDER-3", "售后类型": "退货退款"}]
        )

        结果 = await 页面对象.翻页并拦截()

        assert 结果 == [{"订单号": "ORDER-3", "售后类型": "退货退款"}]
        页面对象.翻页.assert_awaited_once()
        页面对象.批量抓取当前页.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_检查有下一页_BeastCore禁用态返回False(self, 模拟页面):
        from pages.售后页 import 售后页

        按钮定位器 = MagicMock()
        按钮定位器.get_attribute = AsyncMock(
            side_effect=[None, "PGT_next_5-163-0 PGT_disabled_5-163-0"]
        )
        列表定位器 = MagicMock()
        列表定位器.first = 按钮定位器
        模拟页面.locator.return_value = 列表定位器

        页面对象 = 售后页(模拟页面)

        结果 = await 页面对象._检查有下一页()

        assert 结果 is False

    def test_下一页按钮选择器_优先BeastCore分页(self):
        from selectors.售后页选择器 import 售后页选择器

        assert 售后页选择器.下一页按钮.主选择器 == '//li[@data-testid="beast-core-pagination-next"]'
        assert "//li[contains(@class, 'PGT_next')]" in 售后页选择器.下一页按钮.备选选择器
        assert "//li[contains(@class, 'ant-pagination-next')]" in 售后页选择器.下一页按钮.备选选择器

    @pytest.mark.asyncio
    async def test_获取售后单数量_通过JS读取真实列表行数量(self, 模拟页面):
        from pages.售后页 import 售后页

        模拟页面.evaluate = AsyncMock(return_value=3)
        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        结果 = await 页面对象.获取售后单数量()

        assert 结果 == 3
        模拟页面.evaluate.assert_awaited_once()
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_获取第N行信息_返回清洗后的完整字段(self, 模拟页面):
        from pages.售后页 import 售后页

        模拟页面.evaluate = AsyncMock(
            return_value={
                "订单号": "260311-138328215900728",
                "申请时间": "2026-03-14 17:13:26",
                "剩余处理时间": "5天8时29分52秒",
                "商品名称": "大捞粗篱用漏瓢防烫捞面勺大号大漏漏勺油炸木纹厨房用品孔家",
                "商品规格": "x1；富贵木柄特厚升级款【12#大漏】1支",
                "实收金额": "¥3.79",
                "退款金额": "退款：¥3.61",
                "发货状态": "已发货",
                "售后类型": "退货退款",
                "售后状态": "退货退款，待商家确认收货",
                "售后协商": "",
                "售后原因": "不想要了",
                "操作按钮": ["同意退款", "查看详情", "添加备注"],
            }
        )
        页面对象 = 售后页(模拟页面)
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        结果 = await 页面对象.获取第N行信息(1)

        assert 结果["订单号"] == "260311-138328215900728"
        assert 结果["申请时间"] == "2026-03-14 17:13:26"
        assert 结果["商品规格"] == "x1；富贵木柄特厚升级款【12#大漏】1支"
        assert 结果["退款金额"] == "退款：¥3.61"
        assert 结果["操作按钮"] == ["同意退款", "查看详情", "添加备注"]
        模拟页面.evaluate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_扫描所有待处理_只收集有订单号的数据(self, 模拟页面):
        from pages.售后页 import 售后页

        页面对象 = 售后页(模拟页面)
        页面对象.确保待商家处理已选中 = AsyncMock()
        页面对象.获取售后单数量 = AsyncMock(side_effect=[2, 1])
        页面对象.获取第N行信息 = AsyncMock(
            side_effect=[
                {"订单号": "ORDER-1", "售后类型": "退货退款"},
                {},
                {"订单号": "ORDER-2", "售后类型": "仅退款"},
            ]
        )
        页面对象.翻页 = AsyncMock(side_effect=[True, False])

        结果 = await 页面对象.扫描所有待处理()

        assert 结果 == [
            {"订单号": "ORDER-1", "售后类型": "退货退款"},
            {"订单号": "ORDER-2", "售后类型": "仅退款"},
        ]

    @pytest.mark.asyncio
    async def test_点击订单详情并切换标签_等待并切换到新标签(self, 模拟页面):
        from pages.售后页 import 售后页

        新页面 = MagicMock()
        新页面.wait_for_load_state = AsyncMock()
        新页面.wait_for_selector = AsyncMock()
        模拟页面.context.wait_for_event = AsyncMock(return_value=新页面)

        页面对象 = 售后页(模拟页面)
        页面对象.点击订单详情 = AsyncMock()
        页面对象._等待详情页区域 = AsyncMock(return_value=True)

        await 页面对象.点击订单详情并切换标签("ORDER-1001")

        页面对象.点击订单详情.assert_awaited_once_with("ORDER-1001")
        新页面.wait_for_load_state.assert_awaited_once_with("domcontentloaded")
        assert 页面对象._详情页 is 新页面

    @pytest.mark.asyncio
    async def test_检查是否需要处理_分别返回真和假(self, 模拟页面):
        from pages.售后页 import 售后页

        页面对象 = 售后页(模拟页面)
        页面对象.读取当前所有按钮 = AsyncMock(side_effect=[["同意退款", "拒绝"], ["查看物流"]])

        assert await 页面对象.检查是否需要处理() is True
        assert await 页面对象.检查是否需要处理() is False

    @pytest.mark.asyncio
    async def test_抓取详情页完整信息_返回完整dict(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(
            return_value={
                "订单编号": "ORDER-2001",
                "售后类型": "仅退款",
                "退款金额": 6.5,
                "可用按钮列表": ["同意退款", "拒绝"],
            }
        )
        详情页.wait_for_selector = AsyncMock()

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()
        页面对象._等待详情页区域 = AsyncMock(return_value=True)

        结果 = await 页面对象.抓取详情页完整信息()

        assert 结果["订单编号"] == "ORDER-2001"
        assert 结果["售后类型"] == "仅退款"
        assert 结果["可用按钮列表"] == ["同意退款", "拒绝"]

    @pytest.mark.asyncio
    async def test_弹窗扫描循环_纯确认框处理成功(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(
            side_effect=[
                {"文本": "确认处理", "按钮": ["确定"], "有选择框": False, "单选选项": [], "有输入框": False, "有翻页": False},
                None,
            ]
        )

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.随机延迟 = AsyncMock()
        页面对象._JS点击弹窗按钮 = AsyncMock(return_value=True)

        结果 = await 页面对象.弹窗扫描循环()

        assert 结果 == "成功"
        页面对象._JS点击弹窗按钮.assert_awaited_once_with(详情页, "确定")

    @pytest.mark.asyncio
    async def test_弹窗扫描循环_单选偏好命中(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(
            side_effect=[
                {"文本": "请选择原因", "按钮": ["提交"], "有选择框": False, "单选选项": ["质量问题"], "有输入框": False, "有翻页": False},
                None,
            ]
        )

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.随机延迟 = AsyncMock()
        页面对象._JS点击包含文本 = AsyncMock(return_value=True)
        页面对象._JS点击弹窗按钮 = AsyncMock(return_value=True)

        结果 = await 页面对象.弹窗扫描循环({"选项偏好": ["质量问题"]})

        assert 结果 == "成功"
        页面对象._JS点击包含文本.assert_awaited_once_with(详情页, "质量问题")

    @pytest.mark.asyncio
    async def test_弹窗扫描循环_下拉偏好命中(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(
            side_effect=[
                {"文本": "请选择物流", "按钮": ["提交"], "有选择框": True, "单选选项": [], "有输入框": False, "有翻页": False},
                None,
            ]
        )

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.随机延迟 = AsyncMock()
        页面对象._JS选择下拉选项 = AsyncMock(return_value=True)
        页面对象._JS点击弹窗按钮 = AsyncMock(return_value=True)

        结果 = await 页面对象.弹窗扫描循环({"下拉偏好": "顺丰"})

        assert 结果 == "成功"
        页面对象._JS选择下拉选项.assert_awaited_once_with(详情页, "顺丰")

    @pytest.mark.asyncio
    async def test_弹窗扫描循环_无法识别时返回人工处理(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(
            return_value={"文本": "复杂弹窗", "按钮": ["下一步"], "有选择框": False, "单选选项": ["A", "B"], "有输入框": False, "有翻页": True}
        )

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.随机延迟 = AsyncMock()
        页面对象.详情页截图 = AsyncMock(return_value="shot.png")

        结果 = await 页面对象.弹窗扫描循环()

        assert 结果 == "人工处理"
        页面对象.详情页截图.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_JS点击弹窗按钮_成功时才执行后置延迟(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(side_effect=[True, False])

        页面对象 = 售后页(模拟页面)
        页面对象.操作后延迟 = AsyncMock()

        assert await 页面对象._JS点击弹窗按钮(详情页, "确定") is True
        页面对象.操作后延迟.assert_awaited_once()

        页面对象.操作后延迟.reset_mock()
        assert await 页面对象._JS点击弹窗按钮(详情页, "取消") is False
        页面对象.操作后延迟.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_点击指定按钮_JS执行(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(side_effect=[True, False])

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        assert await 页面对象.点击指定按钮("同意退款") is True
        页面对象.操作后延迟.assert_awaited_once()

        页面对象.操作后延迟.reset_mock()
        assert await 页面对象.点击指定按钮("不存在按钮") is False
        页面对象.操作后延迟.assert_not_awaited()

        首次调用参数 = 详情页.evaluate.await_args_list[0].args[1]
        assert 'a[data-testid="beast-core-button-link"]' in 首次调用参数["按钮选择器"]
        assert 'a[data-testid="beast-core-button"]' in 首次调用参数["按钮选择器"]

    @pytest.mark.asyncio
    async def test_读取当前所有按钮_JS参数覆盖新版data_testid选择器(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(return_value=["同意退款", "驳回退款"])

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        结果 = await 页面对象.读取当前所有按钮()

        assert 结果 == ["同意退款", "驳回退款"]
        assert 'a[data-testid="beast-core-button-link"]' in 详情页.evaluate.await_args.args[1]
        assert 'a[data-testid="beast-core-button"]' in 详情页.evaluate.await_args.args[1]

    @pytest.mark.asyncio
    async def test_详情页截图_保存到截图目录(self, 模拟页面, tmp_path):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.screenshot = AsyncMock()

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        with patch("pages.售后页.配置实例") as 配置实例模拟:
            配置实例模拟.DATA_DIR = str(tmp_path)
            结果 = await 页面对象.详情页截图("detail-case")

        assert 结果 == str(tmp_path / "screenshots" / "detail-case.png")
        详情页.screenshot.assert_awaited_once_with(
            path=str(tmp_path / "screenshots" / "detail-case.png"),
            full_page=True,
        )

    @pytest.mark.asyncio
    async def test_列表页添加备注_成功保存(self, 模拟页面):
        from pages.售后页 import 售后页

        页面对象 = 售后页(模拟页面)
        页面对象.安全点击 = AsyncMock()
        页面对象.安全填写 = AsyncMock()
        页面对象.随机延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        结果 = await 页面对象.列表页添加备注("ORDER-1", "转人工处理")

        assert 结果 is True
        assert 页面对象.安全点击.await_count == 2
        页面对象.安全填写.assert_awaited_once()
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_详情页添加备注_成功保存(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象._点击目标页面元素 = AsyncMock()
        页面对象._填写目标页面元素 = AsyncMock()
        页面对象.随机延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()

        结果 = await 页面对象.详情页添加备注("需要人工复核")

        assert 结果 is True
        assert 页面对象._点击目标页面元素.await_count == 2
        页面对象._填写目标页面元素.assert_awaited_once()
        页面对象.操作后延迟.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_抓取退货物流信息_有退货物流时返回解析结果(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(
            return_value={
                "有退货物流": True,
                "退货快递公司": "极兔速递",
                "退货快递单号": "JT123456",
                "轨迹全文": "完整物流",
                "轨迹列表": [{"时间": "2026-03-16 10:00", "描述": "快递员陈喜德正在派件"}],
                "最新轨迹": {"时间": "2026-03-16 10:00", "描述": "快递员陈喜德正在派件"},
                "退货物流状态": "快递员陈喜德正在派件",
                "派件人": "陈喜德",
                "网点": "合肥站点",
            }
        )

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象._点击目标页面元素 = AsyncMock()
        页面对象.随机延迟 = AsyncMock()

        结果 = await 页面对象.抓取退货物流信息()

        assert 结果["有退货物流"] is True
        assert 结果["退货快递公司"] == "极兔速递"
        assert 结果["退货物流状态"] == "快递员陈喜德正在派件"
        assert 页面对象._点击目标页面元素.await_count >= 1

    @pytest.mark.asyncio
    async def test_抓取退货物流信息_没有Tab时返回无物流(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象._点击目标页面元素 = AsyncMock(side_effect=RuntimeError("not found"))
        页面对象.随机延迟 = AsyncMock()

        结果 = await 页面对象.抓取退货物流信息()

        assert 结果 == {"有退货物流": False}

    @pytest.mark.asyncio
    async def test_抓取详情页完整信息_JS参数覆盖新版data_testid选择器(self, 模拟页面):
        from pages.售后页 import 售后页

        详情页 = MagicMock()
        详情页.evaluate = AsyncMock(return_value={"订单编号": "ORDER-3001", "可用按钮列表": ["同意退款"]})
        详情页.wait_for_selector = AsyncMock()

        页面对象 = 售后页(模拟页面)
        页面对象._详情页 = 详情页
        页面对象.操作前延迟 = AsyncMock()
        页面对象.操作后延迟 = AsyncMock()
        页面对象._等待详情页区域 = AsyncMock(return_value=True)

        结果 = await 页面对象.抓取详情页完整信息()

        assert 结果["订单编号"] == "ORDER-3001"
        assert 'a[data-testid="beast-core-button-link"]' in 详情页.evaluate.await_args.args[1]
        assert 'a[data-testid="beast-core-button"]' in 详情页.evaluate.await_args.args[1]
