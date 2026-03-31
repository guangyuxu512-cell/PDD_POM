"""抖音平台定义。"""
from __future__ import annotations

from platforms.base.base_platform import BasePlatform, register_platform


@register_platform("douyin")
class DouyinPlatform(BasePlatform):
    """抖音电商平台。"""

    @property
    def platform_id(self) -> str:
        return "douyin"

    @property
    def display_name(self) -> str:
        return "抖音"

    @property
    def icon(self) -> str:
        return "🎵"

    @property
    def login_url(self) -> str:
        return "https://fxg.jinritemai.com/login/common"

    def get_available_tasks(self) -> list[str]:
        return []
