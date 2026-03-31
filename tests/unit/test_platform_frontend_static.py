"""
单平台前端静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_单平台前端接口:
    def test_平台store与接口文件已删除(self):
        平台接口路径 = 仓库根目录 / "frontend/src/api/platforms.ts"
        平台状态路径 = 仓库根目录 / "frontend/src/stores/platform.ts"
        类型文件 = 读取文件("frontend/src/api/types.ts")

        assert not 平台接口路径.exists()
        assert not 平台状态路径.exists()
        assert "export interface Platform" not in 类型文件
        assert "platform?: string" not in 类型文件
        assert "platform: string" in 类型文件

    def test_店铺页与shops_api已去掉平台选择逻辑(self):
        店铺接口 = 读取文件("frontend/src/api/shops.ts")
        店铺页面 = 读取文件("frontend/src/views/ShopManage.vue")

        assert "export function listShops()" in 店铺接口
        assert "URLSearchParams" not in 店铺接口
        assert "platform?.trim()" not in 店铺接口

        for 已移除关键字 in [
            "usePlatformStore",
            "platformStore",
            "formPlatform",
            "selectedFormPlatform",
            "currentPlatformLabel",
            "payload.platform",
            "watch(() => platformStore.currentPlatform",
            "void platformStore.loadPlatforms().then(loadShops)",
            "<Listbox",
            "所属平台",
            "按平台管理店铺账号、代理与邮箱连接配置。",
            "当前平台下暂无店铺数据。",
        ]:
            assert 已移除关键字 not in 店铺页面

        for 保留关键字 in [
            "管理店铺账号、代理与邮箱连接配置。",
            "暂无店铺数据。",
            "const result = await listShops()",
            "grid gap-4 md:grid-cols-1",
            "留空则不修改",
        ]:
            assert 保留关键字 in 店铺页面

        assert "<style" not in 店铺页面
