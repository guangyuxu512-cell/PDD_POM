from selectors.选择器配置 import 选择器配置


class 商品列表页选择器:
    """商品列表页元素选择器"""

    弹窗关闭按钮 = 选择器配置(
        主选择器="[data-testid='beast-core-icon-close']",
        备选选择器=[".ant-modal-close"],
    )
    弹窗关闭文本 = 选择器配置(
        主选择器="button:has-text('我知道了')",
        备选选择器=["button:has-text('关闭')"],
    )
    商品ID搜索框 = 选择器配置(
        主选择器="[data-tracking-viewid='goods_id'] input",
        备选选择器=["input[placeholder='请输入商品ID']"],
    )
    查询按钮 = 选择器配置(
        主选择器="button[data-tracking-click-viewid='ele_inquire']",
        备选选择器=["button:has-text('查询')"],
    )
    发布相似按钮 = 选择器配置(
        主选择器="a[data-tracking-viewid='new_similar']",
        备选选择器=["a:has-text('发布相似品')"],
    )
    发布相似品弹窗_确认按钮 = 选择器配置(
        主选择器="button[data-tracking-viewid='el_release_similar_pop_ups']",
        备选选择器=["button:has-text('确认')"],
    )
    商品列表容器 = 选择器配置(
        主选择器="table tbody",
        备选选择器=["[data-testid='beast-core-table-body']", ".goods-list-table"],
    )
    商品项 = 选择器配置(
        主选择器="table tbody tr",
        备选选择器=["[data-testid='beast-core-table-row']", ".goods-list-table tr"],
    )
