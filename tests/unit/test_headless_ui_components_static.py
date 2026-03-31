"""
Headless UI 公共组件静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_HeadlessUI公共组件:
    """校验 Modal / ConfirmDialog / Toast 已切换到 Headless UI + Tailwind。"""

    def test_Modal_使用_Dialog_并保留兼容类名(self):
        弹窗文件 = 读取文件("frontend/src/components/Modal.vue")

        assert "import {" in 弹窗文件
        assert "DialogPanel" in 弹窗文件
        assert "TransitionRoot" in 弹窗文件
        assert 'class="modal-container flex max-h-[90vh] w-full flex-col overflow-hidden rounded-md border border-gray-200 bg-white shadow-lg"' in 弹窗文件
        assert 'class="modal-body flex-1 overflow-y-auto px-5 py-4 text-sm text-gray-600"' in 弹窗文件
        assert "bg-black/30 backdrop-blur-sm" in 弹窗文件
        assert "<style" not in 弹窗文件
        assert "background: #1e1e2e;" not in 弹窗文件
        assert "modal-enter-active" not in 弹窗文件

    def test_ConfirmDialog_保持旧API并移除蓝色按钮(self):
        确认框文件 = 读取文件("frontend/src/components/ConfirmDialog.vue")

        assert "DialogPanel" in 确认框文件
        assert "TransitionRoot" in 确认框文件
        assert "close: []" in 确认框文件
        assert "confirm: []" in 确认框文件
        assert "cancel: []" in 确认框文件
        assert "bg-rose-600 text-white hover:bg-rose-700" in 确认框文件
        assert "bg-gray-900 text-white hover:bg-gray-800" in 确认框文件
        assert "border border-gray-300 bg-white" in 确认框文件
        assert "bg-black/30 backdrop-blur-sm" in 确认框文件
        assert "<style" not in 确认框文件
        assert "btn-info" not in 确认框文件
        assert "#3b82f6" not in 确认框文件

    def test_Toast_固定右上角并按类型映射颜色(self):
        提示文件 = 读取文件("frontend/src/components/Toast.vue")

        assert "TransitionRoot" in 提示文件
        assert "TransitionChild" in 提示文件
        assert "fixed right-4 top-4 z-50" in 提示文件
        assert "border-emerald-200 bg-emerald-50 text-emerald-800" in 提示文件
        assert "border-rose-200 bg-rose-50 text-rose-800" in 提示文件
        assert "border-amber-200 bg-amber-50 text-amber-800" in 提示文件
        assert "border-gray-200 bg-gray-50 text-gray-800" in 提示文件
        assert "<style" not in 提示文件
        assert "toast-container" not in 提示文件
        assert "#3b82f6" not in 提示文件
