"""拼多多后台售后管理页选择器。"""
from selectors.选择器配置 import 选择器配置


class 售后页选择器:
    """售后管理页面元素定位。"""

    售后列表页URL = "https://mms.pinduoduo.com/aftersales/aftersale_list?msfrom=mms_sidenav"

    列表容器 = 选择器配置(
        主选择器="//div[contains(@class, 'order_list')]",
        备选选择器=[
            "//div[contains(@class, 'order_item_list')]",
            "//div[contains(@class, 'after-sales-list')]",
            "//div[contains(@class, 'refund-list')]",
        ],
    )

    待商家处理卡片 = 选择器配置(
        主选择器='//span[text()="待商家处理"]/ancestor::div[@data-testid="beast-core-card"]',
        备选选择器=[
            "//span[contains(., '待商家处理')]/ancestor::div[@data-testid='beast-core-card']",
        ],
    )

    待商家处理选中类名片段 = "CAD_beastCardChecked"

    售后单行 = 选择器配置(
        主选择器='//div[contains(@class, "order_item")]',
        备选选择器=[
            "//tr[contains(@class, 'ant-table-row')]",
            "//div[contains(@class, 'refund-item')]",
        ],
    )

    待商家处理Tab = 选择器配置(
        主选择器='//span[text()="待商家处理"]/ancestor::div[@data-testid="beast-core-card"]',
        备选选择器=[
            "//div[contains(@class, 'ant-tabs-tab') and contains(., '待商家处理')]",
            "//div[contains(@class, 'ant-tabs-tab') and contains(., '待处理')]",
        ],
    )

    待处理Tab = 选择器配置(
        主选择器="//div[contains(@class, 'ant-tabs-tab') and contains(., '待处理')]",
    )

    已处理Tab = 选择器配置(
        主选择器="//div[contains(@class, 'ant-tabs-tab') and contains(., '已处理')]",
    )

    搜索输入框 = 选择器配置(
        主选择器="//input[contains(@placeholder, '订单号') or contains(@placeholder, '售后单号')]",
        备选选择器=["//input[contains(@placeholder, '搜索')]"],
    )

    搜索按钮 = 选择器配置(
        主选择器="//button[.//span[text()='查询'] or .//span[text()='搜索']]",
    )

    售后类型标签 = 选择器配置(
        主选择器="//span[contains(@class, 'refund-type') or contains(@class, 'after-sale-type')]",
    )

    退款金额 = 选择器配置(
        主选择器="//span[contains(@class, 'refund-amount') or contains(@class, 'refund-money')]",
        备选选择器=["//td[contains(., '退款金额')]/following-sibling::td[1]"],
    )

    订单号 = 选择器配置(
        主选择器="//span[contains(@class, 'order-sn')]",
        备选选择器=["//td[contains(., '订单号')]/following-sibling::td[1]"],
    )

    商品名称 = 选择器配置(
        主选择器="//span[contains(@class, 'goods-name')]",
        备选选择器=["//td[contains(., '商品')]/following-sibling::td[1]"],
    )

    退款原因 = 选择器配置(
        主选择器="//span[contains(@class, 'refund-reason')]",
        备选选择器=["//td[contains(., '退款原因')]/following-sibling::td[1]"],
    )

    发货状态 = 选择器配置(
        主选择器="//span[contains(@class, 'shipping-status')]",
        备选选择器=["//td[contains(., '物流状态')]/following-sibling::td[1]"],
    )

    同意退款按钮 = 选择器配置(
        主选择器="//button[.//span[text()='同意退款']]",
        备选选择器=[
            "//button[contains(., '同意')]",
            "//a[contains(., '同意退款')]",
        ],
    )

    同意退货按钮 = 选择器配置(
        主选择器="//button[.//span[text()='同意退货']]",
        备选选择器=["//button[contains(., '同意退货')]"],
    )

    拒绝按钮 = 选择器配置(
        主选择器="//button[.//span[text()='拒绝']]",
        备选选择器=["//button[contains(., '拒绝退款')]"],
    )

    查看详情按钮 = 选择器配置(
        主选择器="//a[contains(., '查看详情')]",
        备选选择器=["//button[contains(., '详情')]"],
    )

    确认弹窗 = 选择器配置(
        主选择器="//div[contains(@class, 'ant-modal-content')]",
    )

    确认弹窗确定按钮 = 选择器配置(
        主选择器="//div[contains(@class, 'ant-modal-content')]//button[.//span[text()='确定']]",
        备选选择器=[
            "//div[contains(@class, 'ant-modal')]//button[contains(@class, 'ant-btn-primary')]",
        ],
    )

    确认弹窗取消按钮 = 选择器配置(
        主选择器="//div[contains(@class, 'ant-modal-content')]//button[.//span[text()='取消']]",
    )

    物流单号输入框 = 选择器配置(
        主选择器="//input[contains(@placeholder, '物流单号') or contains(@placeholder, '快递单号')]",
    )

    物流公司选择框 = 选择器配置(
        主选择器="//div[contains(@class, 'logistics-select')]//input",
        备选选择器=["//input[contains(@placeholder, '物流公司') or contains(@placeholder, '快递公司')]"],
    )

    详情页区域 = 选择器配置(
        主选择器="//div[contains(@class, 'after-sale') and contains(@class, 'detail')]",
        备选选择器=[
            "//div[contains(@class, 'aftersale') and contains(@class, 'detail')]",
            "//div[contains(@class, 'refund') and contains(@class, 'detail')]",
        ],
    )

    下一页按钮 = 选择器配置(
        主选择器="//li[contains(@class, 'ant-pagination-next')]",
    )

    @staticmethod
    def 获取订单详情链接(订单号: str) -> 选择器配置:
        """按订单号定位该行的查看详情链接。"""
        return 选择器配置(
            主选择器=(
                f'//span[text()="{订单号}"]/ancestor::div[contains(@class, "order_item")]'
                '//a[span[text()="查看详情"]]'
            ),
            备选选择器=[
                (
                    f'//span[text()="{订单号}"]/ancestor::div[contains(@class, "order_item")]'
                    '//a[contains(., "详情")]'
                ),
                (
                    f'//span[text()="{订单号}"]/ancestor::tr[contains(@class, "ant-table-row")]'
                    '//a[contains(., "详情")]'
                ),
            ],
        )

    @staticmethod
    def 获取订单操作按钮(订单号: str, 操作文本: str) -> 选择器配置:
        """按订单号定位该行的指定操作按钮。"""
        return 选择器配置(
            主选择器=(
                f'//span[text()="{订单号}"]/ancestor::div[contains(@class, "order_item")]'
                f'//a[span[text()="{操作文本}"]] | '
                f'//span[text()="{订单号}"]/ancestor::div[contains(@class, "order_item")]'
                f'//button[span[text()="{操作文本}"]]'
            ),
            备选选择器=[
                (
                    f'//span[text()="{订单号}"]/ancestor::div[contains(@class, "order_item")]'
                    f'//a[contains(., "{操作文本}")] | '
                    f'//span[text()="{订单号}"]/ancestor::div[contains(@class, "order_item")]'
                    f'//button[contains(., "{操作文本}")]'
                ),
                (
                    f'//span[text()="{订单号}"]/ancestor::tr[contains(@class, "ant-table-row")]'
                    f'//a[contains(., "{操作文本}")] | '
                    f'//span[text()="{订单号}"]/ancestor::tr[contains(@class, "ant-table-row")]'
                    f'//button[contains(., "{操作文本}")]'
                ),
            ],
        )

    @staticmethod
    def 获取第N行操作按钮(行号: int, 操作文本: str) -> 选择器配置:
        """获取列表第 N 行的指定操作按钮。"""
        return 选择器配置(
            主选择器=f'(//div[contains(@class, "order_item")])[{行号}]//button[contains(., "{操作文本}")]',
            备选选择器=[
                f'(//div[contains(@class, "order_item")])[{行号}]//a[contains(., "{操作文本}")]',
                f"(//tr[contains(@class, 'ant-table-row')])[{行号}]//button[contains(., '{操作文本}')]",
                f"(//tr[contains(@class, 'ant-table-row')])[{行号}]//a[contains(., '{操作文本}')]",
            ],
        )

    @staticmethod
    def 获取第N行详情链接(行号: int) -> 选择器配置:
        """获取列表第 N 行的查看详情链接。"""
        return 选择器配置(
            主选择器=f'(//div[contains(@class, "order_item")])[{行号}]//a[contains(., "查看详情")]',
            备选选择器=[
                f'(//div[contains(@class, "order_item")])[{行号}]//a[contains(., "详情")]',
                f"(//tr[contains(@class, 'ant-table-row')])[{行号}]//a[contains(., '查看详情')]",
                f"(//div[contains(@class, 'refund-item')])[{行号}]//a[contains(., '详情')]",
            ],
        )
