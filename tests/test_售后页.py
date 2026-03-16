"""售后页单元测试。"""
from __future__ import annotations

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
