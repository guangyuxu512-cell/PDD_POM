"""
平台切换器前端静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_平台切换器前端接入:
    """校验平台选择器相关前端接线。"""

    def test_平台store与接口_支持持久化和平台列表加载(self):
        """platform store 应负责本地持久化和平台列表加载。"""
        平台接口 = 读取文件("frontend/src/api/platforms.ts")
        平台类型 = 读取文件("frontend/src/api/types.ts")
        平台状态 = 读取文件("frontend/src/stores/platform.ts")
        平台选择器 = 读取文件("frontend/src/components/PlatformSelector.vue")

        assert "export function listPlatforms()" in 平台接口
        assert "/api/platforms" in 平台接口
        assert "export interface Platform" in 平台类型
        assert "currentPlatform" in 平台状态
        assert "selectedPlatform" in 平台状态
        assert "window.localStorage.setItem('selectedPlatform', id)" in 平台状态
        assert "loadPlatforms" in 平台状态
        assert "PlatformSelector" not in 平台状态
        assert "store.currentPlatform" in 平台选择器
        assert "store.platforms" in 平台选择器

    def test_App与店铺页_接入当前平台过滤和默认绑定(self):
        """平台切换入口应移入店铺页 header，App 侧边栏不再挂载该组件。"""
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
        assert 'class="header-actions"' in 店铺页面
        assert 'class="platform-tabs"' in 店铺页面
        assert 'class="platform-tab"' in 店铺页面
        assert "platformStore.setPlatform(p.id)" in 店铺页面

    def test_平台选择器与侧边栏_改为灰色主题(self):
        """备用选择器与侧边栏都应移除蓝色调。"""
        应用入口 = 读取文件("frontend/src/App.vue")
        平台选择器 = 读取文件("frontend/src/components/PlatformSelector.vue")

        assert "background: #1e1e2e;" in 应用入口
        assert "border-right: 1px solid #2e2e3e;" in 应用入口
        assert "background: #2a2a3a;" in 应用入口
        assert "background: #312e81;" in 应用入口
        assert "background: #2a2a3a;" in 平台选择器
        assert "border: 1px solid #3a3a4a;" in 平台选择器
        assert "border-color: #4f46e5;" in 平台选择器
