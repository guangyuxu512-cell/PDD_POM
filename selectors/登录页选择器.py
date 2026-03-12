class 登录页选择器:
    """登录页元素选择器"""

    账号登录文本列表: list[str] = ["账号登录"]
    手机号输入框占位符列表: list[str] = ["请输入账号名/手机号"]
    密码输入框占位符列表: list[str] = ["请输入密码"]
    登录按钮测试ID列表: list[str] = ["beast-core-button"]
    滑块验证码选择器列表: list[str] = [
        ".captcha-container",
        ".captcha-slider",
        ".sc-jrQzAO",
        "#captcha_container",
    ]
    短信验证码输入框选择器列表: list[str] = [
        "[placeholder*='请输入短信验证码']",
        "[placeholder*='短信验证码']",
    ]
