"""
规则配置页静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_规则配置页:
    """校验规则配置页关键骨架与 API 调用。"""

    def test_规则配置页_包含核心交互结构(self):
        页面文件 = 读取文件("frontend/src/views/RuleManage.vue")

        for 关键字 in [
            "规则配置",
            "新建规则",
            "测试匹配",
            "筛选:",
            "全部平台",
            "全部业务",
            "全部店铺",
            "暂无规则，点击上方\"新建规则\"添加",
            "modal-overlay",
            "modal-content",
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
            "input",
            "datalist",
            "rule-field-options",
            "showTitle",
            "confirm(`确定删除规则 ${rule.name}？`)",
        ]:
            assert 关键字 in 页面文件

    def test_规则配置页_调用规则与店铺接口(self):
        页面文件 = 读取文件("frontend/src/views/RuleManage.vue")
        数据页文件 = 读取文件("frontend/src/views/DataManage.vue")

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
        ]:
            assert 关键字 in 页面文件

        assert "import RuleManage from './RuleManage.vue'" in 数据页文件
        assert '<RuleManage v-else :show-title="false" />' in 数据页文件
