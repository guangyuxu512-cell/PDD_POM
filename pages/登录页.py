"""拼多多商家后台登录页面的页面对象模型"""
import json
from pathlib import Path
from pages.基础页 import 基础页
from selectors.基础页选择器 import 基础页选择器
from selectors.登录页选择器 import 登录页选择器
from backend.配置 import 配置实例


class 登录页(基础页):
    """拼多多商家后台登录页 POM"""

    def __init__(self, 页面):
        super().__init__(页面)
        self.登录地址 = 基础页选择器.登录页URL
        self.首页地址 = 基础页选择器.首页URL

    # === 导航 ===

    async def 导航(self) -> None:
        """打开登录页"""
        await self.页面.goto(self.登录地址, wait_until="domcontentloaded")
        await self.随机延迟(1, 3)

    async def 访问首页(self) -> None:
        """访问首页（用于 Cookie 验证）"""
        await self.页面.goto(self.首页地址, wait_until="domcontentloaded")
        await self.随机延迟(2, 4)

    # === Cookie 管理 ===

    def _获取Cookie文件路径(self, 店铺ID: str) -> Path:
        """
        获取 Cookie 文件路径

        Args:
            店铺ID: 店铺 ID

        Returns:
            Path: Cookie 文件路径
        """
        Cookie目录 = Path(配置实例.DATA_DIR) / "cookies"
        Cookie目录.mkdir(parents=True, exist_ok=True)
        return Cookie目录 / f"{店铺ID}.json"

    async def 保存Cookie(self, 店铺ID: str) -> None:
        """
        保存当前浏览器的 Cookie 到文件

        Args:
            店铺ID: 店铺 ID
        """
        # 获取浏览器上下文
        上下文 = self.页面.context

        # 获取所有 Cookie
        cookies = await 上下文.cookies()

        # 保存到文件
        Cookie文件 = self._获取Cookie文件路径(店铺ID)
        with open(Cookie文件, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print(f"✓ Cookie 已保存: {Cookie文件}")

    async def 加载Cookie(self, 店铺ID: str) -> bool:
        """
        从文件加载 Cookie 到浏览器

        Args:
            店铺ID: 店铺 ID

        Returns:
            bool: 是否加载成功
        """
        Cookie文件 = self._获取Cookie文件路径(店铺ID)

        # 检查文件是否存在
        if not Cookie文件.exists():
            print(f"⚠ Cookie 文件不存在: {Cookie文件}")
            return False

        try:
            # 读取 Cookie
            with open(Cookie文件, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            # 获取浏览器上下文
            上下文 = self.页面.context

            # 添加 Cookie
            await 上下文.add_cookies(cookies)

            print(f"✓ Cookie 已加载: {Cookie文件}")
            return True

        except Exception as e:
            print(f"✗ Cookie 加载失败: {e}")
            return False

    async def 检测Cookie是否有效(self) -> bool:
        """
        检测 Cookie 是否有效（访问首页，检查是否被重定向到登录页）

        Returns:
            bool: Cookie 是否有效
        """
        try:
            # 访问首页
            await self.访问首页()

            # 检查当前 URL 是否在首页
            当前URL = self.页面.url
            if "mms.pinduoduo.com/home" in 当前URL:
                print(f"✓ Cookie 有效，当前 URL: {当前URL}")
                return True
            else:
                print(f"✗ Cookie 失效，被重定向到: {当前URL}")
                return False

        except Exception as e:
            print(f"✗ Cookie 验证失败: {e}")
            return False

    # === 登录操作 ===

    async def 切换账号登录(self) -> None:
        """点击'账号登录'标签"""
        最后异常 = None
        for 选择器 in 登录页选择器.账号登录.所有选择器():
            try:
                await self.页面.click(选择器, timeout=5000)
                await self.随机延迟(0.5, 1)
                return
            except Exception as 异常:
                最后异常 = 异常
        raise RuntimeError(f"点击账号登录失败: {最后异常}")

    async def 填写手机号(self, 手机号: str) -> None:
        """
        填写手机号或账号名

        Args:
            手机号: 手机号或账号名
        """
        最后异常 = None
        for 选择器 in 登录页选择器.账号输入框.所有选择器():
            try:
                await self.安全填写(选择器, 手机号)
                return
            except Exception as 异常:
                最后异常 = 异常
        raise RuntimeError(f"填写账号失败: {最后异常}")

    async def 填写密码(self, 密码: str) -> None:
        """
        填写密码

        Args:
            密码: 密码
        """
        最后异常 = None
        for 选择器 in 登录页选择器.密码输入框.所有选择器():
            try:
                await self.安全填写(选择器, 密码)
                return
            except Exception as 异常:
                最后异常 = 异常
        raise RuntimeError(f"填写密码失败: {最后异常}")

    async def 点击登录(self) -> None:
        """点击登录按钮"""
        最后异常 = None
        for 选择器 in 登录页选择器.登录按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=5000)
                await self.随机延迟(2, 4)
                return
            except Exception as 异常:
                最后异常 = 异常
        raise RuntimeError(f"点击登录失败: {最后异常}")

    # === 状态检测 ===

    async def 是否登录成功(self) -> bool:
        """
        检查是否跳转到首页

        处理页面跳转导致的 context destroyed 异常。
        如果捕获到 context destroyed 或 navigation 异常，说明页面发生了跳转，
        此时等待一段时间后检查 URL 是否在首页。

        Returns:
            bool: 是否登录成功
        """
        try:
            # 等待页面跳转到首页
            await self.页面.wait_for_url("**/home**", timeout=10000)
            当前URL = self.页面.url
            return isinstance(当前URL, str) and "mms.pinduoduo.com/home" in 当前URL
        except Exception as e:
            错误信息 = str(e).lower()

            # 如果是 context destroyed 或 navigation 相关异常，说明页面发生了跳转
            if "context" in 错误信息 or "destroyed" in 错误信息 or "navigation" in 错误信息:
                print(f"⚠ 捕获到页面跳转异常: {e}，等待后检查 URL")
                # 等待页面稳定
                await self.随机延迟(3, 5)

                try:
                    # 检查当前 URL 是否在首页
                    当前URL = self.页面.url
                    if "mms.pinduoduo.com/home" in 当前URL:
                        print(f"✓ 页面已跳转到首页: {当前URL}")
                        return True
                except Exception as e2:
                    print(f"✗ 检查 URL 失败: {e2}")
                    return False

            print(f"✗ 登录失败: {e}")
            return False

    async def 检测滑块验证码(self) -> bool:
        """
        检测是否出现滑块验证码

        Returns:
            bool: 是否出现滑块验证码
        """
        滑块 = await self.页面.query_selector(", ".join(登录页选择器.滑块验证码.所有选择器()))
        return 滑块 is not None

    async def 检测短信验证码(self) -> bool:
        """
        检测是否出现短信验证码输入框

        Returns:
            bool: 是否出现短信验证码输入框
        """
        验证码输入 = await self.页面.query_selector(", ".join(登录页选择器.短信验证码输入框.所有选择器()))
        return 验证码输入 is not None

    async def 截图登录状态(self) -> str:
        """
        截图当前登录状态

        Returns:
            str: 截图文件路径
        """
        return await self.截图("登录状态")
