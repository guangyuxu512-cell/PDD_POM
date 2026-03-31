"""
系统设置读写工具模块

提供同步 settings 读取、写入与脱敏列表能力，供配置代理和 API 共用。
"""
from __future__ import annotations

import sqlite3
from typing import Any, Iterable

from backend.config import DB_PATH
from backend.models.settings_model import 获取默认设置列表, 设置表定义
from backend.utils.crypto import decrypt_value, encrypt_value


def _open_connection() -> sqlite3.Connection:
    """打开同步 SQLite 连接。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_settings_schema() -> None:
    """确保 settings 表和默认配置存在。"""
    with _open_connection() as connection:
        connection.execute(设置表定义.生成建表SQL())
        for 设置项 in 获取默认设置列表():
            记录 = 设置项.转数据库记录()
            connection.execute(
                """
                INSERT OR IGNORE INTO settings (
                    key, value, category, encrypted, label, hint, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    记录["key"],
                    记录["value"],
                    记录["category"],
                    记录["encrypted"],
                    记录["label"],
                    记录["hint"],
                ),
            )
        connection.commit()


def get_setting(key: str, default: str | None = None) -> str | None:
    """
    从数据库读取配置值。加密字段自动解密。

    替代原先的环境变量读取，所有业务配置统一从这里读取。
    """
    ensure_settings_schema()

    with _open_connection() as connection:
        row = connection.execute(
            "SELECT value, encrypted FROM settings WHERE key = ?",
            (key,),
        ).fetchone()

    if not row or row["value"] in (None, ""):
        return default

    if row["encrypted"]:
        try:
            return decrypt_value(str(row["value"]))
        except Exception:
            return default

    return str(row["value"])


def get_setting_bool(key: str, default: bool = False) -> bool:
    """读取布尔配置。"""
    value = get_setting(key)
    if value is None:
        return default
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def get_setting_int(key: str, default: int = 0) -> int:
    """读取整数配置。"""
    value = get_setting(key)
    if value is None:
        return default
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def list_settings() -> list[dict[str, Any]]:
    """返回全部设置项，已按前端要求做脱敏。"""
    ensure_settings_schema()

    with _open_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM settings ORDER BY category, key"
        ).fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        if item["encrypted"] and item["value"]:
            item["has_value"] = True
            item["value"] = None
        else:
            item["has_value"] = bool(item["value"])
        result.append(item)
    return result


def _get_setting_meta(connection: sqlite3.Connection, key: str) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT key, encrypted FROM settings WHERE key = ?",
        (key,),
    ).fetchone()


def update_setting(key: str, value: str | None) -> None:
    """更新单个配置项。"""
    ensure_settings_schema()

    with _open_connection() as connection:
        row = _get_setting_meta(connection, key)
        if not row:
            raise KeyError(key)

        stored_value = value
        if row["encrypted"] and value:
            stored_value = encrypt_value(value)

        connection.execute(
            "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
            (stored_value, key),
        )
        connection.commit()


def batch_update_settings(items: Iterable[dict[str, Any]]) -> int:
    """批量更新配置项。"""
    ensure_settings_schema()

    updated_count = 0
    with _open_connection() as connection:
        for item in items:
            key = str(item.get("key") or "").strip()
            if not key:
                continue

            row = _get_setting_meta(connection, key)
            if not row:
                continue

            value = item.get("value")
            if row["encrypted"] and not value:
                continue

            stored_value = value
            if row["encrypted"] and value:
                stored_value = encrypt_value(str(value))

            connection.execute(
                "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
                (stored_value, key),
            )
            updated_count += 1

        connection.commit()

    return updated_count


__all__ = [
    "ensure_settings_schema",
    "get_setting",
    "get_setting_bool",
    "get_setting_int",
    "list_settings",
    "update_setting",
    "batch_update_settings",
]
