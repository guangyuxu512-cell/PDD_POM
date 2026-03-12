from selectors.选择器配置 import 选择器配置


class 登录页选择器:
    """登录页元素选择器"""

    账号输入框 = 选择器配置(主选择器="#usernameId")
    密码输入框 = 选择器配置(主选择器="#passwordId")
    登录按钮 = 选择器配置(主选择器="button:has-text('登录')")
    账号登录 = 选择器配置(
        主选择器=".login-tab div:has-text('账号登录')",
        备选选择器=["text=账号登录", ".login-tab-item"],
    )
    短信验证码输入框 = 选择器配置(
        主选择器="input[placeholder='请输入短信验证码']",
        备选选择器=["input[placeholder='验证码']", "input[placeholder='短信']"],
    )
    发送验证码按钮 = 选择器配置(
        主选择器="button:has-text('发送验证码')",
        备选选择器=["button:has-text('获取验证码')"],
    )
    验证码提交按钮 = 选择器配置(
        主选择器="button:has-text('确定')",
        备选选择器=["button:has-text('提交')", "button[type='submit']"],
    )
    滑块验证码 = 选择器配置(
        主选择器=".captcha-container",
        备选选择器=[".captcha-slider", ".sc-jrQzAO", "#captcha_container"],
    )
