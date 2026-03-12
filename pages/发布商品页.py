"""拼多多发布商品页的页面对象模型"""
import inspect
import random
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pages.基础页 import 基础页
from selectors.发布商品页选择器 import 发布商品页选择器


class 发布商品页(基础页):
    """拼多多发布商品页 POM"""

    def __init__(self, 页面):
        super().__init__(页面)

    async def _获取页面标题(self):
        """兼容真实页面与测试替身，获取页面标题。"""
        标题结果 = self.页面.title()
        if inspect.isawaitable(标题结果):
            return await 标题结果
        return 标题结果

    async def 初始化页面(self) -> None:
        """等待页面初始加载并关闭可能的弹窗。"""
        await self.页面.wait_for_load_state("domcontentloaded")
        print(f"[发布商品页] 初始化页面: load_state完成, URL: {self.页面.url}")
        await self.随机延迟(1, 2)
        print(f"[发布商品页] 初始化页面: 准备关闭弹窗, URL: {self.页面.url}")
        await self.关闭所有弹窗()
        print(f"[发布商品页] 初始化页面: 关闭弹窗完成, URL: {self.页面.url}")
        print(f"[发布商品页] 页面标题: {await self._获取页面标题()}")

    async def 关闭所有弹窗(self, 最大尝试次数: int = 3) -> None:
        """按优先级关闭发布页常见弹窗。"""
        for 次数 in range(1, 最大尝试次数 + 1):
            已处理 = False

            for 选择器 in 发布商品页选择器.弹窗关闭按钮.所有选择器():
                元素 = await self.页面.query_selector(选择器)
                if 元素 is not None:
                    print(f"[发布商品页] 关闭弹窗: 第{次数}次, 匹配到: {选择器}")
                    await 元素.click()
                    await self.随机延迟(0.3, 0.8)
                    已处理 = True
                    break

            if 已处理:
                continue

            for 选择器 in 发布商品页选择器.弹窗关闭文本.所有选择器():
                try:
                    定位器 = self.页面.locator(选择器).first
                    if await 定位器.count() > 0:
                        print(f"[发布商品页] 关闭弹窗: 第{次数}次, 匹配到: {选择器}")
                        await 定位器.click()
                        await self.随机延迟(0.3, 0.8)
                        已处理 = True
                        break
                except Exception:
                    continue

            if not 已处理:
                print("[发布商品页] 无弹窗，退出")
                break

    def 从URL提取新商品ID(self) -> str:
        """从当前页面 URL 提取 goods_id。"""
        当前URL = getattr(self.页面, "url", "") or ""
        查询参数 = parse_qs(urlparse(当前URL).query)
        return 查询参数.get("goods_id", [""])[0]

    async def 获取当前URL(self) -> str:
        """获取当前页面URL。"""
        return getattr(self.页面, "url", "") or ""

    async def 提取商品ID(self) -> str:
        """从当前页面 URL 提取 goods_id。"""
        当前URL = await self.获取当前URL()
        查询参数 = parse_qs(urlparse(当前URL).query)
        return 查询参数.get("goods_id", [""])[0]

    async def 输入商品标题(self, 标题: str) -> None:
        """输入商品标题。"""
        print(f"[发布商品页] 输入商品标题: 开始, URL: {self.页面.url}")
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 发布商品页选择器.商品标题输入框.所有选择器():
            try:
                标题输入框 = self.页面.locator(选择器).first
                await 标题输入框.click()
                await self.页面.keyboard.press("Control+A")
                await self.随机延迟(0.2, 0.5)
                await 标题输入框.fill(标题)
                await self.操作后延迟()
                print(f"[发布商品页] 输入商品标题: 完成, URL: {self.页面.url}")
                return
            except Exception as 异常:
                最后异常 = 异常
        raise RuntimeError(f"商品标题输入失败: {最后异常}")

    async def 修改标题(self, 新标题: str) -> None:
        """清空并填写商品标题。"""
        print(f"[发布商品页] 修改标题: 开始, URL: {self.页面.url}")
        最后异常 = None
        for 选择器 in 发布商品页选择器.商品标题输入框.所有选择器():
            try:
                标题输入框 = self.页面.locator(选择器).first
                await 标题输入框.click()
                await self.页面.keyboard.press("Control+A")
                await 标题输入框.fill(新标题)
                await self.随机延迟(0.3, 0.8)
                print(f"[发布商品页] 修改标题: 完成, URL: {self.页面.url}")
                return
            except Exception as 异常:
                最后异常 = 异常
        raise RuntimeError(f"修改标题失败: {最后异常}")

    async def 获取商品标题(self) -> str:
        """读取当前标题输入框中的实际值。"""
        for 选择器 in 发布商品页选择器.商品标题输入框.所有选择器():
            try:
                标题输入框 = self.页面.locator(选择器).first
                try:
                    标题 = await 标题输入框.input_value()
                except Exception:
                    标题 = await 标题输入框.get_attribute("value")
                return str(标题 or "").strip()
            except Exception:
                continue
        return ""

    async def 获取主图列表(self):
        """获取当前页面中的主图元素列表。"""
        for 配置 in (发布商品页选择器.商品图片_所有图片项, 发布商品页选择器.图片容器):
            for 选择器 in 配置.所有选择器():
                try:
                    图片列表 = await self.页面.query_selector_all(选择器)
                    if 图片列表:
                        return 图片列表
                except Exception:
                    continue
        return []

    async def 拖拽主图(self, 源索引: int, 目标索引: int) -> None:
        """将指定主图拖拽到目标位置。"""
        await self.操作前延迟()
        图片列表 = await self.获取主图列表()

        if 源索引 < 0 or 目标索引 < 0 or 源索引 >= len(图片列表) or 目标索引 >= len(图片列表):
            raise RuntimeError("主图拖拽失败: 索引超出范围")
        源框 = await 图片列表[源索引].bounding_box()
        目标框 = await 图片列表[目标索引].bounding_box()
        if not 源框 or not 目标框:
            raise RuntimeError("主图拖拽失败: 无法获取元素位置")

        起点X = 源框["x"] + 源框["width"] / 2 + random.uniform(-3, 3)
        起点Y = 源框["y"] + 源框["height"] / 2 + random.uniform(-3, 3)
        终点X = 目标框["x"] + 目标框["width"] / 2 + random.uniform(-3, 3)
        终点Y = 目标框["y"] + 目标框["height"] / 2 + random.uniform(-3, 3)

        步数 = random.randint(8, 15)
        await self.页面.mouse.move(起点X, 起点Y)
        await self.页面.mouse.down()
        for 步骤序号 in range(1, 步数 + 1):
            比例 = 步骤序号 / 步数
            当前X = 起点X + (终点X - 起点X) * 比例 + random.uniform(-2, 2)
            当前Y = 起点Y + (终点Y - 起点Y) * 比例 + random.uniform(-2, 2)
            await self.页面.mouse.move(当前X, 当前Y)
            await self.随机延迟(0.02, 0.06)
        await self.页面.mouse.up()
        await self.操作后延迟()

    async def 获取主图数量(self) -> int:
        """获取当前主图数量。"""
        图片列表 = await self._获取图片列表()
        return len(图片列表)

    async def _获取图片列表(self):
        """按优先级获取页面中的图片列表。"""
        return await self.获取主图列表()

    async def 上传主图(self, 图片路径: str) -> None:
        """上传主图文件。"""
        文件路径 = Path(图片路径)
        if not 文件路径.exists():
            raise FileNotFoundError(f"图片不存在: {文件路径}")

        最后异常 = None
        for 选择器 in 发布商品页选择器.图片更换按钮文本.所有选择器():
            try:
                选择图片按钮 = self.页面.locator(选择器).first
                await 选择图片按钮.set_input_files(str(文件路径))
                await self.随机延迟(0.5, 1)
                break
            except Exception as 异常:
                最后异常 = 异常
        else:
            raise RuntimeError(f"选择图片失败: {最后异常}")

        for 选择器 in 发布商品页选择器.图片确认按钮文本.所有选择器():
            try:
                确认按钮 = self.页面.locator(选择器).first
                if await 确认按钮.count() > 0:
                    await 确认按钮.click()
                    await self.随机延迟(0.5, 1)
                    break
            except Exception:
                continue

    async def 随机调整主图到第一位(self) -> str:
        """随机将第 2~5 张主图拖到第 1 位。"""
        图片列表 = await self.获取主图列表()
        数量 = len(图片列表)
        if 数量 <= 1:
            return "跳过"

        目标索引 = random.randint(1, min(数量 - 1, 4))
        await self.拖拽主图(目标索引, 0)
        return f"第{目标索引 + 1}张调到第1位（共{数量}张）"

    async def 点击提交并上架(self) -> None:
        """点击提交并上架按钮。"""
        print(f"[发布商品页] 点击提交并上架: 开始, URL: {self.页面.url}")
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 发布商品页选择器.提交并上架按钮.所有选择器():
            try:
                await self.页面.click(选择器, timeout=10000)
                await self.页面加载延迟()
                print(f"[发布商品页] 点击提交并上架: 完成, URL: {self.页面.url}")
                return
            except Exception as 异常:
                最后异常 = 异常
        raise RuntimeError(f"点击提交并上架失败: {最后异常}")

    async def 等待发布成功(self) -> bool:
        """等待发布成功提示或成功页 URL。"""
        print(f"[发布商品页] 等待发布成功: 开始, URL: {self.页面.url}")
        当前URL = getattr(self.页面, "url", "") or ""
        if 发布商品页选择器.发布成功页URL特征 in 当前URL:
            await self.随机延迟(1.0, 2.0)
            print(f"[发布商品页] 等待发布成功: 已命中成功URL, URL: {self.页面.url}")
            return True

        try:
            await self.页面.wait_for_url(
                re.compile(rf".*/{re.escape(发布商品页选择器.发布成功页URL特征)}.*"),
                timeout=10000,
            )
            await self.随机延迟(1.0, 2.0)
            print(f"[发布商品页] 等待发布成功: wait_for_url命中成功页, URL: {self.页面.url}")
            return True
        except Exception:
            pass

        for 选择器 in 发布商品页选择器.发布成功提示.所有选择器():
            try:
                提交成功文本 = self.页面.locator(选择器).first
                if await 提交成功文本.count() > 0:
                    await self.随机延迟(1.0, 2.0)
                    print(f"[发布商品页] 等待发布成功: 文本检测结果=True, URL: {self.页面.url}")
                    return True
            except Exception:
                continue

        print(f"[发布商品页] 等待发布成功: 文本检测结果=False, URL: {self.页面.url}")
        return False

    async def 是否发布成功(self) -> bool:
        """检测是否已进入发布成功页。"""
        print(f"[发布商品页] 是否发布成功: 开始, URL: {self.页面.url}")
        当前URL = getattr(self.页面, "url", "") or ""
        if 发布商品页选择器.发布成功页URL特征 in 当前URL:
            print(f"[发布商品页] 是否发布成功: 已命中成功URL, URL: {self.页面.url}")
            return True

        try:
            await self.页面.wait_for_url(
                re.compile(rf".*/{re.escape(发布商品页选择器.发布成功页URL特征)}.*"),
                timeout=10000,
            )
            print(f"[发布商品页] 是否发布成功: wait_for_url命中成功页, URL: {self.页面.url}")
            return True
        except Exception:
            pass

        for 选择器 in 发布商品页选择器.发布成功提示.所有选择器():
            try:
                提交成功文本 = self.页面.locator(选择器).first
                是否成功 = await 提交成功文本.count() > 0
                if 是否成功:
                    print(f"[发布商品页] 是否发布成功: 文本检测结果=True, URL: {self.页面.url}")
                    return True
            except Exception:
                continue

        print(f"[发布商品页] 是否发布成功: 文本检测结果=False, URL: {self.页面.url}")
        return False

    def 从成功页提取商品ID(self) -> str:
        """从成功页 URL 中提取商品 ID。"""
        return self.从URL提取新商品ID()

    async def 检测滑块验证码(self) -> bool:
        """检测是否出现滑块验证码。"""
        验证码 = await self.页面.query_selector(", ".join(发布商品页选择器.滑块验证码.所有选择器()))
        return 验证码 is not None

    async def 截图当前状态(self) -> str:
        """截图当前页面。"""
        return await self.截图("发布商品页状态")

    async def 关闭当前标签页(self) -> None:
        """关闭当前标签页。"""
        print(f"[发布商品页] 关闭当前标签页: 开始, URL: {self.页面.url}")
        await self.操作前延迟()
        await self.页面.close()
        print(f"[发布商品页] 关闭当前标签页: 完成, URL: {self.页面.url}")

    async def 关闭页面(self) -> None:
        """关闭当前标签页。"""
        print(f"[发布商品页] 关闭页面: 开始, URL: {self.页面.url}")
        await self.页面.close()
        print(f"[发布商品页] 关闭页面: 完成, URL: {self.页面.url}")
