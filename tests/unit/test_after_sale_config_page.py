"""
售后配置页静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_售后配置页:
    """校验售后配置页和前端 API 接线。"""

    def test_API封装_导出售后配置接口(self):
        文件内容 = 读取文件("frontend/src/api/aftersaleConfig.ts")

        for 关键字 in [
            "getAftersaleConfig",
            "updateAftersaleConfig",
            "getAllAftersaleConfigs",
            "deleteAftersaleConfig",
            "/api/aftersale-config",
        ]:
            assert 关键字 in 文件内容

    def test_售后配置页改为_tailwind表单分段与_listbox店铺选择(self):
        页面文件 = 读取文件("frontend/src/views/AftersaleConfig.vue")

        for 关键字 in [
            "售后配置",
            "店铺选择",
            "重置为默认",
            "保存配置",
            "全局设置",
            "退货退款",
            "仅退款",
            "通知配置",
            "弹窗与备注",
            "执行策略",
            "飞书多维表",
            '<Listbox v-model="selectedShopId">',
            'class="tag-chip inline-flex items-center gap-2 rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-700"',
            '<div class="whitelist overflow-x-auto rounded-md border border-gray-200">',
            '<table class="config-table min-w-[920px] w-full divide-y divide-gray-200 text-sm">',
            "📭 暂无白名单配置",
            "🏪 暂无店铺，请先创建店铺",
            "border-t border-gray-100 pt-4",
        ]:
            assert 关键字 in 页面文件

        for 已移除关键字 in [
            "<style",
            "<select",
        ]:
            assert 已移除关键字 not in 页面文件

    def test_路由和侧边栏_包含售后配置导航(self):
        路由文件 = 读取文件("frontend/src/router/index.ts")
        入口文件 = 读取文件("frontend/src/App.vue")

        assert "path: '/aftersale-config'" in 路由文件
        assert "AftersaleConfig.vue" in 路由文件
        assert "path: '/aftersale-config'" in 入口文件
        assert ':to="item.path"' in 入口文件
        assert "售后配置" in 入口文件
