"""
微信页测试
"""
from __future__ import annotations

from types import SimpleNamespace


class 假值模式:
    def __init__(self):
        self.值 = None

    def SetValue(self, 值: str):
        self.值 = 值


class 假控件:
    def __init__(self, *, 存在: bool = True):
        self._存在 = 存在
        self._值模式 = 假值模式()
        self.按键列表: list[str] = []
        self.激活次数 = 0
        self.置顶记录: list[bool] = []

    def Exists(self, maxSearchSeconds: float = 3):
        return self._存在

    def GetValuePattern(self):
        return self._值模式

    def SendKeys(self, 键: str):
        self.按键列表.append(键)

    def SetActive(self):
        self.激活次数 += 1

    def SetTopmost(self, 值: bool):
        self.置顶记录.append(值)


class 测试_微信页:
    def test_激活窗口_窗口不存在时返回False(self, monkeypatch):
        from pages import 微信页 as 微信页模块

        monkeypatch.setattr(微信页模块, "uia", None)
        页面对象 = 微信页模块.微信页()
        页面对象._窗口 = 假控件(存在=False)

        assert 页面对象.激活窗口() is False

    def test_搜索联系人_按顺序点击搜索输入并打开联系人(self, monkeypatch):
        from pages.微信页 import 微信页

        页面对象 = 微信页()
        monkeypatch.setattr(页面对象, "点击", lambda 配置: 配置.名称 in {"搜索", "张三"})
        monkeypatch.setattr(页面对象, "输入文本", lambda *_args, **_kwargs: True)
        monkeypatch.setattr(页面对象, "_随机等待", lambda *_args: None)

        assert 页面对象.搜索联系人("张三") is True

    def test_发送消息到当前聊天_发送按钮失败时回退Enter(self, monkeypatch):
        from pages.微信页 import 微信页
        from selectors.微信选择器 import 微信选择器

        聊天框 = 假控件()
        页面对象 = 微信页()
        monkeypatch.setattr(页面对象, "激活窗口", lambda: True)
        monkeypatch.setattr(页面对象, "输入文本", lambda *_args, **_kwargs: True)
        monkeypatch.setattr(
            页面对象,
            "点击",
            lambda 配置: False if 配置 is 微信选择器.发送按钮 else True,
        )
        monkeypatch.setattr(页面对象, "查找", lambda 配置: 聊天框 if 配置 is 微信选择器.聊天输入框 else None)
        monkeypatch.setattr(页面对象, "_随机等待", lambda *_args: None)

        assert 页面对象.发送消息到当前聊天("你好") is True
        assert 聊天框.按键列表 == ["{Enter}"]

    def test_发送消息_窗口激活或搜索失败时返回False(self, monkeypatch):
        from pages.微信页 import 微信页

        页面对象 = 微信页()
        monkeypatch.setattr(页面对象, "激活窗口", lambda: False)
        assert 页面对象.发送消息("张三", "你好") is False

        monkeypatch.setattr(页面对象, "激活窗口", lambda: True)
        monkeypatch.setattr(页面对象, "搜索联系人", lambda _联系人: False)
        assert 页面对象.发送消息("张三", "你好") is False

    def test_初始化_使用微信窗口配置(self, monkeypatch):
        from pages import 微信页 as 微信页模块

        捕获参数: dict[str, object] = {}

        def 假窗口控件(**kwargs):
            捕获参数.update(kwargs)
            return 假控件()

        monkeypatch.setattr(微信页模块, "uia", SimpleNamespace(WindowControl=假窗口控件))

        页面对象 = 微信页模块.微信页()

        assert isinstance(页面对象._窗口, 假控件)
        assert 捕获参数 == {"Name": "微信", "ClassName": "WeChatMainWndForPC"}
