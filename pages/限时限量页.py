"""限时限量页的页面对象模型。"""
from pages.基础页 import 基础页
from selectors.限时限量页选择器 import 限时限量页选择器


class 限时限量页(基础页):
    """拼多多限时限量活动创建页。"""

    def __init__(self, 页面):
        super().__init__(页面)
        self.创建页地址 = "https://mms.pinduoduo.com/tool/promotion/create?tool_full_channel=10921_77271"

    async def 导航到创建页(self) -> None:
        """打开限时限量创建页。"""
        await self.页面.goto(self.创建页地址, wait_until="domcontentloaded")
        print(f"[限时限量页] 创建页加载完成: {self.页面.url}")
        await self.页面加载延迟()

    async def 点击展开更多设置(self) -> None:
        """点击展开更多设置按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 限时限量页选择器.展开更多设置按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[限时限量页] 展开更多设置完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 展开更多设置失败({选择器}): {异常}")
        raise RuntimeError(f"展开更多设置失败: {最后异常}")

    async def 勾选自动创建(self) -> None:
        """勾选自动创建活动。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 限时限量页选择器.自动创建活动勾选项.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[限时限量页] 自动创建勾选完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 自动创建勾选失败({选择器}): {异常}")
        raise RuntimeError(f"自动创建勾选失败: {最后异常}")

    async def 点击选择商品(self) -> None:
        """点击选择商品按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 限时限量页选择器.选择商品按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[限时限量页] 选择商品弹窗已打开: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 选择商品按钮点击失败({选择器}): {异常}")
        raise RuntimeError(f"选择商品按钮点击失败: {最后异常}")

    async def 弹窗输入商品ID(self, 商品ID: str) -> None:
        """在选品弹窗搜索框输入商品ID。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 限时限量页选择器.选择商品弹窗_搜索输入框.所有选择器():
            try:
                输入框 = self.页面.locator(选择器).first
                await 输入框.click(timeout=10000)
                await self.页面.keyboard.press("Control+A")
                await self.随机延迟(0.2, 0.5)
                await 输入框.fill(商品ID)
                await self.操作后延迟()
                print(f"[限时限量页] 弹窗商品ID填写完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 弹窗商品ID填写失败({选择器}): {异常}")
        raise RuntimeError(f"弹窗商品ID填写失败: {最后异常}")

    async def 弹窗点击查询(self) -> None:
        """点击选品弹窗查询按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 限时限量页选择器.选择商品弹窗_查询按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[限时限量页] 弹窗查询完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 弹窗查询失败({选择器}): {异常}")
        raise RuntimeError(f"弹窗查询失败: {最后异常}")

    async def 弹窗等待结果(self) -> None:
        """等待弹窗查询结果出现。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 限时限量页选择器.选择商品弹窗_第一行勾选框.所有选择器():
            try:
                await self.页面.wait_for_selector(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[限时限量页] 弹窗查询结果已出现: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 弹窗查询结果等待失败({选择器}): {异常}")
        raise RuntimeError(f"弹窗查询结果等待失败: {最后异常}")

    async def 弹窗勾选第一行(self) -> None:
        """勾选选品弹窗第一行商品。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 限时限量页选择器.选择商品弹窗_第一行勾选框.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[限时限量页] 弹窗第一行勾选完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 弹窗第一行勾选失败({选择器}): {异常}")
        raise RuntimeError(f"弹窗第一行勾选失败: {最后异常}")

    async def 弹窗点击确认选择(self) -> None:
        """点击弹窗确认选择按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 限时限量页选择器.选择商品弹窗_确认选择按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[限时限量页] 弹窗确认选择完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 弹窗确认选择失败({选择器}): {异常}")
        raise RuntimeError(f"弹窗确认选择失败: {最后异常}")

    async def 填写折扣(self, 折扣值: float) -> None:
        """填写统一折扣。"""
        await self.操作前延迟()
        最后异常 = None
        文本值 = str(int(折扣值)) if float(折扣值).is_integer() else str(折扣值)
        for 选择器 in 限时限量页选择器.折扣输入框.所有选择器():
            try:
                输入框 = self.页面.locator(选择器).first
                await 输入框.click(timeout=10000)
                await self.页面.keyboard.press("Control+A")
                await self.随机延迟(0.2, 0.5)
                await 输入框.fill(文本值)
                await self.操作后延迟()
                print(f"[限时限量页] 折扣填写完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 折扣填写失败({选择器}): {异常}")
        raise RuntimeError(f"折扣填写失败: {最后异常}")

    async def 点击确认设置(self) -> None:
        """点击确认设置按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 限时限量页选择器.确认设置按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[限时限量页] 确认设置完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 确认设置失败({选择器}): {异常}")
        raise RuntimeError(f"确认设置失败: {最后异常}")

    async def 点击创建(self) -> None:
        """点击创建按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 限时限量页选择器.创建按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[限时限量页] 创建按钮点击完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[限时限量页] 创建按钮点击失败({选择器}): {异常}")
        raise RuntimeError(f"创建按钮点击失败: {最后异常}")

    async def 等待创建成功(self) -> bool:
        """等待创建成功提示。"""
        await self.操作前延迟()
        for 选择器 in 限时限量页选择器.创建成功提示.所有选择器():
            try:
                await self.页面.wait_for_selector(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[限时限量页] 创建成功提示已出现: {选择器}")
                return True
            except Exception as 异常:
                print(f"[限时限量页] 创建成功提示等待失败({选择器}): {异常}")
        return False
