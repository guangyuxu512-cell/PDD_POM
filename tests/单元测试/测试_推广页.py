"""
推广页单元测试
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from selectors.选择器配置 import 选择器配置


class 测试_推广页:
    """测试推广页 POM。"""

    @pytest.fixture
    def 模拟页面(self):
        页面 = MagicMock()
        页面.goto = AsyncMock()
        页面.go_back = AsyncMock()
        页面.click = AsyncMock()
        页面.screenshot = AsyncMock()
        页面.wait_for_selector = AsyncMock()
        页面.query_selector = AsyncMock(return_value=None)
        页面.evaluate = AsyncMock()
        页面.url = "https://yingxiao.pinduoduo.com/goods/promotion/list?msfrom=mms_sidenav"
        页面.locator = MagicMock()
        页面.keyboard = MagicMock()
        页面.keyboard.press = AsyncMock()
        页面.mouse = MagicMock()
        页面.mouse.wheel = AsyncMock()
        return 页面

    @pytest.mark.asyncio
    async def test_导航到全站推广页_打开固定URL(self, 模拟页面):
        from pages.推广页 import 推广页

        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()

        await 页面对象.导航到全站推广页()

        模拟页面.goto.assert_awaited_once_with(
            "https://yingxiao.pinduoduo.com/goods/promotion/list?msfrom=mms_sidenav",
            wait_until="domcontentloaded",
        )
        页面对象._随机等待.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_商品行是否存在_按商品ID动态选择器判断(self, 模拟页面):
        from pages.推广页 import 推广页

        模拟页面.query_selector = AsyncMock(return_value=object())
        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()

        结果 = await 页面对象.商品行是否存在("123456789012")

        assert 结果 is True
        assert "create_item_123456789012" in 模拟页面.query_selector.await_args.args[0]

    @pytest.mark.asyncio
    async def test_获取极速起量高级版状态_根据class判断开关(self, 模拟页面):
        from pages.推广页 import 推广页

        元素 = MagicMock()
        元素.get_attribute = AsyncMock(return_value="anq-switch anq-switch-checked")
        定位器 = MagicMock()
        定位器.first = 元素
        模拟页面.locator.return_value = 定位器

        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()

        结果 = await 页面对象.获取极速起量高级版状态("123456789012")

        assert 结果 == "true"

    @pytest.mark.asyncio
    async def test_点击预算日限额_按选择器回退(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        async def 点击副作用(选择器, timeout=10000):
            if 选择器 == "bad-selector":
                raise RuntimeError("bad selector")
            return None

        monkeypatch.setattr(
            推广页选择器,
            "预算日限额菜单项",
            选择器配置("bad-selector", ["good-selector"]),
        )
        模拟页面.click.side_effect = 点击副作用

        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()

        结果 = await 页面对象.点击预算日限额()

        assert 结果 is True
        assert 模拟页面.click.await_args_list[0].args[0] == "bad-selector"
        assert 模拟页面.click.await_args_list[1].args[0] == "good-selector"

    @pytest.mark.asyncio
    async def test_确认关闭全局起量_等待确认按钮后点击(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        monkeypatch.setattr(
            推广页选择器,
            "全局起量关闭确认按钮",
            选择器配置("confirm-close"),
        )

        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()
        页面对象._确认弹窗后等待 = AsyncMock()

        结果 = await 页面对象.确认关闭全局起量()

        assert 结果 is True
        模拟页面.wait_for_selector.assert_awaited_once_with("confirm-close", timeout=5000)
        模拟页面.click.assert_awaited_once_with("confirm-close", timeout=5000)
        页面对象._确认弹窗后等待.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_确认关闭极速起量_优先命中商品绑定按钮(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        monkeypatch.setattr(
            推广页选择器,
            "获取极速起量高级版关闭确认按钮",
            staticmethod(lambda 商品ID: 选择器配置(f"popover-main-{商品ID}", [f"assist-close-{商品ID}", "confirm-close"])),
        )

        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()
        页面对象._确认弹窗后等待 = AsyncMock()

        结果 = await 页面对象.确认关闭极速起量("123")

        assert 结果 is True
        模拟页面.wait_for_selector.assert_awaited_once_with("popover-main-123", timeout=3000)
        模拟页面.click.assert_awaited_once_with("popover-main-123", timeout=3000)
        页面对象._确认弹窗后等待.assert_awaited_once()

    def test_极速起量确认关闭选择器_主选择器使用极速起量标题锚点(self):
        from selectors.推广页选择器 import 推广页选择器

        选择器 = 推广页选择器.获取极速起量高级版关闭确认按钮("123")
        assert 'contains(text(), "极速起量")' in 选择器.主选择器
        assert 'contains(@class, "anq-popover")' in 选择器.主选择器
        assert 'contains(@class, "anq-btn-primary")' in 选择器.主选择器
        assert './/span[text()="确定关闭"]' in 选择器.主选择器

    def test_极速起量确认关闭选择器_商品绑定与兜底顺序正确(self):
        from selectors.推广页选择器 import 推广页选择器

        选择器列表 = 推广页选择器.获取极速起量高级版关闭确认按钮("123").所有选择器()
        assert 'contains(@data-testid, "assist_close") and contains(@data-testid, "123")' in 选择器列表[1]
        assert 选择器列表[2] == '//button[.//span[text()="确定关闭"]]'

    @pytest.mark.asyncio
    async def test_确认关闭极速起量_商品绑定失败后回退_popover(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        monkeypatch.setattr(
            推广页选择器,
            "获取极速起量高级版关闭确认按钮",
            staticmethod(lambda 商品ID: 选择器配置(f"popover-main-{商品ID}", [f"assist-close-{商品ID}", "confirm-close"])),
        )

        async def 等待副作用(选择器, timeout=2000):
            if 选择器 == "popover-main-123":
                raise RuntimeError("not found")
            if 选择器 == "assist-close-123":
                return None
            raise RuntimeError("should not reach fallback")

        模拟页面.wait_for_selector = AsyncMock(side_effect=等待副作用)
        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()
        页面对象._确认弹窗后等待 = AsyncMock()

        结果 = await 页面对象.确认关闭极速起量("123")

        assert 结果 is True
        assert 模拟页面.wait_for_selector.await_args_list[0].args == ("popover-main-123",)
        assert 模拟页面.wait_for_selector.await_args_list[1].args == ("assist-close-123",)
        assert 模拟页面.click.await_args.args == ("assist-close-123",)

    @pytest.mark.asyncio
    async def test_确认关闭极速起量_前两种失败后回退_确定关闭按钮(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        monkeypatch.setattr(
            推广页选择器,
            "获取极速起量高级版关闭确认按钮",
            staticmethod(lambda 商品ID: 选择器配置(f"popover-main-{商品ID}", [f"assist-close-{商品ID}", "confirm-close"])),
        )

        async def 等待副作用(选择器, timeout=2000):
            if 选择器 in {"popover-main-123", "assist-close-123"}:
                raise RuntimeError("not found")
            return None

        模拟页面.wait_for_selector = AsyncMock(side_effect=等待副作用)
        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()
        页面对象._确认弹窗后等待 = AsyncMock()

        结果 = await 页面对象.确认关闭极速起量("123")

        assert 结果 is True
        assert 模拟页面.wait_for_selector.await_args_list[0].args == ("popover-main-123",)
        assert 模拟页面.wait_for_selector.await_args_list[1].args == ("assist-close-123",)
        assert 模拟页面.wait_for_selector.await_args_list[2].args == ("confirm-close",)
        assert 模拟页面.click.await_args.args == ("confirm-close",)

    @pytest.mark.asyncio
    async def test_确认关闭极速起量_双形态都失败时截图并返回False(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        monkeypatch.setattr(
            推广页选择器,
            "获取极速起量高级版关闭确认按钮",
            staticmethod(lambda 商品ID: 选择器配置(f"popover-main-{商品ID}", [f"assist-close-{商品ID}", "confirm-close"])),
        )
        模拟页面.wait_for_selector = AsyncMock(side_effect=RuntimeError("timeout"))

        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()
        页面对象._确认弹窗后等待 = AsyncMock()
        页面对象.截图 = AsyncMock(return_value="fail.png")

        结果 = await 页面对象.确认关闭极速起量("123")

        assert 结果 is False
        页面对象.截图.assert_awaited_once_with("极速起量确认弹窗未找到")
        页面对象._确认弹窗后等待.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_点击开启推广_点击失败时使用JS兜底(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        monkeypatch.setattr(推广页选择器, "开启推广按钮", 选择器配置("bad-button", ["good-button"]))

        async def 点击副作用(选择器, timeout=10000):
            raise RuntimeError("click failed")

        模拟页面.click.side_effect = 点击副作用
        模拟页面.evaluate = AsyncMock(return_value=None)
        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()

        结果 = await 页面对象.点击开启推广()

        assert 结果 is True
        模拟页面.mouse.wheel.assert_awaited_once()
        模拟页面.evaluate.assert_awaited()

    @pytest.mark.asyncio
    async def test_等待推广成功_toast命中即返回成功(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        模拟页面.url = "https://yingxiao.pinduoduo.com/goods/promotion/create"
        monkeypatch.setattr(推广页选择器, "推广成功Toast提示", 选择器配置("toast-success", ["toast-opened"]))
        monkeypatch.setattr(推广页选择器, "推广中状态文案", 选择器配置("status-running"))
        monkeypatch.setattr(推广页选择器, "开启推广按钮", 选择器配置("begin-button"))

        async def 查询副作用(选择器):
            if 选择器 == "toast-success":
                return object()
            return None

        模拟页面.query_selector = AsyncMock(side_effect=查询副作用)
        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()
        页面对象._按钮是否仍可见 = AsyncMock(return_value=True)

        结果 = await 页面对象.等待推广成功()

        assert 结果 is True
        页面对象._按钮是否仍可见.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_等待推广成功_开启推广按钮消失即返回成功(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        模拟页面.url = "https://yingxiao.pinduoduo.com/goods/promotion/create"
        monkeypatch.setattr(推广页选择器, "推广成功Toast提示", 选择器配置("toast-success"))
        monkeypatch.setattr(推广页选择器, "推广中状态文案", 选择器配置("status-running"))

        模拟页面.query_selector = AsyncMock(return_value=None)
        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()
        页面对象._按钮是否仍可见 = AsyncMock(return_value=False)

        结果 = await 页面对象.等待推广成功()

        assert 结果 is True
        页面对象._按钮是否仍可见.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_等待推广成功_超时后截图返回False(self, 模拟页面, monkeypatch):
        from pages.推广页 import 推广页
        from selectors.推广页选择器 import 推广页选择器

        模拟页面.url = "https://yingxiao.pinduoduo.com/goods/promotion/create"
        monkeypatch.setattr(推广页选择器, "推广成功Toast提示", 选择器配置("toast-success"))
        monkeypatch.setattr(推广页选择器, "推广中状态文案", 选择器配置("status-running"))
        模拟页面.query_selector = AsyncMock(return_value=None)

        页面对象 = 推广页(模拟页面)
        页面对象._随机等待 = AsyncMock()
        页面对象._按钮是否仍可见 = AsyncMock(return_value=True)
        页面对象.截图 = AsyncMock(return_value="timeout.png")

        with patch("pages.推广页.time.monotonic", side_effect=[0.0, 0.2, 1.2]), \
                patch("pages.推广页.asyncio.sleep", new=AsyncMock()):
            结果 = await 页面对象.等待推广成功(超时秒数=1)

        assert 结果 is False
        页面对象.截图.assert_awaited_once_with("推广成功检测超时")
