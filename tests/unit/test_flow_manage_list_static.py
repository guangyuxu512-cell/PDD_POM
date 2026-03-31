"""
流程管理列表静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_流程管理列表静态页:
    def test_流程管理页改为_tailwind统计栏与表格列表(self):
        页面文件 = 读取文件("frontend/src/views/FlowManage.vue")

        for 关键字 in [
            'class="inline-stats text-sm text-gray-500"',
            "{{ totalFlows }}",
            "{{ totalSteps }}",
            "{{ tasks.length }}",
            '<table class="flow-table min-w-[920px] w-full table-fixed divide-y divide-gray-200">',
            "流程名称",
            "步骤摘要",
            'class="flow-name-link font-medium text-gray-900 underline-offset-4 transition hover:text-gray-700 hover:underline"',
            'href="#"',
            '@click.prevent="openEditModal(flow)"',
            'class="step-badge inline-flex min-w-8 items-center justify-center rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700"',
            'class="ghost-button btn-sm text-xs font-medium text-gray-500 transition hover:text-gray-700"',
            'class="danger-button btn-sm text-xs font-medium text-rose-600 transition hover:text-rose-700"',
            "getStepSummary(flow) ||",
            "🪹 当前还没有流程模板。",
            "overflow-x-auto",
        ]:
            assert 关键字 in 页面文件

        for 旧结构 in [
            'class="summary-grid"',
            'class="summary-card"',
            'class="flow-grid"',
            'class="flow-card"',
            "<style",
        ]:
            assert 旧结构 not in 页面文件

    def test_流程管理页表格密度依赖_tailwind原子类(self):
        页面文件 = 读取文件("frontend/src/views/FlowManage.vue")

        for 关键字 in [
            "table-fixed divide-y divide-gray-200",
            "border-b border-gray-100 transition hover:bg-gray-50/50",
            "font-mono text-xs text-gray-500",
            "max-w-0 truncate px-4 py-3 text-xs text-gray-500",
            "space-x-2 whitespace-nowrap px-4 py-3 text-center",
        ]:
            assert 关键字 in 页面文件

        for 旧样式片段 in [
            ".inline-stats {",
            ".flow-table {",
            ".cell-desc,",
            ".cell-summary {",
            ".cell-actions {",
            ".btn-sm {",
            ".flow-name-link:hover {",
        ]:
            assert 旧样式片段 not in 页面文件
