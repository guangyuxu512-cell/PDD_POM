"""
选择器提取单元测试
"""
import importlib
import importlib.util
from pathlib import Path
import sys
import sysconfig
from unittest.mock import AsyncMock, MagicMock

import pytest


class 测试_选择器提取:
    """测试 selectors 包导入兼容和回退链路。"""

    def test_基础页导入时兼容标准库selectors模块(self):
        原始选择器模块 = sys.modules.get("selectors")
        原始基础页模块 = sys.modules.get("pages.基础页")
        原始基础页选择器模块 = sys.modules.get("selectors.基础页选择器")

        try:
            sys.modules.pop("pages.基础页", None)
            sys.modules.pop("selectors.基础页选择器", None)

            标准库选择器文件 = Path(sysconfig.get_path("stdlib")) / "selectors.py"
            标准库选择器规格 = importlib.util.spec_from_file_location("selectors", 标准库选择器文件)
            assert 标准库选择器规格 is not None
            assert 标准库选择器规格.loader is not None

            标准库选择器模块 = importlib.util.module_from_spec(标准库选择器规格)
            标准库选择器规格.loader.exec_module(标准库选择器模块)
            sys.modules["selectors"] = 标准库选择器模块

            importlib.import_module("pages.基础页")
            当前选择器模块 = sys.modules["selectors"]

            assert hasattr(当前选择器模块, "__path__")
            assert hasattr(当前选择器模块, "DefaultSelector")

            基础页选择器模块 = importlib.import_module("selectors.基础页选择器")
            assert 基础页选择器模块.基础页选择器.通用弹窗关闭按钮 == [
                "[data-testid='beast-core-icon-close']",
                ".ant-modal-close",
            ]
        finally:
            sys.modules.pop("pages.基础页", None)
            sys.modules.pop("selectors.基础页选择器", None)

            if 原始基础页模块 is not None:
                sys.modules["pages.基础页"] = 原始基础页模块
            if 原始基础页选择器模块 is not None:
                sys.modules["selectors.基础页选择器"] = 原始基础页选择器模块
            if 原始选择器模块 is not None:
                sys.modules["selectors"] = 原始选择器模块
            else:
                sys.modules.pop("selectors", None)

    @pytest.mark.asyncio
    async def test_商品列表页搜索类型下拉按选择器列表回退(self, monkeypatch):
        from pages.商品列表页 import 商品列表页
        from selectors.商品列表页选择器 import 商品列表页选择器

        模拟页面 = MagicMock()
        模拟页面.mouse = MagicMock()
        模拟页面.mouse.move = AsyncMock()
        模拟页面.mouse.click = AsyncMock()
        模拟页面.mouse.down = AsyncMock()
        模拟页面.mouse.up = AsyncMock()
        模拟页面.mouse.wheel = AsyncMock()
        模拟页面.keyboard = MagicMock()
        模拟页面.keyboard.type = AsyncMock()
        模拟页面.keyboard.press = AsyncMock()
        模拟页面.get_by_text = MagicMock()

        第一个下拉 = MagicMock()
        第一个下拉.click = AsyncMock(side_effect=Exception("bad selector"))
        第一个入口 = MagicMock()
        第一个入口.first = 第一个下拉

        第二个下拉 = MagicMock()
        第二个下拉.click = AsyncMock()
        第二个入口 = MagicMock()
        第二个入口.first = 第二个下拉

        模拟页面.locator.side_effect = lambda 选择器: {
            "bad-selector": 第一个入口,
            "good-selector": 第二个入口,
        }[选择器]

        monkeypatch.setattr(商品列表页选择器, "搜索类型下拉CSS列表", ["bad-selector", "good-selector"])
        monkeypatch.setattr(商品列表页选择器, "搜索类型下拉文本列表", [])

        页面对象 = 商品列表页(模拟页面)

        await 页面对象._点击搜索类型下拉()

        第一个下拉.click.assert_awaited_once_with(timeout=10000)
        第二个下拉.click.assert_awaited_once_with(timeout=10000)
