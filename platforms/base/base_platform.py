"""多平台注册表与平台基类。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


_平台注册表: Dict[str, "BasePlatform"] = {}


def register_platform(platform_id: str):
    """装饰器：注册一个平台到全局注册表。"""

    def decorator(cls):
        _平台注册表[platform_id] = cls()
        return cls

    return decorator


def get_platform(platform_id: str) -> "BasePlatform":
    """根据平台 ID 获取注册实例。"""
    if platform_id not in _平台注册表:
        raise ValueError(f"未注册的平台: {platform_id}")
    return _平台注册表[platform_id]


def list_platforms() -> List[Dict[str, str]]:
    """返回全部已注册平台的精简信息。"""
    return [
        {
            "id": 平台ID,
            "name": 平台.display_name,
            "icon": 平台.icon,
        }
        for 平台ID, 平台 in _平台注册表.items()
    ]


class BasePlatform(ABC):
    """平台基类。"""

    @property
    @abstractmethod
    def platform_id(self) -> str:
        """平台唯一标识。"""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """平台显示名称。"""

    @property
    def icon(self) -> str:
        """平台图标。"""
        return "🏪"

    @property
    @abstractmethod
    def login_url(self) -> str:
        """平台登录页地址。"""

    @abstractmethod
    def get_available_tasks(self) -> List[str]:
        """返回平台支持的任务名称列表。"""
