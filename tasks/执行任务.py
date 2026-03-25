"""
批量执行 Celery 任务模块

负责执行批次中的单个步骤任务，并根据 on_fail 策略控制链路。
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict, List, Optional

import httpx

from backend.配置 import 配置实例
from tasks.celery应用 import celery应用, 初始化Worker环境
from backend.services.执行服务 import (
    同步更新批次店铺状态,
    同步检查取消标记,
    同步读取批次状态,
    获取队列名称,
)
from tasks.注册表 import 获取任务类


def _在线程中执行临时协程(协程):
    """当当前线程已有运行中的事件循环时，退回到临时线程执行协程。"""
    结果容器: dict[str, object] = {}
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
        raise RuntimeError(f"临时线程执行协程失败: {结果容器['error']}") from 结果容器["error"]  # type: ignore[index]

    return 结果容器.get("result")


def _运行异步任务(协程):
    """兼容旧测试与其它调用方：在同步上下文中执行异步协程。"""
    try:
        当前事件循环 = asyncio.get_running_loop()
    except RuntimeError:
        当前事件循环 = None

    if 当前事件循环 is not None:
        return _在线程中执行临时协程(协程)

    return asyncio.run(协程)


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
    flow_param_ids: Optional[List[int]] = None,
    flow_mode: bool = False,
    merge: bool = False,
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
    标准流程参数ID列表 = [int(记录ID) for 记录ID in (flow_param_ids or []) if int(记录ID) > 0]
    显式传入多记录 = bool(标准流程参数ID列表)
    if not 标准流程参数ID列表 and flow_param_id is not None:
        标准流程参数ID列表 = [int(flow_param_id)]
    无流程参数运行模式 = flow_mode and flow_param_id is None and not 标准流程参数ID列表

    任务参数 = {
        "batch_id": batch_id,
        "shop_name": shop_name,
        "step_index": step_index,
        "total_steps": total_steps,
        "celery_task_id": self.request.id,
        "on_fail": on_fail,
    }
    if flow_mode:
        任务参数["flow_mode"] = True
    if 标准流程参数ID列表:
        任务参数["flow_param_ids"] = 标准流程参数ID列表
        任务参数["merge"] = bool(merge)
    elif flow_mode:
        任务参数["flow_context"] = {}

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

    请求体 = {
        "shop_id": shop_id,
        "task_name": task_name,
        "params": 任务参数,
    }
    if flow_param_id is not None and not 显式传入多记录 and len(标准流程参数ID列表) == 1:
        请求体["flow_param_id"] = 标准流程参数ID列表[0]

    def _投递下一步():
        """当前步骤完成后，按批次状态投递下一步 Celery 任务。"""
        if not batch_id or step_index >= total_steps:
            return

        批次数据 = 同步读取批次状态(batch_id)
        if not 批次数据 or 批次数据.get("stopped") or 同步检查取消标记(batch_id):
            return

        店铺状态 = 批次数据.get("shops", {}).get(shop_id, {})
        步骤列表 = 店铺状态.get("steps", [])
        if step_index >= len(步骤列表):
            return

        下一步骤 = 步骤列表[step_index]
        下一步任务名 = 下一步骤["task"]
        下一步失败策略 = 下一步骤.get("on_fail", "abort")
        下一步合并 = bool(下一步骤.get("merge", False))
        队列名称 = 批次数据.get("queue_name") or 获取队列名称()

        下一步参数 = {
            "batch_id": batch_id,
            "shop_id": shop_id,
            "shop_name": shop_name,
            "task_name": 下一步任务名,
            "on_fail": 下一步失败策略,
            "step_index": step_index + 1,
            "total_steps": total_steps,
            "merge": 下一步合并,
        }
        if flow_mode:
            下一步参数["flow_mode"] = True
        if flow_param_ids:
            下一步参数["flow_param_ids"] = flow_param_ids
        elif flow_param_id is not None:
            下一步参数["flow_param_id"] = flow_param_id

        下一步签名 = 执行任务.si(**下一步参数).set(
            queue=队列名称,
            routing_key=队列名称,
        )
        下一步签名.apply_async()
        print(
            f"[执行任务] 已投递下一步: shop_id={shop_id}, "
            f"task={下一步任务名}, step={step_index + 1}/{total_steps}"
        )

    基础地址 = str(配置实例.API_BASE_URL or "http://localhost:8000").rstrip("/")
    with httpx.Client(timeout=httpx.Timeout(1800.0, connect=10.0)) as 客户端:
        响应 = 客户端.post(f"{基础地址}/api/tasks/execute-internal", json=请求体)
        响应.raise_for_status()
        响应数据 = 响应.json()
        if not isinstance(响应数据, dict) or 响应数据.get("code") != 0:
            raise RuntimeError(
                (响应数据.get("msg") if isinstance(响应数据, dict) else None)
                or "主进程执行失败"
            )
        执行结果 = 响应数据.get("data") or {}
    if shop_name is not None:
        执行结果.setdefault("shop_name", 展示店铺名)

    if batch_id and (同步检查取消标记(batch_id) or 执行结果.get("status") == "cancelled"):
        同步更新批次店铺状态(
            batch_id,
            shop_id,
            step_index=step_index,
            task_name=task_name,
            shop_status="stopped",
            error="用户手动停止",
        )
        返回结果 = {
            "status": "cancelled",
            "shop_id": shop_id,
            "task_name": task_name,
            "error": "用户手动停止",
        }
        if shop_name is not None:
            返回结果["shop_name"] = 展示店铺名
        return 返回结果

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
            if not 无流程参数运行模式:
                _投递下一步()
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
            if not 无流程参数运行模式:
                _投递下一步()
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
