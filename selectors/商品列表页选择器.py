from selectors.选择器配置 import 选择器配置


class 商品列表页选择器:
    """商品列表页元素选择器"""

    弹窗关闭按钮 = 选择器配置(
        主选择器="[data-testid='beast-core-icon-close']",
        备选选择器=[".ant-modal-close"],
    )
    弹窗关闭文本 = 选择器配置(
        主选择器="text=我知道了",
        备选选择器=["text=关闭"],
    )
    搜索类型下拉 = 选择器配置(
        主选择器="[data-testid='beast-core-select-selection']",
        备选选择器=[".search-select-trigger", "text=商品名称", "text=商品ID", "i"],
    )
    商品ID选项 = 选择器配置(
        主选择器="[data-testid='beast-core-select-option']:has-text('商品ID')",
        备选选择器=['role=option[name="商品ID"]', "text=商品ID"],
    )
    商品ID搜索框 = 选择器配置(
        主选择器="[data-tracking-viewid='goods_id'] input",
        备选选择器=[
            ".search-item:has-text('商品ID') input",
            "input[placeholder*='多个查询']",
            "div:has-text('商品ID') [data-testid='beast-core-input-htmlInput']",
        ],
    )
    查询按钮 = 选择器配置(
        主选择器="button[data-tracking-click-viewid='ele_inquire']",
        备选选择器=["button:has-text('查询')"],
    )
    发布相似按钮 = 选择器配置(
        主选择器="a[data-tracking-viewid='new_similar']",
        备选选择器=["a:has-text('发布相似品')", "text='发布相似品'"],
    )
    发布相似品弹窗_确认按钮 = 选择器配置(
        主选择器="button[data-tracking-viewid='el_release_similar_pop_ups']",
        备选选择器=["div[data-testid='beast-core-modal-body'] button:has-text('确认')"],
    )
    商品列表容器 = 选择器配置(
        主选择器=".goods-list",
        备选选择器=["[class*='goodsList']", ".product-list"],
    )
    商品项 = 选择器配置(
        主选择器=".goods-item",
        备选选择器=["[class='goodsItem']", "tr[class='goods']"],
    )
