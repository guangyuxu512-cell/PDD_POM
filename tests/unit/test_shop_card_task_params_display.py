"""
店铺卡片与任务参数显示回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_店铺卡片与任务参数显示:
    def test_店铺卡片_显示店铺ID(self):
        店铺卡片文件 = 读取文件("frontend/src/components/ShopCard.vue")

        assert "ID:" in 店铺卡片文件
        assert "shop.id" in 店铺卡片文件
        assert "shop-meta" in 店铺卡片文件

    def test_任务参数页改为在store和导入弹窗中处理显示文本(self):
        store文件 = 读取文件("frontend/src/views/task-params/useTaskParamsStore.ts")
        弹窗文件 = 读取文件("frontend/src/views/task-params/ImportCsvModal.vue")

        assert "function formatShopLabel(taskParam: TaskParam)" in store文件
        assert "（${taskParam.shop_id}）" in store文件
        assert "“店铺ID”列支持填写店铺 ID 或店铺名称，导入时会自动匹配。" in 弹窗文件
        assert "成功 {{ store.importSummary.success_count }} 条 / 跳过 {{ store.importSummary.failed_count }} 条" in 弹窗文件
