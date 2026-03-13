"""
流程参数导入静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_流程参数导入静态页:
    """校验前端已接入流程参数导入入口。"""

    def test_flow_params_api_封装已存在(self):
        API文件 = 读取文件("frontend/src/api/flowParams.ts")

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
            assert 关键字 in API文件

    def test_任务参数页_导入弹窗支持绑定流程(self):
        页面文件 = 读取文件("frontend/src/views/TaskParamsManage.vue")

        for 关键字 in [
            "importFlowParams",
            "listFlows",
            "type ImportBindingMode = 'task' | 'flow'",
            "const importBindingMode = ref<ImportBindingMode>('task')",
            "const importFlowId = ref('')",
            "const flows = ref<Flow[]>([])",
            "async function loadFlows()",
            "绑定任务",
            "绑定流程",
            "importBindingMode === 'flow'",
            "请选择流程",
            "绑定流程时，除“店铺ID”“发布次数”外，其余列都会进入共享参数池，并在步骤间自动共享。",
        ]:
            assert 关键字 in 页面文件
