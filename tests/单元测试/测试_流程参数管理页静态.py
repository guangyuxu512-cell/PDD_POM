"""
流程参数管理页静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_流程参数管理页静态:
    """验证任务参数页已接入 flow_params 列表与操作入口。"""

    def test_flow_params_api_包含单条与批量方法(self):
        API文件 = 读取文件("frontend/src/api/flowParams.ts")

        for 关键字 in [
            "listFlowParams",
            "deleteFlowParam",
            "resetFlowParam",
            "enableFlowParam",
            "disableFlowParam",
            "batchResetFlowParams",
            "batchEnableFlowParams",
            "batchDisableFlowParams",
            "clearFlowParams",
        ]:
            assert 关键字 in API文件

    def test_页面骨架_新增流程参数tab和列表(self):
        页面文件 = 读取文件("frontend/src/views/TaskParamsManage.vue")

        for 关键字 in [
            "type TabKey = 'taskList' | 'resultList' | 'flowParams'",
            "const flowParams = ref<FlowParam[]>([])",
            "const flowParamTotal = ref(0)",
            "const flowParamPage = ref(1)",
            "const flowParamFilters = ref({",
            "流程参数",
            "async function loadFlowParams(",
            "handleFlowParamSearch",
            "runFlowParamBatchAction",
            "handleToggleFlowParamEnabled",
            "handleResetFlowParam",
            "handleDeleteFlowParam",
            "getFlowName(flowParam.flow_id)",
            "formatFlowProgress(flowParam)",
            "formatStepResultsSummary(flowParam.step_results)",
            "暂无流程参数记录",
            "activeTab.value = 'flowParams'",
            "await loadFlowParams(1)",
        ]:
            assert 关键字 in 页面文件
