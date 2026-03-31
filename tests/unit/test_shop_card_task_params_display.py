"""
店铺卡片与任务参数显示回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_店铺卡片与任务参数显示:
    def test_店铺卡片_改为紧凑列表行(self):
        店铺卡片文件 = 读取文件("frontend/src/components/ShopCard.vue")
        状态徽标文件 = 读取文件("frontend/src/components/StatusBadge.vue")

        assert "border-b border-gray-100 px-4 py-3 transition-colors hover:bg-gray-50" in 店铺卡片文件
        assert "lg:grid lg:grid-cols-[minmax(0,2.2fr)_minmax(0,1.2fr)_minmax(0,1.4fr)_auto] lg:items-center" in 店铺卡片文件
        assert 'StatusBadge :status="shop.status" type="shop"' in 店铺卡片文件
        assert "{{ shop.id }}" in 店铺卡片文件
        assert "font-mono text-[11px] text-gray-500" in 店铺卡片文件
        assert "shop.smtp_user" in 店铺卡片文件
        assert "shop.last_login ||" in 店铺卡片文件
        assert "text-xs font-medium text-gray-500 transition hover:text-gray-700" in 店铺卡片文件
        assert "<style" not in 店铺卡片文件

        assert "inline-flex items-center gap-2 whitespace-nowrap text-xs font-medium" in 状态徽标文件
        assert "bg-emerald-500" in 状态徽标文件
        assert "bg-gray-300" in 状态徽标文件
        assert "bg-amber-400" in 状态徽标文件
        assert "animate-pulse" in 状态徽标文件
        assert "<style" not in 状态徽标文件

    def test_任务参数页改为在store和导入弹窗中处理显示文本(self):
        store文件 = 读取文件("frontend/src/views/task-params/useTaskParamsStore.ts")
        弹窗文件 = 读取文件("frontend/src/views/task-params/ImportCsvModal.vue")

        assert "function formatShopLabel(taskParam: TaskParam)" in store文件
        assert "（${taskParam.shop_id}）" in store文件
        assert "“店铺ID”列支持填写店铺 ID 或店铺名称，导入时会自动匹配。" in 弹窗文件
        assert "成功 {{ store.importSummary.success_count }} 条 / 跳过 {{ store.importSummary.failed_count }} 条" in 弹窗文件
