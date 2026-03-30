"""
任务参数管理页静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


def 读取行数(相对路径: str) -> int:
    return len(读取文件(相对路径).splitlines())


class 测试_任务参数管理页:
    def test_API封装_包含任务参数相关方法(self):
        api入口 = 读取文件("frontend/src/api/index.ts")
        api文件 = 读取文件("frontend/src/api/taskParams.ts")

        assert "postForm" in api入口
        for 导出名称 in [
            "listTaskParams",
            "listTaskParamResults",
            "listTaskParamBatchOptions",
            "createTaskParam",
            "updateTaskParam",
            "deleteTaskParam",
            "clearTaskParams",
            "importTaskParamsCsv",
        ]:
            assert 导出名称 in api文件

    def test_页面已拆分为容器页和子组件(self):
        页面文件 = 读取文件("frontend/src/views/TaskParamsManage.vue")
        store文件 = 读取文件("frontend/src/views/task-params/useTaskParamsStore.ts")

        for 相对路径 in [
            "frontend/src/views/task-params/TaskListTab.vue",
            "frontend/src/views/task-params/TaskResultTab.vue",
            "frontend/src/views/task-params/FlowParamsTab.vue",
            "frontend/src/views/task-params/ImportCsvModal.vue",
            "frontend/src/views/task-params/JsonTooltip.vue",
            "frontend/src/views/task-params/TaskParamsManage.css",
        ]:
            assert (仓库根目录 / 相对路径).exists()

        for 关键字 in [
            "useTaskParamsStore",
            "TaskListTab",
            "TaskResultTab",
            "FlowParamsTab",
            "ImportCsvModal",
            "JsonTooltip",
            "ConfirmDialog",
            "<component",
            "type=\"date\"",
            "handleBatchAction",
            "handleToggleEnabled",
            "task-params/TaskParamsManage.css",
        ]:
            assert 关键字 in 页面文件

        for 关键字 in [
            "const currentTemplateColumns = computed",
            "const currentTemplateSampleRow = computed",
            "const currentRequiredFields = computed",
            "function handleImport()",
            "function runBatchAction(",
            "function runFlowParamBatchAction(",
        ]:
            assert 关键字 in store文件

        assert 读取行数("frontend/src/views/TaskParamsManage.vue") < 200
        assert 读取行数("frontend/src/views/task-params/TaskListTab.vue") < 300
        assert 读取行数("frontend/src/views/task-params/TaskResultTab.vue") < 300
        assert 读取行数("frontend/src/views/task-params/FlowParamsTab.vue") < 300
