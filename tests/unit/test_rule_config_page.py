"""
规则配置页静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_规则配置页:
    """校验规则配置页骨架、筛选器和 API 调用。"""

    def test_规则配置页包含_headless_ui筛选器与_modal(self):
        页面文件 = 读取文件("frontend/src/views/RuleManage.vue")

        for 关键字 in [
            "规则配置",
            "+ 新建规则",
            "测试匹配",
            "筛选:",
            "全部平台",
            "全部业务",
            "全部店铺",
            "🧾 暂无规则，点击上方&quot;新建规则&quot;添加",
            "编辑规则",
            "规则名称",
            "业务类型",
            "优先级",
            "逻辑关系",
            "+ 添加条件",
            "+ 添加动作",
            "页面操作",
            "微信通知",
            "飞书通知",
            "标记",
            "同意退款",
            "同意退货",
            "拒绝",
            "发消息",
            "发工单",
            "人工审核",
            "匹配测试",
            "命中规则",
            "动作:",
            'list="rule-field-options"',
            '<datalist id="rule-field-options">',
            "showTitle",
            "<Modal :show=\"showEditor\"",
            "<Modal :show=\"showTestMatch\"",
            '<Listbox v-model="filter.platform">',
            '<Listbox v-model="filter.business">',
            '<Listbox v-model="filter.shop_id">',
            '<Listbox v-model="form.platform">',
            '<Listbox v-model="form.business">',
            '<Listbox v-model="form.shop_id">',
            '<Listbox v-model="form.conditions.operator">',
            '<Listbox v-model="condition.op">',
            '<Listbox v-model="action.action">',
            "overflow-x-auto",
        ]:
            assert 关键字 in 页面文件

        for 已移除关键字 in [
            "modal-overlay",
            "modal-content",
            "<style",
            "<select",
        ]:
            assert 已移除关键字 not in 页面文件

    def test_规则配置页调用规则与店铺接口(self):
        页面文件 = 读取文件("frontend/src/views/RuleManage.vue")

        for 关键字 in [
            "listShops",
            "get<RuleListResponse | Rule[]>",
            "/api/rules",
            "/api/rules/match",
            "post('/api/rules'",
            "put(`/api/rules/${editingRuleId.value}`",
            "del(`/api/rules/${rule.id}`)",
            "put(`/api/rules/${rule.id}/toggle`",
            "toast.success",
            "toast.error",
            "window.confirm",
            "if (!window.confirm(`确定删除规则 ${rule.name}？`)) {",
        ]:
            assert 关键字 in 页面文件

    def test_规则配置页不再出现在数据管理页(self):
        数据页文件 = 读取文件("frontend/src/views/DataManage.vue")

        assert "RuleManage" not in 数据页文件
        assert "规则配置" not in 数据页文件
