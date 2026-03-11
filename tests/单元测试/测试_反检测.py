"""
反检测模块单元测试
"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock


class 测试_真人模拟器:
    """测试真人模拟器的各种方法"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = AsyncMock()
        页面.query_selector = AsyncMock()
        页面.click = AsyncMock()
        页面.keyboard = MagicMock()
        页面.keyboard.type = AsyncMock()
        页面.keyboard.press = AsyncMock()
        页面.mouse = MagicMock()
        页面.mouse.move = AsyncMock()
        页面.mouse.click = AsyncMock()
        页面.mouse.wheel = AsyncMock()

        # 模拟元素
        模拟元素 = AsyncMock()
        模拟元素.is_visible = AsyncMock(return_value=True)
        模拟元素.bounding_box = AsyncMock(
            return_value={"x": 100, "y": 100, "width": 200, "height": 50}
        )
        页面.query_selector.return_value = 模拟元素

        return 页面

    @pytest.mark.asyncio
    async def test_随机延迟在范围内(self, 模拟页面):
        """测试随机延迟是否在指定范围内"""
        from browser.反检测 import 真人模拟器

        模拟器 = 真人模拟器(模拟页面)
        最小秒 = 0.01
        最大秒 = 0.02

        # 统计 100 次延迟
        for _ in range(100):
            开始时间 = time.time()
            await 模拟器.随机延迟(最小秒, 最大秒)
            结束时间 = time.time()
            实际延迟 = 结束时间 - 开始时间

            # 验证延迟在范围内（允许系统调度误差）
            assert 最小秒 <= 实际延迟 <= 最大秒 + 0.02

    @pytest.mark.asyncio
    async def test_贝塞尔曲线终点正确(self, 模拟页面):
        """测试贝塞尔曲线移动的终点是否正确"""
        from browser.反检测 import 真人模拟器

        模拟器 = 真人模拟器(模拟页面)
        目标x = 500.0
        目标y = 300.0

        await 模拟器._贝塞尔移动(目标x, 目标y, 步数=20)

        # 获取最后一次 mouse.move 调用的参数
        最后调用 = 模拟页面.mouse.move.call_args_list[-1]
        最终x = 最后调用[0][0]
        最终y = 最后调用[0][1]

        # 验证终点坐标（误差 < 1px）
        assert abs(最终x - 目标x) < 1
        assert abs(最终y - 目标y) < 1

    @pytest.mark.asyncio
    async def test_模拟打字调用逐字输入(self, 模拟页面):
        """测试模拟打字是否逐字输入"""
        from browser.反检测 import 真人模拟器

        模拟器 = 真人模拟器(模拟页面)
        文本 = "abc"

        await 模拟器.模拟打字("#input", 文本)

        # keyboard.type 被调用次数应该 >= 文本长度
        # （可能有打错字的情况，所以可能更多）
        assert 模拟页面.keyboard.type.call_count >= len(文本)

    @pytest.mark.asyncio
    async def test_移动并点击完成点击(self, 模拟页面):
        """测试移动并点击是否完成点击操作"""
        from browser.反检测 import 真人模拟器

        模拟器 = 真人模拟器(模拟页面)

        await 模拟器.移动并点击("#button")

        # 验证 mouse.click 被调用
        模拟页面.mouse.click.assert_called()

    @pytest.mark.asyncio
    async def test_元素未找到抛出异常(self, 模拟页面):
        """测试元素未找到时抛出异常"""
        from browser.反检测 import 真人模拟器

        模拟器 = 真人模拟器(模拟页面)
        模拟页面.query_selector.return_value = None

        with pytest.raises(Exception, match="元素未找到"):
            await 模拟器.移动并点击("#not-exist")

    @pytest.mark.asyncio
    async def test_元素不可见抛出异常(self, 模拟页面):
        """测试元素不可见时抛出异常"""
        from browser.反检测 import 真人模拟器

        模拟器 = 真人模拟器(模拟页面)
        模拟元素 = AsyncMock()
        模拟元素.is_visible = AsyncMock(return_value=False)
        模拟页面.query_selector.return_value = 模拟元素

        with pytest.raises(Exception, match="元素不可见"):
            await 模拟器.移动并点击("#hidden")
