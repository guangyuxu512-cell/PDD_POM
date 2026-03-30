"""
售后配置页静态回归测试
"""
from pathlib import Path


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_售后配置页:
    """校验售后配置页和前端 API 接线。"""

    def test_API封装_导出售后配置接口(self):
        文件内容 = 读取文件("frontend/src/api/aftersaleConfig.ts")

        for 关键字 in [
            "getAftersaleConfig",
            "updateAftersaleConfig",
            "getAllAftersaleConfigs",
            "deleteAftersaleConfig",
            "/api/aftersale-config",
        ]:
            assert 关键字 in 文件内容

    def test_售后配置页_包含核心表单结构(self):
        页面文件 = 读取文件("frontend/src/views/AftersaleConfig.vue")

        for 关键字 in [
            "售后配置",
            "店铺选择",
            "重置为默认",
            "保存配置",
            "全局设置",
            "退货退款",
            "仅退款",
            "通知配置",
            "弹窗与备注",
            "执行策略",
            "飞书多维表",
            "启用自动售后",
            "不支持自动处理类型",
            "退货物流白名单",
            "自动退款金额上限",
            "自动同意金额上限",
            "最大拒绝次数",
            "拒绝后等待",
            "飞书 Webhook",
            "微信群ID",
            "每批最大处理数",
            "单条超时秒数",
            "失败重试次数",
            "扫描间隔分钟",
            "App Token",
            "Table ID",
            "tag-chip",
            "config-table",
            "whitelist",
            "popupOptionPreferences",
        ]:
            assert 关键字 in 页面文件

    def test_路由和侧边栏_包含售后配置导航(self):
        路由文件 = 读取文件("frontend/src/router/index.ts")
        入口文件 = 读取文件("frontend/src/App.vue")

        assert "path: '/aftersale-config'" in 路由文件
        assert "AftersaleConfig.vue" in 路由文件
        assert 'to="/aftersale-config"' in 入口文件
        assert "售后配置" in 入口文件
