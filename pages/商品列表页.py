"""拼多多商品列表页的页面对象模型"""
from datetime import datetime
import inspect
from pathlib import Path
import re

from pages.基础页 import 基础页
from selectors.商品列表页选择器 import 商品列表页选择器


class 商品列表页(基础页):
    """拼多多商品列表页 POM"""

    def __init__(self, 页面):
        super().__init__(页面)
        self.页面地址 = "https://mms.pinduoduo.com/goods/goods_list?msfrom=mms_sidenav"

    async def 导航(self) -> None:
        """打开商品列表页并尝试关闭弹窗。"""
        await self.页面.goto(self.页面地址, wait_until="domcontentloaded")
        print(f"[商品列表页] 当前URL: {self.页面.url}")
        await self.随机延迟(1, 2)
        await self.关闭所有弹窗()
        print(f"[商品列表页] 当前URL: {self.页面.url}")

    async def _保存搜索失败截图(self) -> None:
        """保存搜索失败时的页面截图。"""
        时间戳 = datetime.now().strftime("%Y%m%d_%H%M%S")
        截图目录 = Path("data/screenshots")
        截图目录.mkdir(parents=True, exist_ok=True)
        截图路径 = 截图目录 / f"搜索失败_{时间戳}.png"
        try:
            await self.页面.screenshot(path=str(截图路径))
            print(f"[商品列表页] 已保存失败截图: {截图路径}")
        except Exception as 异常:
            print(f"[商品列表页] 保存失败截图失败: {异常}")

    async def _点击搜索类型下拉(self) -> None:
        """尝试点击搜索类型下拉按钮。"""
        候选定位器 = []
        for 选择器 in 商品列表页选择器.搜索类型下拉CSS列表:
            候选定位器.append((选择器, lambda 当前选择器=选择器: self.页面.locator(当前选择器).first, False))
        for 文本 in 商品列表页选择器.搜索类型下拉文本列表:
            候选定位器.append((文本, lambda 当前文本=文本: self.页面.get_by_text(当前文本), True))

        最后异常 = None
        for 描述, 工厂, 需要检查数量 in 候选定位器:
            try:
                print(f"[商品列表页] 尝试点击搜索类型下拉: {描述}")
                定位器 = 工厂()
                if 需要检查数量:
                    数量 = await 定位器.count()
                    if 数量 <= 0:
                        raise RuntimeError(f"{描述} 未找到可点击元素")
                    定位器 = getattr(定位器, "first", 定位器)
                await 定位器.click(timeout=10000)
                print(f"[商品列表页] 已点击搜索类型下拉: {描述}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[商品列表页] 点击搜索类型下拉失败({描述}): {异常}")

        raise RuntimeError(f"搜索类型下拉点击失败: {最后异常}")

    async def _选择商品ID选项(self) -> None:
        """尝试在下拉中选择商品ID。"""
        定位器候选 = []
        for 选择器 in 商品列表页选择器.商品ID选项CSS列表:
            定位器候选.append(
                (
                    选择器,
                    lambda 当前选择器=选择器: self.页面.locator(当前选择器).filter(
                        has_text=商品列表页选择器.商品ID选项角色文本列表[0]
                    ),
                )
            )
        for 文本 in 商品列表页选择器.商品ID选项角色文本列表:
            定位器候选.append((文本, lambda 当前文本=文本: self.页面.get_by_role("option", name=当前文本)))

        最后异常 = None
        for 描述, 工厂 in 定位器候选:
            try:
                print(f"[商品列表页] 尝试选择商品ID选项: {描述}")
                定位器 = 工厂()
                数量 = await 定位器.count()
                if 数量 <= 0:
                    raise RuntimeError(f"{描述} 未找到商品ID选项")
                await 定位器.click(timeout=10000)
                print(f"[商品列表页] 已选择商品ID选项: {描述}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[商品列表页] 选择商品ID选项失败({描述}): {异常}")

        try:
            for 文本 in 商品列表页选择器.商品ID选项兼容文本列表:
                print(f"[商品列表页] 尝试选择商品ID选项: {文本}")
                await self.安全点击_文本(文本)
                print(f"[商品列表页] 已选择商品ID选项: {文本}")
                return
        except Exception as 异常:
            最后异常 = 异常
            print(f"[商品列表页] 选择商品ID选项失败({商品列表页选择器.商品ID选项兼容文本列表[0]}): {异常}")

        raise RuntimeError(f"选择商品ID选项失败: {最后异常}")

    async def 关闭所有弹窗(self, 最大尝试次数: int = 5) -> None:
        """按优先级循环关闭商品列表页可能出现的弹窗。"""
        for _ in range(最大尝试次数):
            已处理 = False

            for 选择器 in 商品列表页选择器.弹窗关闭按钮列表:
                弹窗 = await self.页面.query_selector(选择器)
                if 弹窗 is not None:
                    await 弹窗.click()
                    await self.随机延迟(0.3, 0.8)
                    已处理 = True
                    break

            if 已处理:
                continue

            for 文本 in 商品列表页选择器.弹窗关闭文本列表:
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
        print(f"[商品列表页] 开始搜索商品，商品ID: {商品ID}")

        print("[商品列表页] 准备点击搜索类型下拉")
        try:
            await self._点击搜索类型下拉()
            await self.随机延迟(0.3, 0.8)
            print("[商品列表页] 搜索类型下拉点击完成")
        except Exception as 异常:
            print(f"[商品列表页] 点击搜索类型下拉失败: {异常}")
            await self._保存搜索失败截图()
            raise

        print("[商品列表页] 准备选择商品ID选项")
        try:
            await self._选择商品ID选项()
            await self.随机延迟(0.3, 0.8)
            print("[商品列表页] 商品ID选项选择完成")
        except Exception as 异常:
            print(f"[商品列表页] 选择商品ID选项失败: {异常}")
            await self._保存搜索失败截图()
            raise

        print("[商品列表页] 准备填写商品ID输入框")
        try:
            输入框 = (
                self.页面.locator(商品列表页选择器.商品ID输入区域容器选择器列表[0])
                .filter(has_text=re.compile(商品列表页选择器.商品ID输入区域文本列表[0]))
                .get_by_test_id(商品列表页选择器.商品ID输入框测试ID列表[0])
            )
            await 输入框.click(timeout=10000)
            print("[商品列表页] 已点击商品ID输入框")
            await 输入框.fill(商品ID)
            await self.随机延迟(0.3, 0.8)
            print(f"[商品列表页] 商品ID填写完成: {商品ID}")
        except Exception as 异常:
            print(f"[商品列表页] 填写商品ID失败: {异常}")
            await self._保存搜索失败截图()
            raise

        print("[商品列表页] 准备点击查询按钮")
        try:
            查询按钮 = self.页面.get_by_role("button", name=商品列表页选择器.查询按钮文本列表[0])
            await 查询按钮.click(timeout=10000)
            await self.随机延迟(1, 2)
            print("[商品列表页] 查询按钮点击完成")
        except Exception as 异常:
            print(f"[商品列表页] 点击查询按钮失败: {异常}")
            await self._保存搜索失败截图()
            raise

    async def 点击发布相似品(self):
        """点击发布相似品并返回新打开的页面对象。"""
        发布链接 = self.页面.locator(商品列表页选择器.发布相似品链接选择器列表[0]).filter(
            has_text=商品列表页选择器.发布相似品链接文本列表[0]
        ).first
        await 发布链接.click()
        await self.随机延迟(0.5, 1)

        确认按钮 = (
            self.页面.get_by_test_id(商品列表页选择器.发布相似品弹窗容器测试ID列表[0])
            .get_by_test_id(商品列表页选择器.发布相似品弹窗确认按钮测试ID列表[0])
            .first
        )
        async with self.页面.expect_popup() as 弹窗信息:
            await 确认按钮.click()

        新页面 = await 弹窗信息.value
        print(f"[商品列表页] 已拿到新页面, URL: {新页面.url}")
        print(f"[商品列表页] 准备等待编辑页URL, URL: {新页面.url}")
        等待结果 = 新页面.wait_for_url(
            lambda url: "goods_edit" in url or "edit" in url or "add" in url or "goods_add" in url,
            timeout=30000,
        )
        if inspect.isawaitable(等待结果):
            await 等待结果
        print(f"[商品列表页] 编辑页URL等待完成, URL: {新页面.url}")
        print(f"[商品列表页] 准备等待新页面加载完成, URL: {新页面.url}")
        await 新页面.wait_for_load_state("domcontentloaded")
        print(f"[商品列表页] 新页面加载完成, URL: {新页面.url}")
        return 新页面
