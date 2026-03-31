"""
流程编辑器静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_流程编辑器静态页:
    def test_流程编辑弹窗改为紧凑表格并放大尺寸(self):
        页面文件 = 读取文件("frontend/src/views/FlowManage.vue")

        for 关键字 in [
            'width="min(80vw, 900px)"',
            ':deep(.modal-container)',
            'max-height: 80vh',
            'class="step-table-shell"',
            'class="step-table-header"',
            'class="step-row"',
            '序号',
            '任务',
            '失败策略',
            '同步屏障',
            '合并执行',
            '操作',
            '+ 添加步骤',
        ]:
            assert 关键字 in 页面文件

    def test_流程编辑弹窗保留新增聚焦_拖拽插入线和保存校验(self):
        页面文件 = 读取文件("frontend/src/views/FlowManage.vue")

        for 关键字 in [
            'const taskSelectRefs = ref<Record<string, HTMLSelectElement | null>>({})',
            'async function focusTaskSelect(stepId: string)',
            'await focusTaskSelect(step.id)',
            'const dropIndicator = ref<DropIndicator | null>(null)',
            'function handleDragOver(stepId: string, event: DragEvent)',
            'function handleDrop(stepId: string)',
            "'drop-before'",
            "'drop-after'",
            '请至少添加一个步骤',
            '请为每个步骤选择任务',
        ]:
            assert 关键字 in 页面文件
