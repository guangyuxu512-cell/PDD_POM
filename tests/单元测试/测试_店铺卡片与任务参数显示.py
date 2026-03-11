"""
店铺卡片与任务参数页面显示回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_店铺卡片与任务参数显示:
    """校验本轮前端显示改动已经落地。"""

    def test_店铺卡片_显示店铺ID(self):
        """店铺卡片应在店铺名称区域展示店铺 ID。"""
        店铺卡片文件 = 读取文件("frontend/src/components/ShopCard.vue")

        assert "ID:" in 店铺卡片文件
        assert "shop.id" in 店铺卡片文件
        assert "shop-meta" in 店铺卡片文件

    def test_任务参数页_显示店铺名称和ID并提示名称导入(self):
        """任务参数页应显示店铺名称（#ID），并提示 CSV 可填写店铺名称。"""
        页面文件 = 读取文件("frontend/src/views/TaskParamsManage.vue")

        assert "formatShopLabel" in 页面文件
        assert "（#" in 页面文件
        assert "店铺ID”列支持填写店铺ID或店铺名称" in 页面文件
        assert "成功 {{ importSummary.success_count }} 条 / 跳过 {{ importSummary.failed_count }} 条" in 页面文件
