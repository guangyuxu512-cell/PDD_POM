"""
前端 Tailwind 接入静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_Tailwind接入:
    """校验 Tailwind 样式基建已接入并清理旧入口。"""

    def test_vite与样式入口_切换到_tailwind(self):
        vite配置 = 读取文件("frontend/vite.config.ts")
        入口文件 = 读取文件("frontend/src/main.ts")
        全局样式 = 读取文件("frontend/src/style.css")
        前端依赖 = 读取文件("frontend/package.json")

        assert "import tailwindcss from '@tailwindcss/vite'" in vite配置
        assert "plugins: [vue(), tailwindcss()]" in vite配置
        assert "target: 'http://localhost:8000'" in vite配置
        assert "import './styles/variables.css'" not in 入口文件
        assert '@import "tailwindcss";' in 全局样式
        assert "font-family:" in 全局样式
        assert "'Inter'" in 全局样式
        assert "box-sizing: border-box;" not in 全局样式
        assert '"tailwindcss":' in 前端依赖
        assert '"@tailwindcss/vite":' in 前端依赖
        assert '"@headlessui/vue":' in 前端依赖

    def test_旧样式变量与示例组件_已移除(self):
        assert not (仓库根目录 / "frontend/src/styles").exists()
        assert not (仓库根目录 / "frontend/src/components/HelloWorld.vue").exists()

    def test_中等页面与组件_统一为灰白Tailwind结构(self):
        断言映射 = {
            "frontend/src/views/Settings.vue": [
                "rounded-md border border-gray-200 bg-white p-5 shadow-sm",
                "测试 Webhook",
                "健康检查",
            ],
            "frontend/src/views/TaskMonitor.vue": [
                "手动触发任务",
                "StatusBadge",
                "bg-gray-50/60 text-xs font-medium uppercase tracking-wider text-gray-500",
            ],
            "frontend/src/views/LogViewer.vue": [
                "导出 CSV",
                "清空日志",
                "<LogTable :logs=\"paginatedLogs\" :loading=\"loading\" show-shop />",
            ],
            "frontend/src/views/TaskParamsManage.vue": [
                "rounded-md border border-gray-200 bg-white p-4 shadow-sm",
                "导入 CSV",
                "JsonTooltip",
            ],
            "frontend/src/views/BatchExecute.vue": [
                "目标店铺",
                "当前步骤",
                "最近更新：",
            ],
            "frontend/src/views/BrowserManager.vue": [
                "初始化配置",
                "运行中实例",
                "关闭全部",
            ],
            "frontend/src/components/StatCard.vue": [
                "font-mono text-2xl font-semibold text-gray-900",
                "text-xs font-medium uppercase tracking-wider text-gray-500",
            ],
            "frontend/src/components/LogTable.vue": [
                "overflow-hidden rounded-md border border-gray-200 bg-white shadow-sm",
                "font-mono text-xs uppercase tracking-wide text-gray-500",
            ],
            "frontend/src/components/BrowserStatus.vue": [
                "rounded-md border border-gray-200 bg-white p-4 shadow-sm",
                "bg-rose-600",
                "font-mono text-sm text-gray-900",
            ],
        }

        for 相对路径, 关键字列表 in 断言映射.items():
            文件内容 = 读取文件(相对路径)
            assert "<style" not in 文件内容
            for 关键字 in 关键字列表:
                assert 关键字 in 文件内容

            for 禁止关键字 in ["blue-", "indigo-", "cyan-", "sky-", "#3b82f6", "#2563eb", "#1d4ed8"]:
                assert 禁止关键字 not in 文件内容
