"""
桌面基础页测试
"""
from __future__ import annotations

from pathlib import Path

from selectors.桌面选择器配置 import 桌面选择器配置


class 假值模式:
    def __init__(self):
        self.值 = None

    def SetValue(self, 值: str):
        self.值 = 值


class 假控件:
    def __init__(self, *, 存在: bool = True, 名称: str = "控件"):
        self._存在 = 存在
        self.Name = 名称
        self._值模式 = 假值模式()
        self.点击次数 = 0
        self.按键列表: list[str] = []
        self.截图路径: str | None = None
        self.激活次数 = 0
        self.置顶记录: list[bool] = []

    def Exists(self, maxSearchSeconds: float = 3):
        return self._存在

    def Click(self):
        self.点击次数 += 1

    def GetValuePattern(self):
        return self._值模式

    def SendKeys(self, 键: str):
        self.按键列表.append(键)

    def CaptureToImage(self, 路径: str):
        self.截图路径 = 路径

    def SetActive(self):
        self.激活次数 += 1

    def SetTopmost(self, 值: bool):
        self.置顶记录.append(值)


class 假搜索范围:
    def __init__(self, 映射: dict[str, object]):
        self._映射 = 映射

    def __getattr__(self, 名称: str):
        if 名称 not in self._映射:
            raise AttributeError(名称)

        返回值 = self._映射[名称]

        def _方法(**_kwargs):
            return 返回值

        return _方法


class 测试_桌面选择器配置:
    def test_所有配置_包含主配置与备选(self):
        备选 = 桌面选择器配置(控件类型="EditControl", 名称="备选")
        主配置 = 桌面选择器配置(控件类型="ButtonControl", 名称="主用", 备选=[备选])

        结果 = 主配置.所有配置()

        assert 结果 == [主配置, 备选]


class 测试_桌面基础页:
    def test_查找_按主配置和备选回退(self):
        from pages.桌面基础页 import 桌面基础页

        失败控件 = 假控件(存在=False)
        成功控件 = 假控件()
        页面对象 = 桌面基础页(假搜索范围({
            "ButtonControl": 失败控件,
            "EditControl": 成功控件,
        }))
        配置 = 桌面选择器配置(
            控件类型="ButtonControl",
            名称="主用",
            备选=[桌面选择器配置(控件类型="EditControl", 名称="备选")],
        )

        assert 页面对象.查找(配置) is 成功控件

    def test_输入文本_清空后逐字发送(self, monkeypatch):
        from pages.桌面基础页 import 桌面基础页

        控件 = 假控件()
        页面对象 = 桌面基础页(假搜索范围({"EditControl": 控件}))
        monkeypatch.setattr(页面对象, "_随机等待", lambda *_args: None)

        结果 = 页面对象.输入文本(桌面选择器配置(控件类型="EditControl", 名称="输入"), "微信")

        assert 结果 is True
        assert 控件.GetValuePattern().值 == ""
        assert 控件.按键列表 == ["微", "信"]

    def test_点击和截图_使用窗口控件(self, tmp_path: Path, monkeypatch):
        from pages import 桌面基础页 as 桌面基础页模块

        控件 = 假控件()
        monkeypatch.setattr(桌面基础页模块.配置实例, "DATA_DIR", str(tmp_path))
        页面对象 = 桌面基础页模块.桌面基础页(控件)
        monkeypatch.setattr(页面对象, "_随机等待", lambda *_args: None)
        monkeypatch.setattr(页面对象, "查找", lambda *_args, **_kwargs: 控件)

        assert 页面对象.点击(桌面选择器配置(控件类型="WindowControl")) is True
        路径 = 页面对象.截图("桌面测试")

        assert 控件.点击次数 == 1
        assert 路径.endswith(".png")
        assert Path(路径).parent == tmp_path / "screenshots"
        assert 控件.截图路径 == 路径
