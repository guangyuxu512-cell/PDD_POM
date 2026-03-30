"""
反检测模块

提供真人模拟器，模拟真实用户的操作行为，包括随机延迟、贝塞尔曲线鼠标移动、打字错误等。
"""
import asyncio
import random
import time
from typing import Optional
from playwright.async_api import Page


class 真人模拟器:
    """真人行为模拟器，提供各种模拟真实用户操作的方法"""

    def __init__(self, 页面: Page):
        """
        初始化真人模拟器

        Args:
            页面: Playwright Page 对象
        """
        self.页面 = 页面
        self.当前鼠标x = 0.0
        self.当前鼠标y = 0.0

    async def 随机延迟(self, 最小秒: float = 0.5, 最大秒: float = 2.0) -> None:
        """
        随机延迟

        Args:
            最小秒: 最小延迟时间（秒）
            最大秒: 最大延迟时间（秒）
        """
        延迟时间 = random.uniform(最小秒, 最大秒)
        if 延迟时间 <= 0:
            return

        if 延迟时间 <= 0.03:
            结束时间 = time.perf_counter() + 延迟时间 + 0.001
            while time.perf_counter() < 结束时间:
                pass
            return

        开始时间 = time.perf_counter()
        主等待秒数 = max(0.0, 延迟时间 - 0.01)
        if 主等待秒数 > 0:
            await asyncio.sleep(主等待秒数)

        while True:
            剩余时间 = 延迟时间 - (time.perf_counter() - 开始时间)
            if 剩余时间 <= 0:
                break

            if 剩余时间 > 0.002:
                await asyncio.sleep(剩余时间 / 2)
            else:
                await asyncio.sleep(0)

    async def 模拟打字(self, 选择器: str, 文本: str) -> None:
        """
        模拟真人打字，包括随机间隔、打错字、停顿思考等

        Args:
            选择器: 输入框的 CSS 选择器
            文本: 要输入的文本

        Raises:
            Exception: 元素未找到或不可见
        """
        # 检查元素是否存在
        元素 = await self.页面.query_selector(选择器)
        if not 元素:
            raise Exception(f"元素未找到: {选择器}")

        # 检查元素是否可见
        是否可见 = await 元素.is_visible()
        if not 是否可见:
            raise Exception(f"元素不可见: {选择器}")

        # 先点击输入框
        await self.页面.click(选择器)
        await self.随机延迟(0.2, 0.5)

        for i, 字符 in enumerate(文本):
            # 5% 概率打错再删
            if random.random() < 0.05:
                错误字符 = random.choice("abcdefghijklmnopqrstuvwxyz")
                await self.页面.keyboard.type(错误字符)
                await self.随机延迟(0.1, 0.3)
                await self.页面.keyboard.press("Backspace")
                await self.随机延迟(0.1, 0.2)

            # 输入正确字符
            await self.页面.keyboard.type(字符)

            # 10% 概率停顿思考
            if random.random() < 0.1:
                await self.随机延迟(0.5, 1.5)
            else:
                await self.随机延迟(0.05, 0.2)

    async def 移动并点击(self, 选择器: str) -> None:
        """
        使用贝塞尔曲线移动鼠标到元素并点击

        Args:
            选择器: 元素的 CSS 选择器

        Raises:
            Exception: 元素未找到或不可见
        """
        # 获取元素
        元素 = await self.页面.query_selector(选择器)
        if not 元素:
            raise Exception(f"元素未找到: {选择器}")

        # 检查元素是否可见
        是否可见 = await 元素.is_visible()
        if not 是否可见:
            raise Exception(f"元素不可见: {选择器}")

        # 获取元素位置
        边界框 = await 元素.bounding_box()
        if not 边界框:
            raise Exception(f"无法获取元素边界框: {选择器}")

        # 计算目标位置（中心 + 随机偏移）
        偏移比例x = random.uniform(0.3, 0.7)
        偏移比例y = random.uniform(0.3, 0.7)

        目标x = 边界框["x"] + 边界框["width"] * 偏移比例x
        目标y = 边界框["y"] + 边界框["height"] * 偏移比例y

        # 贝塞尔曲线移动
        await self._贝塞尔移动(目标x, 目标y)

        # 随机延迟后点击
        await self.随机延迟(0.1, 0.3)
        await self.页面.mouse.click(目标x, 目标y)
        await self.随机延迟(0.2, 0.5)

    async def _贝塞尔移动(self, 目标x: float, 目标y: float, 步数: int = 20) -> None:
        """
        使用三次贝塞尔曲线移动鼠标

        Args:
            目标x: 目标 X 坐标
            目标y: 目标 Y 坐标
            步数: 移动步数
        """
        # 起点是当前鼠标位置
        起点x = self.当前鼠标x
        起点y = self.当前鼠标y

        # 生成两个随机控制点
        控制点1x = 起点x + (目标x - 起点x) * random.uniform(0.2, 0.4)
        控制点1y = 起点y + (目标y - 起点y) * random.uniform(0.1, 0.3)

        控制点2x = 起点x + (目标x - 起点x) * random.uniform(0.6, 0.8)
        控制点2y = 起点y + (目标y - 起点y) * random.uniform(0.7, 0.9)

        # 按贝塞尔曲线移动
        for i in range(步数 + 1):
            t = i / 步数

            # 三次贝塞尔曲线公式
            x = (
                (1 - t) ** 3 * 起点x
                + 3 * (1 - t) ** 2 * t * 控制点1x
                + 3 * (1 - t) * t ** 2 * 控制点2x
                + t ** 3 * 目标x
            )
            y = (
                (1 - t) ** 3 * 起点y
                + 3 * (1 - t) ** 2 * t * 控制点1y
                + 3 * (1 - t) * t ** 2 * 控制点2y
                + t ** 3 * 目标y
            )

            await self.页面.mouse.move(x, y)
            await asyncio.sleep(0.01)

        # 更新当前鼠标位置
        self.当前鼠标x = 目标x
        self.当前鼠标y = 目标y

    async def 随机滚动(self, 距离: int = 300) -> None:
        """
        随机滚动页面，分多次小幅滚动

        Args:
            距离: 总滚动距离（像素）
        """
        已滚动 = 0
        while 已滚动 < 距离:
            # 每次滚动 30-100px
            本次滚动 = random.randint(30, 100)
            await self.页面.mouse.wheel(0, 本次滚动)
            已滚动 += 本次滚动

            # 15% 概率回滚一点
            if random.random() < 0.15:
                回滚距离 = random.randint(10, 30)
                await self.页面.mouse.wheel(0, -回滚距离)
                已滚动 -= 回滚距离

            await self.随机延迟(0.1, 0.3)

    async def 随机无意义操作(self) -> None:
        """随机执行一些无意义操作，模拟真人闲置习惯"""
        操作 = random.choice(["移动鼠标", "滚动", "等待"])

        if 操作 == "移动鼠标":
            目标x = random.uniform(100, 800)
            目标y = random.uniform(100, 600)
            await self._贝塞尔移动(目标x, 目标y, 步数=10)
        elif 操作 == "滚动":
            距离 = random.randint(50, 150)
            await self.页面.mouse.wheel(0, 距离)
            await self.随机延迟(0.1, 0.3)
        else:  # 等待
            await self.随机延迟(1, 3)
