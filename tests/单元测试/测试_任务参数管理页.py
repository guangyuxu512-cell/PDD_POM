"""
任务参数管理页静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_任务参数管理页:
    """校验任务参数管理页已接入前端入口与 API。"""

    def test_API封装_包含任务参数相关方法(self):
        """任务参数 API wrapper 与 FormData 支持应已存在。"""
        API入口 = 读取文件("frontend/src/api/index.ts")
        API文件 = 读取文件("frontend/src/api/taskParams.ts")

        assert "postForm" in API入口
        for 导出名称 in [
            "listTaskParams",
            "listTaskParamBatchOptions",
            "createTaskParam",
            "updateTaskParam",
            "deleteTaskParam",
            "clearTaskParams",
            "importTaskParamsCsv",
        ]:
            assert 导出名称 in API文件

    def test_路由和侧边栏_注册任务参数管理页(self):
        """router 和 App 导航都应包含 /task-params 入口。"""
        路由文件 = 读取文件("frontend/src/router/index.ts")
        入口文件 = 读取文件("frontend/src/App.vue")

        assert "path: '/task-params'" in 路由文件
        assert "TaskParamsManage.vue" in 路由文件
        assert 'to="/task-params"' in 入口文件
        assert "任务参数" in 入口文件

    def test_页面骨架_包含筛选导入清空和模板说明(self):
        """任务参数页应包含本轮要求的关键交互。"""
        页面文件 = 读取文件("frontend/src/views/TaskParamsManage.vue")

        for 关键字 in [
            "任务参数管理",
            "任务列表",
            "执行结果",
            "导入CSV",
            "清空",
            "全部任务类型",
            "全部状态",
            "全部店铺",
            "全部批次",
            "全部执行状态",
            "CSV 模板说明",
            "下载模板",
            "店铺ID”列支持填写店铺ID或店铺名称",
            "StatusBadge",
            "listTaskParams",
            "listTaskParamBatchOptions",
            "importTaskParamsCsv",
            "clearTaskParams",
            "deleteTaskParam",
            "type=\"date\"",
            "formatJsonTooltip",
            "formatBatchOptionLabel",
            "新ID:",
            "updated_from",
            "updated_to",
            "父商品ID",
            "新商品ID",
            "折扣",
            "投产比",
            "图片路径",
            "formatShopLabel",
        ]:
            assert 关键字 in 页面文件
