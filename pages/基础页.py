"""
基础页模块

POM 层基类，提供所有页面通用的安全操作方法。
"""
import asyncio
import inspect
from pathlib import Path
from playwright.async_api import Page
from backend.配置 import 配置实例
from browser.反检测 import 真人模拟器


class 基础页:
    """页面对象模型基类，所有页面类都应继承此类"""

    def __init__(self, 页面: Page):
        """
        初始化基础页

        Args:
            页面: Playwright Page 对象
        """
        self.页面 = 页面
        self.模拟器 = 真人模拟器(页面)

    async def 导航(self, 网址: str, 等待加载: bool = True) -> None:
        """
        导航到指定 URL

        Args:
            网址: 目标 URL
            等待加载: 是否等待页面加载完成
        """
        await self.页面.goto(网址, wait_until="domcontentloaded" if 等待加载 else "commit")
        await self.模拟器.随机延迟(1, 3)

    async def 安全点击(self, 选择器: str, 超时: int = 10000) -> None:
        """
        安全点击元素（等待元素出现 + 真人模拟点击）

        Args:
            选择器: CSS 选择器
            超时: 等待超时时间（毫秒）
        """
        await self.页面.wait_for_selector(选择器, timeout=超时)
        await self.模拟器.移动并点击(选择器)

    async def 安全填写(self, 选择器: str, 内容: str, 超时: int = 10000) -> None:
        """
        安全填写输入框（等待元素出现 + 真人模拟打字）

        Args:
            选择器: CSS 选择器
            内容: 要填写的内容
            超时: 等待超时时间（毫秒）
        """
        await self.页面.wait_for_selector(选择器, timeout=超时)
        await self.模拟器.模拟打字(选择器, 内容)

    async def 安全滚动(self, 距离: int = 300) -> None:
        """
        安全滚动页面（真人模拟滚动）

        Args:
            距离: 滚动距离（像素）
        """
        await self.模拟器.随机滚动(距离)

    async def 截图(self, 名称: str) -> str:
        """
        截图并保存

        Args:
            名称: 截图文件名（不含扩展名）

        Returns:
            str: 截图文件的完整路径
        """
        截图目录 = Path(配置实例.DATA_DIR) / "screenshots"
        截图目录.mkdir(parents=True, exist_ok=True)

        时间戳 = asyncio.get_event_loop().time()
        文件名 = f"{名称}_{int(时间戳)}.png"
        文件路径 = 截图目录 / 文件名

        await self.页面.screenshot(path=str(文件路径))
        return str(文件路径)

    async def 元素是否存在(self, 选择器: str, 超时: int = 1000) -> bool:
        """
        检查元素是否存在

        Args:
            选择器: CSS 选择器
            超时: 等待超时时间（毫秒）

        Returns:
            bool: 元素是否存在
        """
        try:
            元素 = await self.页面.query_selector(选择器)
            return 元素 is not None
        except Exception:
            return False

    async def 随机延迟(self, 最小秒: float = 0.5, 最大秒: float = 2) -> None:
        """
        随机延迟

        Args:
            最小秒: 最小延迟秒数
            最大秒: 最大延迟秒数
        """
        await self.模拟器.随机延迟(最小秒, 最大秒)

    async def 安全点击_文本(self, 文本: str) -> None:
        """
        通过文本定位并安全点击

        Args:
            文本: 要点击的元素文本
        """
        元素 = self.页面.get_by_text(文本)
        if inspect.isawaitable(元素):
            元素 = await 元素
        await 元素.click()
        await self.模拟器.随机延迟(0.3, 1)

    async def 安全填写_占位符(self, 占位符: str, 内容: str) -> None:
        """
        通过 placeholder 定位并安全填写

        Args:
            占位符: 输入框的 placeholder 文本
            内容: 要填写的内容
        """
        输入框 = self.页面.get_by_placeholder(占位符)
        if inspect.isawaitable(输入框):
            输入框 = await 输入框
        await 输入框.click()
        await self.模拟器.随机延迟(0.2, 0.5)
        await 输入框.fill(内容)
        await self.模拟器.随机延迟(0.3, 0.8)
