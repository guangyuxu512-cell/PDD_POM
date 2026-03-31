"""
流程参数管理页静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_流程参数管理页静态:
    def test_flow_params_api_包含单条与批量方法(self):
        api文件 = 读取文件("frontend/src/api/flowParams.ts")

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
            assert 关键字 in api文件

    def test_流程参数逻辑与列表已拆入专用文件(self):
        store文件 = 读取文件("frontend/src/views/task-params/useTaskParamsStore.ts")
        列表文件 = 读取文件("frontend/src/views/task-params/FlowParamsTab.vue")

        for 关键字 in [
            "const flowParams = ref<FlowParam[]>([])",
            "const flowParamTotal = ref(0)",
            "const flowParamPage = ref(1)",
            "const flowParamFilters = ref({ flow_id: '', status: '', shop_id: '' })",
            "async function loadFlowParams(",
            "async function handleToggleFlowParamEnabled(",
            "async function handleResetFlowParam(",
            "async function handleDeleteFlowParam(",
            "async function runFlowParamBatchAction(",
            "activeTab.value = 'flowParams'",
        ]:
            assert 关键字 in store文件

        for 关键字 in [
            "formatFlowParamShopLabel",
            "getFlowName(flowParam.flow_id)",
            "formatFlowProgress(flowParam)",
            "step-result-tag",
            "toggleStepResultDetail",
            "暂无流程参数记录",
            "switch-slider",
        ]:
            assert 关键字 in 列表文件
