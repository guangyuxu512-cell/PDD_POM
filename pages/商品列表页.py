"""拼多多商品列表页的页面对象模型"""
from datetime import datetime
import inspect
from pathlib import Path

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

    async def 导航到商品列表(self) -> None:
        """导航到商品列表页 URL。"""
        await self.页面.goto(self.页面地址, wait_until="domcontentloaded")
        print(f"[商品列表页] 商品列表页加载完成: {self.页面.url}")
        await self.页面加载延迟()

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

    async def 等待搜索结果(self) -> None:
        """等待列表刷新完成。"""
        print("[商品列表页] 准备等待搜索结果刷新")
        等待方法 = getattr(self.页面, "wait_for_selector", None)
        if 等待方法 is None:
            await self.随机延迟(1.0, 2.0)
            print("[商品列表页] 页面未提供 wait_for_selector，已使用随机延迟代替")
            return

        最后异常 = None
        候选选择器 = [
            *商品列表页选择器.商品列表容器.所有选择器(),
            *商品列表页选择器.商品项.所有选择器(),
        ]
        for 选择器 in 候选选择器:
            try:
                等待结果 = 等待方法(选择器, timeout=5000)
                if inspect.isawaitable(等待结果):
                    await 等待结果
                await self.随机延迟(1.0, 2.0)
                print(f"[商品列表页] 搜索结果刷新完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[商品列表页] 搜索结果等待失败({选择器}): {异常}")

        await self.随机延迟(1.0, 2.0)
        print(f"[商品列表页] 搜索结果未命中候选选择器，已回退随机延迟: {最后异常}")

    async def 输入商品ID(self, 商品ID: str) -> None:
        """在搜索框输入商品ID。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 商品列表页选择器.商品ID搜索框.所有选择器():
            try:
                print(f"[商品列表页] 尝试定位商品ID输入框: {选择器}")
                输入框 = self.页面.locator(选择器).first
                await 输入框.click(timeout=10000)
                await self.随机延迟(0.2, 0.5)
                await 输入框.fill(商品ID)
                await self.操作后延迟()
                print(f"[商品列表页] 商品ID填写完成: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[商品列表页] 商品ID输入框定位失败({选择器}): {异常}")
        raise RuntimeError("商品ID输入框定位失败: 所有选择器均超时")

    async def 点击查询(self) -> None:
        """点击查询按钮。"""
        await self.操作前延迟()
        for 选择器 in 商品列表页选择器.查询按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[商品列表页] 查询按钮点击完成: {选择器}")
                return
            except Exception as 异常:
                print(f"[商品列表页] 查询按钮点击失败({选择器}): {异常}")
        raise RuntimeError("查询按钮点击失败: 所有选择器均超时")

    async def 点击发布相似(self) -> None:
        """点击发布相似品按钮。"""
        await self.操作前延迟()
        for 选择器 in 商品列表页选择器.发布相似按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.操作后延迟()
                print(f"[商品列表页] 发布相似品按钮点击完成: {选择器}")
                return
            except Exception as 异常:
                print(f"[商品列表页] 发布相似品按钮点击失败({选择器}): {异常}")
        raise RuntimeError("发布相似品按钮点击失败: 所有选择器均超时")

    async def 确认发布相似弹窗(self) -> None:
        """点击发布相似品弹窗中的确认按钮。"""
        await self.操作前延迟()
        for 选择器 in 商品列表页选择器.发布相似品弹窗_确认按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.页面加载延迟()
                print(f"[商品列表页] 发布相似品弹窗确认完成: {选择器}")
                return
            except Exception as 异常:
                print(f"[商品列表页] 发布相似品弹窗确认失败({选择器}): {异常}")
        raise RuntimeError("发布相似品弹窗确认失败: 所有选择器均超时")

    async def 切回前台(self) -> None:
        """关闭编辑页后尽量切回商品列表页标签。"""
        切换方法 = getattr(self.页面, "bring_to_front", None)
        if 切换方法 is None:
            return

        切换结果 = 切换方法()
        if inspect.isawaitable(切换结果):
            await 切换结果

    async def 关闭所有弹窗(self, 最大尝试次数: int = 5) -> None:
        """按优先级循环关闭商品列表页可能出现的弹窗。"""
        for _ in range(最大尝试次数):
            已处理 = False

            for 选择器 in 商品列表页选择器.弹窗关闭按钮.所有选择器():
                弹窗 = await self.页面.query_selector(选择器)
                if 弹窗 is not None:
                    await 弹窗.click()
                    await self.随机延迟(0.3, 0.8)
                    已处理 = True
                    break

            if 已处理:
                continue

            for 选择器 in 商品列表页选择器.弹窗关闭文本.所有选择器():
                try:
                    await self.页面.click(选择器, timeout=1000)
                    await self.随机延迟(0.3, 0.8)
                    已处理 = True
                    break
                except Exception:
                    continue

            if not 已处理:
                break

    async def 点击发布相似品(self):
        """点击发布相似品并返回新打开的页面对象。"""
        最后异常 = None
        for 选择器 in 商品列表页选择器.发布相似按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                break
            except Exception as 异常:
                最后异常 = 异常
        else:
            raise RuntimeError(f"点击发布相似品失败: {最后异常}")
        await self.随机延迟(0.5, 1)
        async with self.页面.expect_popup() as 弹窗信息:
            最后异常 = None
            for 选择器 in 商品列表页选择器.发布相似品弹窗_确认按钮.所有选择器():
                try:
                    await self.页面.click(选择器, timeout=10000)
                    break
                except Exception as 异常:
                    最后异常 = 异常
            else:
                raise RuntimeError(f"点击发布相似品确认按钮失败: {最后异常}")

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
