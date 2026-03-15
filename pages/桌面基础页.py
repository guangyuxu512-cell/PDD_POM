"""桌面应用页面对象模型基类。"""
from __future__ import annotations

import importlib.util
import random
import time
from pathlib import Path
from typing import Any, Optional
import sys

from backend.配置 import 配置实例

if "selectors" in sys.modules and not hasattr(sys.modules["selectors"], "__path__"):
    选择器包目录 = Path(__file__).resolve().parents[1] / "selectors"
    选择器初始化文件 = 选择器包目录 / "__init__.py"
    选择器规格 = importlib.util.spec_from_file_location(
        "selectors",
        选择器初始化文件,
        submodule_search_locations=[str(选择器包目录)],
    )
    if 选择器规格 is None or 选择器规格.loader is None:
        raise ImportError("无法加载项目 selectors 包")
    选择器模块 = importlib.util.module_from_spec(选择器规格)
    sys.modules["selectors"] = 选择器模块
    选择器规格.loader.exec_module(选择器模块)

try:
    import uiautomation as uia
except ImportError:  # pragma: no cover - 依赖缺失时走兜底
    uia = None

from selectors.桌面选择器配置 import 桌面选择器配置


class 桌面基础页:
    """桌面应用 POM 基类，所有桌面页面类继承此类。"""

    def __init__(self, 窗口控件: Optional[Any] = None):
        self._窗口 = 窗口控件

    def _获取根控件(self) -> Optional[Any]:
        if self._窗口 is not None:
            return self._窗口
        if uia is None:
            return None
        获取根控件 = getattr(uia, "GetRootControl", None)
        if not callable(获取根控件):
            return None
        return 获取根控件()

    def _查找控件(self, 配置: 桌面选择器配置, 父控件: Optional[Any] = None) -> Optional[Any]:
        """根据桌面选择器配置查找控件。"""
        搜索范围 = 父控件 or self._获取根控件()
        if 搜索范围 is None:
            return None

        搜索参数: dict[str, Any] = {}
        if 配置.深度 > 0:
            搜索参数["searchDepth"] = 配置.深度
        if 配置.名称:
            搜索参数["Name"] = 配置.名称
        if 配置.自动化ID:
            搜索参数["AutomationId"] = 配置.自动化ID
        if 配置.类名:
            搜索参数["ClassName"] = 配置.类名

        控件类型方法 = getattr(搜索范围, 配置.控件类型, None)
        if not callable(控件类型方法):
            return None
        return 控件类型方法(**搜索参数)

    def 查找(self, 配置: 桌面选择器配置, 父控件: Optional[Any] = None) -> Optional[Any]:
        """按主配置和备选配置依次查找控件。"""
        for 单个配置 in 配置.所有配置():
            try:
                控件 = self._查找控件(单个配置, 父控件)
                if 控件 and 控件.Exists(maxSearchSeconds=3):
                    return 控件
            except Exception:
                continue
        return None

    def 点击(self, 配置: 桌面选择器配置) -> bool:
        """查找并点击控件。"""
        控件 = self.查找(配置)
        if not 控件:
            print(f"[桌面基础页] 未找到控件: {配置.名称 or 配置.控件类型}")
            return False
        控件.Click()
        self.操作后延迟()
        return True

    def 输入文本(self, 配置: 桌面选择器配置, 文本: str, 清空: bool = True) -> bool:
        """查找控件并输入文本。"""
        控件 = self.查找(配置)
        if not 控件:
            print(f"[桌面基础页] 未找到输入控件: {配置.名称 or 配置.控件类型}")
            return False

        if 清空:
            try:
                值模式 = 控件.GetValuePattern()
                值模式.SetValue("")
            except Exception:
                pass

        for 字符 in 文本:
            控件.SendKeys(字符)
            time.sleep(random.uniform(0.05, 0.15))

        self._随机等待(0.3, 0.5)
        return True

    def 获取文本(self, 配置: 桌面选择器配置) -> str:
        """获取控件文本。"""
        控件 = self.查找(配置)
        if not 控件:
            return ""
        return str(getattr(控件, "Name", "") or "")

    def 元素是否存在(self, 配置: 桌面选择器配置, 超时秒: float = 3) -> bool:
        """检查控件是否存在。"""
        控件 = self.查找(配置)
        if not 控件:
            return False
        try:
            return bool(控件.Exists(maxSearchSeconds=超时秒))
        except Exception:
            return False

    def 截图(self, 名称: str) -> str:
        """对窗口截图。"""
        截图目录 = Path(配置实例.DATA_DIR) / "screenshots"
        截图目录.mkdir(parents=True, exist_ok=True)
        文件路径 = 截图目录 / f"{名称}_{int(time.time())}.png"

        if self._窗口 is None:
            raise RuntimeError("窗口控件不存在，无法截图")

        self._窗口.CaptureToImage(str(文件路径))
        return str(文件路径)

    @staticmethod
    def _随机等待(最小秒: float = 0.5, 最大秒: float = 2.0):
        """同步随机等待。"""
        time.sleep(random.uniform(最小秒, 最大秒))

    def 操作前延迟(self):
        self._随机等待(0.3, 0.8)

    def 操作后延迟(self):
        self._随机等待(0.8, 2.0)
