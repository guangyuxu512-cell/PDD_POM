"""
任务参数启用/重置管理页静态测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_任务参数启用重置管理页:
    """验证前端已接入本轮新增交互。"""

    def test_API封装_包含启用禁用重置与批量方法(self):
        """任务参数 API 文件应导出单条与批量操作方法。"""
        API文件 = 读取文件("frontend/src/api/taskParams.ts")

        for 关键字 in [
            "enableTaskParam",
            "disableTaskParam",
            "resetTaskParam",
            "batchResetTaskParams",
            "batchEnableTaskParams",
            "batchDisableTaskParams",
        ]:
            assert 关键字 in API文件

    def test_页面骨架_包含开关执行次数与批量按钮(self):
        """任务参数页应包含启用开关、执行次数列和批量操作入口。"""
        页面文件 = 读取文件("frontend/src/views/TaskParamsManage.vue")

        for 关键字 in [
            "批量重置",
            "批量启用",
            "批量禁用",
            "已执行次数",
            "handleToggleEnabled",
            "handleResetTaskParam",
            "switch-slider",
            "run_count",
            "taskParam.enabled",
            "发布次数",
            "批次序号",
            "is-disabled",
        ]:
            assert 关键字 in 页面文件
