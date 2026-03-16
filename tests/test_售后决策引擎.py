"""售后决策引擎单元测试。"""
from __future__ import annotations

import pytest

from backend.services.售后决策引擎 import 售后决策引擎


class 测试_售后决策引擎:
    @pytest.fixture
    def 引擎(self):
        return 售后决策引擎()

    @pytest.mark.asyncio
    async def test_退货退款_存在同意退货按钮时直接同意退货(self, 引擎):
        结果 = await 引擎.决策(
            {"售后类型": "退货退款", "可用按钮列表": ["同意退货", "拒绝"]},
            {},
            {},
        )
        assert 结果["操作"] == "同意退货"
        assert 结果["目标按钮"] == "同意退货"
        assert 结果["需要飞书通知"] is False

    @pytest.mark.asyncio
    async def test_退货退款_存在同意退款按钮时直接退款(self, 引擎):
        结果 = await 引擎.决策(
            {"售后类型": "退货退款", "可用按钮列表": ["同意退款"]},
            {},
            {},
        )
        assert 结果["操作"] == "同意退款"
        assert 结果["目标按钮"] == "同意退款"

    @pytest.mark.asyncio
    async def test_仅退款_小额自动同意并写备注(self, 引擎):
        结果 = await 引擎.决策(
            {"售后类型": "仅退款", "退款金额": 8, "可用按钮列表": ["同意退款", "拒绝"]},
            {"自动同意金额上限": 10},
            {"拒绝次数": 0},
        )
        assert 结果["操作"] == "同意退款"
        assert 结果["目标按钮"] == "同意退款"
        assert 结果["需要备注"] is True
        assert 结果["备注内容"] == "小额自动退款"

    @pytest.mark.asyncio
    async def test_仅退款_有售后图片时转人工(self, 引擎):
        结果 = await 引擎.决策(
            {
                "售后类型": "仅退款",
                "退款金额": 20,
                "有售后图片": True,
                "订单编号": "ORDER-1",
                "可用按钮列表": ["同意退款", "拒绝"],
            },
            {"自动同意金额上限": 10},
            {},
        )
        assert 结果["操作"] == "人工处理"
        assert 结果["人工原因"] == "有售后图片需人工查看"
        assert "ORDER-1" in 结果["飞书通知内容"]

    @pytest.mark.asyncio
    async def test_仅退款_物流拒收时优先同意拒收退款(self, 引擎):
        结果 = await 引擎.决策(
            {
                "售后类型": "仅退款",
                "退款金额": 30,
                "物流最新状态": "包裹拒收退回仓库",
                "可用按钮列表": ["同意拒收后退款", "拒绝"],
            },
            {"自动同意金额上限": 10},
            {},
        )
        assert 结果["操作"] == "同意拒收退款"
        assert 结果["目标按钮"] == "同意拒收后退款"
        assert 结果["需要飞书通知"] is False

    @pytest.mark.asyncio
    async def test_仅退款_规则要求拒绝且拒绝次数未满三次(self, 引擎):
        结果 = await 引擎.决策(
            {"售后类型": "仅退款", "退款金额": 30, "可用按钮列表": ["拒绝"]},
            {"自动同意金额上限": 10, "需要拒绝": True, "弹窗偏好": {"选项偏好": ["质量问题"]}},
            {"拒绝次数": 2},
        )
        assert 结果["操作"] == "拒绝"
        assert 结果["目标按钮"] == "拒绝"
        assert 结果["弹窗偏好"] == {"选项偏好": ["质量问题"]}
        assert 结果["备注内容"] == "系统拒绝第3次"

    @pytest.mark.asyncio
    async def test_仅退款_规则要求拒绝但已满三次时跳过(self, 引擎):
        结果 = await 引擎.决策(
            {
                "售后类型": "仅退款",
                "退款金额": 30,
                "订单编号": "ORDER-2",
                "可用按钮列表": ["拒绝"],
            },
            {"自动同意金额上限": 10, "需要拒绝": True},
            {"拒绝次数": 3},
        )
        assert 结果["操作"] == "跳过"
        assert 结果["人工原因"] == "已拒绝3次，不再自动处理"
        assert "ORDER-2" in 结果["飞书通知内容"]

    @pytest.mark.asyncio
    async def test_无操作按钮时直接跳过(self, 引擎):
        结果 = await 引擎.决策(
            {"售后类型": "仅退款", "可用按钮列表": ["查看物流"]},
            {},
            {},
        )
        assert 结果["操作"] == "跳过"
        assert 结果["需要飞书通知"] is False

    @pytest.mark.asyncio
    async def test_换货场景返回人工处理(self, 引擎):
        结果 = await 引擎.决策(
            {"售后类型": "换货", "可用按钮列表": ["同意换货"]},
            {},
            {},
        )
        assert 结果["操作"] == "人工处理"
        assert 结果["人工原因"] == "换货暂不支持自动处理"

    def test_找按钮按优先级返回首个匹配项(self, 引擎):
        结果 = 引擎._找按钮(
            ["同意退款", "同意拒收后退款", "拒绝"],
            ["同意拒收后退款", "同意退款"],
        )
        assert 结果 == "同意拒收后退款"
