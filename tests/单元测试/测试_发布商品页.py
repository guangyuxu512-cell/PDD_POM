"""
发布商品页单元测试
"""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class 测试_发布商品页:
    """测试发布商品页 POM。"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        页面.url = "https://mms.pinduoduo.com/goods/goods_add/index?goods_id=9988"
        页面.wait_for_load_state = AsyncMock()
        页面.wait_for_url = AsyncMock()
        页面.query_selector = AsyncMock(return_value=None)
        页面.query_selector_all = AsyncMock(return_value=[])
        页面.get_by_role = MagicMock()
        页面.get_by_text = MagicMock()
        页面.get_by_placeholder = MagicMock()
        页面.get_by_test_id = MagicMock()
        页面.screenshot = AsyncMock()
        页面.close = AsyncMock()
        页面.mouse = MagicMock()
        页面.mouse.move = AsyncMock()
        页面.mouse.click = AsyncMock()
        页面.mouse.down = AsyncMock()
        页面.mouse.up = AsyncMock()
        页面.mouse.wheel = AsyncMock()
        页面.keyboard = MagicMock()
        页面.keyboard.type = AsyncMock()
        页面.keyboard.press = AsyncMock()
        return 页面

    @pytest.mark.asyncio
    async def test_初始化页面_等待加载后关闭弹窗(self, 模拟页面):
        from pages.发布商品页 import 发布商品页

        页面对象 = 发布商品页(模拟页面)
        页面对象.随机延迟 = AsyncMock()
        页面对象.关闭所有弹窗 = AsyncMock()

        await 页面对象.初始化页面()

        模拟页面.wait_for_load_state.assert_awaited_once_with("domcontentloaded")
        页面对象.关闭所有弹窗.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_关闭所有弹窗_点击素材弹窗关闭(self, 模拟页面):
        from pages.发布商品页 import 发布商品页

        关闭元素 = MagicMock()
        关闭元素.click = AsyncMock()
        模拟页面.query_selector = AsyncMock(side_effect=[关闭元素, None, None, None, None, None])

        页面对象 = 发布商品页(模拟页面)
        页面对象.随机延迟 = AsyncMock()

        await 页面对象.关闭所有弹窗()

        关闭元素.click.assert_awaited_once()

    def test_从URL提取新商品ID_正常与缺失场景(self, 模拟页面):
        from pages.发布商品页 import 发布商品页

        页面对象 = 发布商品页(模拟页面)
        assert 页面对象.从URL提取新商品ID() == "9988"

        模拟页面.url = "https://mms.pinduoduo.com/goods/goods_add/index"
        assert 页面对象.从URL提取新商品ID() == ""

    @pytest.mark.asyncio
    async def test_修改标题_先全选再填写(self, 模拟页面):
        from pages.发布商品页 import 发布商品页

        标题输入框 = MagicMock()
        标题输入框.click = AsyncMock()
        标题输入框.fill = AsyncMock()
        模拟页面.get_by_placeholder.return_value = 标题输入框

        页面对象 = 发布商品页(模拟页面)
        页面对象.随机延迟 = AsyncMock()

        await 页面对象.修改标题("新的标题")

        模拟页面.keyboard.press.assert_awaited_once_with("Control+A")
        标题输入框.fill.assert_awaited_once_with("新的标题")

    @pytest.mark.asyncio
    async def test_获取主图数量(self, 模拟页面):
        from pages.发布商品页 import 发布商品页

        模拟页面.query_selector_all.return_value = [MagicMock(), MagicMock(), MagicMock()]
        页面对象 = 发布商品页(模拟页面)

        assert await 页面对象.获取主图数量() == 3

    @pytest.mark.asyncio
    async def test_随机调整主图到第一位_单图跳过(self, 模拟页面):
        from pages.发布商品页 import 发布商品页

        模拟页面.query_selector_all.return_value = [MagicMock()]
        页面对象 = 发布商品页(模拟页面)

        assert await 页面对象.随机调整主图到第一位() == "跳过"

    @pytest.mark.asyncio
    async def test_随机调整主图到第一位_多图拖拽(self, 模拟页面):
        from pages.发布商品页 import 发布商品页

        图片列表 = [MagicMock() for _ in range(5)]
        图片列表[2].drag_to = AsyncMock()
        图片列表[0].drag_to = AsyncMock()
        模拟页面.query_selector_all.return_value = 图片列表

        页面对象 = 发布商品页(模拟页面)
        页面对象.随机延迟 = AsyncMock()

        with patch("pages.发布商品页.random.randint", return_value=2):
            结果 = await 页面对象.随机调整主图到第一位()

        assert 结果 == "第3张调到第1位（共5张）"
        图片列表[2].drag_to.assert_awaited_once_with(图片列表[0])

    @pytest.mark.asyncio
    async def test_上传主图_文件不存在抛异常(self, 模拟页面):
        from pages.发布商品页 import 发布商品页

        页面对象 = 发布商品页(模拟页面)

        with pytest.raises(FileNotFoundError):
            await 页面对象.上传主图("E:/not-exists/demo.png")

    @pytest.mark.asyncio
    async def test_上传主图_成功设置文件并确认(self, 模拟页面, tmp_path: Path):
        from pages.发布商品页 import 发布商品页

        图片文件 = tmp_path / "demo.png"
        图片文件.write_bytes(b"fake")

        选择图片按钮 = MagicMock()
        选择图片按钮.set_input_files = AsyncMock()
        确认按钮 = MagicMock()
        确认按钮.count = AsyncMock(return_value=1)
        确认按钮.first = MagicMock()
        确认按钮.first.click = AsyncMock()
        模拟页面.get_by_role.side_effect = lambda role, name: {
            ("button", "选择图片"): 选择图片按钮,
            ("button", "确认"): 确认按钮,
        }[(role, name)]

        页面对象 = 发布商品页(模拟页面)
        页面对象.随机延迟 = AsyncMock()

        await 页面对象.上传主图(str(图片文件))

        选择图片按钮.set_input_files.assert_awaited_once_with(str(图片文件))
        确认按钮.first.click.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_是否发布成功_支持成功页URL与文本兜底(self, 模拟页面):
        from pages.发布商品页 import 发布商品页

        页面对象 = 发布商品页(模拟页面)
        模拟页面.wait_for_url.side_effect = Exception("timeout")
        空文本 = MagicMock()
        空文本.count = AsyncMock(return_value=0)
        模拟页面.get_by_text.return_value = 空文本
        assert await 页面对象.是否发布成功() is False

        模拟页面.url = "https://mms.pinduoduo.com/goods/goods_add/success?goods_id=9988"
        assert await 页面对象.是否发布成功() is True

        模拟页面.url = "https://mms.pinduoduo.com/goods/goods_add/index?goods_id=9988"
        成功文本 = MagicMock()
        成功文本.count = AsyncMock(return_value=1)
        模拟页面.get_by_text.return_value = 成功文本
        assert await 页面对象.是否发布成功() is True

    @pytest.mark.asyncio
    async def test_检测滑块验证码与关闭页面(self, 模拟页面):
        from pages.发布商品页 import 发布商品页

        模拟页面.query_selector.return_value = MagicMock()
        页面对象 = 发布商品页(模拟页面)

        assert await 页面对象.检测滑块验证码() is True
        await 页面对象.关闭页面()
        模拟页面.close.assert_awaited_once()
