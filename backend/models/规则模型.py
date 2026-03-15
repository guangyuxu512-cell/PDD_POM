"""通用规则模型。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar

import aiosqlite

from backend.models.表结构 import 字段定义, 数据表定义, 生成数据库记录


规则字段映射 = {
    "规则ID": "id",
    "名称": "name",
    "平台": "platform",
    "业务": "business",
    "店铺ID": "shop_id",
    "优先级": "priority",
    "条件组": "conditions",
    "动作列表": "actions",
    "是否启用": "enabled",
    "创建时间": "created_at",
    "更新时间": "updated_at",
}


@dataclass(slots=True)
class 规则模型:
    """rules 表对应的数据模型。"""

    规则ID: int | None
    名称: str
    平台: str = "*"
    业务: str = ""
    店铺ID: str = "*"
    优先级: int = 0
    条件组: dict[str, Any] | str | None = None
    动作列表: list[dict[str, Any]] | str | None = None
    是否启用: bool = True
    创建时间: datetime | None = None
    更新时间: datetime | None = None

    字段映射: ClassVar[dict[str, str]] = 规则字段映射

    def __post_init__(self) -> None:
        if not self.名称:
            raise ValueError("规则名称不能为空")
        if not self.业务:
            raise ValueError("业务类型不能为空")
        if self.条件组 in (None, ""):
            self.条件组 = {}
        if self.动作列表 in (None, ""):
            self.动作列表 = []

    def 转数据库记录(self) -> dict[str, Any]:
        """转换为数据库记录。"""
        记录 = 生成数据库记录(self, self.字段映射)
        记录["conditions"] = json.dumps(
            self.条件组 if isinstance(self.条件组, dict) else json.loads(str(self.条件组 or "{}")),
            ensure_ascii=False,
        )
        记录["actions"] = json.dumps(
            self.动作列表 if isinstance(self.动作列表, list) else json.loads(str(self.动作列表 or "[]")),
            ensure_ascii=False,
        )
        记录["enabled"] = 1 if self.是否启用 else 0
        return 记录


def 创建规则表定义() -> 数据表定义:
    """创建 rules 表结构定义。"""
    return 数据表定义(
        表名="rules",
        字段列表=(
            字段定义("规则ID", "id", "INTEGER", 主键=True, 自增=True),
            字段定义("名称", "name", "TEXT", 非空=True),
            字段定义("平台", "platform", "TEXT", 非空=True, 默认值SQL="'*'"),
            字段定义("业务", "business", "TEXT", 非空=True),
            字段定义("店铺ID", "shop_id", "TEXT", 非空=True, 默认值SQL="'*'"),
            字段定义("优先级", "priority", "INTEGER", 非空=True, 默认值SQL="0"),
            字段定义("条件组", "conditions", "TEXT", 非空=True, 默认值SQL="'{}'"),
            字段定义("动作列表", "actions", "TEXT", 非空=True, 默认值SQL="'[]'"),
            字段定义("是否启用", "enabled", "INTEGER", 非空=True, 默认值SQL="1"),
            字段定义("创建时间", "created_at", "TEXT", 非空=True, 默认值SQL="(datetime('now', 'localtime'))"),
            字段定义("更新时间", "updated_at", "TEXT", 非空=True, 默认值SQL="(datetime('now', 'localtime'))"),
        ),
    )


规则表定义 = 创建规则表定义()
建表SQL = """
CREATE TABLE IF NOT EXISTS rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    platform    TEXT NOT NULL DEFAULT '*',
    business    TEXT NOT NULL,
    shop_id     TEXT NOT NULL DEFAULT '*',
    priority    INTEGER NOT NULL DEFAULT 0,
    conditions  TEXT NOT NULL DEFAULT '{}',
    actions     TEXT NOT NULL DEFAULT '[]',
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""


async def 初始化规则表(连接: aiosqlite.Connection | None = None) -> None:
    """初始化规则表。"""
    if 连接 is not None:
        await 连接.execute(建表SQL)
        return

    from backend.models.数据库 import 获取连接

    async with 获取连接() as 数据库连接:
        await 数据库连接.execute(建表SQL)
        await 数据库连接.commit()


__all__ = [
    "规则模型",
    "规则字段映射",
    "规则表定义",
    "建表SQL",
    "初始化规则表",
    "创建规则表定义",
]
