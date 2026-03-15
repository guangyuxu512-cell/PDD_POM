Task 38.8（精简版）：极速起量"确定"按钮选择器替换
涉及文件
selectors/推广页选择器.py
测试同步更新
修改内容
获取极速起量高级版关闭确认按钮(商品ID) 修改为：
@staticmethod
def 获取极速起量高级版关闭确认按钮(商品ID: str) -> 选择器配置:
    return 选择器配置(
        主选择器=f'//button[contains(@data-testid, "assist_close") and contains(@data-testid, "{商品ID}")]',
        备选选择器=[
            '//button[.//span[text()="确定关闭"]]',
            '//div[contains(@class, "anq-flex")]/button[normalize-space(.)="确定"]',
        ],
    )
​
选择器尝试顺序：
主用：assist_close + 商品ID（形态A 带 testid 的"确定关闭"）
备用1：span[text()="确定关闭"]（形态A 通用"确定关闭"文字）
备用2：//div[contains(@class, "anq-flex")]/button[normalize-space(.)="确定"]（形态B popover 内的"确定"）
约束
"确定关闭"的两个选择器必须保留
新增的"确定"选择器用你指定的 anq-flex 容器限定
测试同步更新，确保 pytest 通过