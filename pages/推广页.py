"""推广页的页面对象模型。"""
from __future__ import annotations

import asyncio
import random
import re
from typing import List

from pages.基础页 import 基础页
from selectors.推广页选择器 import 推广页选择器


class 推广页(基础页):
    """拼多多全站推广页 POM。"""

    全站推广URL = "https://yingxiao.pinduoduo.com/goods/promotion/list?msfrom=mms_sidenav"
    商品ID正则 = re.compile(r"\b\d{12}\b")

    def __init__(self, 页面):
        super().__init__(页面)

    async def _随机等待(self) -> None:
        await asyncio.sleep(random.uniform(0.5, 1.5))

    async def 导航到全站推广页(self) -> None:
        """打开全站推广页。"""
        await self.页面.goto(self.全站推广URL, wait_until="domcontentloaded")
        print(f"[推广页] 全站推广页加载完成: {self.页面.url}")
        await self._随机等待()

    async def 返回商品列表页(self) -> None:
        """返回上一页商品列表。"""
        await self.页面.go_back(wait_until="domcontentloaded")
        print(f"[推广页] 已返回上一页: {self.页面.url}")
        await self._随机等待()

    async def 关闭广告弹窗(self) -> bool:
        """尝试关闭广告弹窗。"""
        已关闭 = False
        for _ in range(3):
            await self._随机等待()
            弹窗存在 = False
            for 选择器 in 推广页选择器.广告弹窗关闭按钮.所有选择器():
                try:
                    元素 = await self.页面.query_selector(选择器)
                    if 元素 is None:
                        continue
                    弹窗存在 = True
                    try:
                        await 元素.click()
                    except Exception:
                        await self.页面.evaluate(
                            "(selector) => document.querySelector(selector)?.click()",
                            选择器,
                        )
                    已关闭 = True
                    print(f"[推广页] 已关闭广告弹窗: {选择器}")
                    await self._随机等待()
                    break
                except Exception:
                    continue
            if 已关闭:
                continue
            if 弹窗存在:
                try:
                    await self.页面.keyboard.press("Escape")
                    已关闭 = True
                    print("[推广页] 已使用 ESC 尝试关闭广告弹窗")
                    await self._随机等待()
                    continue
                except Exception:
                    pass
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

    async def 获取全局优先起量状态(self) -> str:
        """获取全局优先起量开关状态。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.全局优先起量开关.所有选择器():
            try:
                元素 = self.页面.locator(选择器).first
                aria_checked = await 元素.get_attribute("aria-checked")
                if aria_checked in {"true", "false"}:
                    print(f"[推广页] 全局优先起量状态: {aria_checked}")
                    return aria_checked
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

    async def 确认关闭优先起量(self) -> bool:
        """确认关闭全局优先起量。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.确认关闭优先起量按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已确认关闭优先起量: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 确认关闭优先起量失败({选择器}): {异常}")
        return False

    async def 输入商品ID(self, 商品ID字符串: str) -> bool:
        """输入商品ID查询条件。"""
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

    async def 获取列表商品ID(self) -> list[str]:
        """从列表数据行中提取商品ID。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.商品列表数据行.所有选择器():
            try:
                行列表 = await self.页面.query_selector_all(选择器)
                结果列表: List[str] = []
                for 行 in 行列表:
                    文本 = str(await 行.inner_text())
                    命中 = self.商品ID正则.findall(文本)
                    for 商品ID in 命中:
                        if 商品ID not in 结果列表:
                            结果列表.append(商品ID)
                if 结果列表:
                    print(f"[推广页] 已提取商品ID列表: {结果列表}")
                    return 结果列表
            except Exception as 异常:
                print(f"[推广页] 提取商品ID失败({选择器}): {异常}")
        return []

    async def 点击全选(self) -> bool:
        """点击全选复选框。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.全选复选框.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击全选复选框: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 点击全选失败({选择器}): {异常}")
        return False

    async def 点击投产设置按钮(self, 商品ID: str) -> bool:
        """点击指定商品的投产设置按钮。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取投产设置按钮(商品ID).所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击投产设置按钮: {商品ID}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 点击投产设置按钮失败({选择器}): {异常}")
        return False

    async def 获取极速起量状态(self, 商品ID: str) -> str:
        """获取指定商品极速起量开关状态。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取极速起量开关(商品ID).所有选择器():
            try:
                元素 = self.页面.locator(选择器).first
                aria_checked = await 元素.get_attribute("aria-checked")
                if aria_checked in {"true", "false"}:
                    print(f"[推广页] 极速起量状态({商品ID}): {aria_checked}")
                    return aria_checked
            except Exception:
                continue
        return "not_found"

    async def 点击极速起量开关(self, 商品ID: str) -> bool:
        """点击指定商品的极速起量开关。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取极速起量开关(商品ID).所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击极速起量开关: {商品ID}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 点击极速起量开关失败({选择器}): {异常}")
        return False

    async def 确认关闭极速起量(self) -> bool:
        """确认关闭极速起量。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.确认关闭优先起量按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已确认关闭极速起量: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 确认关闭极速起量失败({选择器}): {异常}")
        return False

    async def 填写一阶段投产比(self, 投产比: float) -> bool:
        """填写一阶段投产比。"""
        await self._随机等待()
        文本值 = str(投产比)
        for 选择器 in 推广页选择器.投产输入框.所有选择器():
            try:
                输入框 = self.页面.locator(选择器).first
                await 输入框.click(timeout=10000)
                await self.页面.keyboard.press("Control+A")
                await self._随机等待()
                await 输入框.fill(文本值)
                print(f"[推广页] 已填写一阶段投产比: {文本值}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 填写一阶段投产比失败({选择器}): {异常}")
        return False

    async def 检测投产比限制(self) -> bool:
        """检测是否出现投产比限制提示。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.投产比限制提示.所有选择器():
            try:
                元素 = await self.页面.query_selector(选择器)
                if 元素 is not None:
                    print(f"[推广页] 检测到投产比限制提示: {选择器}")
                    return True
            except Exception:
                continue
        return False

    async def 点击编辑二阶段(self, 商品ID: str) -> bool:
        """点击进入二阶段投产编辑。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.二阶段投产输入框.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已点击编辑二阶段: {商品ID}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 点击编辑二阶段失败({选择器}): {异常}")
        return False

    async def 填写二阶段投产比(self, 投产比: float) -> bool:
        """填写二阶段投产比。"""
        await self._随机等待()
        文本值 = str(投产比)
        for 选择器 in 推广页选择器.二阶段投产输入框.所有选择器():
            try:
                输入框 = self.页面.locator(选择器).first
                await 输入框.click(timeout=10000)
                await self.页面.keyboard.press("Control+A")
                await self._随机等待()
                await 输入框.fill(文本值)
                print(f"[推广页] 已填写二阶段投产比: {文本值}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 填写二阶段投产比失败({选择器}): {异常}")
        return False

    async def 确认二阶段(self) -> bool:
        """确认二阶段投产比。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.二阶段确认按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已确认二阶段设置: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 确认二阶段失败({选择器}): {异常}")
        return False

    async def 确认投产设置(self, 商品ID: str) -> bool:
        """确认当前商品投产设置。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取确认按钮(商品ID).所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已确认投产设置: {商品ID}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 确认投产设置失败({选择器}): {异常}")
        return False

    async def 取消投产设置(self, 商品ID: str) -> bool:
        """取消当前商品投产设置。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取取消按钮(商品ID).所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已取消投产设置: {商品ID}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 取消投产设置失败({选择器}): {异常}")
        return False

    async def 取消勾选商品(self, 商品ID: str) -> bool:
        """取消勾选指定商品。"""
        await self._随机等待()
        for 选择器 in 推广页选择器.获取取消勾选框(商品ID).所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                print(f"[推广页] 已取消勾选商品: {商品ID}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 取消勾选商品失败({选择器}): {异常}")
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
                await self._random_wait_after_click()
                return True
            except Exception:
                try:
                    await self.页面.evaluate(
                        "(selector) => document.querySelector(selector)?.click()",
                        选择器,
                    )
                    print(f"[推广页] 已通过 JS 点击开启推广: {选择器}")
                    await self._random_wait_after_click()
                    return True
                except Exception as 异常:
                    print(f"[推广页] 点击开启推广失败({选择器}): {异常}")
        return False

    async def _random_wait_after_click(self) -> None:
        await self._随机等待()

    async def 等待推广成功(self, 超时秒: int = 3) -> bool:
        """等待推广成功弹窗出现。"""
        await self._随机等待()
        超时毫秒 = max(1, 超时秒) * 1000
        for 选择器 in 推广页选择器.推广成功弹窗.所有选择器():
            try:
                await self.页面.wait_for_selector(选择器, timeout=超时毫秒)
                print(f"[推广页] 已检测到推广成功弹窗: {选择器}")
                await self._随机等待()
                return True
            except Exception as 异常:
                print(f"[推广页] 等待推广成功失败({选择器}): {异常}")
        return False
