"""
定时任务模型模块

定义 execution_schedules 表的数据模型以及店铺列表序列化逻辑。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Iterable

from backend.models.表结构 import 字段定义, 数据表定义, 生成数据库记录


定时任务字段映射 = {
    "计划ID": "id",
    "名称": "name",
    "流程ID": "flow_id",
    "店铺ID列表": "shop_ids",
    "并发数": "concurrency",
    "间隔秒数": "interval_seconds",
    "Cron表达式": "cron_expr",
    "重叠策略": "overlap_policy",
    "启用": "enabled",
    "上次运行时间": "last_run_at",
    "下次运行时间": "next_run_at",
    "创建时间": "created_at",
    "更新时间": "updated_at",
}


def 标准化店铺ID列表(店铺ID列表: Iterable[str]) -> list[str]:
    """校验并标准化店铺 ID 列表。"""
    标准结果: list[str] = []

    for 店铺ID in 店铺ID列表:
        if not isinstance(店铺ID, str) or not 店铺ID.strip():
            raise ValueError("shop_ids 必须是非空字符串列表")
        标准结果.append(店铺ID.strip())

    if not 标准结果:
        raise ValueError("shop_ids 不能为空")

    return 标准结果


@dataclass(slots=True)
class 定时任务模型:
    """execution_schedules 表对应的数据模型。"""

    计划ID: str
    名称: str
    流程ID: str
    店铺ID列表: list[str]
    并发数: int = 3
    间隔秒数: int | None = None
    Cron表达式: str | None = None
    重叠策略: str = "wait"
    启用: bool = True
    上次运行时间: datetime | None = None
    下次运行时间: datetime | None = None
    创建时间: datetime | None = None
    更新时间: datetime | None = None

    字段映射: ClassVar[dict[str, str]] = 定时任务字段映射

    def __post_init__(self) -> None:
        if not self.计划ID:
            raise ValueError("定时任务 ID 不能为空")
        if not self.名称:
            raise ValueError("定时任务名称不能为空")
        if not self.流程ID:
            raise ValueError("flow_id 不能为空")
        if self.并发数 <= 0:
            raise ValueError("concurrency 必须大于 0")

        self.店铺ID列表 = 标准化店铺ID列表(self.店铺ID列表)

        if self.间隔秒数 is None and not self.Cron表达式:
            raise ValueError("interval_seconds 和 cron_expr 至少要提供一个")
        if self.间隔秒数 is not None and self.间隔秒数 <= 0:
            raise ValueError("interval_seconds 必须大于 0")

    def 转数据库记录(self) -> dict[str, object]:
        """转换为数据库记录，列表和布尔值会按 SQLite 兼容格式写入。"""
        记录 = 生成数据库记录(self, self.字段映射)
        记录["shop_ids"] = json.dumps(self.店铺ID列表, ensure_ascii=False)
        记录["enabled"] = 1 if self.启用 else 0
        return 记录


def 创建定时任务表定义() -> 数据表定义:
    """创建 execution_schedules 表结构定义。"""
    return 数据表定义(
        表名="execution_schedules",
        字段列表=(
            字段定义("计划ID", "id", "TEXT", 主键=True),
            字段定义("名称", "name", "TEXT", 非空=True),
            字段定义("流程ID", "flow_id", "TEXT", 非空=True),
            字段定义("店铺ID列表", "shop_ids", "TEXT", 非空=True),
            字段定义("并发数", "concurrency", "INTEGER", 默认值SQL="3"),
            字段定义("间隔秒数", "interval_seconds", "INTEGER"),
            字段定义("Cron表达式", "cron_expr", "TEXT"),
            字段定义("重叠策略", "overlap_policy", "TEXT", 默认值SQL="'wait'"),
            字段定义("启用", "enabled", "INTEGER", 默认值SQL="1"),
            字段定义("上次运行时间", "last_run_at", "DATETIME"),
            字段定义("下次运行时间", "next_run_at", "DATETIME"),
            字段定义("创建时间", "created_at", "DATETIME", 默认值SQL="CURRENT_TIMESTAMP"),
            字段定义("更新时间", "updated_at", "DATETIME", 默认值SQL="CURRENT_TIMESTAMP"),
        ),
        表级约束=(
            "FOREIGN KEY(flow_id) REFERENCES flows(id)",
        ),
    )


定时任务表定义 = 创建定时任务表定义()


__all__ = [
    "定时任务模型",
    "定时任务字段映射",
    "定时任务表定义",
    "标准化店铺ID列表",
    "创建定时任务表定义",
]
