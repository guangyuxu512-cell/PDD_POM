"""
店铺展示与任务参数显示回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_店铺展示与任务参数显示:
    def test_店铺页改为表格直出且不再依赖_ShopCard(self):
        店铺页 = 读取文件("frontend/src/views/ShopManage.vue")
        状态徽标文件 = 读取文件("frontend/src/components/StatusBadge.vue")
        店铺卡片路径 = 仓库根目录 / "frontend/src/components/ShopCard.vue"

        assert '<table class="w-full min-w-[900px] table-fixed divide-y divide-brand-300/30">' in 店铺页
        assert "当前平台下暂无店铺数据。" in 店铺页
        assert "StatusBadge :status=\"shop.status\" type=\"shop\"" in 店铺页
        assert "shop.smtp_user || '未配置'" in 店铺页
        assert "shop.last_login ? new Date(shop.last_login).toLocaleString('zh-CN')" in 店铺页
        assert "handleOpenBrowser(shop.id)" in 店铺页
        assert "handleCheckStatus(shop.id)" in 店铺页
        assert "openDeleteConfirm(shop.id)" in 店铺页
        assert "ShopCard" not in 店铺页
        assert not 店铺卡片路径.exists()

        assert "inline-flex items-center gap-2 whitespace-nowrap text-xs font-medium" in 状态徽标文件
        assert "bg-emerald-500" in 状态徽标文件
        assert "bg-brand-300" in 状态徽标文件
        assert "bg-amber-400" in 状态徽标文件
        assert "animate-pulse" in 状态徽标文件
        assert "<style" not in 状态徽标文件

    def test_任务参数导入与显示文本仍在_store_和弹窗中维护(self):
        store文件 = 读取文件("frontend/src/views/task-params/useTaskParamsStore.ts")
        弹窗文件 = 读取文件("frontend/src/views/task-params/ImportCsvModal.vue")

        assert "function formatShopLabel(taskParam: TaskParam)" in store文件
        assert "function formatFlowParamShopLabel(flowParam: FlowParam)" in store文件
        assert "店铺ID" in 弹窗文件
        assert "store.importSummary.success_count" in 弹窗文件
        assert "store.importSummary.failed_count" in 弹窗文件
