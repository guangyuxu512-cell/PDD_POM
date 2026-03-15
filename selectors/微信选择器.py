"""微信桌面版选择器。"""
from selectors.桌面选择器配置 import 桌面选择器配置


class 微信选择器:
    """微信 PC 版控件选择器集合。"""

    主窗口 = 桌面选择器配置(
        控件类型="WindowControl",
        名称="微信",
        类名="WeChatMainWndForPC",
    )

    搜索按钮 = 桌面选择器配置(
        控件类型="ButtonControl",
        名称="搜索",
    )

    搜索输入框 = 桌面选择器配置(
        控件类型="EditControl",
        名称="搜索",
    )

    聊天输入框 = 桌面选择器配置(
        控件类型="EditControl",
        名称="输入",
    )

    发送按钮 = 桌面选择器配置(
        控件类型="ButtonControl",
        名称="sendBtn",
        备选=[
            桌面选择器配置(控件类型="ButtonControl", 名称="发送(S)"),
        ],
    )

    @staticmethod
    def 获取联系人项(联系人名称: str) -> 桌面选择器配置:
        """根据联系人名称生成搜索结果列表项选择器。"""
        return 桌面选择器配置(
            控件类型="ListItemControl",
            名称=联系人名称,
        )
