"""
前端管理页静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_前端管理页:
    """校验新增管理页已注册到前端入口。"""

    def test_API封装文件_导出核心函数(self):
        """新增的 API wrapper 应全部存在并导出关键函数。"""
        断言映射 = {
            "frontend/src/api/shops.ts": ["listShops", "createShop", "updateShop", "deleteShop"],
            "frontend/src/api/flows.ts": ["listFlows", "createFlow", "updateFlow", "deleteFlow"],
            "frontend/src/api/execute.ts": ["createBatch", "stopBatch", "createBatchStatusEventSource"],
            "frontend/src/api/schedules.ts": [
                "listSchedules",
                "createSchedule",
                "updateSchedule",
                "deleteSchedule",
                "pauseSchedule",
                "resumeSchedule",
            ],
            "frontend/src/api/tasks.ts": ["listAvailableTasks"],
        }

        for 相对路径, 导出名称列表 in 断言映射.items():
            文件内容 = 读取文件(相对路径)
            for 导出名称 in 导出名称列表:
                assert 导出名称 in 文件内容, f"{相对路径} 缺少 {导出名称}"

    def test_路由和侧边栏_注册四个管理页(self):
        """router 和 App 导航都应包含 shops/flows/execute/schedules。"""
        路由文件 = 读取文件("frontend/src/router/index.ts")
        入口文件 = 读取文件("frontend/src/App.vue")

        for 路径 in ["/shops", "/flows", "/execute", "/schedules"]:
            assert f"path: '{路径}'" in 路由文件
            assert f'to="{路径}"' in 入口文件

        for 视图文件 in [
            "ShopManage.vue",
            "FlowManage.vue",
            "BatchExecute.vue",
            "ScheduleManage.vue",
        ]:
            assert 视图文件 in 路由文件

    def test_新页面_包含关键交互骨架(self):
        """关键视图应包含本轮要求的核心交互入口。"""
        店铺页 = 读取文件("frontend/src/views/ShopManage.vue")
        流程页 = 读取文件("frontend/src/views/FlowManage.vue")
        批量页 = 读取文件("frontend/src/views/BatchExecute.vue")
        定时页 = 读取文件("frontend/src/views/ScheduleManage.vue")

        assert "新增店铺" in 店铺页
        assert "删除店铺" in 店铺页

        assert 'draggable="true"' in 流程页
        assert "listAvailableTasks" in 流程页
        assert "retry:N" in 流程页
        assert "同步屏障" in 流程页
        assert "合并执行" in 流程页

        assert "createBatchStatusEventSource" in 批量页
        assert "全部停止" in 批量页
        assert "实时进度" in 批量页

        assert "pauseSchedule" in 定时页
        assert "resumeSchedule" in 定时页
        assert "Cron 表达式" in 定时页
