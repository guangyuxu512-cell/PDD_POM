"""
平台切换前端静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_平台切换前端接口:
    """校验平台切换入口已经收敛到店铺页页头。"""

    def test_平台store与接口_支持持久化和平台列表加载(self):
        平台接口 = 读取文件("frontend/src/api/platforms.ts")
        平台类型 = 读取文件("frontend/src/api/types.ts")
        平台状态 = 读取文件("frontend/src/stores/platform.ts")
        平台选择器路径 = 仓库根目录 / "frontend/src/components/PlatformSelector.vue"

        assert "export function listPlatforms()" in 平台接口
        assert "/api/platforms" in 平台接口
        assert "export interface Platform" in 平台类型
        assert "currentPlatform" in 平台状态
        assert "selectedPlatform" in 平台状态
        assert "window.localStorage.setItem('selectedPlatform', id)" in 平台状态
        assert "loadPlatforms" in 平台状态
        assert "PlatformSelector" not in 平台状态
        assert not 平台选择器路径.exists()

    def test_App与店铺页_平台切换移入页头(self):
        应用入口 = 读取文件("frontend/src/App.vue")
        店铺接口 = 读取文件("frontend/src/api/shops.ts")
        店铺类型 = 读取文件("frontend/src/api/types.ts")
        店铺页面 = 读取文件("frontend/src/views/ShopManage.vue")

        assert "PlatformSelector" not in 应用入口
        assert "function listShops(platform?: string)" in 店铺接口
        assert "URLSearchParams" in 店铺接口
        assert "platform: string" in 店铺类型
        assert "platform?: string" in 店铺类型
        assert "usePlatformStore" in 店铺页面
        assert "void platformStore.loadPlatforms().then(loadShops)" in 店铺页面
        assert "listShops(platformStore.currentPlatform)" in 店铺页面
        assert "payload.platform = formPlatform.value" in 店铺页面
        assert "watch(() => platformStore.currentPlatform" in 店铺页面
        assert 'class="flex gap-1 rounded-md bg-gray-100 p-0.5"' in 店铺页面
        assert "bg-white text-gray-900 shadow-sm rounded-md font-medium" in 店铺页面
        assert "text-gray-500 hover:text-gray-700" in 店铺页面
        assert "platformStore.setPlatform(p.id)" in 店铺页面
        assert "<style" not in 店铺页面

    def test_App主布局_保持灰白导航壳(self):
        应用入口 = 读取文件("frontend/src/App.vue")
        店铺卡片 = 读取文件("frontend/src/components/ShopCard.vue")
        状态徽标 = 读取文件("frontend/src/components/StatusBadge.vue")

        assert "useRoute" in 应用入口
        assert "const navItems = [" in 应用入口
        assert 'class="flex h-screen bg-gray-50"' in 应用入口
        assert 'class="flex w-52 flex-shrink-0 flex-col border-r border-gray-200 bg-white"' in 应用入口
        assert "route.path.startsWith(item.path)" in 应用入口
        assert "'bg-gray-100 font-medium text-gray-900'" in 应用入口
        assert "'text-gray-500 hover:bg-gray-50 hover:text-gray-700'" in 应用入口
        assert 'class="flex-1 overflow-auto bg-gray-50"' in 应用入口
        assert "<style" not in 应用入口
        assert "background: #1e1e2e;" not in 应用入口
        assert "#4f46e5" not in 应用入口
        assert "<style" not in 店铺卡片
        assert "<style" not in 状态徽标
