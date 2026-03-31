"""平台基类导出。"""

from platforms.base.base_platform import (
    BasePlatform,
    get_platform,
    list_platforms,
    register_platform,
)

__all__ = [
    "BasePlatform",
    "get_platform",
    "list_platforms",
    "register_platform",
]
