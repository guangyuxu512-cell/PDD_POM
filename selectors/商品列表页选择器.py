class 商品列表页选择器:
    """商品列表页元素选择器"""

    弹窗关闭按钮列表: list[str] = [
        "[data-testid='beast-core-icon-close']",
        ".ant-modal-close",
    ]
    弹窗关闭文本列表: list[str] = ["我知道了", "关闭"]
    搜索类型下拉CSS列表: list[str] = [
        "[data-testid='beast-core-select-selection']",
        ".search-select-trigger",
        "i",
    ]
    搜索类型下拉文本列表: list[str] = ["商品名称", "商品ID"]
    商品ID选项CSS列表: list[str] = ["[data-testid='beast-core-select-option']"]
    商品ID选项角色文本列表: list[str] = ["商品ID"]
    商品ID选项兼容文本列表: list[str] = ["商品ID"]
    商品ID输入区域容器选择器列表: list[str] = ["div"]
    商品ID输入区域文本列表: list[str] = [r"^商品ID$"]
    商品ID输入框测试ID列表: list[str] = ["beast-core-input-htmlInput"]
    查询按钮文本列表: list[str] = ["查询"]
    发布相似品链接选择器列表: list[str] = ["a"]
    发布相似品链接文本列表: list[str] = ["发布相似品"]
    发布相似品弹窗容器测试ID列表: list[str] = ["beast-core-modal-body"]
    发布相似品弹窗确认按钮测试ID列表: list[str] = ["beast-core-button"]
