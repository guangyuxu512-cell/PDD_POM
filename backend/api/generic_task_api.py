"""
通用任务接口模块

提供任务发现、Schema 查询与参数校验接口。
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body

from backend.models.data_structure import 统一响应, 成功, 失败
from tasks.registry import 任务注册表, 获取任务元数据, 获取所有任务


路由 = APIRouter(prefix="/api/task-registry", tags=["任务注册表"])


@路由.get("/", summary="获取所有已注册任务及其 Schema")
async def 列出已注册任务() -> 统一响应:
    """返回所有已注册任务的元数据。"""
    try:
        return 成功(data=获取所有任务())
    except Exception as e:
        return 失败(f"获取任务注册表失败: {str(e)}")


@路由.get("/{task_name}/schema", summary="获取单个任务的参数 Schema")
async def 获取任务Schema(task_name: str) -> 统一响应:
    """返回指定任务的输入 Schema 与输入要求。"""
    if task_name not in 任务注册表:
        return 失败(f"任务未注册: {task_name}")

    try:
        信息 = 获取任务元数据(task_name)
        输入模型 = 信息.get("input_schema")
        return 成功(
            data={
                "name": task_name,
                "input_schema": 输入模型.model_json_schema() if 输入模型 else None,
                "required_fields": list(信息.get("required_fields") or []),
                "requires_input": bool(信息.get("requires_input", False)),
            }
        )
    except Exception as e:
        return 失败(f"获取任务 Schema 失败: {str(e)}")


@路由.post("/{task_name}/validate", summary="校验任务参数")
async def 校验任务参数(
    task_name: str,
    params: Optional[dict[str, Any]] = Body(default=None),
) -> 统一响应:
    """使用任务声明的输入 Schema 校验参数。"""
    if task_name not in 任务注册表:
        return 失败(f"任务未注册: {task_name}")

    try:
        信息 = 获取任务元数据(task_name)
        输入模型 = 信息.get("input_schema")
        if 输入模型 is None:
            return 成功(data={"valid": True, "message": "该任务无参数约束"})

        输入模型.model_validate(dict(params or {}))
        return 成功(data={"valid": True})
    except Exception as e:
        return 失败(f"参数校验失败: {str(e)}")
