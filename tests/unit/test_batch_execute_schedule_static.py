"""
批量执行与定时任务页静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_批量执行页静态结构:
    def test_批量执行页改为_brand_双栏和表格详情(self):
        页面文件 = 读取文件("frontend/src/views/BatchExecute.vue")

        for 关键字 in [
            "type ExecuteMode = 'flow' | 'task'",
            "const mode = ref<ExecuteMode>('flow')",
            "selectedShopIds",
            "selectedInputSetId",
            "loadFlowInputSets",
            "listFlowInputSets",
            "toggleSelectAll",
            "submitStart",
            "createBatchStatusEventSource",
            "批量执行",
            "执行配置",
            "流程模式",
            "单任务模式",
            "流程输入集",
            "不使用输入集，沿用 flow_params",
            "目标店铺",
            "已选择 {{ selectedShopIds.length }} / {{ totalShops }}",
            "执行状态",
            "当前步骤",
            "进度",
            "查看详情",
            "收起详情",
            "最近更新：",
            "getProgressBarClass",
            "getStatusClass",
            "getDetailSummary",
            "rounded-md border border-brand-300/50 bg-white p-5 shadow-sm",
            "bg-brand-700/10 text-xs font-medium uppercase tracking-wider text-brand-700",
        ]:
            assert 关键字 in 页面文件

        assert "ExecuteConfigPanel" not in 页面文件
        assert not (仓库根目录 / "frontend/src/views/batch-execute/ExecuteConfigPanel.vue").exists()
        assert not (仓库根目录 / "frontend/src/views/batch-execute/BatchStatusPanel.vue").exists()
        assert "<style" not in 页面文件

    def test_批量执行页使用_brand_状态色与进度条(self):
        页面文件 = 读取文件("frontend/src/views/BatchExecute.vue")

        for 关键字 in [
            "bg-brand-100 text-brand-700",
            "bg-amber-100 text-amber-700",
            "bg-emerald-100 text-emerald-700",
            "bg-rose-100 text-rose-700",
            "bg-brand-300/40 text-brand-700",
            "bg-amber-500",
            "bg-emerald-500",
            "bg-rose-500",
            "bg-brand-300",
            "rounded-md bg-brand-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-brand-700",
            "rounded-md bg-rose-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-rose-700",
        ]:
            assert 关键字 in 页面文件


class 测试_定时任务页静态结构:
    def test_定时任务页切换为品牌表格_listbox_和_tabgroup(self):
        页面文件 = 读取文件("frontend/src/views/ScheduleManage.vue")

        for 关键字 in [
            'class="inline-stats text-sm text-brand-500"',
            '<table class="schedule-table min-w-[1040px] w-full table-fixed divide-y divide-brand-300/30">',
            "开关",
            "任务名称",
            "执行流程",
            "执行周期",
            "上次执行",
            "下次执行",
            "目标店铺数",
            'class="switch inline-flex cursor-pointer items-center"',
            'class="switch-slider relative h-6 w-11 rounded-full bg-gray-200 transition',
            'class="count-badge inline-flex items-center justify-center rounded-full bg-brand-100 px-2.5 py-1 text-xs font-medium text-brand-700"',
            'width="min(80vw, 900px)"',
            '<Listbox v-model="form.flowId">',
            '<Listbox v-model="form.concurrency">',
            '<Listbox v-model="form.overlapPolicy">',
            "<TabGroup",
            "overflow-x-auto",
            "当前还没有定时任务。",
            "import Modal from '../components/Modal.vue'",
        ]:
            assert 关键字 in 页面文件

        for 旧结构 in [
            'class="summary-grid"',
            'class="summary-card"',
            'class="schedule-grid"',
            'class="schedule-card"',
            ':deep(.modal-container)',
            "<style",
            "<select",
        ]:
            assert 旧结构 not in 页面文件

    def test_定时任务页紧凑布局依赖_brand_原子类(self):
        页面文件 = 读取文件("frontend/src/views/ScheduleManage.vue")

        for 关键字 in [
            "border-b border-brand-300/30 transition hover:bg-brand-100/50",
            "font-mono text-xs text-brand-500",
            "peer-checked:bg-brand-500",
            "peer-checked:after:translate-x-5",
            "grid grid-cols-2 gap-2 rounded-md bg-brand-100 p-1",
            "rounded-md border border-brand-300/50 bg-brand-100 p-4",
            "focus:ring-1 focus:ring-brand-500",
        ]:
            assert 关键字 in 页面文件

        for 旧样式片段 in [
            ".schedule-table {",
            ".schedule-table td {",
            ".cell-actions {",
            ".name-link {",
            ".switch-slider {",
            ".count-badge {",
        ]:
            assert 旧样式片段 not in 页面文件
