"""
流程编辑器静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_流程编辑器静态页:
    def test_流程编辑弹窗切换为_headless_ui_与_brand_结构(self):
        页面文件 = 读取文件("frontend/src/views/FlowManage.vue")

        for 关键字 in [
            "import Modal from '../components/Modal.vue'",
            "<Modal",
            'width="min(80vw, 900px)"',
            'class="step-table-shell overflow-hidden rounded-md border border-brand-300/50 bg-white"',
            'class="step-table-header grid',
            'class="step-row relative grid',
            '<Listbox v-model="step.task">',
            '<Listbox v-model="step.failurePolicy">',
            'class="field-hint text-xs text-brand-500"',
            "流程名称",
            "流程说明",
            "步骤编排",
            "+ 添加步骤",
        ]:
            assert 关键字 in 页面文件

        for 已移除关键字 in [
            ":deep(.modal-container)",
            "max-height: 80vh",
            "<style",
            "<select",
        ]:
            assert 已移除关键字 not in 页面文件

    def test_流程编辑弹窗保留聚焦_拖拽和保存校验逻辑(self):
        页面文件 = 读取文件("frontend/src/views/FlowManage.vue")

        for 关键字 in [
            "const taskSelectRefs = ref<Record<string, HTMLElement | null>>({})",
            "async function focusTaskSelect(stepId: string)",
            "await focusTaskSelect(step.id)",
            "const dropIndicator = ref<DropIndicator | null>(null)",
            "function handleDragOver(stepId: string, event: DragEvent)",
            "function handleDrop(stepId: string)",
            "dropIndicator.position === 'before'",
            "dropIndicator.position === 'after'",
            "before:absolute before:left-3 before:right-3 before:top-0",
            "after:absolute after:left-3 after:right-3 after:bottom-0",
            "流程至少需要一个步骤",
            "请为每个步骤选择任务",
            'class="sr-only"',
            'type="text"',
            "readonly",
        ]:
            assert 关键字 in 页面文件

    def test_流程编辑弹窗保留紧凑表格布局与动作控件(self):
        页面文件 = 读取文件("frontend/src/views/FlowManage.vue")

        for 关键字 in [
            "min-w-[860px]",
            "grid-cols-[44px_48px_minmax(220px,1.5fr)_minmax(220px,1.2fr)_92px_92px_72px]",
            "row-handle inline-flex h-6 w-6 items-center justify-center rounded-md",
            "icon-danger-button inline-flex h-7 w-7 items-center justify-center rounded-md",
            "retry-inline-input w-full rounded-md border border-brand-300/50 bg-white px-3 py-2 text-sm text-gray-900",
            "focus:ring-1 focus:ring-brand-500",
            "bg-brand-700/10",
        ]:
            assert 关键字 in 页面文件

        for 旧样式片段 in [
            ".step-table-header {",
            ".step-table-body {",
            ".step-row {",
            ".row-handle {",
            ".icon-danger-button {",
        ]:
            assert 旧样式片段 not in 页面文件
