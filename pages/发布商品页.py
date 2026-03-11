"""拼多多发布商品页的页面对象模型"""
import random
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pages.基础页 import 基础页


class 发布商品页(基础页):
    """拼多多发布商品页 POM"""

    def __init__(self, 页面):
        super().__init__(页面)

    async def 初始化页面(self) -> None:
        """等待页面初始加载并关闭可能的弹窗。"""
        await self.页面.wait_for_load_state("domcontentloaded")
        await self.随机延迟(1, 2)
        await self.关闭所有弹窗()

    async def 关闭所有弹窗(self, 最大尝试次数: int = 8) -> None:
        """按优先级关闭发布页常见弹窗。"""
        for _ in range(最大尝试次数):
            已处理 = False

            for 选择器 in [
                ".MaterialModalButton_v2_actionBox__1v6rw > div:nth-child(3)",
                "[data-testid='beast-core-icon-close']",
                ".ant-modal-close",
            ]:
                元素 = await self.页面.query_selector(选择器)
                if 元素 is not None:
                    await 元素.click()
                    await self.随机延迟(0.3, 0.8)
                    已处理 = True
                    break

            if 已处理:
                continue

            for 定位器 in [
                self.页面.get_by_role("button", name="我知道了"),
                self.页面.get_by_test_id("beast-core-modal-body").get_by_test_id("beast-core-button"),
                self.页面.get_by_test_id("beast-core-modal-container").get_by_test_id("beast-core-icon-close"),
                self.页面.get_by_text("关闭"),
            ]:
                try:
                    if await 定位器.count() > 0:
                        await 定位器.first.click()
                        await self.随机延迟(0.3, 0.8)
                        已处理 = True
                        break
                except Exception:
                    continue

            if not 已处理:
                break

    def 从URL提取新商品ID(self) -> str:
        """从当前页面 URL 提取 goods_id。"""
        当前URL = getattr(self.页面, "url", "") or ""
        查询参数 = parse_qs(urlparse(当前URL).query)
        return 查询参数.get("goods_id", [""])[0]

    async def 修改标题(self, 新标题: str) -> None:
        """清空并填写商品标题。"""
        标题输入框 = self.页面.get_by_placeholder("商品标题组成：商品描述+规格，最多输入30个汉字（60")
        await 标题输入框.click()
        await self.页面.keyboard.press("Control+A")
        await 标题输入框.fill(新标题)
        await self.随机延迟(0.3, 0.8)

    async def 获取主图数量(self) -> int:
        """获取当前主图数量。"""
        图片列表 = await self.页面.query_selector_all(".MaterialModalButton_v2_imageBox__1NfrZ")
        return len(图片列表)

    async def 上传主图(self, 图片路径: str) -> None:
        """上传主图文件。"""
        文件路径 = Path(图片路径)
        if not 文件路径.exists():
            raise FileNotFoundError(f"图片不存在: {文件路径}")

        选择图片按钮 = self.页面.get_by_role("button", name="选择图片")
        await 选择图片按钮.set_input_files(str(文件路径))
        await self.随机延迟(0.5, 1)

        确认按钮 = self.页面.get_by_role("button", name="确认")
        try:
            if await 确认按钮.count() > 0:
                await 确认按钮.first.click()
                await self.随机延迟(0.5, 1)
        except Exception:
            pass

    async def 随机调整主图到第一位(self) -> str:
        """随机将第 2~5 张主图拖到第 1 位。"""
        图片列表 = await self.页面.query_selector_all(".MaterialModalButton_v2_imageBox__1NfrZ")
        数量 = len(图片列表)
        if 数量 <= 1:
            return "跳过"

        目标索引 = random.randint(1, min(数量 - 1, 4))
        await 图片列表[目标索引].drag_to(图片列表[0])
        await self.随机延迟(0.5, 1)
        return f"第{目标索引 + 1}张调到第1位（共{数量}张）"

    async def 点击提交并上架(self) -> None:
        """点击提交并上架按钮。"""
        提交按钮 = self.页面.get_by_role("button", name="提交并上架")
        await 提交按钮.click()
        await self.随机延迟(1, 2)

    async def 是否发布成功(self) -> bool:
        """检测是否已进入发布成功页。"""
        当前URL = getattr(self.页面, "url", "") or ""
        if "goods_add/success" in 当前URL:
            return True

        try:
            await self.页面.wait_for_url(re.compile(r".*/goods_add/success.*"), timeout=10000)
            return True
        except Exception:
            pass

        try:
            提交成功文本 = self.页面.get_by_text("提交成功")
            return await 提交成功文本.count() > 0
        except Exception:
            return False

    def 从成功页提取商品ID(self) -> str:
        """从成功页 URL 中提取商品 ID。"""
        return self.从URL提取新商品ID()

    async def 检测滑块验证码(self) -> bool:
        """检测是否出现滑块验证码。"""
        验证码 = await self.页面.query_selector("#slide-button, .captcha-container, .captcha-slider")
        return 验证码 is not None

    async def 截图当前状态(self) -> str:
        """截图当前页面。"""
        return await self.截图("发布商品页状态")

    async def 关闭页面(self) -> None:
        """关闭当前标签页。"""
        await self.页面.close()
