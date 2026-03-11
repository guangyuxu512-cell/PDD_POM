"""
数据表结构定义模块

提供轻量级表结构声明，供数据库初始化时生成建表 SQL。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class 字段定义:
    """定义单个数据表字段。"""

    属性名: str
    列名: str
    列类型: str
    非空: bool = False
    主键: bool = False
    自增: bool = False
    默认值SQL: str | None = None

    def 生成SQL(self) -> str:
        """生成当前字段的建表 SQL 片段。"""
        片段 = [self.列名, self.列类型]

        if self.主键:
            片段.append("PRIMARY KEY")
        if self.自增:
            片段.append("AUTOINCREMENT")
        if self.非空:
            片段.append("NOT NULL")
        if self.默认值SQL is not None:
            片段.append(f"DEFAULT {self.默认值SQL}")

        return " ".join(片段)


@dataclass(frozen=True, slots=True)
class 数据表定义:
    """定义一张数据表的结构。"""

    表名: str
    字段列表: tuple[字段定义, ...]
    表级约束: tuple[str, ...] = ()

    @property
    def 属性到列名映射(self) -> dict[str, str]:
        """返回中文属性名到英文列名的映射。"""
        return {字段.属性名: 字段.列名 for 字段 in self.字段列表}

    def 生成建表SQL(self) -> str:
        """生成 CREATE TABLE IF NOT EXISTS 语句。"""
        字段SQL列表 = [字段.生成SQL() for 字段 in self.字段列表]
        字段SQL列表.extend(self.表级约束)
        字段定义文本 = ",\n                ".join(字段SQL列表)
        return f"""
            CREATE TABLE IF NOT EXISTS {self.表名} (
                {字段定义文本}
            )
        """


def 序列化时间值(值: Any) -> Any:
    """将 datetime 转成 SQLite 更容易接受的时间字符串。"""
    if isinstance(值, datetime):
        return 值.isoformat(sep=" ", timespec="seconds")
    return 值


def 生成数据库记录(模型对象: Any, 字段映射: Mapping[str, str]) -> dict[str, Any]:
    """按字段映射将中文属性对象转换为英文列名字典。"""
    记录: dict[str, Any] = {}

    for 属性名, 列名 in 字段映射.items():
        记录[列名] = 序列化时间值(getattr(模型对象, 属性名))

    return 记录


__all__ = [
    "字段定义",
    "数据表定义",
    "序列化时间值",
    "生成数据库记录",
]
