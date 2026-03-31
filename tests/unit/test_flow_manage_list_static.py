"""
流程管理列表静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_流程管理列表静态页:
    def test_流程管理页_统计栏改为单行文案且列表改为表格(self):
        页面文件 = 读取文件("frontend/src/views/FlowManage.vue")

        for 关键字 in [
            'class="inline-stats"',
            '共 <strong>{{ totalFlows }}</strong> 个流程',
            '<strong>{{ totalSteps }}</strong> 个步骤',
            '<strong>{{ tasks.length }}</strong> 个可用任务',
            'class="flow-table"',
            '流程名称',
            '步骤摘要',
            'class="flow-name-link"',
            'href="#"',
            '@click.prevent="openEditModal(flow)"',
            'class="step-badge"',
            'class="ghost-button btn-sm"',
            'class="danger-button btn-sm"',
            "getStepSummary(flow) || '—'",
        ]:
            assert 关键字 in 页面文件

        for 旧结构 in [
            'class="summary-grid"',
            'class="summary-card"',
            'class="flow-grid"',
            'class="flow-card"',
        ]:
            assert 旧结构 not in 页面文件

    def test_流程管理页_表格样式保持紧凑密度(self):
        页面文件 = 读取文件("frontend/src/views/FlowManage.vue")

        for 关键字 in [
            '.inline-stats {',
            '.flow-table {',
            'table-layout: fixed;',
            'height: 44px;',
            '.cell-desc,',
            '.cell-summary {',
            '.cell-actions {',
            '.btn-sm {',
            '.flow-name-link:hover {',
        ]:
            assert 关键字 in 页面文件
