"""
流程参数导入静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_流程参数导入静态页:
    def test_flow_params_api_封装已存在(self):
        api文件 = 读取文件("frontend/src/api/flowParams.ts")

        for 关键字 in [
            "listFlowParams",
            "importFlowParams",
            "createFlowParam",
            "updateFlowParam",
            "deleteFlowParam",
            "clearFlowParams",
            "batchResetFlowParams",
            "batchEnableFlowParams",
            "batchDisableFlowParams",
            "/api/flow-params/import",
        ]:
            assert 关键字 in api文件

    def test_导入弹窗支持绑定流程并显示共享参数说明(self):
        store文件 = 读取文件("frontend/src/views/task-params/useTaskParamsStore.ts")
        弹窗文件 = 读取文件("frontend/src/views/task-params/ImportCsvModal.vue")

        for 关键字 in [
            "type ImportBindingMode = 'task' | 'flow'",
            "const importBindingMode = ref<ImportBindingMode>('task')",
            "const importFlowId = ref('')",
            "async function loadFlows()",
            "await importFlowParams(importFlowId.value, selectedFile.value)",
        ]:
            assert 关键字 in store文件

        for 关键字 in [
            "绑定任务",
            "绑定流程",
            "请选择流程",
            "流程模式下，除“店铺ID”外的列都会进入流程共享参数。",
            'class="space-y-5"',
            "border-brand-300 bg-white px-3 py-2 text-sm text-gray-900",
            "file:bg-brand-700",
            "text-sm font-medium text-gray-800",
            "text-xs text-gray-600",
        ]:
            assert 关键字 in 弹窗文件

        assert "<style" not in 弹窗文件
