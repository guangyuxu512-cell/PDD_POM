"""拼多多商品列表页的页面对象模型"""
import re

from pages.基础页 import 基础页


class 商品列表页(基础页):
    """拼多多商品列表页 POM"""

    def __init__(self, 页面):
        super().__init__(页面)
        self.页面地址 = "https://mms.pinduoduo.com/goods/goods_list?msfrom=mms_sidenav"

    async def 导航(self) -> None:
        """打开商品列表页并尝试关闭弹窗。"""
        await self.页面.goto(self.页面地址, wait_until="domcontentloaded")
        await self.随机延迟(1, 2)
        await self.关闭所有弹窗()

    async def 关闭所有弹窗(self, 最大尝试次数: int = 5) -> None:
        """按优先级循环关闭商品列表页可能出现的弹窗。"""
        for _ in range(最大尝试次数):
            已处理 = False

            for 选择器 in [
                "[data-testid='beast-core-icon-close']",
                ".ant-modal-close",
            ]:
                弹窗 = await self.页面.query_selector(选择器)
                if 弹窗 is not None:
                    await 弹窗.click()
                    await self.随机延迟(0.3, 0.8)
                    已处理 = True
                    break

            if 已处理:
                continue

            for 文本 in ["我知道了", "关闭"]:
                按钮 = self.页面.get_by_text(文本)
                try:
                    if await 按钮.count() > 0:
                        await 按钮.first.click()
                        await self.随机延迟(0.3, 0.8)
                        已处理 = True
                        break
                except Exception:
                    continue

            if not 已处理:
                break

    async def 搜索商品(self, 商品ID: str) -> None:
        """按商品 ID 搜索。"""
        搜索切换 = self.页面.locator("i").first
        await 搜索切换.click()
        await self.随机延迟(0.3, 0.8)
        await self.安全点击_文本("商品ID")
        await self.随机延迟(0.3, 0.8)

        输入框 = (
            self.页面.locator("div")
            .filter(has_text=re.compile(r"^商品ID$"))
            .get_by_test_id("beast-core-input-htmlInput")
        )
        await 输入框.click()
        await 输入框.fill(商品ID)
        await self.随机延迟(0.3, 0.8)

        查询按钮 = self.页面.get_by_role("button", name="查询")
        await 查询按钮.click()
        await self.随机延迟(1, 2)

    async def 点击发布相似品(self):
        """点击发布相似品并返回新打开的页面对象。"""
        发布链接 = self.页面.locator("a").filter(has_text="发布相似品").first
        await 发布链接.click()
        await self.随机延迟(0.5, 1)

        确认按钮 = (
            self.页面.get_by_test_id("beast-core-modal-body")
            .get_by_test_id("beast-core-button")
            .first
        )
        async with self.页面.expect_popup() as 弹窗信息:
            await 确认按钮.click()

        新页面 = await 弹窗信息.value
        await 新页面.wait_for_load_state("domcontentloaded")
        return 新页面
