"""推广页的页面对象模型。"""
from __future__ import annotations

import asyncio
import inspect
import random
import time

from pages.基础页 import 基础页
from selectors.推广页选择器 import 推广页选择器


class 推广页(基础页):
    """拼多多全站推广页 POM。"""

    全站推广URL = "https://yingxiao.pinduoduo.com/goods/promotion/list?msfrom=mms_sidenav"

    def __init__(self, 页面):
        super().__init__(页面)

    async def _随机等待(self) -> None:
        await asyncio.sleep(random.uniform(1.0, 3.0))

    async def _确认弹窗后等待(self) -> None:
        await asyncio.sleep(random.uniform(1.0, 2.0))

    async def 导航到全站推广页(self) -> None:
        """打开全站推广页。"""
        await self.页面.goto(self.全站推广URL, wait_until="domcontentloaded")
        print(f"[推广页] 全站推广页加载完成: {self.页面.url}")
        await self._随机等待()

    async def 返回商品列表页(self) -> None:
        """返回商品列表页。"""
        await self.页面.go_back(wait_until="domcontentloaded")
        print(f"[推广页] 已返回商品列表页: {self.页面.url}")
        await self._随机等待()

    async def 关闭广告弹窗(self) -> bool:
        """尝试关闭广告弹窗。"""
        已关闭 = False
        for _ in range(3):
            await self._随机等待()
            命中元素 = False
            for 选择器 in 推广页选择器.广告弹窗关闭按钮.所有选择器():
                try:
                    元素 = await self.页面.query_selector(选择器)
                    if 元素 is None:
                        continue
                    命中元素 = True
                    try:
                        await 元素.click()
                    except Exception:
                        try:
                            await self.页面.evaluate(
                                "(selector) => document.querySelector(selector)?.click()",
                                选择器,
                            )
                        except Exception:
                            await self.页面.keyboard.press("Escape")
                    print(f"[推广页] 已关闭广告弹窗: {选择器}")
                    已关闭 = True
                    break
                except Exception:
                    continue

            if 已关闭:
                continue

            if not 命中元素:
                break

        return 已关闭

    async def 点击添加推广商品(self) -> bool:
        """点击添加推广商品按钮。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.添加推广商品按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击添加推广商品: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 添加推广商品点击失败({选择器}): {异常}")
        return False

    async def 输入商品ID(self, 商品ID字符串: str) -> bool:
        """输入商品ID。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.商品ID输入框.所有选择器():
            try:
                输入框 = self.页面.locator(选择器).first
                await 输入框.click(timeout=10000)
                await self.页面.keyboard.press("Control+A")
                await self._随机等待()
                await 输入框.fill(商品ID字符串)
                print(f"[推广页] 已输入商品ID: {商品ID字符串}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 商品ID输入失败({选择器}): {异常}")
        return False

    async def 点击查询(self) -> bool:
        """点击查询按钮。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.查询按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击查询按钮: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 查询按钮点击失败({选择器}): {异常}")
        return False

    async def 商品行是否存在(self, 商品ID: str) -> bool:
        """检查商品行是否存在。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取商品行容器(商品ID).所有选择器():
            try:
                元素 = await self.页面.query_selector(选择器)
                if 元素 is not None:
                    print(f"[推广页] 已找到商品行: {商品ID}")
                    return True
            except Exception as 异常:
                print(f"[推广页] 检查商品行失败({选择器}): {异常}")
        return False

    async def 获取全局优先起量状态(self) -> str:
        """获取全局优先起量状态。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.全局优先起量开关.所有选择器():
            try:
                元素 = self.页面.locator(选择器).first
                aria_checked = await 元素.get_attribute("aria-checked")
                if aria_checked in {"true", "false"}:
                    return aria_checked
                class_name = str(await 元素.get_attribute("class") or "")
                return "true" if "checked" in class_name else "false"
            except Exception:
                continue
        return "not_found"

    async def 点击全局优先起量开关(self) -> bool:
        """点击全局优先起量开关。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.全局优先起量开关.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击全局优先起量开关: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 点击全局优先起量开关失败({选择器}): {异常}")
        return False

    async def 确认关闭全局起量(self) -> bool:
        """点击全局起量关闭确认按钮。"""
        await self._随机等待()
        最后异常 = None
        for 选择器 in 推广页选择器.全局起量关闭确认按钮.所有选择器():
            try:
                await self.页面.wait_for_selector(选择器, timeout=5000)
                await self.页面.click(选择器, timeout=5000)
                print(f"[推广页] 已确认关闭全局起量: {选择器}")
                await self._确认弹窗后等待()
                return True
            except Exception as 异常:
                最后异常 = 异常
                print(f"[推广页] 确认关闭全局起量失败({选择器}): {异常}")
        try:
            await self.截图("全局起量确认弹窗失败")
        except Exception:
            pass
        print(f"[推广页] 全局起量确认弹窗处理失败: {最后异常}")
        return False

    async def 点击更多设置(self, 商品ID: str) -> bool:
        """点击指定商品的更多设置按钮。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取更多设置按钮(商品ID).所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击更多设置: {商品ID}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 点击更多设置失败({选择器}): {异常}")
        return False

    async def 点击预算日限额(self) -> bool:
        """点击预算日限额菜单项。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.预算日限额菜单项.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击预算日限额: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 点击预算日限额失败({选择器}): {异常}")
        return False

    async def 输入日限额(self, 金额: float) -> bool:
        """输入日限额金额。"""
        await self._随机等待()
        文本值 = str(int(金额)) if float(金额).is_integer() else str(金额)
        for 选择器 in 推广页选择器.日限额输入框.所有选择器():
            try:
                输入框 = self.页面.locator(选择器).first
                await 输入框.click(timeout=10000)
                await self.页面.keyboard.press("Control+A")
                await self._随机等待()
                await 输入框.fill(文本值)
                print(f"[推广页] 已输入日限额: {文本值}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 输入日限额失败({选择器}): {异常}")
        return False

    async def 确认日限额(self) -> bool:
        """确认日限额设置。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.日限额确认按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已确认日限额: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 确认日限额失败({选择器}): {异常}")
        return False

    async def 点击修改投产铅笔按钮(self, 商品ID: str) -> bool:
        """点击修改投产铅笔按钮。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取修改投产铅笔按钮(商品ID).所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击修改投产铅笔按钮: {商品ID}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 点击修改投产铅笔按钮失败({选择器}): {异常}")
        return False

    async def 等待投产弹窗(self) -> bool:
        """等待投产弹窗出现。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.投产比输入框.所有选择器():
            try:
                await self.页面.wait_for_selector(选择器, timeout=10000)
                print(f"[推广页] 投产弹窗已出现: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 等待投产弹窗失败({选择器}): {异常}")
        return False

    async def 获取极速起量高级版状态(self, 商品ID: str) -> str:
        """获取极速起量高级版状态。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取极速起量高级版开关(商品ID).所有选择器():
            try:
                元素 = self.页面.locator(选择器).first
                class_name = str(await 元素.get_attribute("class") or "")
                return "true" if "anq-switch-checked" in class_name else "false"
            except Exception:
                continue
        return "not_found"

    async def 点击极速起量高级版开关(self, 商品ID: str) -> bool:
        """点击极速起量高级版开关。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取极速起量高级版开关(商品ID).所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击极速起量高级版开关: {商品ID}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 点击极速起量高级版开关失败({选择器}): {异常}")
        return False

    async def 确认关闭极速起量(self, 商品ID: str) -> bool:
        """点击极速起量高级版关闭确认按钮。"""
        await self._随机等待()
        最后异常 = None
        for 选择器 in 推广页选择器.获取极速起量高级版关闭确认按钮(商品ID).所有选择器():
            try:
                await self.页面.wait_for_selector(选择器, timeout=2000)
                await self.页面.click(选择器, timeout=2000)
                print(f"[推广页] 已通过商品绑定确认按钮关闭极速起量: 商品ID={商品ID}, 选择器={选择器}")
                await self._确认弹窗后等待()
                return True
            except Exception as 异常:
                最后异常 = 异常
                print(f"[推广页] 商品绑定极速起量确认失败(商品ID={商品ID}, 选择器={选择器}): {异常}")

        for 选择器 in 推广页选择器.极速起量高级版关闭确认按钮_Popover.所有选择器():
            try:
                await self.页面.wait_for_selector(选择器, timeout=2000)
                await self.页面.click(选择器, timeout=2000)
                print(f"[推广页] 已通过Popover确认按钮关闭极速起量: 商品ID={商品ID}, 选择器={选择器}")
                await self._确认弹窗后等待()
                return True
            except Exception as 异常:
                最后异常 = 异常
                print(f"[推广页] Popover极速起量确认失败(商品ID={商品ID}, 选择器={选择器}): {异常}")

        for 选择器 in 推广页选择器.极速起量高级版关闭确认按钮.所有选择器():
            try:
                await self.页面.wait_for_selector(选择器, timeout=2000)
                await self.页面.click(选择器, timeout=2000)
                print(f"[推广页] 已通过通用确认关闭按钮关闭极速起量: 商品ID={商品ID}, 选择器={选择器}")
                await self._确认弹窗后等待()
                return True
            except Exception as 异常:
                最后异常 = 异常
                print(f"[推广页] 通用确认关闭按钮失败(商品ID={商品ID}, 选择器={选择器}): {异常}")
        try:
            await self.截图("极速起量确认弹窗未找到")
        except Exception:
            pass
        print(f"[推广页] 极速起量确认弹窗处理失败: 商品ID={商品ID}, error={最后异常}")
        return False

    async def 输入投产比(self, 投产比: float) -> bool:
        """输入投产比。"""
        await self._随机等待()
        文本值 = str(int(投产比)) if float(投产比).is_integer() else str(投产比)
        for 选择器 in 推广页选择器.投产比输入框.所有选择器():
            try:
                输入框 = self.页面.locator(选择器).first
                await 输入框.click(timeout=10000)
                await self.页面.keyboard.press("Control+A")
                await self._随机等待()
                await 输入框.fill(文本值)
                print(f"[推广页] 已输入投产比: {文本值}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 输入投产比失败({选择器}): {异常}")
        return False

    async def 确认投产比设置(self, 商品ID: str) -> bool:
        """确认投产比设置。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取投产设置确认按钮(商品ID).所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已确认投产比设置: {商品ID}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 确认投产比设置失败({选择器}): {异常}")
        return False

    async def 点击开启推广(self) -> bool:
        """点击开启推广按钮。"""
        await self._随机等待()
        try:
            await self.页面.mouse.wheel(0, 1200)
        except Exception:
            pass
        await self._随机等待()
        for 选择器 in 推广页选择器.开启推广按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击开启推广: {选择器}")
                await self._随机等待()
                return True
            except Exception:
                try:
                    if 选择器.startswith("//"):
                        await self.页面.evaluate(
                            "(selector) => document.evaluate(selector, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.click?.()",
                            选择器,
                        )
                    else:
                        await self.页面.evaluate(
                            "(selector) => document.querySelector(selector)?.click()",
                            选择器,
                        )
                    print(f"[推广页] 已通过 JS 点击开启推广: {选择器}")
                    await self._随机等待()
                    return True
                except Exception as 异常:
                    print(f"[推广页] 点击开启推广失败({选择器}): {异常}")
        return False

    async def _按钮是否仍可见(self) -> bool:
        """检查开启推广按钮是否仍可见。"""
        for 选择器 in 推广页选择器.开启推广按钮.所有选择器():
            try:
                定位器 = self.页面.locator(选择器).first
                可见方法 = getattr(定位器, "is_visible", None)
                if callable(可见方法):
                    结果 = 可见方法()
                    if inspect.isawaitable(结果):
                        结果 = await 结果
                    if isinstance(结果, bool):
                        return 结果

                元素 = await self.页面.query_selector(选择器)
                if 元素 is not None:
                    return True
            except Exception as 异常:
                print(f"[推广页] 检查开启推广按钮可见性失败({选择器}): {异常}")
        return False

    async def 等待推广成功(self, 超时秒数: int = 15) -> bool:
        """轮询检测推广成功，任一成功条件命中即返回。"""
        await self._随机等待()
        截止时间 = time.monotonic() + max(1, 超时秒数)

        while time.monotonic() < 截止时间:
            for 选择器 in 推广页选择器.推广成功Toast提示.所有选择器():
                try:
                    元素 = await self.页面.query_selector(选择器)
                    if 元素 is not None:
                        print(f"[推广页] 已命中推广成功Toast: {选择器}")
                        return True
                except Exception as 异常:
                    print(f"[推广页] 检查推广成功Toast失败({选择器}): {异常}")

            当前地址 = str(getattr(self.页面, "url", "") or "")
            if "promotion/list" in 当前地址 and "create" not in 当前地址:
                print(f"[推广页] 已通过URL检测到推广成功: {当前地址}")
                return True

            if not await self._按钮是否仍可见():
                print("[推广页] 已通过开启推广按钮消失检测到推广成功")
                return True

            for 选择器 in 推广页选择器.推广中状态文案.所有选择器():
                try:
                    元素 = await self.页面.query_selector(选择器)
                    if 元素 is not None:
                        print(f"[推广页] 已检测到推广中状态: {选择器}")
                        return True
                except Exception as 异常:
                    print(f"[推广页] 检查推广中状态失败({选择器}): {异常}")

            await asyncio.sleep(0.5)

        try:
            await self.截图("推广成功检测超时")
        except Exception:
            pass
        print("[推广页] 推广成功检测超时")
        return False
