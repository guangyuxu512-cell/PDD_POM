"""
任务注册表模块

提供任务注册、自动发现与查询能力。
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Any, Optional, Type


任务注册表: dict[str, dict[str, Any]] = {}
排除模块 = {
    "__init__",
    "注册表",
    "任务注册表",
    "基础任务",
    "celery应用",
    "桥接任务",
    "执行任务",
    "定时任务",
}


def register_task(
    名称: str,
    描述: str,
    *,
    requires_input: bool = False,
    required_fields: Optional[list[str]] = None,
    supports_empty_context: bool = True,
):
    """
    注册任务装饰器。

    参数:
        名称: 任务显示名称
        描述: 任务说明
    """
    if not 名称:
        raise ValueError("任务名称不能为空")
    if not 描述:
        raise ValueError("任务描述不能为空")

    def 装饰器(任务类: Type[Any]) -> Type[Any]:
        任务注册表[名称] = {
            "class": 任务类,
            "description": 描述,
            "requires_input": bool(requires_input),
            "required_fields": list(required_fields or []),
            "supports_empty_context": bool(supports_empty_context),
        }
        print(f"[任务注册] {名称} - {描述}")
        return 任务类

    return 装饰器


注册任务 = register_task


def 获取所有任务() -> list[dict[str, str]]:
    """
    获取所有已注册任务的前端展示信息。

    返回:
        list[dict[str, str]]: 任务列表
    """
    return [
        {
            "name": 名称,
            "description": str(信息["description"]),
        }
        for 名称, 信息 in 任务注册表.items()
    ]


def 获取任务类(名称: str) -> Type[Any]:
    """
    根据名称获取任务类。

    参数:
        名称: 任务名称

    返回:
        Type[Any]: 对应任务类
    """
    if 名称 not in 任务注册表:
        raise KeyError(f"任务未注册: {名称}，可用任务: {list(任务注册表.keys())}")
    return 任务注册表[名称]["class"]


def 获取任务元数据(名称: str) -> dict[str, Any]:
    """根据名称获取任务元数据。"""
    if 名称 not in 任务注册表:
        raise KeyError(f"任务未注册: {名称}，可用任务: {list(任务注册表.keys())}")

    信息 = 任务注册表[名称]
    return {
        "requires_input": bool(信息.get("requires_input", False)),
        "required_fields": list(信息.get("required_fields") or []),
        "supports_empty_context": bool(信息.get("supports_empty_context", True)),
    }


def 获取任务(名称: str) -> Any:
    """
    根据名称获取任务实例。

    参数:
        名称: 任务名称

    返回:
        Any: 任务实例
    """
    return 获取任务类(名称)()


def 清空任务注册表() -> None:
    """清空注册表，供测试场景使用。"""
    任务注册表.clear()


def _列出任务模块() -> list[str]:
    """列出 tasks 目录下需要自动导入的任务模块。"""
    模块目录 = Path(__file__).resolve().parent
    模块列表: list[str] = []

    for 模块信息 in pkgutil.iter_modules([str(模块目录)]):
        if 模块信息.name in 排除模块:
            continue
        模块列表.append(模块信息.name)

    模块列表.sort()
    return 模块列表


def 初始化任务注册表() -> None:
    """
    初始化任务注册表。

    自动导入 tasks 目录下的任务模块，触发装饰器注册。
    """
    if 任务注册表:
        print(f"[任务注册表初始化完成] 已注册 {len(任务注册表)} 个任务")
        return

    for 模块名 in _列出任务模块():
        完整模块名 = f"tasks.{模块名}"
        if 完整模块名 in sys.modules:
            importlib.reload(sys.modules[完整模块名])
        else:
            importlib.import_module(完整模块名)

    print(f"[任务注册表初始化完成] 已注册 {len(任务注册表)} 个任务")


__all__ = [
    "任务注册表",
    "register_task",
    "注册任务",
    "获取所有任务",
    "获取任务类",
    "获取任务元数据",
    "获取任务",
    "清空任务注册表",
    "初始化任务注册表",
]
