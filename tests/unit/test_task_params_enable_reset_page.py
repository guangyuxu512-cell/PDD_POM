"""
任务参数启用/重置管理页静态测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_任务参数启用重置管理页:
    def test_API封装_包含启用禁用重置与批量方法(self):
        api文件 = 读取文件("frontend/src/api/taskParams.ts")

        for 关键字 in [
            "enableTaskParam",
            "disableTaskParam",
            "resetTaskParam",
            "batchResetTaskParams",
            "batchEnableTaskParams",
            "batchDisableTaskParams",
        ]:
            assert 关键字 in api文件

    def test_任务页和流程页子组件都保留批量操作与开关(self):
        任务列表文件 = 读取文件("frontend/src/views/task-params/TaskListTab.vue")
        流程列表文件 = 读取文件("frontend/src/views/task-params/FlowParamsTab.vue")

        for 关键字 in ["批量重置", "批量启用", "批量禁用", "switch-slider", "run_count", "taskParam.enabled"]:
            assert 关键字 in 任务列表文件

        for 关键字 in ["批量重置", "批量启用", "批量禁用", "switch-slider", "step-result-tag", "flowParam.enabled"]:
            assert 关键字 in 流程列表文件
