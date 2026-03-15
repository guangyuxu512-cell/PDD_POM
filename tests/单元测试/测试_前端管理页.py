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

    def test_路由和侧边栏_重组为五个主菜单(self):
        """router 和 App 导航应切换到 shops/business/data/monitor/settings 五个主菜单。"""
        路由文件 = 读取文件("frontend/src/router/index.ts")
        入口文件 = 读取文件("frontend/src/App.vue")

        for 路径 in ["/shops", "/business", "/data", "/monitor", "/settings"]:
            assert f"path: '{路径}'" in 路由文件
            assert f'to="{路径}"' in 入口文件

        for 视图文件 in [
            "ShopManage.vue",
            "BusinessManage.vue",
            "DataManage.vue",
            "MonitorManage.vue",
            "Settings.vue",
        ]:
            assert 视图文件 in 路由文件

        for 旧路径, 新路径 in {
            "/flows": "/business?tab=flow",
            "/execute": "/business?tab=execute",
            "/schedules": "/business?tab=schedule",
            "/task-params": "/data?tab=params",
            "/logs": "/monitor?tab=logs",
            "/tasks": "/monitor?tab=monitor",
        }.items():
            assert f"path: '{旧路径}'" in 路由文件
            assert f"redirect: '{新路径}'" in 路由文件

        assert "path: '/dashboard'" in 路由文件
        assert "path: '/browser'" in 路由文件

    def test_容器页_包含关键交互骨架(self):
        """新的容器页应包含 Tab 容器并嵌入现有页面。"""
        店铺页 = 读取文件("frontend/src/views/ShopManage.vue")
        业务页 = 读取文件("frontend/src/views/BusinessManage.vue")
        数据页 = 读取文件("frontend/src/views/DataManage.vue")
        监控页 = 读取文件("frontend/src/views/MonitorManage.vue")

        assert "新增店铺" in 店铺页
        assert "删除店铺" in 店铺页

        for 关键字 in [
            "业务管理",
            "FlowManage",
            "BatchExecute",
            "ScheduleManage",
            ":show-title=\"false\"",
            "流程管理",
            "批量执行",
            "定时任务",
        ]:
            assert 关键字 in 业务页

        for 关键字 in [
            "数据管理",
            "TaskParamsManage",
            "RuleManage",
            "CSV导入 / 执行结果",
            "规则配置",
            ":show-title=\"false\"",
        ]:
            assert 关键字 in 数据页

        for 关键字 in [
            "运行监控",
            "LogViewer",
            "TaskMonitor",
            "运行日志",
            "任务监控",
        ]:
            assert 关键字 in 监控页
