"""
浏览器管理器模块

管理所有浏览器实例的生命周期，包括启动、关闭、状态查询。
"""
import sys
import asyncio
from typing import Dict, Optional, Any
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from browser.用户目录工厂 import 用户目录工厂
from backend.配置 import 配置实例


def _设置Windows事件循环策略():
    """
    Windows 平台下设置正确的事件循环策略

    uvicorn --reload 模式下，子进程默认使用 SelectorEventLoop，
    不支持 subprocess，导致 Playwright 无法启动浏览器驱动。
    需要切换到 ProactorEventLoop。
    """
    if sys.platform == 'win32':
        try:
            # 尝试设置 WindowsProactorEventLoopPolicy
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            print("✓ Windows 事件循环策略已设置为 ProactorEventLoop")
        except Exception as e:
            print(f"⚠ 设置 Windows 事件循环策略失败: {e}")


class 浏览器管理器:
    """浏览器实例池管理器"""

    def __init__(self):
        """初始化浏览器管理器"""
        self.实例集: Dict[str, Dict[str, Any]] = {}
        self.playwright实例: Optional[Playwright] = None
        self.用户目录工厂 = 用户目录工厂()

    @staticmethod
    def _页面已关闭(页面: Any) -> bool:
        """兼容真实 Page 与测试替身，判断页面是否已关闭。"""
        if 页面 is None:
            return True

        检查方法 = getattr(页面, "is_closed", None)
        if not callable(检查方法):
            return False

        try:
            检查结果 = 检查方法()
        except Exception:
            return False

        return 检查结果 if isinstance(检查结果, bool) else False

    async def 初始化(self, 配置: dict = None) -> None:
        """
        启动 Playwright

        参数:
            配置: 可选配置字典，包含 chrome_path, max_instances, default_proxy 等
        """
        if not self.playwright实例:
            # Windows 平台下设置事件循环策略，解决 NotImplementedError
            _设置Windows事件循环策略()

            # 启动 Playwright
            self._playwright上下文 = async_playwright()
            self.playwright实例 = await self._playwright上下文.start()
            print(f"✓ Playwright 已启动: {self.playwright实例}")

    async def 打开店铺(self, 店铺ID: str, 店铺配置: dict) -> dict:
        """
        打开指定店铺的浏览器实例

        Args:
            店铺ID: 店铺的唯一标识
            店铺配置: 店铺配置字典，包含 proxy 等信息

        Returns:
            dict: 包含 "浏览器" 和 "页面" 的字典

        Raises:
            RuntimeError: 超过最大实例数或 Playwright 未初始化
        """
        # 如果已打开，直接返回
        if 店铺ID in self.实例集:
            print(f"✓ 店铺 {店铺ID} 已打开，复用实例")
            return self.实例集[店铺ID]

        # 检查是否超过最大实例数
        最大实例数 = 配置实例.MAX_BROWSER_INSTANCES
        if len(self.实例集) >= 最大实例数:
            raise RuntimeError(f"已达到最大浏览器实例数限制: {最大实例数}")

        # 确保 Playwright 已初始化
        if not self.playwright实例:
            raise RuntimeError("Playwright 未初始化，请先调用 初始化() 方法")

        # 获取用户数据目录
        用户目录 = self.用户目录工厂.获取或创建(店铺ID)

        # 从店铺配置中获取 headless 参数，默认为 False
        headless模式 = 店铺配置.get("headless", False)

        # 准备启动参数
        启动参数 = {
            "channel": "chrome",
            "headless": headless模式,
            "viewport": None,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--start-maximized",
            ]
        }

        # 如果配置了 Chrome 路径，使用指定路径
        chrome路径 = 配置实例.CHROME_PATH
        if chrome路径:
            启动参数["executable_path"] = chrome路径
            # 有自定义路径时不使用 channel
            del 启动参数["channel"]

        # 如果配置了代理，注入代理
        代理 = 店铺配置.get("proxy") or 配置实例.DEFAULT_PROXY
        if 代理:
            启动参数["proxy"] = {"server": 代理}

        # 启动浏览器
        浏览器上下文: BrowserContext = await self.playwright实例.chromium.launch_persistent_context(
            用户目录,
            no_viewport=True,
            **启动参数
        )

        # 注册浏览器关闭事件，自动清理实例记录
        浏览器上下文.on("close", lambda: self._清理实例(店铺ID))

        # 获取或创建页面
        页面列表 = 浏览器上下文.pages
        if 页面列表:
            页面: Page = 页面列表[0]
        else:
            页面: Page = await 浏览器上下文.new_page()

        # 存储实例
        实例信息 = {
            "浏览器": 浏览器上下文,
            "页面": 页面,
            "page": 页面  # 添加 page 键，方便外部使用
        }
        self.实例集[店铺ID] = 实例信息

        print(f"✓ 店铺 {店铺ID} 浏览器已启动 (headless={headless模式})")
        return 实例信息

    async def 关闭店铺(self, 店铺ID: str) -> None:
        """
        关闭指定店铺的浏览器实例

        Args:
            店铺ID: 店铺的唯一标识
        """
        if 店铺ID not in self.实例集:
            print(f"⚠ 店铺 {店铺ID} 未打开")
            return

        实例 = self.实例集[店铺ID]
        浏览器 = 实例["浏览器"]

        try:
            await 浏览器.close()
            print(f"✓ 店铺 {店铺ID} 浏览器已关闭")
        except Exception as e:
            print(f"✗ 关闭浏览器失败: {e}")
        finally:
            del self.实例集[店铺ID]

    async def 关闭全部(self) -> None:
        """关闭所有浏览器实例"""
        店铺列表 = list(self.实例集.keys())
        for 店铺ID in 店铺列表:
            await self.关闭店铺(店铺ID)
        print("✓ 所有浏览器实例已关闭")

    def 获取页面(self, 店铺ID: str) -> Page:
        """
        获取指定店铺的页面对象

        Args:
            店铺ID: 店铺的唯一标识

        Returns:
            Page: Playwright 页面对象

        Raises:
            RuntimeError: 店铺未启动
        """
        if 店铺ID not in self.实例集:
            raise RuntimeError(f"店铺 {店铺ID} 未启动，请先调用 打开店铺() 方法")

        实例 = self.实例集[店铺ID]
        页面 = 实例.get("页面") or 实例.get("page")
        浏览器 = 实例["浏览器"]

        if self._页面已关闭(页面):
            可用页面列表 = [
                当前页面
                for 当前页面 in getattr(浏览器, "pages", [])
                if not self._页面已关闭(当前页面)
            ]
            if not 可用页面列表:
                raise RuntimeError(f"店铺 {店铺ID} 所有页面已关闭，需要重新打开")

            页面 = 可用页面列表[0]
            实例["页面"] = 页面
            实例["page"] = 页面
            print(f"✓ 店铺 {店铺ID} 页面已刷新")

        return 页面

    def 获取实例列表(self) -> Dict[str, dict]:
        """
        列出所有运行中实例的状态

        Returns:
            Dict[str, dict]: 店铺 ID 到实例状态的映射
        """
        状态字典 = {}
        for 店铺ID, 实例 in self.实例集.items():
            状态字典[店铺ID] = {
                "店铺ID": 店铺ID,
                "状态": "运行中",
                "页面数": len(实例["浏览器"].pages)
            }
        return 状态字典

    def _清理实例(self, 店铺ID: str) -> None:
        """
        清理指定店铺的实例记录（浏览器被手动关闭时调用）

        Args:
            店铺ID: 店铺的唯一标识
        """
        if 店铺ID in self.实例集:
            del self.实例集[店铺ID]
            print(f"✓ 店铺 {店铺ID} 实例已自动清理（浏览器被手动关闭）")
