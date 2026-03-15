"""微信桌面版页面对象。"""
from __future__ import annotations

from typing import Any, Optional

try:
    import uiautomation as uia
except ImportError:  # pragma: no cover - 依赖缺失时走兜底
    uia = None

from pages.桌面基础页 import 桌面基础页
from selectors.微信选择器 import 微信选择器


class 微信页(桌面基础页):
    """微信 PC 版操作页面。"""

    def __init__(self):
        微信窗口: Optional[Any] = None
        if uia is not None:
            窗口控件类型 = getattr(uia, "WindowControl", None)
            if callable(窗口控件类型):
                微信窗口 = 窗口控件类型(Name="微信", ClassName="WeChatMainWndForPC")
        super().__init__(微信窗口)

    def 激活窗口(self) -> bool:
        """将微信窗口置顶激活。"""
        if not self._窗口 or not self._窗口.Exists(maxSearchSeconds=5):
            print("[微信页] 微信窗口未找到，请确认微信已登录")
            return False
        self._窗口.SetActive()
        self._窗口.SetTopmost(True)
        self._随机等待(0.5, 1.0)
        self._窗口.SetTopmost(False)
        return True

    def 搜索联系人(self, 联系人: str) -> bool:
        """通过搜索框搜索联系人并打开聊天。"""
        if not self.点击(微信选择器.搜索按钮):
            print("[微信页] 搜索按钮未找到")
            return False
        self._随机等待(0.5, 1.0)

        if not self.输入文本(微信选择器.搜索输入框, 联系人):
            print("[微信页] 搜索输入框未找到")
            return False
        self._随机等待(1.0, 2.0)

        联系人选择器 = 微信选择器.获取联系人项(联系人)
        if not self.点击(联系人选择器):
            print(f"[微信页] 联系人未找到: {联系人}")
            return False
        self._随机等待(0.5, 1.0)
        return True

    def 发送消息(self, 联系人: str, 消息: str) -> bool:
        """搜索联系人并发送文本消息。"""
        if not self.激活窗口():
            return False
        if not self.搜索联系人(联系人):
            return False
        return self.发送消息到当前聊天(消息)

    def 发送消息到当前聊天(self, 消息: str) -> bool:
        """在当前已打开的聊天窗口直接发送消息。"""
        if not self.激活窗口():
            return False

        if not self.输入文本(微信选择器.聊天输入框, 消息, 清空=True):
            print("[微信页] 聊天输入框未找到")
            return False
        self._随机等待(0.3, 0.8)

        if not self.点击(微信选择器.发送按钮):
            聊天框 = self.查找(微信选择器.聊天输入框)
            if 聊天框:
                聊天框.SendKeys("{Enter}")
            else:
                print("[微信页] 发送按钮和 Enter 都失败")
                return False

        self._随机等待(1.0, 2.0)
        print("[微信页] 已发送消息到当前聊天")
        return True
