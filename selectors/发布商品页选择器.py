class 发布商品页选择器:
    """发布商品页元素选择器"""

    弹窗关闭按钮列表: list[str] = [
        ".MaterialModalButton_v2_actionBox__1v6rw > div:nth-child(3)",
        ".ant-modal-close",
    ]
    弹窗关闭文本列表: list[str] = ["我知道了", "关闭"]
    商品标题输入框占位符列表: list[str] = ["商品标题组成：商品描述+规格，最多输入30个汉字（60"]
    提交并上架按钮文本列表: list[str] = ["提交并上架"]
    发布成功页URL特征: list[str] = ["goods_add/success"]
    发布成功页文本列表: list[str] = ["提交成功"]
    图片容器选择器列表: list[str] = [".MaterialModalButton_v2_imageBox__1NfrZ"]
    图片更换按钮文本列表: list[str] = ["选择图片"]
    图片确认按钮文本列表: list[str] = ["确认"]
    滑块验证码选择器列表: list[str] = [
        "#slide-button",
        ".captcha-container",
        ".captcha-slider",
    ]
