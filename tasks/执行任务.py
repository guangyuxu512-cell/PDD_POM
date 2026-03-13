"""
批量执行 Celery 任务模块

负责执行批次中的单个步骤任务，并根据 on_fail 策略控制链路。
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict, Optional

try:
    import nest_asyncio
except ModuleNotFoundError:  # pragma: no cover - 当前环境未安装依赖时退化为 no-op，正式运行仍应通过 requirements 安装
    class nest_asyncio:  # type: ignore[no-redef]
        @staticmethod
        def apply() -> None:
            return None

from tasks.celery应用 import celery应用, 初始化Worker环境, 获取Worker事件循环
from backend.services.流程参数服务 import 流程参数服务实例
from backend.services.任务服务 import 任务服务实例
from backend.services.执行服务 import 同步更新批次店铺状态
from tasks.注册表 import 获取任务类

nest_asyncio.apply()


def _在线程中执行临时协程(协程):
    """当当前线程已有运行中的事件循环时，退回到临时线程执行协程。"""
    结果容器: dict[str, Any] = {}
    完成事件 = threading.Event()

    def _执行():
        try:
            结果容器["result"] = asyncio.run(协程)
        except Exception as e:
            结果容器["error"] = e
        finally:
            完成事件.set()

    线程 = threading.Thread(target=_执行, daemon=True)
    线程.start()
    完成事件.wait()

    if "error" in 结果容器:
        raise RuntimeError(f"临时线程执行协程失败: {结果容器['error']}") from 结果容器["error"]

    return 结果容器.get("result")


def _运行异步任务(协程):
    """在同步 Celery Task 中执行异步协程。"""
    try:
        当前事件循环 = asyncio.get_running_loop()
    except RuntimeError:
        当前事件循环 = None

    if 当前事件循环 is not None:
        return _在线程中执行临时协程(协程)

    try:
        事件循环 = 获取Worker事件循环()
        asyncio.set_event_loop(事件循环)
    except Exception as e:
        print(f"[Celery] 获取 Worker 事件循环失败，回退到临时事件循环: {e}")
        return asyncio.run(协程)

    try:
        return 事件循环.run_until_complete(协程)
    except Exception as e:
        raise RuntimeError(f"Worker 事件循环执行协程失败: {e}") from e


def _解析重试次数(on_fail: str) -> int:
    """解析 retry:N 中的重试次数。"""
    if not on_fail.startswith("retry:"):
        return 0
    try:
        return int(on_fail.split(":", 1)[1])
    except Exception:
        return 0


@celery应用.task(name="执行任务", bind=True)
def 执行任务(
    self,
    *,
    batch_id: str,
    shop_id: str,
    shop_name: Optional[str] = None,
    task_name: str,
    on_fail: str = "abort",
    step_index: int = 1,
    total_steps: int = 1,
    flow_param_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    执行批次中的单个步骤任务。

    参数:
        batch_id: 批次 ID
        shop_id: 店铺 ID
        shop_name: 店铺名称
        task_name: 任务名称
        on_fail: 失败策略
        step_index: 当前步骤序号
        total_steps: 总步骤数
    """
    初始化Worker环境()
    获取任务类(task_name)
    展示店铺名 = shop_name or shop_id
    任务参数 = {
        "batch_id": batch_id,
        "shop_name": shop_name,
        "step_index": step_index,
        "total_steps": total_steps,
        "celery_task_id": self.request.id,
    }

    if flow_param_id is not None:
        _运行异步任务(
            流程参数服务实例.更新(
                flow_param_id,
                {
                    "status": "running",
                    "current_step": step_index,
                    "error": None,
                    "batch_id": batch_id,
                },
            )
        )
        任务参数["flow_param_id"] = flow_param_id
        任务参数["flow_context"] = _运行异步任务(
            流程参数服务实例.获取步骤上下文(flow_param_id, task_name)
        )

    print(
        f"[执行任务] 开始执行: shop_name={展示店铺名}, "
        f"shop_id={shop_id}, task_name={task_name}, step={step_index}/{total_steps}"
    )

    if batch_id:
        同步更新批次店铺状态(
            batch_id,
            shop_id,
            step_index=step_index,
            task_name=task_name,
            step_status="running",
            shop_status="running",
        )

    任务记录 = _运行异步任务(
        任务服务实例.创建任务记录(
            shop_id=shop_id,
            task_name=task_name,
            params=任务参数,
        )
    )

    执行结果 = _运行异步任务(
        任务服务实例.统一执行任务(
            task_id=任务记录["task_id"],
            shop_id=shop_id,
            task_name=task_name,
            params=任务参数,
            来源="batch",
        )
    )
    if shop_name is not None:
        执行结果.setdefault("shop_name", 展示店铺名)

    if flow_param_id is not None:
        业务成功 = 执行结果["status"] == "completed" and 执行结果.get("result") == "成功"
        if 业务成功:
            _运行异步任务(
                流程参数服务实例.回写步骤结果(
                    flow_param_id,
                    task_name,
                    执行结果.get("result_data") or {},
                    step_index,
                )
            )
            if step_index >= total_steps:
                _运行异步任务(
                    流程参数服务实例.更新执行状态(flow_param_id, "success", None)
                )

            if batch_id:
                同步更新批次店铺状态(
                    batch_id,
                    shop_id,
                    step_index=step_index,
                    task_name=task_name,
                    step_status="completed",
                    shop_status="completed" if step_index >= total_steps else "running",
                    result=执行结果.get("result"),
                )
            return 执行结果

        错误信息 = 执行结果.get("error") or 执行结果.get("result") or "任务执行失败"
        最大重试次数 = _解析重试次数(on_fail)
        当前重试次数 = getattr(self.request, "retries", 0)

        if 最大重试次数 > 0 and 当前重试次数 < 最大重试次数:
            if batch_id:
                同步更新批次店铺状态(
                    batch_id,
                    shop_id,
                    step_index=step_index,
                    task_name=task_name,
                    step_status="running",
                    shop_status="running",
                    error=f"{错误信息}，准备重试 {当前重试次数 + 1}/{最大重试次数}",
                )
            raise self.retry(exc=RuntimeError(错误信息), countdown=0)

        if on_fail in {"continue", "log_and_skip"}:
            if step_index >= total_steps:
                _运行异步任务(
                    流程参数服务实例.更新执行状态(flow_param_id, "failed", 错误信息)
                )
            if batch_id:
                同步更新批次店铺状态(
                    batch_id,
                    shop_id,
                    step_index=step_index,
                    task_name=task_name,
                    step_status="failed",
                    shop_status="completed" if step_index >= total_steps else "running",
                    error=错误信息,
                )
            返回结果 = {
                "task_id": 执行结果["task_id"],
                "shop_id": shop_id,
                "task_name": task_name,
                "status": "continued",
                "result": None,
                "error": 错误信息,
            }
            if shop_name is not None:
                返回结果["shop_name"] = 展示店铺名
            return 返回结果

        _运行异步任务(
            流程参数服务实例.更新执行状态(flow_param_id, "failed", 错误信息)
        )
        if batch_id:
            同步更新批次店铺状态(
                batch_id,
                shop_id,
                step_index=step_index,
                task_name=task_name,
                step_status="failed",
                shop_status="failed",
                error=错误信息,
            )
        raise RuntimeError(错误信息)

    if 执行结果["status"] == "completed":
        if batch_id:
            同步更新批次店铺状态(
                batch_id,
                shop_id,
                step_index=step_index,
                task_name=task_name,
                step_status="completed",
                shop_status="completed" if step_index >= total_steps else "running",
                result=执行结果.get("result"),
            )
        return 执行结果

    错误信息 = 执行结果.get("error") or "任务执行失败"
    最大重试次数 = _解析重试次数(on_fail)
    当前重试次数 = getattr(self.request, "retries", 0)

    if 最大重试次数 > 0 and 当前重试次数 < 最大重试次数:
        if batch_id:
            同步更新批次店铺状态(
                batch_id,
                shop_id,
                step_index=step_index,
                task_name=task_name,
                step_status="running",
                shop_status="running",
                error=f"{错误信息}，准备重试 {当前重试次数 + 1}/{最大重试次数}",
            )
        raise self.retry(exc=RuntimeError(错误信息), countdown=0)

    if on_fail in {"continue", "log_and_skip"}:
        if batch_id:
            同步更新批次店铺状态(
                batch_id,
                shop_id,
                step_index=step_index,
                task_name=task_name,
                step_status="failed",
                shop_status="completed" if step_index >= total_steps else "running",
                error=错误信息,
            )
        返回结果 = {
            "task_id": 执行结果["task_id"],
            "shop_id": shop_id,
            "task_name": task_name,
            "status": "continued",
            "result": None,
            "error": 错误信息,
        }
        if shop_name is not None:
            返回结果["shop_name"] = 展示店铺名
        return 返回结果

    if batch_id:
        同步更新批次店铺状态(
            batch_id,
            shop_id,
            step_index=step_index,
            task_name=task_name,
            step_status="failed",
            shop_status="failed",
            error=错误信息,
        )

    raise RuntimeError(错误信息)
