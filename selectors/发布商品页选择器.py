from selectors.选择器配置 import 选择器配置


class 发布商品页选择器:
    """发布商品页元素选择器"""

    弹窗关闭按钮 = 选择器配置(
        主选择器=".ant-modal-close",
        备选选择器=["button[aria-label='Close']", "[data-testid='beast-core-icon-close']"],
    )
    弹窗关闭文本 = 选择器配置(
        主选择器="button:has-text('我知道了')",
        备选选择器=["button:has-text('关闭')"],
    )
    商品标题输入框 = 选择器配置(
        主选择器="input[data-tracking-click-viewid='title_input_area']",
        备选选择器=[
            "input[placeholder*='商品标题组成']",
            "input[data-testid='beast-core-input-htmlInput'][maxlength='60']",
        ],
    )
    提交并上架按钮 = 选择器配置(
        主选择器="#submit_button",
        备选选择器=["button:has-text('提交并上架')"],
    )
    商品图片_所有图片项 = 选择器配置(
        主选择器="div[class='MaterialModalButton_v2_imageWrapper']",
        备选选择器=["span[class='MaterialModalButton_v2_imgContainer'] >> xpath=.."],
    )
    图片容器 = 选择器配置(
        主选择器="div[class*='MaterialModalButton_v2_imageBox']",
    )
    图片更换按钮文本 = 选择器配置(
        主选择器="button:has-text('选择图片')",
    )
    图片确认按钮文本 = 选择器配置(
        主选择器="button:has-text('确认')",
    )
    发布成功提示 = 选择器配置(
        主选择器=".success-title:has-text('提交成功')",
        备选选择器=[".success-wrapper", "svg[data-testid='beast-core-icon-check-circle_filled']"],
    )
    发布成功页URL特征: str = "goods_add/success"
    滑块验证码 = 选择器配置(
        主选择器="#slide-button",
        备选选择器=[".captcha-container", ".captcha-slider"],
    )
    主图拖拽目标 = 选择器配置(
        主选择器="//form//div[contains(@class, 'col')]//span/div[contains(@class, 'imageBox')]",
        备选选择器=[
            "div[class*='MaterialModalButton_v2_imageBox']",
            "div[class*='imageBox']"
        ]
    )
