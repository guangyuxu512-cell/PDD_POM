"""拼多多平台定义。"""
from __future__ import annotations

from platforms.base.base_platform import BasePlatform, register_platform


@register_platform("pdd")
class PddPlatform(BasePlatform):
    """拼多多平台。"""

    @property
    def platform_id(self) -> str:
        return "pdd"

    @property
    def display_name(self) -> str:
        return "拼多多"

    @property
    def icon(self) -> str:
        return "🟠"

    @property
    def login_url(self) -> str:
        return "https://mms.pinduoduo.com/login"

    def get_available_tasks(self) -> list[str]:
        return [
            "登录",
            "售后处理",
            "发布相似商品",
            "发布换图商品",
            "限时限量",
            "设置推广",
        ]
