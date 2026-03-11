"""
滑块验证码处理模块

处理滑块验证码的完整流程：截图 → 识别 → 生成轨迹 → 执行滑动。
"""
import asyncio
import random
from typing import List, Tuple
from playwright.async_api import Page
from browser.验证码识别 import 验证码识别器
from browser.反检测 import 真人模拟器


class 滑块处理器:
    """滑块验证码处理器，完成滑块验证码的识别和滑动"""

    # 类属性：选择器（后续根据实际页面调整）
    背景图选择器 = ".captcha-bg"
    滑块选择器 = ".captcha-slider"
    滑块按钮选择器 = ".captcha-slider-btn"

    def __init__(self, 识别器: 验证码识别器, 模拟器: 真人模拟器):
        """
        初始化滑块处理器

        Args:
            识别器: 验证码识别器实例
            模拟器: 真人模拟器实例
        """
        self.识别器 = 识别器
        self.模拟器 = 模拟器

    async def 处理(self, 页面: Page) -> bool:
        """
        处理滑块验证码的完整流程

        Args:
            页面: Playwright Page 对象

        Returns:
            bool: 是否成功通过验证码
        """
        try:
            # 1. 截取背景图和滑块图
            背景图 = await self._截图验证码元素(页面, self.背景图选择器)
            滑块图 = await self._截图验证码元素(页面, self.滑块选择器)

            # 2. 识别滑动距离
            距离 = await self.识别器.识别滑块(背景图, 滑块图)

            # 3. 生成滑动轨迹
            轨迹 = self._生成滑动轨迹(距离)

            # 4. 执行滑动
            await self._执行滑动(页面, self.滑块按钮选择器, 轨迹)

            # 5. 检查是否成功（滑块元素消失）
            await asyncio.sleep(1)
            滑块元素 = await 页面.query_selector(self.滑块选择器)
            if 滑块元素:
                是否可见 = await 滑块元素.is_visible()
                return not 是否可见
            return True

        except Exception as e:
            print(f"滑块验证码处理失败: {e}")
            return False

    async def _截图验证码元素(self, 页面: Page, 选择器: str) -> bytes:
        """
        截取指定元素的图片

        Args:
            页面: Playwright Page 对象
            选择器: CSS 选择器

        Returns:
            bytes: 图片的字节数据

        Raises:
            Exception: 元素未找到
        """
        元素 = await 页面.query_selector(选择器)
        if not 元素:
            raise Exception(f"元素未找到: {选择器}")

        图片字节 = await 元素.screenshot()
        return 图片字节

    def _生成滑动轨迹(self, 距离: int) -> List[Tuple[float, float, float]]:
        """
        生成人类滑动轨迹（先加速后减速）

        Args:
            距离: 滑动距离（像素）

        Returns:
            List[Tuple[float, float, float]]: 轨迹列表 [(x, y, 时间间隔), ...]
        """
        轨迹 = []
        当前位置 = 0
        步数 = random.randint(20, 30)

        # 前 70% 匀加速，后 30% 匀减速
        加速阶段步数 = int(步数 * 0.7)
        减速阶段步数 = 步数 - 加速阶段步数

        # 加速阶段
        加速距离 = 距离 * 0.7
        for i in range(加速阶段步数):
            # 匀加速：距离 = 1/2 * a * t^2
            # 第 i 步的位移 = (i+1)^2 - i^2 = 2i + 1
            步长 = 加速距离 * (2 * i + 1) / (加速阶段步数 ** 2)
            当前位置 += 步长

            # 添加随机抖动
            x抖动 = random.uniform(-2, 2)
            y抖动 = random.uniform(-3, 3)

            # 时间间隔：加速阶段时间较短
            时间间隔 = random.uniform(0.01, 0.02)

            轨迹.append((当前位置 + x抖动, y抖动, 时间间隔))

        # 减速阶段
        减速距离 = 距离 - 加速距离
        for i in range(减速阶段步数):
            # 匀减速：从最大速度逐渐减速到 0
            # 第 i 步的位移 = 总距离 * (2 * (n - i) - 1) / n^2
            步长 = 减速距离 * (2 * (减速阶段步数 - i) - 1) / (减速阶段步数 ** 2)
            当前位置 += 步长

            # 添加随机抖动
            x抖动 = random.uniform(-2, 2)
            y抖动 = random.uniform(-3, 3)

            # 时间间隔：减速阶段时间较长
            时间间隔 = random.uniform(0.02, 0.03)

            轨迹.append((当前位置 + x抖动, y抖动, 时间间隔))

        return 轨迹

    async def _执行滑动(self, 页面: Page, 滑块按钮选择器: str, 轨迹: List[Tuple[float, float, float]]) -> None:
        """
        按轨迹执行滑动操作

        Args:
            页面: Playwright Page 对象
            滑块按钮选择器: 滑块按钮的 CSS 选择器
            轨迹: 滑动轨迹列表 [(x, y, 时间间隔), ...]

        Raises:
            Exception: 滑块按钮未找到
        """
        # 获取滑块按钮
        滑块按钮 = await 页面.query_selector(滑块按钮选择器)
        if not 滑块按钮:
            raise Exception(f"滑块按钮未找到: {滑块按钮选择器}")

        # 获取滑块按钮位置
        边界框 = await 滑块按钮.bounding_box()
        if not 边界框:
            raise Exception(f"无法获取滑块按钮边界框: {滑块按钮选择器}")

        # 移动到滑块按钮中心
        起始x = 边界框["x"] + 边界框["width"] / 2
        起始y = 边界框["y"] + 边界框["height"] / 2
        await 页面.mouse.move(起始x, 起始y)
        await asyncio.sleep(0.1)

        # 按下鼠标
        await 页面.mouse.down()
        await asyncio.sleep(0.1)

        # 按轨迹滑动
        for x偏移, y偏移, 时间间隔 in 轨迹:
            目标x = 起始x + x偏移
            目标y = 起始y + y偏移
            await 页面.mouse.move(目标x, 目标y)
            await asyncio.sleep(时间间隔)

        # 释放鼠标
        await asyncio.sleep(0.2)
        await 页面.mouse.up()
