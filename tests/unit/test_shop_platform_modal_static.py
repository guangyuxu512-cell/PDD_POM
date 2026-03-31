"""
店铺弹窗单平台静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_店铺弹窗单平台:
    def test_店铺弹窗已移除平台字段但保留账号密码占位(self):
        店铺页 = 读取文件("frontend/src/views/ShopManage.vue")

        for 关键字 in [
            "店铺名称",
            "账号",
            "密码",
            "代理",
            "邮箱配置",
            "留空则不修改",
            "grid gap-4 md:grid-cols-1",
        ]:
            assert 关键字 in 店铺页

        for 已移除关键字 in [
            "Listbox",
            "ListboxButton",
            "ListboxOption",
            "ListboxOptions",
            "所属平台",
            "formPlatform",
            "selectedFormPlatform",
            "payload.platform",
        ]:
            assert 已移除关键字 not in 店铺页

    def test_店铺页与Modal_仍保持_brand_白底表单样式(self):
        店铺页 = 读取文件("frontend/src/views/ShopManage.vue")
        弹窗 = 读取文件("frontend/src/components/Modal.vue")

        assert (
            "w-full rounded-md border border-brand-300/50 bg-white px-3 py-2 text-sm text-gray-900 "
            "placeholder:text-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        ) in 店铺页
        assert "rounded-md border border-brand-300/50 bg-white px-3 py-1.5 text-sm text-brand-700 transition hover:bg-brand-100/50 hover:text-brand-900" in 店铺页
        assert "rounded-md bg-brand-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-brand-700" in 店铺页
        assert "DialogPanel" in 弹窗
        assert "bg-white shadow-lg" in 弹窗
        assert "border border-brand-300/50" in 弹窗
        assert "bg-black/30 backdrop-blur-sm" in 弹窗
        assert "<style" not in 店铺页
