"""淘宝平台定义。"""
from __future__ import annotations

from platforms.base.base_platform import BasePlatform, register_platform


@register_platform("taobao")
class TaoBaoPlatform(BasePlatform):
    """淘宝电商平台。"""

    @property
    def platform_id(self) -> str:
        return "taobao"

    @property
    def display_name(self) -> str:
        return "淘宝"

    @property
    def icon(self) -> str:
        return "🟧"

    @property
    def login_url(self) -> str:
        return "https://myseller.taobao.com/"

    def get_available_tasks(self) -> list[str]:
        return []
