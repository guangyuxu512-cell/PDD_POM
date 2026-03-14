
Task 38.7：极速起量确认弹窗 — 用标题锚点统一匹配所有形态
一、做什么
用弹窗标题文字"极速起量"做锚点，统一匹配所有形态的确认按钮，彻底解决误匹配投产比弹窗"确定"按钮的问题。
二、涉及文件
selectors/推广页选择器.py — 替换所有极速起量确认弹窗选择器
pages/推广页.py — 简化 确认关闭极速起量 方法
测试同步更新
三、选择器修改
selectors/推广页选择器.py 修改：
删除以下三个选择器定义：
极速起量高级版关闭确认按钮_Popover
极速起量高级版关闭确认按钮（静态）
获取极速起量高级版关闭确认按钮(商品ID)（动态方法）
替换为一个统一方法：
@staticmethod
def 获取极速起量高级版关闭确认按钮(商品ID: str) -> 选择器配置:
    return 选择器配置(
        主选择器=(
            '//div[contains(@class, "anq-popover") and '
            './/div[contains(text(), "极速起量")]]'
            '//button[contains(@class, "anq-btn-primary") or '
            './/span[text()="确定关闭"]]'
        ),
        备选选择器=[
            f'//button[contains(@data-testid, "assist_close") and contains(@data-testid, "{商品ID}")]',
            '//button[.//span[text()="确定关闭"]]',
        ],
    )
​
选择器逻辑：
主用：找到包含"极速起量"文字的 popover 容器 → 在里面找 primary 按钮或"确定关闭"文字按钮。覆盖所有形态，不会误匹配
备用1：带商品ID的 data-testid 按钮（兼容 assist_close 拼接）
备用2：全局匹配"确定关闭"文字按钮（最后兜底）
四、POM 修改
pages/推广页.py 简化 确认关闭极速起量(商品ID) 方法：
async def 确认关闭极速起量(self, 商品ID: str) -> bool:
    await self._随机等待()
    最后异常 = None
    for 选择器 in 推广页选择器.获取极速起量高级版关闭确认按钮(商品ID).所有选择器():
        try:
            await self.页面.wait_for_selector(选择器, timeout=3000)
            await self.页面.click(选择器, timeout=3000)
            print(f"[推广页] 已确认关闭极速起量: 商品ID={商品ID}, 选择器={选择器}")
            await self._确认弹窗后等待()
            return True
        except Exception as 异常:
            最后异常 = 异常
            print(f"[推广页] 极速起量确认失败(商品ID={商品ID}, 选择器={选择器}): {异常}")
    try:
        await self.截图("极速起量确认弹窗未找到")
    except Exception:
        pass
    print(f"[推广页] 极速起量确认弹窗处理失败: 商品ID={商品ID}, error={最后异常}")
    return False
​
不再分三段尝试不同的选择器组，一个循环搞定。
五、约束
主用选择器必须用 contains(text(), "极速起量") 限定 popover 范围
主用选择器同时匹配 anq-btn-primary（"确定"按钮）和 span[text()="确定关闭"]（"确定关闭"按钮），用 or 连接
每个选择器超时设 3 秒（比之前的 2 秒稍长，给 popover 更多渲染时间）
删除旧的三个选择器定义，只保留统一的 获取极速起量高级版关闭确认按钮 方法
测试同步更新，确保 pytest 通过