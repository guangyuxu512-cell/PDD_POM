"""
店铺平台弹窗静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_店铺平台弹窗:
    def test_店铺页新增平台选择和密码占位(self):
        店铺页 = 读取文件("frontend/src/views/ShopManage.vue")

        assert "Listbox" in 店铺页
        assert "ListboxButton" in 店铺页
        assert "ListboxOption" in 店铺页
        assert "ListboxOptions" in 店铺页
        assert "const formPlatform = ref(platformStore.currentPlatform)" in 店铺页
        assert "selectedFormPlatform" in 店铺页
        assert "formPlatform.value = platformStore.currentPlatform" in 店铺页
        assert "formPlatform.value = shop.platform || 'pdd'" in 店铺页
        assert "payload.platform = formPlatform.value" in 店铺页
        assert 'v-model="formPlatform"' in 店铺页
        assert ':disabled="!!editingShop"' in 店铺页
        assert "cursor-not-allowed bg-brand-100 text-brand-300" in 店铺页
        assert 'v-slot="{ active, selected }"' in 店铺页
        assert "留空则不修改" in 店铺页

    def test_店铺页与Modal_弹窗样式改为_brand_白底表单(self):
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
        assert "background: #1e1e2e;" not in 弹窗
        assert "border: 1px solid #2e2e3e;" not in 弹窗
        assert "<style" not in 店铺页
