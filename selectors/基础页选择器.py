from selectors.选择器配置 import 选择器配置


class 基础页选择器:
    """基础页通用元素选择器"""

    通用弹窗关闭按钮 = 选择器配置(
        主选择器="[data-testid='beast-core-icon-close']",
        备选选择器=[".ant-modal-close"],
    )
    首页URL: str = "https://mms.pinduoduo.com/home"
    登录页URL: str = "https://mms.pinduoduo.com/login/"
