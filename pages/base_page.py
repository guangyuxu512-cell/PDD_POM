"""
基础页模块

POM 层基类，提供所有页面通用的安全操作方法。
"""
import asyncio
import inspect
from pathlib import Path
from playwright.async_api import Page
from backend.config import 配置实例
from backend.logging_config import get_logger
from browser.anti_detection import 真人模拟器
from browser.session_monitor import 登录态监控实例
from pdd_selectors.base_page_selector import 基础页选择器


日志记录器 = get_logger()


class 基础页:
    """页面对象模型基类，所有页面类都应继承此类"""

    def __init__(self, 页面: Page, 店铺ID: str | None = None, 店铺名称: str | None = None):
        """
        初始化基础页

        Args:
            页面: Playwright Page 对象
        """
        self.页面 = 页面
        self.店铺ID = 店铺ID or getattr(页面, "_shop_id", None)
        self.店铺名称 = 店铺名称 or getattr(页面, "_shop_name", None)
        self.模拟器 = 真人模拟器(页面)
        self.通用弹窗关闭按钮选择器 = 基础页选择器.通用弹窗关闭按钮.所有选择器()

    @staticmethod
    def _是否浏览器关闭异常(异常: Exception) -> bool:
        错误信息 = str(异常 or "").lower()
        return any(
            关键字 in 错误信息
            for 关键字 in (
                "target closed",
                "has been closed",
                "page closed",
                "context closed",
                "browser has been closed",
            )
        )

    async def 检查并处理登录态(self) -> bool:
        """在关键页面操作前检查登录态，失效时直接中断主流程。"""
        if self.__class__.__name__ == "登录页":
            return True

        if not self.店铺ID:
            return True

        已登录 = await 登录态监控实例.检查登录态(self.页面, self.店铺ID)
        if 已登录:
            return True

        当前地址 = str(getattr(self.页面, "url", "") or "")
        原因 = f"页面地址或 Cookie 检测失败，当前 URL: {当前地址}"
        await 登录态监控实例.触发失效告警(self.店铺ID, self.店铺名称, 原因)
        日志记录器.error(f"登录态已失效: shop_id={self.店铺ID}, url={当前地址}")
        raise RuntimeError("登录态已失效")

    async def 导航(self, 网址: str, 等待加载: bool = True) -> None:
        """
        导航到指定 URL

        Args:
            网址: 目标 URL
            等待加载: 是否等待页面加载完成
        """
        await self.检查并处理登录态()
        try:
            await self.页面.goto(网址, wait_until="domcontentloaded" if 等待加载 else "commit")
            await self.模拟器.随机延迟(1, 3)
        except Exception as 异常:
            if self._是否浏览器关闭异常(异常):
                raise RuntimeError("浏览器上下文已关闭，需要恢复") from 异常
            raise

    async def 安全点击(self, 选择器: str, 超时: int = 10000) -> None:
        """
        安全点击元素（等待元素出现 + 真人模拟点击）

        Args:
            选择器: CSS 选择器
            超时: 等待超时时间（毫秒）
        """
        await self.检查并处理登录态()
        try:
            await self.页面.wait_for_selector(选择器, timeout=超时)
            await self.模拟器.移动并点击(选择器)
        except Exception as 异常:
            if self._是否浏览器关闭异常(异常):
                raise RuntimeError("浏览器上下文已关闭，需要恢复") from 异常
            raise

    async def 安全填写(self, 选择器: str, 内容: str, 超时: int = 10000) -> None:
        """
        安全填写输入框（等待元素出现 + 真人模拟打字）

        Args:
            选择器: CSS 选择器
            内容: 要填写的内容
            超时: 等待超时时间（毫秒）
        """
        await self.检查并处理登录态()
        try:
            await self.页面.wait_for_selector(选择器, timeout=超时)
            await self.模拟器.模拟打字(选择器, 内容)
        except Exception as 异常:
            if self._是否浏览器关闭异常(异常):
                raise RuntimeError("浏览器上下文已关闭，需要恢复") from 异常
            raise

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

    async def 操作前延迟(self) -> None:
        """每次页面操作前的短延迟。"""
        await self.随机延迟(0.3, 0.8)

    async def 操作后延迟(self) -> None:
        """每次页面操作后的延迟。"""
        await self.随机延迟(0.8, 2.0)

    async def 页面加载延迟(self) -> None:
        """等待页面加载或跳转后的延迟。"""
        await self.随机延迟(1.5, 3.0)

    async def 安全点击_文本(self, 文本: str) -> None:
        """
        通过文本定位并安全点击

        Args:
            文本: 要点击的元素文本
        """
        await self.检查并处理登录态()
        try:
            元素 = self.页面.get_by_text(文本)
            if inspect.isawaitable(元素):
                元素 = await 元素
            await 元素.click()
            await self.模拟器.随机延迟(0.3, 1)
        except Exception as 异常:
            if self._是否浏览器关闭异常(异常):
                raise RuntimeError("浏览器上下文已关闭，需要恢复") from 异常
            raise

    async def 安全填写_占位符(self, 占位符: str, 内容: str) -> None:
        """
        通过 placeholder 定位并安全填写

        Args:
            占位符: 输入框的 placeholder 文本
            内容: 要填写的内容
        """
        await self.检查并处理登录态()
        try:
            输入框 = self.页面.get_by_placeholder(占位符)
            if inspect.isawaitable(输入框):
                输入框 = await 输入框
            await 输入框.click()
            await self.模拟器.随机延迟(0.2, 0.5)
            await 输入框.fill(内容)
            await self.模拟器.随机延迟(0.3, 0.8)
        except Exception as 异常:
            if self._是否浏览器关闭异常(异常):
                raise RuntimeError("浏览器上下文已关闭，需要恢复") from 异常
            raise
