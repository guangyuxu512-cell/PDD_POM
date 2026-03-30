"""桌面应用选择器配置基类。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class 桌面选择器配置:
    """保存桌面控件定位属性。"""

    控件类型: str
    名称: Optional[str] = None
    自动化ID: Optional[str] = None
    类名: Optional[str] = None
    深度: int = 0
    备选: List["桌面选择器配置"] = field(default_factory=list)

    def 所有配置(self) -> List["桌面选择器配置"]:
        """按主配置优先返回全部候选配置。"""
        return [self] + list(self.备选)
