"""通用工具模块。"""

from __future__ import annotations

from importlib import import_module
from typing import Any


_导出映射 = {
    "decrypt_value": ("backend.utils.crypto", "decrypt_value"),
    "encrypt_value": ("backend.utils.crypto", "encrypt_value"),
    "get_setting": ("backend.utils.settings", "get_setting"),
    "get_setting_bool": ("backend.utils.settings", "get_setting_bool"),
    "get_setting_int": ("backend.utils.settings", "get_setting_int"),
    "ensure_settings_schema": ("backend.utils.settings", "ensure_settings_schema"),
    "list_settings": ("backend.utils.settings", "list_settings"),
    "update_setting": ("backend.utils.settings", "update_setting"),
    "batch_update_settings": ("backend.utils.settings", "batch_update_settings"),
}


def __getattr__(名称: str) -> Any:
    if 名称 not in _导出映射:
        raise AttributeError(名称)

    模块路径, 属性名 = _导出映射[名称]
    模块 = import_module(模块路径)
    值 = getattr(模块, 属性名)
    globals()[名称] = 值
    return 值


__all__ = list(_导出映射)
