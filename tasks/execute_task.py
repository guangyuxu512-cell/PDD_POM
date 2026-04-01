"""
批量执行 Celery 任务模块

负责执行批次中的单个步骤任务，并根据 on_fail 策略控制链路。
"""
from __future__ import annotations

from time import perf_counter
from typing import Any, Dict, List, Optional

import httpx

from backend.config import 配置实例
from backend.logging_config import get_logger
from backend.services.metrics_service import 指标服务实例
from browser.recovery import 浏览器恢复实例
from tasks.async_utils import 运行异步任务 as _运行异步任务
from tasks.celery_app import celery_app, 初始化Worker环境, 刷新Celery配置
from tasks.registry import 获取任务类
from backend.services.execute_service import (
    同步更新批次店铺状态,
    同步检查取消标记,
    同步读取批次状态,
    获取队列名称,
)


浏览器异常关键字 = (
    "页面已关闭",
    "浏览器已断开",
    "target closed",
    "浏览器上下文已关闭，需要恢复",
)


def _解析重试次数(on_fail: str) -> int:
    """解析 retry:N 中的重试次数。"""
    if not on_fail.startswith("retry:"):
        return 0
    try:
        return int(on_fail.split(":", 1)[1])
    except Exception:
        return 0


def _是浏览器关闭异常(错误信息: str) -> bool:
    标准错误信息 = str(错误信息 or "").lower()
    return any(关键字.lower() in 标准错误信息 for 关键字 in 浏览器异常关键字)


def _尝试恢复浏览器(shop_id: str, 日志记录器) -> bool:
    """最佳努力触发一次浏览器恢复；无本地管理器时仍允许继续恢复性重试。"""

    async def _执行恢复() -> bool:
        try:
            from backend.services import browser_service as 浏览器服务模块

            await 浏览器服务模块.确保已初始化()
            管理器实例 = 浏览器服务模块.获取当前管理器实例()
            if 管理器实例 is None:
                日志记录器.warning(f"未找到浏览器管理器实例，跳过显式恢复: shop_id={shop_id}")
                return True

            实例信息 = getattr(管理器实例, "实例集", {}).get(shop_id, {}) or {}
            店铺配置 = dict(实例信息.get("店铺配置") or {})
            if not 店铺配置:
                日志记录器.warning(f"缺少浏览器恢复配置，改为执行恢复性重试: shop_id={shop_id}")
                return True

            return await 浏览器恢复实例.尝试恢复(管理器实例, shop_id, 店铺配置)
        except Exception as 异常:
            日志记录器.warning(f"浏览器恢复触发失败，改为执行恢复性重试: shop_id={shop_id}, error={异常}")
            return True

    return bool(_运行异步任务(_执行恢复()))


def _调用主进程执行(基础地址: str, 请求体: dict[str, Any]) -> dict[str, Any]:
    with httpx.Client(timeout=httpx.Timeout(1800.0, connect=10.0)) as 客户端:
        响应 = 客户端.post(f"{基础地址}/api/tasks/execute-internal", json=请求体)
        响应.raise_for_status()
        响应数据 = 响应.json()
        if not isinstance(响应数据, dict) or 响应数据.get("code") != 0:
            raise RuntimeError(
                (响应数据.get("msg") if isinstance(响应数据, dict) else None)
                or "主进程执行失败"
            )
        return 响应数据.get("data") or {}


@celery_app.task(name="执行任务", bind=True)
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
    刷新Celery配置()
    获取任务类(task_name)
    追踪ID = (str(batch_id or "").strip() or str(getattr(self.request, "id", "") or "—"))[:8] or "—"
    日志记录器 = get_logger(追踪ID)
    展示店铺名 = shop_name or shop_id
    标准流程参数ID列表 = [int(记录ID) for 记录ID in (flow_param_ids or []) if int(记录ID) > 0]
    显式传入多记录 = bool(标准流程参数ID列表)
    if not 标准流程参数ID列表 and flow_param_id is not None:
        标准流程参数ID列表 = [int(flow_param_id)]
    无流程参数运行模式 = flow_mode and flow_param_id is None and not 标准流程参数ID列表
    执行开始时间 = perf_counter()
    指标服务实例.记录任务开始()

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

    日志记录器.info(
        f"开始执行: shop_name={展示店铺名}, "
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
        日志记录器.info(
            f"已投递下一步: shop_id={shop_id}, "
            f"task={下一步任务名}, step={step_index + 1}/{total_steps}"
        )

    基础地址 = str(配置实例.API_BASE_URL or "http://localhost:8000").rstrip("/")
    自动恢复已重试 = False
    任务已收尾 = False

    try:
        try:
            执行结果 = _调用主进程执行(基础地址, 请求体)
        except Exception as 异常:
            if on_fail != "abort" and _是浏览器关闭异常(str(异常)) and _尝试恢复浏览器(shop_id, 日志记录器):
                自动恢复已重试 = True
                日志记录器.warning(
                    f"检测到浏览器上下文异常，准备恢复后重试当前步骤: shop_id={shop_id}, task={task_name}"
                )
                执行结果 = _调用主进程执行(基础地址, 请求体)
            else:
                raise

        if (
            on_fail != "abort"
            and not 自动恢复已重试
            and 执行结果.get("status") == "failed"
            and _是浏览器关闭异常(str(执行结果.get("error") or ""))
            and _尝试恢复浏览器(shop_id, 日志记录器)
        ):
            自动恢复已重试 = True
            日志记录器.warning(
                f"检测到浏览器崩溃类失败结果，准备恢复后重试当前步骤: shop_id={shop_id}, task={task_name}"
            )
            执行结果 = _调用主进程执行(基础地址, 请求体)

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
            指标服务实例.记录任务完成(False, (perf_counter() - 执行开始时间) * 1000)
            任务已收尾 = True
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
            指标服务实例.记录任务完成(True, (perf_counter() - 执行开始时间) * 1000)
            任务已收尾 = True
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
            指标服务实例.记录任务完成(False, (perf_counter() - 执行开始时间) * 1000)
            任务已收尾 = True
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
            指标服务实例.记录任务完成(False, (perf_counter() - 执行开始时间) * 1000)
            任务已收尾 = True
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

        指标服务实例.记录任务完成(False, (perf_counter() - 执行开始时间) * 1000)
        任务已收尾 = True
        raise RuntimeError(错误信息)
    except Exception:
        if not 任务已收尾:
            指标服务实例.记录任务完成(False, (perf_counter() - 执行开始时间) * 1000)
        raise
