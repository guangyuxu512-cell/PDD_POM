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
        主选择器='//div[@class="Footer_mallAdditionalMaxCostCardInCreateWrapper__6jkyL"]/div/label',
        备选选择器=[
            '//div[@class="Footer_mallAdditionalMaxCostCardInCreateWrapper__6jkyL"]/div/label',
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

    预算日限额菜单项 = 选择器配置(
        主选择器='//span[@class="anq-dropdown-menu-title-content" and text()="预算日限额"]',
        备选选择器=[
            '//span[contains(@class, "anq-dropdown-menu-title-content") and text()="预算日限额"]',
        ],
    )

    日限额输入框 = 选择器配置(
        主选择器='//input[@data-testid="CustomInputNumber" and @placeholder="请输入"]',
        备选选择器=[
            '//input[@data-testid="CustomInputNumber" and @type="text"]',
        ],
    )

    日限额确认按钮 = 选择器配置(
        主选择器='//button[@class="anq-btn anq-btn-primary" and span/text()="确定"]',
        备选选择器=[
            '//button[contains(@class, "anq-btn-primary") and .//span[text()="确定"]]',
        ],
    )

    投产比输入框 = 选择器配置(
        主选择器='//input[@data-testid="CustomInputNumber" and @class="anq-input" and @placeholder="请输入" and @inputwidth="280"]',
        备选选择器=[
            '//input[@data-testid="CustomInputNumber" and @type="text"]',
        ],
    )

    开启推广按钮 = 选择器配置(
        主选择器='//button[@data-testid="beginPromotionButton" and @class="anq-btn anq-btn-primary" and contains(span/text(), "开启推广")]',
        备选选择器=[
            '//button[contains(@class, "anq-btn-primary") and not(contains(@class, "anq-btn-disabled")) and @data-testid="beginPromotionButton" and .//span[contains(text(), "开启推广")]]',
        ],
    )

    推广成功弹窗 = 选择器配置(
        主选择器="div:has-text('推广成功')",
        备选选择器=[
            "div[class*='success']",
        ],
    )

    @staticmethod
    def 获取商品行容器(商品ID: str) -> 选择器配置:
        """根据商品ID生成商品行容器选择器。"""
        return 选择器配置(
            主选择器=f'//div[@data-testid="create_item_{商品ID}"]',
            备选选择器=[],
        )

    @staticmethod
    def 获取修改投产铅笔按钮(商品ID: str) -> 选择器配置:
        """根据商品ID生成修改投产铅笔按钮选择器。"""
        return 选择器配置(
            主选择器=(
                f'//span[@data-testid="editBid_{商品ID}_create_create" and '
                'contains(@class, "MultiSuggestBidPop_triggerNode__Qx_dI")]'
            ),
            备选选择器=[
                (
                    f'//div[@data-testid="create_goods_promotion_setting_container_{商品ID}"]'
                    '//span[contains(@class, "MultiSuggestBidPop_icon__4lMUm")]'
                ),
            ],
        )

    @staticmethod
    def 获取更多设置按钮(商品ID: str) -> 选择器配置:
        """根据商品ID生成更多设置按钮选择器。"""
        return 选择器配置(
            主选择器=f'//div[@data-testid="create_goods_more-setting_{商品ID}"]/button',
            备选选择器=[
                (
                    f'//div[@data-testid="create_goods_more-setting_{商品ID}"]'
                    '/button[contains(@class, "anq-dropdown-trigger")]'
                ),
            ],
        )

    @staticmethod
    def 获取极速起量高级版开关(商品ID: str) -> 选择器配置:
        """根据商品ID生成极速起量高级版开关选择器。"""
        return 选择器配置(
            主选择器=f'//button[@data-testid="bidPop-{商品ID}-assist-switch"]',
            备选选择器=[
                f'//button[@data-testid="bidPop-{商品ID}-assist-switch" and @role="switch"]',
            ],
        )

    @staticmethod
    def 获取投产设置确认按钮(商品ID: str) -> 选择器配置:
        """根据商品ID生成投产设置确认按钮选择器。"""
        return 选择器配置(
            主选择器=f'//button[@data-testid="confirm_{商品ID}" and @class="anq-btn anq-btn-primary anq-btn-sm"]',
            备选选择器=[
                (
                    f'//button[@data-testid="confirm_{商品ID}" and contains(@class, "anq-btn-primary") '
                    'and .//span[text()="确定"]]'
                ),
            ],
        )
