"""
浏览器管理器模块

管理所有浏览器实例的生命周期，包括启动、关闭、状态查询。
"""
import json
import sys
import asyncio
from typing import Dict, Optional, Any
import redis.asyncio as aioredis
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from browser.user_dir_factory import 用户目录工厂
from browser.recovery import 浏览器恢复实例
from browser.session_monitor import 登录态监控实例
from backend.config import 配置实例
from backend.logging_config import get_logger
from backend.services.log_service import 日志服务实例


日志记录器 = get_logger()


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
            日志记录器.success("Windows 事件循环策略已设置为 ProactorEventLoop")
        except Exception as e:
            日志记录器.warning(f"设置 Windows 事件循环策略失败: {e}")


class 浏览器管理器:
    """浏览器实例池管理器"""

    def __init__(self):
        """初始化浏览器管理器"""
        self.实例集: Dict[str, Dict[str, Any]] = {}
        self.playwright实例: Optional[Playwright] = None
        self.用户目录工厂 = 用户目录工厂()
        self.需要重新登录店铺: set[str] = set()

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
            日志记录器.success(f"Playwright 已启动: {self.playwright实例}")

    @staticmethod
    def _同步页面店铺信息(页面: Any, 店铺ID: str, 店铺名称: Optional[str]) -> None:
        """为 Page 对象附加店铺标识，供页面对象自动读取。"""
        for 属性名, 属性值 in {
            "_shop_id": 店铺ID,
            "_shop_name": 店铺名称,
        }.items():
            try:
                setattr(页面, 属性名, 属性值)
            except Exception:
                continue

    def _标记需要重新登录(self, 店铺ID: str, 原因: str) -> None:
        self.需要重新登录店铺.add(店铺ID)
        if 店铺ID in self.实例集:
            self.实例集[店铺ID]["需要重新登录"] = True
            self.实例集[店铺ID]["重新登录原因"] = 原因
        日志记录器.warning(f"店铺 {店铺ID} 被标记为需要重新登录: {原因}")

    @staticmethod
    def _调度后台协程(协程对象) -> None:
        try:
            事件循环 = asyncio.get_running_loop()
            事件循环.create_task(协程对象)
        except RuntimeError:
            try:
                asyncio.run(协程对象)
            except Exception as 异常:
                日志记录器.warning(f"后台协程执行失败: {异常}")

    async def _发布Redis事件(self, 通道: str, 事件数据: dict[str, Any]) -> None:
        Redis地址 = str(配置实例.REDIS_URL or "").strip()
        if not Redis地址:
            return

        客户端 = None
        try:
            客户端 = aioredis.from_url(Redis地址)
            await 客户端.publish(通道, json.dumps(事件数据, ensure_ascii=False))
        except Exception as 异常:
            日志记录器.warning(f"发布 Redis 事件失败: channel={通道}, error={异常}")
        finally:
            if 客户端 is not None:
                try:
                    关闭方法 = getattr(客户端, "aclose", None)
                    if callable(关闭方法):
                        await 关闭方法()
                    else:
                        await 客户端.close()
                except Exception:
                    pass

    async def _处理浏览器崩溃事件(self, 店铺ID: str, 店铺名称: Optional[str]) -> None:
        try:
            await 日志服务实例.写入日志(
                shop_id=店铺ID,
                shop_name=店铺名称,
                level="ERROR",
                source="browser_manager",
                message="浏览器实例已崩溃或被手动关闭",
                detail="browser:crashed",
            )
        except Exception as 异常:
            日志记录器.warning(f"写入浏览器崩溃日志失败: shop_id={店铺ID}, error={异常}")

        await self._发布Redis事件(
            "browser:crashed",
            {
                "shop_id": 店铺ID,
                "shop_name": 店铺名称,
                "event": "browser:crashed",
            },
        )

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
            日志记录器.info(f"店铺 {店铺ID} 已打开，复用实例")
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
        店铺配置副本 = dict(店铺配置 or {})
        headless模式 = 店铺配置副本.get("headless", False)
        店铺名称 = 店铺配置副本.get("name")

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
        代理 = 店铺配置副本.get("proxy") or 配置实例.DEFAULT_PROXY
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

        self._同步页面店铺信息(页面, 店铺ID, 店铺名称)

        # 存储实例
        实例信息 = {
            "浏览器": 浏览器上下文,
            "页面": 页面,
            "page": 页面,  # 添加 page 键，方便外部使用
            "店铺配置": 店铺配置副本,
            "店铺名称": 店铺名称,
            "需要重新登录": False,
        }
        self.实例集[店铺ID] = 实例信息

        if 登录态监控实例.是否登录页地址(str(getattr(页面, "url", "") or "")):
            self._标记需要重新登录(店铺ID, "浏览器启动后落在登录页")

        日志记录器.success(f"店铺 {店铺ID} 浏览器已启动 (headless={headless模式})")
        return 实例信息

    async def 关闭店铺(self, 店铺ID: str) -> None:
        """
        关闭指定店铺的浏览器实例

        Args:
            店铺ID: 店铺的唯一标识
        """
        if 店铺ID not in self.实例集:
            日志记录器.warning(f"店铺 {店铺ID} 未打开")
            return

        实例 = self.实例集[店铺ID]
        浏览器 = 实例["浏览器"]

        try:
            await 浏览器.close()
            日志记录器.success(f"店铺 {店铺ID} 浏览器已关闭")
        except Exception as e:
            日志记录器.error(f"关闭浏览器失败: {e}")
        finally:
            self.实例集.pop(店铺ID, None)
            self.需要重新登录店铺.discard(店铺ID)

    async def 关闭全部(self) -> None:
        """关闭所有浏览器实例"""
        店铺列表 = list(self.实例集.keys())
        for 店铺ID in 店铺列表:
            await self.关闭店铺(店铺ID)
        日志记录器.success("所有浏览器实例已关闭")

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
                raise RuntimeError("所有页面已关闭，浏览器上下文已关闭，需要恢复")

            页面 = 可用页面列表[0]
            实例["页面"] = 页面
            实例["page"] = 页面
            self._同步页面店铺信息(页面, 店铺ID, 实例.get("店铺名称"))
            日志记录器.info(f"店铺 {店铺ID} 页面已刷新")

        if 登录态监控实例.是否登录页地址(str(getattr(页面, "url", "") or "")):
            self._标记需要重新登录(店铺ID, "获取页面时落在登录页")

        return 页面

    async def 安全获取页面(self, 店铺ID: str, 店铺配置: dict | None = None) -> Page:
        """
        获取可用页面；若页面上下文已关闭则尝试自动恢复。
        """
        try:
            return self.获取页面(店铺ID)
        except RuntimeError as 异常:
            if "需要恢复" not in str(异常) and "页面已关闭" not in str(异常):
                raise

        实例信息 = self.实例集.get(店铺ID, {})
        恢复配置 = dict(实例信息.get("店铺配置") or 店铺配置 or {})
        恢复成功 = await 浏览器恢复实例.尝试恢复(self, 店铺ID, 恢复配置)
        if not 恢复成功:
            raise RuntimeError("浏览器上下文已关闭，需要恢复")

        return self.获取页面(店铺ID)

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
        实例 = self.实例集.pop(店铺ID, None)
        if 实例:
            店铺名称 = 实例.get("店铺名称")
            self.需要重新登录店铺.discard(店铺ID)
            self._调度后台协程(self._处理浏览器崩溃事件(店铺ID, 店铺名称))
            日志记录器.warning(f"店铺 {店铺ID} 实例已自动清理（浏览器被手动关闭）")
