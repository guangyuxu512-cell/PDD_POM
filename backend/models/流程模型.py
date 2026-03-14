"""
流程模型模块

定义 flows 表的数据模型、步骤序列化以及失败策略校验。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, Iterable, Mapping

from backend.models.表结构 import 字段定义, 数据表定义, 生成数据库记录


允许的失败策略 = {"skip_shop", "continue", "log_and_skip", "abort"}
流程字段映射 = {
    "流程ID": "id",
    "名称": "name",
    "步骤": "steps",
    "描述": "description",
    "创建时间": "created_at",
    "更新时间": "updated_at",
}


def 校验失败策略(失败策略: str) -> None:
    """校验流程步骤的 on_fail 配置。"""
    if 失败策略 in 允许的失败策略:
        return

    if 失败策略.startswith("retry:"):
        重试次数 = 失败策略.split(":", 1)[1]
        if 重试次数.isdigit() and int(重试次数) > 0:
            return

    raise ValueError(
        "流程步骤 on_fail 仅支持 "
        "skip_shop / continue / log_and_skip / retry:N / abort"
    )


@dataclass(slots=True)
class 流程步骤:
    """单个流程步骤定义。"""

    任务: str
    失败策略: str = "abort"
    同步屏障: bool = False
    合并执行: bool = False

    def __post_init__(self) -> None:
        if not self.任务:
            raise ValueError("流程步骤 task 不能为空")
        校验失败策略(self.失败策略)
        if self.合并执行 and not self.同步屏障:
            raise ValueError("merge=true 时 barrier 必须为 true")

    def 转字典(self) -> dict[str, object]:
        """转换为数据库 JSON 使用的英文键名。"""
        return {
            "task": self.任务,
            "on_fail": self.失败策略,
            "barrier": self.同步屏障,
            "merge": self.合并执行,
        }


def 标准化步骤列表(步骤列表: Iterable[流程步骤 | Mapping[str, Any]]) -> list[流程步骤]:
    """将步骤配置统一转换为流程步骤对象列表。"""
    标准步骤: list[流程步骤] = []

    for 步骤 in 步骤列表:
        if isinstance(步骤, 流程步骤):
            标准步骤.append(步骤)
            continue

        任务 = str(步骤.get("task", "")).strip()
        失败策略 = str(步骤.get("on_fail", "abort")).strip() or "abort"
        同步屏障 = bool(步骤.get("barrier", False))
        合并执行 = bool(步骤.get("merge", False))
        标准步骤.append(
            流程步骤(
                任务=任务,
                失败策略=失败策略,
                同步屏障=同步屏障,
                合并执行=合并执行,
            )
        )

    if not 标准步骤:
        raise ValueError("流程 steps 至少需要一个步骤")

    return 标准步骤


@dataclass(slots=True)
class 流程模型:
    """flows 表对应的数据模型。"""

    流程ID: str
    名称: str
    步骤: list[流程步骤 | Mapping[str, Any]]
    描述: str | None = None
    创建时间: datetime | None = None
    更新时间: datetime | None = None

    字段映射: ClassVar[dict[str, str]] = 流程字段映射

    def __post_init__(self) -> None:
        if not self.流程ID:
            raise ValueError("流程 ID 不能为空")
        if not self.名称:
            raise ValueError("流程名称不能为空")
        self.步骤 = 标准化步骤列表(self.步骤)

    def 转数据库记录(self) -> dict[str, object]:
        """转换为数据库记录，步骤字段会序列化为 JSON。"""
        记录 = 生成数据库记录(self, self.字段映射)
        记录["steps"] = json.dumps(
            [步骤.转字典() for 步骤 in self.步骤],
            ensure_ascii=False,
        )
        return 记录


def 创建流程表定义() -> 数据表定义:
    """创建 flows 表结构定义。"""
    return 数据表定义(
        表名="flows",
        字段列表=(
            字段定义("流程ID", "id", "TEXT", 主键=True),
            字段定义("名称", "name", "TEXT", 非空=True),
            字段定义("步骤", "steps", "TEXT", 非空=True),
            字段定义("描述", "description", "TEXT"),
            字段定义("创建时间", "created_at", "DATETIME", 默认值SQL="CURRENT_TIMESTAMP"),
            字段定义("更新时间", "updated_at", "DATETIME", 默认值SQL="CURRENT_TIMESTAMP"),
        ),
    )


流程表定义 = 创建流程表定义()


__all__ = [
    "流程步骤",
    "流程模型",
    "流程字段映射",
    "流程表定义",
    "允许的失败策略",
    "校验失败策略",
    "标准化步骤列表",
    "创建流程表定义",
]
