"""
店铺平台弹窗静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_店铺平台弹窗:
    """校验店铺弹窗的平台选择与视觉样式。"""

    def test_店铺页_新增平台选择和密码占位(self):
        """店铺弹窗应支持平台选择，并显示新的密码占位文案。"""
        店铺页 = 读取文件("frontend/src/views/ShopManage.vue")

        assert "const formPlatform = ref(platformStore.currentPlatform)" in 店铺页
        assert "formPlatform.value = platformStore.currentPlatform" in 店铺页
        assert "formPlatform.value = shop.platform || 'pdd'" in 店铺页
        assert "payload.platform = formPlatform.value" in 店铺页
        assert "<label>所属平台</label>" in 店铺页
        assert 'v-model="formPlatform"' in 店铺页
        assert ':disabled="!!editingShop"' in 店铺页
        assert "v-for=\"p in platformStore.platforms\"" in 店铺页
        assert "••••••••（留空则不修改）" in 店铺页
        assert ":placeholder=\"editingShop ? '••••••••（留空则不修改）' : '••••••••'\"" in 店铺页

    def test_店铺页与Modal_弹窗改为灰色主题(self):
        """Modal 和店铺表单输入区应去掉蓝色底，改为灰色暗色系。"""
        店铺页 = 读取文件("frontend/src/views/ShopManage.vue")
        弹窗 = 读取文件("frontend/src/components/Modal.vue")

        assert "background: #2a2a3a;" in 店铺页
        assert "border: 1px solid #3a3a4a;" in 店铺页
        assert "border-color: #6366f1;" in 店铺页
        assert "background: #242433;" in 店铺页
        assert "color: #d0d0d0;" in 店铺页
        assert "background: #1e1e2e;" in 弹窗
        assert "border: 1px solid #2e2e3e;" in 弹窗
        assert "background: #2a2a3a;" in 弹窗
        assert "border-top: 1px solid #2e2e3e;" in 弹窗
