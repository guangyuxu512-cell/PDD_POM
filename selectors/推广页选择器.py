"""推广页元素选择器。"""
from selectors.选择器配置 import 选择器配置


class 推广页选择器:
    """全站推广页元素选择器集合。"""

    广告弹窗关闭按钮 = 选择器配置(
        主选择器="div[class*='NormalModal'] span[class*='closeIcon']",
        备选选择器=[
            "div[data-testid^='amsModal'] span[class*='close']",
            "div[class*='anq-modal-wrap'] button[aria-label='Close']",
        ],
    )

    添加推广商品按钮 = 选择器配置(
        主选择器="button:has-text('添加推广商品')",
        备选选择器=[
            "button[data-testid*='add']",
            "a:has-text('添加推广商品')",
        ],
    )

    全局优先起量开关 = 选择器配置(
        主选择器="button[role='switch'][aria-label*='优先起量']",
        备选选择器=[
            "button[role='switch'][class*='Switch']",
        ],
    )

    确认关闭优先起量按钮 = 选择器配置(
        主选择器="button:has-text('确认关闭')",
        备选选择器=[
            "button:has-text('确认')",
            "div[class*='Modal'] button[class*='primary']",
        ],
    )

    商品ID输入框 = 选择器配置(
        主选择器="input[placeholder*='商品ID']",
        备选选择器=[
            "input[placeholder*='输入商品']",
        ],
    )

    查询按钮 = 选择器配置(
        主选择器="button:has-text('查询')",
        备选选择器=[
            "button[data-testid*='search']",
        ],
    )

    商品列表数据行 = 选择器配置(
        主选择器="tr[data-testid*='table-body-tr']",
        备选选择器=[
            "tbody tr",
        ],
    )

    全选复选框 = 选择器配置(
        主选择器="th label[data-testid='beast-core-checkbox']",
        备选选择器=[
            "thead label[data-testid='beast-core-checkbox']",
            "th input[type='checkbox']",
        ],
    )

    投产输入框 = 选择器配置(
        主选择器="input[data-testid*='roi']",
        备选选择器=[
            "input[placeholder*='投产']",
            "div[class*='roi'] input",
        ],
    )

    投产比限制提示 = 选择器配置(
        主选择器="div[class*='error']:has-text('投产')",
        备选选择器=[
            "span[class*='error']",
        ],
    )

    二阶段投产输入框 = 选择器配置(
        主选择器="div[class*='Modal'] input[data-testid*='roi']",
        备选选择器=[
            "div[class*='Modal'] input[placeholder*='投产']",
        ],
    )

    二阶段确认按钮 = 选择器配置(
        主选择器="div[class*='Modal'] button:has-text('确定')",
        备选选择器=[
            "div[class*='Modal'] button[class*='primary']",
        ],
    )

    开启推广按钮 = 选择器配置(
        主选择器="button:has-text('开启推广')",
        备选选择器=[
            "button[class*='primary']:has-text('开启')",
        ],
    )

    推广成功弹窗 = 选择器配置(
        主选择器="div:has-text('推广成功')",
        备选选择器=[
            "div[class*='success']",
        ],
    )

    @staticmethod
    def 获取投产设置按钮(商品ID: str) -> 选择器配置:
        """根据商品ID生成投产设置按钮（铅笔图标）选择器。"""
        return 选择器配置(
            主选择器=f"tr:has-text('{商品ID}') [data-testid*='edit']",
            备选选择器=[
                f"tr:has-text('{商品ID}') svg[class*='edit']",
                f"tr:has-text('{商品ID}') button[class*='edit']",
            ],
        )

    @staticmethod
    def 获取极速起量开关(商品ID: str) -> 选择器配置:
        """根据商品ID生成极速起量开关选择器。"""
        return 选择器配置(
            主选择器=f"tr:has-text('{商品ID}') button[role='switch']",
            备选选择器=[],
        )

    @staticmethod
    def 获取确认按钮(商品ID: str) -> 选择器配置:
        """根据商品ID生成确认按钮选择器。"""
        return 选择器配置(
            主选择器="button:has-text('确定')",
            备选选择器=["button[class*='primary']:has-text('确定')"],
        )

    @staticmethod
    def 获取取消按钮(商品ID: str) -> 选择器配置:
        """根据商品ID生成取消按钮选择器。"""
        return 选择器配置(
            主选择器="button:has-text('取消')",
            备选选择器=["button:has-text('取消')"],
        )

    @staticmethod
    def 获取取消勾选框(商品ID: str) -> 选择器配置:
        """根据商品ID生成取消勾选框选择器。"""
        return 选择器配置(
            主选择器=f"tr:has-text('{商品ID}') label[data-testid='beast-core-checkbox']",
            备选选择器=[],
        )
