"""
执行服务模块

提供批量执行、停止执行与执行状态推送能力。
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit

import httpx
import redis
import redis.asyncio as aioredis

from backend.models import 数据库 as 数据库模块
from backend.models.数据库 import 获取连接
from backend.配置 import 配置实例
from backend.services.店铺服务 import 店铺服务实例
from backend.services.流程输入服务 import 流程输入服务实例
from backend.services.流程服务 import 流程服务实例
from backend.services.流程参数服务 import 流程参数服务实例
from tasks.注册表 import 获取任务元数据, 获取任务类, 初始化任务注册表
from tasks.celery应用 import celery应用


执行状态频道 = "execute:status"
当前批次键 = "execute:current"
批次键前缀 = "execute:batch"
批次回调键前缀 = "execute:callback"
批次取消键前缀 = "execute:cancel"
执行状态心跳标记 = "__keepalive__"
执行状态心跳间隔秒 = 15.0
默认Agent回调地址 = "http://localhost:8001"
批次回调超时秒 = 10.0
批次回调标记过期秒 = 86400
批次取消标记过期秒 = 3600
允许空运行策略集合 = {"allow_empty", "require_input"}
任务参数字段别名映射 = {
    "parent_product_id": ["parent_product_id", "父商品ID"],
    "new_product_id": ["new_product_id", "新商品ID"],
    "discount": ["discount", "折扣"],
    "roi": ["roi", "投产比"],
}


def 批次状态键(batch_id: str) -> str:
    """生成批次状态缓存键。"""
    return f"{批次键前缀}:{batch_id}"


def 批次回调标记键(batch_id: str) -> str:
    """生成批次回调去重键。"""
    return f"{批次回调键前缀}:{batch_id}"


def 批次取消键(batch_id: str) -> str:
    """生成批次取消标记键。"""
    return f"{批次取消键前缀}:{batch_id}"


def 获取默认机器编号() -> str:
    """获取默认机器编号。"""
    机器编号 = (配置实例.AGENT_MACHINE_ID or "").strip()
    return 机器编号 or "default"


def 构建Agent请求头() -> Optional[Dict[str, str]]:
    """构造 Agent 请求头。"""
    密钥 = str(配置实例.X_RPA_KEY or "").strip()
    if not 密钥:
        return None
    return {"X-RPA-KEY": 密钥}


def 校验业务响应(响应: httpx.Response) -> None:
    """校验 Agent 的统一业务响应。"""
    try:
        响应数据: Any = 响应.json()
    except ValueError:
        return

    if isinstance(响应数据, dict) and 响应数据.get("code") not in (None, 0):
        raise RuntimeError(响应数据.get("msg") or "Agent 返回失败")


def 获取Agent回调根地址() -> str:
    """从配置中提取 Agent 服务根地址。"""
    for 原始地址 in (
        str(配置实例.AGENT_CALLBACK_URL or "").strip(),
        默认Agent回调地址,
    ):
        if not 原始地址:
            continue

        解析结果 = urlsplit(原始地址)
        if not 解析结果.scheme or not 解析结果.netloc:
            continue

        return urlunsplit((解析结果.scheme, 解析结果.netloc, "", "", ""))

    return 默认Agent回调地址


def 获取队列名称(machine_id: Optional[str] = None) -> str:
    """获取目标 Celery 队列名称。"""
    return f"worker.{(machine_id or 获取默认机器编号()).strip()}"


def 构建店铺执行状态(
    shop_id: str,
    shop_name: str,
    步骤列表: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """构建单店铺的初始执行状态。"""
    return {
        "shop_id": shop_id,
        "shop_name": shop_name,
        "status": "waiting",
        "current_task": None,
        "current_step": 0,
        "total_steps": len(步骤列表),
        "last_error": None,
        "last_result": None,
        "task_ids": [],
        "steps": [
            {
                "task": 步骤["task"],
                "on_fail": 步骤["on_fail"],
                "barrier": bool(步骤.get("barrier", False)),
                "merge": bool(步骤.get("merge", False)),
                "status": "waiting",
                "error": None,
                "result": None,
            }
            for 步骤 in 步骤列表
        ],
    }


def 批次已完成可回调(批次数据: Dict[str, Any]) -> bool:
    """判断批次是否已进入需要发送完成回调的终态。"""
    if 批次数据.get("stopped"):
        return False
    return 批次数据.get("status") in {"completed", "failed"}


def 获取批次回调地址(批次数据: Dict[str, Any]) -> str:
    """获取批次完成回调地址。"""
    自定义回调地址 = str(批次数据.get("callback_url") or "").strip()
    if 自定义回调地址:
        return 自定义回调地址

    return f"{获取Agent回调根地址().rstrip('/')}/api/batch-callback"


def 构建批次回调载荷(批次数据: Dict[str, Any]) -> Dict[str, Any]:
    """将批次快照转换为 Agent 回调载荷。"""
    结果列表 = []
    for 店铺状态 in 批次数据.get("shops", {}).values():
        店铺执行状态 = str(店铺状态.get("status") or "")
        结果列表.append(
            {
                "shop_id": 店铺状态.get("shop_id"),
                "shop_name": 店铺状态.get("shop_name"),
                "status": "success" if 店铺执行状态 == "completed" else "failed",
                "error": 店铺状态.get("last_error"),
            }
        )

    return {
        "batch_id": 批次数据["batch_id"],
        "status": "completed" if int(批次数据.get("failed") or 0) == 0 else "partial_failed",
        "total": int(批次数据.get("total") or 0),
        "completed": int(批次数据.get("completed") or 0),
        "failed": int(批次数据.get("failed") or 0),
        "results": 结果列表,
    }


def 发送批次完成回调(批次数据: Dict[str, Any]) -> bool:
    """向 Agent 发送批次完成回调。"""
    回调地址 = 获取批次回调地址(批次数据)
    回调载荷 = 构建批次回调载荷(批次数据)
    请求头 = 构建Agent请求头()

    if not 请求头:
        print(f"[执行服务] 批次完成回调已跳过：未配置 X_RPA_KEY, batch_id={批次数据['batch_id']}")
        return False

    print(f"[执行服务] 开始发送批次完成回调: batch_id={批次数据['batch_id']}, url={回调地址}")

    try:
        with httpx.Client(timeout=批次回调超时秒) as 客户端:
            响应 = 客户端.post(回调地址, json=回调载荷, headers=请求头)
            响应.raise_for_status()
            校验业务响应(响应)
        print(f"[执行服务] 批次完成回调成功: batch_id={批次数据['batch_id']}")
        return True
    except Exception as e:
        print(f"[执行服务] 批次完成回调失败（忽略）: batch_id={批次数据['batch_id']}, error={e}")
        return False


def 尝试发送批次完成回调(
    批次数据: Dict[str, Any],
    *,
    Redis客户端: Optional[redis.Redis] = None,
) -> None:
    """在批次进入终态时尝试发送一次完成回调。"""
    if not 批次已完成可回调(批次数据):
        return

    批次ID = str(批次数据["batch_id"])
    回调标记键 = 批次回调标记键(批次ID)
    客户端 = Redis客户端 or 同步获取Redis客户端()
    需要关闭客户端 = Redis客户端 is None

    try:
        首次发送 = 客户端.set(
            回调标记键,
            "1",
            ex=批次回调标记过期秒,
            nx=True,
        )
        if not 首次发送:
            return
        发送批次完成回调(批次数据)
    except Exception as e:
        print(f"[执行服务] 标记批次完成回调失败（忽略）: batch_id={批次ID}, error={e}")
    finally:
        if 需要关闭客户端:
            客户端.close()


def 计算批次汇总(批次数据: Dict[str, Any]) -> Dict[str, Any]:
    """根据店铺状态重算批次汇总信息。"""
    店铺状态表 = 批次数据.get("shops", {})
    waiting = 0
    running = 0
    completed = 0
    failed = 0

    for 店铺状态 in 店铺状态表.values():
        状态 = 店铺状态.get("status")
        if 状态 == "waiting":
            waiting += 1
        elif 状态 == "running":
            running += 1
        elif 状态 == "completed":
            completed += 1
        elif 状态 in {"failed", "stopped"}:
            failed += 1

    批次数据["waiting"] = waiting
    批次数据["running"] = running
    批次数据["completed"] = completed
    批次数据["failed"] = failed

    if 批次数据.get("stopped"):
        批次数据["status"] = "stopped"
    elif waiting > 0 or running > 0:
        批次数据["status"] = "running"
    elif failed > 0 and completed == 0:
        批次数据["status"] = "failed"
    else:
        批次数据["status"] = "completed"

    批次数据["updated_at"] = datetime.now().isoformat()
    return 批次数据


def _映射运行状态(批次数据: Dict[str, Any]) -> str:
    """将批次状态映射到 execution_runs.status。"""
    if 批次数据.get("stopped"):
        return "cancelled"

    批次状态 = str(批次数据.get("status") or "").strip()
    失败数 = int(批次数据.get("failed") or 0)
    成功数 = int(批次数据.get("completed") or 0)

    if 批次状态 == "completed":
        if 失败数 > 0 and 成功数 > 0:
            return "partial_failed"
        if 失败数 > 0:
            return "failed"
        return "completed"
    if 批次状态 == "failed":
        return "failed"
    if 批次状态 == "stopped":
        return "cancelled"
    if 批次状态 == "running":
        return "running"
    return "queued"


def _映射运行项状态(店铺状态: str) -> str:
    """将批次内店铺状态映射到 execution_run_items.status。"""
    状态映射 = {
        "waiting": "queued",
        "running": "running",
        "completed": "success",
        "failed": "failed",
        "stopped": "cancelled",
    }
    return 状态映射.get(str(店铺状态 or "").strip(), "queued")


def _映射运行步骤状态(步骤状态: str) -> str:
    """将批次步骤状态映射到 execution_run_steps.status。"""
    状态映射 = {
        "waiting": "queued",
        "running": "running",
        "completed": "success",
        "failed": "failed",
        "stopped": "cancelled",
    }
    return 状态映射.get(str(步骤状态 or "").strip(), "queued")


def _构造结果JSON(结果值: Any) -> str:
    """将结果值统一转换为 JSON 文本。"""
    if isinstance(结果值, dict):
        结果数据 = dict(结果值)
    elif 结果值 in (None, ""):
        结果数据 = {}
    else:
        结果数据 = {"result": 结果值}
    return json.dumps(结果数据, ensure_ascii=False)


def 同步写入运行实例状态(批次数据: Dict[str, Any]) -> bool:
    """将 Redis 批次快照同步回 execution_run_* 三张表。"""
    运行ID = str(批次数据.get("batch_id") or "").strip()
    if not 运行ID:
        return False

    数据库文件 = getattr(数据库模块, "数据库路径", None)
    if 数据库文件 is None:
        return False

    当前时间 = datetime.now().isoformat()
    运行状态 = _映射运行状态(批次数据)
    店铺状态表 = dict(批次数据.get("shops") or {})

    try:
        with sqlite3.connect(
            数据库文件,
            timeout=数据库模块.数据库忙等待毫秒 / 1000,
        ) as 连接:
            连接.row_factory = sqlite3.Row
            连接.execute("PRAGMA foreign_keys = ON")
            连接.execute(f"PRAGMA busy_timeout = {数据库模块.数据库忙等待毫秒}")

            已存在 = 连接.execute(
                "SELECT id FROM execution_runs WHERE id = ?",
                (运行ID,),
            ).fetchone()
            if not 已存在:
                return False

            queued_items = 0
            running_items = 0
            success_items = 0
            failed_items = 0
            cancelled_items = 0

            for 店铺ID, 店铺状态 in 店铺状态表.items():
                当前运行项状态 = _映射运行项状态(str(店铺状态.get("status") or ""))
                当前步骤列表 = list(店铺状态.get("steps") or [])
                当前步骤序号 = int(店铺状态.get("current_step") or 0)
                最近任务名 = 店铺状态.get("current_task")
                if 最近任务名 is None and 0 < 当前步骤序号 <= len(当前步骤列表):
                    最近任务名 = 当前步骤列表[当前步骤序号 - 1].get("task")
                if 当前运行项状态 == "queued":
                    queued_items += 1
                elif 当前运行项状态 == "running":
                    running_items += 1
                elif 当前运行项状态 == "success":
                    success_items += 1
                elif 当前运行项状态 == "failed":
                    failed_items += 1
                elif 当前运行项状态 == "cancelled":
                    cancelled_items += 1

                开始时间 = 当前时间 if 当前运行项状态 != "queued" else None
                结束时间 = 当前时间 if 当前运行项状态 in {"success", "failed", "cancelled"} else None
                连接.execute(
                    """
                    UPDATE execution_run_items
                    SET current_step = ?,
                        total_steps = ?,
                        status = ?,
                        last_task_name = ?,
                        error = ?,
                        result_data = ?,
                        started_at = COALESCE(started_at, ?),
                        finished_at = CASE
                            WHEN ? IS NOT NULL THEN ?
                            ELSE finished_at
                        END,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        int(店铺状态.get("current_step") or 0),
                        int(店铺状态.get("total_steps") or len(当前步骤列表)),
                        当前运行项状态,
                        最近任务名,
                        店铺状态.get("last_error"),
                        _构造结果JSON(店铺状态.get("last_result")),
                        开始时间,
                        结束时间,
                        结束时间,
                        当前时间,
                        f"{运行ID}:{店铺ID}",
                    ),
                )

                for 步骤序号, 步骤状态 in enumerate(店铺状态.get("steps") or [], start=1):
                    当前步骤状态 = _映射运行步骤状态(str(步骤状态.get("status") or ""))
                    步骤开始时间 = 当前时间 if 当前步骤状态 != "queued" else None
                    步骤结束时间 = 当前时间 if 当前步骤状态 in {"success", "failed", "cancelled", "skipped"} else None
                    连接.execute(
                        """
                        UPDATE execution_run_steps
                        SET status = ?,
                            result_data = ?,
                            error = ?,
                            started_at = COALESCE(started_at, ?),
                            finished_at = CASE
                                WHEN ? IS NOT NULL THEN ?
                                ELSE finished_at
                            END,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            当前步骤状态,
                            _构造结果JSON(步骤状态.get("result")),
                            步骤状态.get("error"),
                            步骤开始时间,
                            步骤结束时间,
                            步骤结束时间,
                            当前时间,
                            f"{运行ID}:{店铺ID}:{步骤序号}",
                        ),
                    )

            运行结束时间 = 当前时间 if 运行状态 in {"completed", "partial_failed", "failed", "cancelled"} else None
            连接.execute(
                """
                UPDATE execution_runs
                SET status = ?,
                    total_items = ?,
                    queued_items = ?,
                    running_items = ?,
                    success_items = ?,
                    failed_items = ?,
                    cancelled_items = ?,
                    error = ?,
                    started_at = COALESCE(started_at, ?),
                    finished_at = CASE
                        WHEN ? IS NOT NULL THEN ?
                        ELSE finished_at
                    END,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    运行状态,
                    int(批次数据.get("total") or len(店铺状态表)),
                    queued_items,
                    running_items,
                    success_items,
                    failed_items,
                    cancelled_items,
                    None if 运行状态 not in {"failed", "partial_failed", "cancelled"} else str(批次数据.get("error") or ""),
                    当前时间,
                    运行结束时间,
                    运行结束时间,
                    当前时间,
                    运行ID,
                ),
            )
            连接.commit()
            return True
    except Exception as e:
        print(f"[执行服务] 同步运行实例状态失败（忽略）: batch_id={运行ID}, error={e}")
        return False


def 更新店铺步骤状态(
    批次数据: Dict[str, Any],
    shop_id: str,
    *,
    step_index: Optional[int] = None,
    task_name: Optional[str] = None,
    step_status: Optional[str] = None,
    shop_status: Optional[str] = None,
    error: Optional[str] = None,
    result: Optional[str] = None,
) -> Dict[str, Any]:
    """更新单店铺的步骤与执行状态。"""
    店铺状态 = 批次数据.get("shops", {}).get(shop_id)
    if not 店铺状态:
        return 批次数据

    if task_name is not None:
        店铺状态["current_task"] = task_name

    if step_index is not None:
        店铺状态["current_step"] = step_index
        if 0 < step_index <= len(店铺状态["steps"]):
            步骤状态 = 店铺状态["steps"][step_index - 1]
            if step_status is not None:
                步骤状态["status"] = step_status
            if error is not None:
                步骤状态["error"] = error
            if result is not None:
                步骤状态["result"] = result

    if shop_status is not None:
        店铺状态["status"] = shop_status
        if shop_status in {"completed", "failed", "stopped"}:
            店铺状态["current_task"] = None

    if error is not None:
        店铺状态["last_error"] = error

    if result is not None:
        店铺状态["last_result"] = result

    return 计算批次汇总(批次数据)


def 同步获取Redis客户端() -> redis.Redis:
    """获取同步 Redis 客户端。"""
    return redis.Redis.from_url(配置实例.REDIS_URL, decode_responses=True)


def 同步读取批次状态(batch_id: str) -> Optional[Dict[str, Any]]:
    """供 Celery Worker 读取批次状态。"""
    客户端 = 同步获取Redis客户端()
    try:
        原始数据 = 客户端.get(批次状态键(batch_id))
        if not 原始数据:
            return None
        return json.loads(原始数据)
    finally:
        客户端.close()


def 同步写入批次状态(批次数据: Dict[str, Any]) -> Dict[str, Any]:
    """供 Celery Worker 写入批次状态并推送事件。"""
    客户端 = 同步获取Redis客户端()
    try:
        序列化数据 = json.dumps(批次数据, ensure_ascii=False)
        客户端.set(批次状态键(批次数据["batch_id"]), 序列化数据)
        客户端.set(当前批次键, 批次数据["batch_id"])
        客户端.publish(执行状态频道, 序列化数据)
        同步写入运行实例状态(批次数据)
        尝试发送批次完成回调(批次数据, Redis客户端=客户端)
        return 批次数据
    finally:
        客户端.close()


def 同步更新批次店铺状态(
    batch_id: str,
    shop_id: str,
    *,
    step_index: Optional[int] = None,
    task_name: Optional[str] = None,
    step_status: Optional[str] = None,
    shop_status: Optional[str] = None,
    error: Optional[str] = None,
    result: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """供 Celery Worker 更新批次状态。"""
    批次数据 = 同步读取批次状态(batch_id)
    if not 批次数据:
        return None

    更新后数据 = 更新店铺步骤状态(
        批次数据,
        shop_id,
        step_index=step_index,
        task_name=task_name,
        step_status=step_status,
        shop_status=shop_status,
        error=error,
        result=result,
    )
    return 同步写入批次状态(更新后数据)


def 同步设置取消标记(batch_id: str) -> bool:
    """为批次写入取消标记，供 Worker 与主进程跨进程读取。"""
    if not str(batch_id or "").strip():
        return False

    客户端 = 同步获取Redis客户端()
    try:
        return bool(
            客户端.set(
                批次取消键(batch_id),
                "1",
                ex=批次取消标记过期秒,
            )
        )
    finally:
        客户端.close()


def 同步检查取消标记(batch_id: str) -> bool:
    """同步检查批次是否已被标记为取消。"""
    if not str(batch_id or "").strip():
        return False

    客户端 = 同步获取Redis客户端()
    try:
        return 客户端.get(批次取消键(batch_id)) == "1"
    finally:
        客户端.close()


def 同步清除取消标记(batch_id: str) -> bool:
    """同步清理批次取消标记。"""
    if not str(batch_id or "").strip():
        return False

    客户端 = 同步获取Redis客户端()
    try:
        return bool(客户端.delete(批次取消键(batch_id)))
    finally:
        客户端.close()


async def 设置取消标记(batch_id: str) -> bool:
    """异步设置批次取消标记。"""
    if not str(batch_id or "").strip():
        return False

    客户端 = aioredis.from_url(配置实例.REDIS_URL, decode_responses=True)
    try:
        return bool(
            await 客户端.set(
                批次取消键(batch_id),
                "1",
                ex=批次取消标记过期秒,
            )
        )
    finally:
        关闭方法 = getattr(客户端, "aclose", None)
        if callable(关闭方法):
            await 关闭方法()
        else:
            await 客户端.close()


async def 检查取消标记(batch_id: str) -> bool:
    """异步检查批次是否已被标记为取消。"""
    if not str(batch_id or "").strip():
        return False

    客户端 = aioredis.from_url(配置实例.REDIS_URL, decode_responses=True)
    try:
        return await 客户端.get(批次取消键(batch_id)) == "1"
    finally:
        关闭方法 = getattr(客户端, "aclose", None)
        if callable(关闭方法):
            await 关闭方法()
        else:
            await 客户端.close()


async def 清除取消标记(batch_id: str) -> bool:
    """异步清理批次取消标记。"""
    if not str(batch_id or "").strip():
        return False

    客户端 = aioredis.from_url(配置实例.REDIS_URL, decode_responses=True)
    try:
        return bool(await 客户端.delete(批次取消键(batch_id)))
    finally:
        关闭方法 = getattr(客户端, "aclose", None)
        if callable(关闭方法):
            await 关闭方法()
        else:
            await 客户端.close()


class 执行服务:
    """批量执行与执行状态服务。"""

    @staticmethod
    def _标准化店铺ID列表(shop_ids: List[str]) -> List[str]:
        """清理并去重店铺 ID 列表。"""
        已出现店铺 = set()
        标准店铺ID列表: List[str] = []
        for 原始店铺ID in shop_ids:
            if not isinstance(原始店铺ID, str):
                continue
            店铺ID = 原始店铺ID.strip()
            if not 店铺ID or 店铺ID in 已出现店铺:
                continue
            已出现店铺.add(店铺ID)
            标准店铺ID列表.append(店铺ID)
        return 标准店铺ID列表

    @staticmethod
    def _字段值有效(值: Any) -> bool:
        """判断字段值是否可视为已提供。"""
        if 值 is None:
            return False
        if isinstance(值, str):
            return bool(值.strip())
        if isinstance(值, (list, tuple, dict, set)):
            return len(值) > 0
        return True

    def _校验空运行策略(self, empty_run_policy: str) -> str:
        """校验并标准化空运行策略。"""
        标准策略 = str(empty_run_policy or "allow_empty").strip() or "allow_empty"
        if 标准策略 not in 允许空运行策略集合:
            raise ValueError("empty_run_policy 仅支持 allow_empty 或 require_input")
        return 标准策略

    @staticmethod
    def _获取任务元数据安全(task_name: str) -> Dict[str, Any]:
        """兼容未显式标注元数据的任务。"""
        try:
            return 获取任务元数据(task_name)
        except KeyError:
            return {
                "requires_input": False,
                "required_fields": [],
                "supports_empty_context": True,
            }

    @staticmethod
    def _标准化流程上下文(上下文数据: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """统一整理输入上下文字段，并补齐常见别名。"""
        if not isinstance(上下文数据, dict):
            return {}

        标准上下文: Dict[str, Any] = {}
        for 原始键, 原始值 in 上下文数据.items():
            键名 = str(原始键 or "").strip()
            if not 键名:
                continue
            标准上下文[键名] = 原始值

        for 目标字段, 别名列表 in 任务参数字段别名映射.items():
            for 别名 in 别名列表:
                if 别名 in 标准上下文 and 目标字段 not in 标准上下文:
                    标准上下文[目标字段] = 标准上下文[别名]

        return 标准上下文

    def _获取字段值(self, 上下文数据: Dict[str, Any], 字段名: str) -> Any:
        """按主字段与别名读取上下文字段值。"""
        别名列表 = 任务参数字段别名映射.get(字段名, [字段名])
        for 当前字段名 in [字段名, *别名列表]:
            if 当前字段名 in 上下文数据 and self._字段值有效(上下文数据[当前字段名]):
                return 上下文数据[当前字段名]
        return None

    def _步骤需要输入(self, task_name: str) -> bool:
        """判断某个任务是否依赖外部输入。"""
        元数据 = self._获取任务元数据安全(task_name)
        return bool(元数据.get("requires_input")) or not bool(元数据.get("supports_empty_context", True))

    def _校验步骤输入(
        self,
        task_name: str,
        上下文数据: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """校验某一步在给定上下文下是否满足输入要求。"""
        元数据 = self._获取任务元数据安全(task_name)
        标准上下文 = self._标准化流程上下文(上下文数据)
        必填字段列表 = [str(字段).strip() for 字段 in (元数据.get("required_fields") or []) if str(字段).strip()]

        缺失字段列表 = [
            字段名
            for 字段名 in 必填字段列表
            if not self._字段值有效(self._获取字段值(标准上下文, 字段名))
        ]
        if 缺失字段列表:
            return f"缺少 {', '.join(缺失字段列表)}"

        需要输入 = bool(元数据.get("requires_input"))
        支持空上下文 = bool(元数据.get("supports_empty_context", True))
        if not 标准上下文 and (需要输入 or not 支持空上下文):
            return "缺少输入数据"

        return None

    async def _获取流程输入行映射(
        self,
        *,
        flow_id: str,
        input_set_id: str,
        shop_ids: List[str],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """读取输入集，并按店铺聚合启用输入行。"""
        输入集 = await 流程输入服务实例.根据ID获取输入集(input_set_id)
        if not 输入集:
            raise ValueError("输入集不存在")
        if str(输入集.get("flow_id") or "") != str(flow_id):
            raise ValueError("输入集不属于当前流程")

        输入行列表 = await 流程输入服务实例.获取启用输入行(
            input_set_id,
            shop_ids=shop_ids,
        )
        输入行映射: Dict[str, List[Dict[str, Any]]] = {店铺ID: [] for 店铺ID in shop_ids}
        for 输入行 in 输入行列表:
            店铺ID = str(输入行.get("shop_id") or "").strip()
            if not 店铺ID:
                continue
            输入行映射.setdefault(店铺ID, []).append(
                {
                    **dict(输入行),
                    "input_data": self._标准化流程上下文(dict(输入行.get("input_data") or {})),
                }
            )
        return 输入行映射

    async def _创建输入集兼容流程参数(
        self,
        *,
        flow_id: str,
        输入行映射: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """将输入行兼容映射为 flow_params 记录，复用现有流程执行链路。"""
        流程参数记录映射: Dict[str, List[Dict[str, Any]]] = {店铺ID: [] for 店铺ID in 输入行映射}
        for 店铺ID, 输入行列表 in 输入行映射.items():
            for 输入行 in 输入行列表:
                记录 = await 流程参数服务实例.创建(
                    {
                        "shop_id": 店铺ID,
                        "flow_id": flow_id,
                        "params": dict(输入行.get("input_data") or {}),
                        "step_results": {},
                        "current_step": 0,
                        "status": "pending",
                        "error": None,
                        "batch_id": None,
                        "enabled": True,
                    }
                )
                记录["input_row_id"] = 输入行.get("id")
                流程参数记录映射.setdefault(店铺ID, []).append(记录)
        return 流程参数记录映射

    def _构建运行项上下文映射(
        self,
        *,
        flow_id: Optional[str],
        shop_ids: List[str],
        流程参数记录映射: Dict[str, List[Dict[str, Any]]],
        输入行映射: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """为运行快照生成每个店铺的初始上下文。"""
        运行项上下文映射: Dict[str, Dict[str, Any]] = {}
        for 店铺ID in shop_ids:
            当前上下文: Dict[str, Any] = {}
            flow_param_ids = [
                int(流程参数记录["id"])
                for 流程参数记录 in 流程参数记录映射.get(店铺ID, [])
                if 流程参数记录.get("id") is not None
            ]
            if flow_param_ids:
                当前上下文["flow_param_ids"] = flow_param_ids

            输入行列表 = list((输入行映射 or {}).get(店铺ID) or [])
            if 输入行列表:
                输入行ID列表 = [
                    int(输入行["id"])
                    for 输入行 in 输入行列表
                    if 输入行.get("id") is not None
                ]
                if 输入行ID列表:
                    当前上下文["input_row_ids"] = 输入行ID列表
                    if len(输入行ID列表) == 1:
                        当前上下文["input_row_id"] = 输入行ID列表[0]

            if flow_id and not flow_param_ids:
                当前上下文["flow_context"] = {}

            运行项上下文映射[店铺ID] = 当前上下文

        return 运行项上下文映射

    async def 预检流程(
        self,
        *,
        flow_id: str,
        shop_ids: List[str],
        input_set_id: Optional[str] = None,
        empty_run_policy: str = "allow_empty",
    ) -> Dict[str, Any]:
        """在启动前校验流程步骤对输入的要求。"""
        标准店铺ID列表 = self._标准化店铺ID列表(shop_ids)
        if not 标准店铺ID列表:
            raise ValueError("shop_ids 不能为空")

        self._校验空运行策略(empty_run_policy)
        for 店铺ID in 标准店铺ID列表:
            if not await 店铺服务实例.根据ID获取(店铺ID):
                raise ValueError(f"店铺不存在: {店铺ID}")

        步骤模板 = await self._构建步骤列表(flow_id=flow_id, task_name=None)
        候选上下文映射: Dict[str, List[Dict[str, Any]]] = {店铺ID: [] for 店铺ID in 标准店铺ID列表}

        if input_set_id:
            输入行映射 = await self._获取流程输入行映射(
                flow_id=flow_id,
                input_set_id=input_set_id,
                shop_ids=标准店铺ID列表,
            )
            for 店铺ID, 输入行列表 in 输入行映射.items():
                候选上下文映射[店铺ID] = [
                    {
                        "input_row_id": 输入行.get("id"),
                        "context_data": dict(输入行.get("input_data") or {}),
                    }
                    for 输入行 in 输入行列表
                ]
        else:
            for 店铺ID in 标准店铺ID列表:
                待执行记录列表 = await 流程参数服务实例.获取待执行列表(店铺ID, flow_id)
                候选上下文映射[店铺ID] = [
                    {
                        "flow_param_id": 记录.get("id"),
                        "context_data": self._标准化流程上下文(dict(记录.get("params") or {})),
                    }
                    for 记录 in 待执行记录列表
                ]

        预检结果项列表: List[Dict[str, Any]] = []
        通过数量 = 0
        失败数量 = 0

        for 店铺ID in 标准店铺ID列表:
            当前候选列表 = list(候选上下文映射.get(店铺ID) or [])
            if not 当前候选列表:
                当前候选列表 = [{"input_row_id": None, "context_data": {}}]

            for 候选项 in 当前候选列表:
                失败信息: Optional[str] = None
                失败步骤序号: Optional[int] = None
                失败任务名: Optional[str] = None
                for 步骤序号, 步骤 in enumerate(步骤模板, start=1):
                    失败信息 = self._校验步骤输入(
                        str(步骤.get("task") or ""),
                        dict(候选项.get("context_data") or {}),
                    )
                    if 失败信息:
                        失败步骤序号 = 步骤序号
                        失败任务名 = str(步骤.get("task") or "")
                        break

                if 失败信息:
                    失败数量 += 1
                else:
                    通过数量 += 1

                预检结果项列表.append(
                    {
                        "shop_id": 店铺ID,
                        "input_row_id": 候选项.get("input_row_id"),
                        "step_index": 失败步骤序号,
                        "task_name": 失败任务名,
                        "ok": 失败信息 is None,
                        "error": 失败信息,
                    }
                )

        return {
            "ok": 失败数量 == 0,
            "summary": {
                "total_items": len(预检结果项列表),
                "pass_items": 通过数量,
                "failed_items": 失败数量,
            },
            "items": 预检结果项列表,
        }

    async def _写入运行实例快照(
        self,
        *,
        run_id: str,
        flow_id: Optional[str],
        task_name: Optional[str],
        shop_ids: List[str],
        步骤模板: List[Dict[str, Any]],
        concurrency: int,
        callback_url: Optional[str],
        流程参数记录映射: Dict[str, List[Dict[str, Any]]],
        input_set_id: Optional[str] = None,
        运行项上下文映射: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """为后续运行中心改造预先落一份运行实例快照。"""
        当前时间 = datetime.now().isoformat()
        实际并发 = min(concurrency, len(shop_ids)) if shop_ids else 0

        async with 获取连接() as 连接:
            await 连接.execute(
                """
                INSERT OR REPLACE INTO execution_runs (
                    id, mode, flow_id, task_name, flow_snapshot, input_set_id, shop_ids,
                    requested_concurrency, actual_concurrency, callback_url, trigger_source,
                    status, total_items, queued_items, running_items, success_items, failed_items,
                    cancelled_items, error, created_at, started_at, finished_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    "flow" if flow_id else "task",
                    flow_id,
                    task_name,
                    json.dumps(步骤模板, ensure_ascii=False),
                    input_set_id,
                    json.dumps(shop_ids, ensure_ascii=False),
                    concurrency,
                    实际并发,
                    callback_url,
                    "manual",
                    "running",
                    len(shop_ids),
                    len(shop_ids),
                    0,
                    0,
                    0,
                    0,
                    None,
                    当前时间,
                    当前时间,
                    None,
                    当前时间,
                ),
            )

            for 店铺ID in shop_ids:
                运行项ID = f"{run_id}:{店铺ID}"
                默认上下文快照: Dict[str, Any] = dict((运行项上下文映射 or {}).get(店铺ID) or {})
                flow_param_ids = list(默认上下文快照.get("flow_param_ids") or [])
                if "flow_param_ids" not in 默认上下文快照:
                    flow_param_ids = [
                        int(流程参数记录["id"])
                        for 流程参数记录 in 流程参数记录映射.get(店铺ID, [])
                        if 流程参数记录.get("id") is not None
                    ]
                    if flow_param_ids:
                        默认上下文快照["flow_param_ids"] = flow_param_ids

                if flow_id and not flow_param_ids and "flow_context" not in 默认上下文快照:
                    默认上下文快照["flow_context"] = {}

                输入行ID = 默认上下文快照.get("input_row_id")
                if 输入行ID is None:
                    输入行ID列表 = list(默认上下文快照.get("input_row_ids") or [])
                    if len(输入行ID列表) == 1:
                        输入行ID = 输入行ID列表[0]

                await 连接.execute(
                    """
                    INSERT OR REPLACE INTO execution_run_items (
                        id, run_id, shop_id, input_row_id, context_data, current_step, total_steps,
                        status, last_task_name, error, result_data, created_at, started_at,
                        finished_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        运行项ID,
                        run_id,
                        店铺ID,
                        输入行ID,
                        json.dumps(默认上下文快照, ensure_ascii=False),
                        0,
                        len(步骤模板),
                        "queued",
                        None,
                        None,
                        json.dumps({}, ensure_ascii=False),
                        当前时间,
                        None,
                        None,
                        当前时间,
                    ),
                )

                for 步骤序号, 步骤 in enumerate(步骤模板, start=1):
                    await 连接.execute(
                        """
                        INSERT OR REPLACE INTO execution_run_steps (
                            id, run_item_id, step_index, task_name, on_fail, barrier, merge,
                            status, params_snapshot, result_data, error, celery_task_id, worker_id,
                            created_at, started_at, finished_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f"{运行项ID}:{步骤序号}",
                            运行项ID,
                            步骤序号,
                            str(步骤.get("task") or ""),
                            str(步骤.get("on_fail") or "abort"),
                            1 if 步骤.get("barrier") else 0,
                            1 if 步骤.get("merge") else 0,
                            "queued",
                            json.dumps({}, ensure_ascii=False),
                            json.dumps({}, ensure_ascii=False),
                            None,
                            None,
                            None,
                            当前时间,
                            None,
                            None,
                            当前时间,
                        ),
                    )

            await 连接.commit()

    async def _获取异步Redis客户端(self):
        """获取异步 Redis 客户端。"""
        return aioredis.from_url(配置实例.REDIS_URL, decode_responses=True)

    async def _关闭异步Redis客户端(self, 客户端) -> None:
        """关闭异步 Redis 客户端。"""
        关闭方法 = getattr(客户端, "aclose", None)
        if callable(关闭方法):
            await 关闭方法()
        else:
            await 客户端.close()

    async def _获取批次状态(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """读取单个批次状态。"""
        客户端 = await self._获取异步Redis客户端()
        try:
            原始数据 = await 客户端.get(批次状态键(batch_id))
            if not 原始数据:
                return None
            return json.loads(原始数据)
        finally:
            await self._关闭异步Redis客户端(客户端)

    async def 获取最新批次状态(self, batch_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取当前批次或指定批次的状态快照。"""
        客户端 = await self._获取异步Redis客户端()
        try:
            目标批次ID = batch_id or await 客户端.get(当前批次键)
            if not 目标批次ID:
                return None
            原始数据 = await 客户端.get(批次状态键(目标批次ID))
            if not 原始数据:
                return None
            return json.loads(原始数据)
        finally:
            await self._关闭异步Redis客户端(客户端)

    async def _写入批次状态(self, 批次数据: Dict[str, Any]) -> Dict[str, Any]:
        """异步写入批次状态并推送事件。"""
        客户端 = await self._获取异步Redis客户端()
        try:
            序列化数据 = json.dumps(批次数据, ensure_ascii=False)
            await 客户端.set(批次状态键(批次数据["batch_id"]), 序列化数据)
            await 客户端.set(当前批次键, 批次数据["batch_id"])
            await 客户端.publish(执行状态频道, 序列化数据)
            同步写入运行实例状态(批次数据)
            return 批次数据
        finally:
            await self._关闭异步Redis客户端(客户端)

    async def _构建步骤列表(
        self,
        flow_id: Optional[str],
        task_name: Optional[str],
    ) -> List[Dict[str, Any]]:
        """根据请求构建执行步骤。"""
        if bool(flow_id) == bool(task_name):
            raise ValueError("flow_id 和 task_name 必须二选一")

        初始化任务注册表()

        if flow_id:
            流程 = await 流程服务实例.根据ID获取(flow_id)
            if not 流程:
                raise ValueError("流程不存在")

            步骤列表 = deepcopy(流程.get("steps", []))
            if not isinstance(步骤列表, list) or not 步骤列表:
                raise ValueError("流程步骤不能为空")

            for 步骤 in 步骤列表:
                try:
                    获取任务类(步骤["task"])
                except KeyError as e:
                    raise ValueError(f"流程步骤任务未注册: {步骤['task']}") from e

            return 步骤列表

        try:
            获取任务类(str(task_name))
        except KeyError as e:
            raise ValueError(f"任务未注册: {task_name}") from e

        return [{"task": str(task_name), "on_fail": "abort", "barrier": False, "merge": False}]

    async def 投递单步任务(
        self,
        *,
        batch_id: str,
        shop_id: str,
        shop_name: str,
        task_name: str,
        on_fail: str,
        step_index: int,
        total_steps: int,
        flow_param_id: Optional[int] = None,
        flow_param_ids: Optional[List[int]] = None,
        flow_mode: bool = False,
        merge: bool = False,
        queue_name: Optional[str] = None,
        批次数据: Optional[Dict[str, Any]] = None,
        立即投递: bool = True,
    ) -> Dict[str, Any]:
        """创建并投递单个 Celery 步骤任务。"""
        from tasks.执行任务 import 执行任务 as 执行Celery任务

        目标队列 = queue_name or 获取队列名称()
        任务签名 = 执行Celery任务.si(
            batch_id=batch_id,
            shop_id=shop_id,
            shop_name=shop_name,
            task_name=task_name,
            on_fail=on_fail,
            step_index=step_index,
            total_steps=total_steps,
            flow_param_id=flow_param_id,
            flow_param_ids=flow_param_ids,
            flow_mode=flow_mode,
            merge=merge,
        ).set(queue=目标队列, routing_key=目标队列)

        冻结方法 = getattr(任务签名, "freeze", None)
        if callable(冻结方法):
            冻结方法()

        任务ID = 任务签名.options.get("task_id")
        待更新批次数据 = 批次数据
        if 待更新批次数据 is None:
            待更新批次数据 = await self._获取批次状态(batch_id)

        if 待更新批次数据:
            店铺状态 = 待更新批次数据.get("shops", {}).get(shop_id)
            if 店铺状态 is not None and 任务ID:
                if 任务ID not in 店铺状态["task_ids"]:
                    店铺状态["task_ids"].append(任务ID)
                if 任务ID not in 待更新批次数据["task_ids"]:
                    待更新批次数据["task_ids"].append(任务ID)

            if 批次数据 is None:
                await self._写入批次状态(计算批次汇总(待更新批次数据))

        if 立即投递:
            投递方法 = getattr(任务签名, "apply_async", None)
            if callable(投递方法):
                投递方法()

        return {
            "task_id": 任务ID,
            "signature": 任务签名,
            "batch": 待更新批次数据,
        }

    async def 创建批次(
        self,
        *,
        flow_id: Optional[str],
        task_name: Optional[str],
        shop_ids: List[str],
        concurrency: int,
        callback_url: Optional[str] = None,
        input_set_id: Optional[str] = None,
        empty_run_policy: str = "allow_empty",
    ) -> Dict[str, Any]:
        """创建批量执行批次并投递 Celery 队列。"""
        标准店铺ID列表 = self._标准化店铺ID列表(shop_ids)
        if not 标准店铺ID列表:
            raise ValueError("shop_ids 不能为空")

        if concurrency <= 0:
            raise ValueError("concurrency 必须大于 0")

        标准空运行策略 = self._校验空运行策略(empty_run_policy)
        if task_name and input_set_id:
            raise ValueError("单任务模式暂不支持 input_set_id")

        店铺信息映射: Dict[str, Dict[str, Any]] = {}
        for 店铺ID in 标准店铺ID列表:
            店铺信息 = await 店铺服务实例.根据ID获取(店铺ID)
            if not 店铺信息:
                raise ValueError(f"店铺不存在: {店铺ID}")
            店铺信息映射[店铺ID] = 店铺信息

        步骤模板 = await self._构建步骤列表(flow_id=flow_id, task_name=task_name)
        可执行店铺ID列表 = list(标准店铺ID列表)
        流程参数记录映射: Dict[str, List[Dict[str, Any]]] = {}
        输入行映射: Dict[str, List[Dict[str, Any]]] = {店铺ID: [] for 店铺ID in 可执行店铺ID列表}

        if flow_id:
            if input_set_id:
                输入行映射 = await self._获取流程输入行映射(
                    flow_id=str(flow_id),
                    input_set_id=input_set_id,
                    shop_ids=标准店铺ID列表,
                )
                流程参数记录映射 = await self._创建输入集兼容流程参数(
                    flow_id=str(flow_id),
                    输入行映射=输入行映射,
                )
            else:
                for 店铺ID in 标准店铺ID列表:
                    待执行记录列表 = await 流程参数服务实例.获取待执行列表(店铺ID, str(flow_id))
                    流程参数记录映射[店铺ID] = 待执行记录列表

            if 标准空运行策略 == "require_input" and any(
                self._步骤需要输入(str(步骤.get("task") or ""))
                for 步骤 in 步骤模板
            ):
                缺失输入店铺列表 = [
                    店铺ID
                    for 店铺ID in 可执行店铺ID列表
                    if not list(流程参数记录映射.get(店铺ID) or [])
                ]
                if 缺失输入店铺列表:
                    raise ValueError(
                        f"以下店铺缺少输入数据: {', '.join(缺失输入店铺列表)}"
                    )

        batch_id = uuid.uuid4().hex
        machine_id = 获取默认机器编号()
        queue_name = 获取队列名称(machine_id)
        标准回调地址 = str(callback_url or "").strip() or None
        运行项上下文映射 = self._构建运行项上下文映射(
            flow_id=flow_id,
            shop_ids=可执行店铺ID列表,
            流程参数记录映射=流程参数记录映射,
            输入行映射=输入行映射,
        )

        await self._写入运行实例快照(
            run_id=batch_id,
            flow_id=flow_id,
            task_name=task_name,
            shop_ids=可执行店铺ID列表,
            步骤模板=步骤模板,
            concurrency=concurrency,
            callback_url=标准回调地址,
            流程参数记录映射=流程参数记录映射,
            input_set_id=input_set_id,
            运行项上下文映射=运行项上下文映射,
        )

        if flow_id:
            for 记录列表 in 流程参数记录映射.values():
                for 流程参数记录 in 记录列表:
                    await 流程参数服务实例.更新(
                        int(流程参数记录["id"]),
                        {
                            "batch_id": batch_id,
                            "error": None,
                            "status": "pending",
                        },
                    )

        批次数据: Dict[str, Any] = {
            "batch_id": batch_id,
            "mode": "flow" if flow_id else "task",
            "flow_id": flow_id,
            "task_name": task_name,
            "input_set_id": input_set_id,
            "callback_url": 标准回调地址,
            "machine_id": machine_id,
            "queue_name": queue_name,
            "requested_concurrency": concurrency,
            "total": len(可执行店铺ID列表),
            "waiting": len(可执行店铺ID列表),
            "running": 0,
            "completed": 0,
            "failed": 0,
            "status": "running",
            "stopped": False,
            "task_ids": [],
            "shops": {
                店铺ID: 构建店铺执行状态(
                    店铺ID,
                    str(店铺信息映射[店铺ID].get("name") or 店铺ID),
                    步骤模板,
                )
                for 店铺ID in 可执行店铺ID列表
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        待投递任务列表: List[Any] = []
        首步骤 = 步骤模板[0]
        for 店铺ID in 可执行店铺ID列表:
            店铺名称 = str(店铺信息映射[店铺ID].get("name") or 店铺ID)
            if flow_id:
                店铺流程参数记录 = 流程参数记录映射.get(店铺ID, [])
                if 首步骤.get("barrier") or 首步骤.get("merge"):
                    投递结果 = await self.投递单步任务(
                        batch_id=batch_id,
                        shop_id=店铺ID,
                        shop_name=店铺名称,
                        task_name=首步骤["task"],
                        on_fail=首步骤["on_fail"],
                        step_index=1,
                        total_steps=len(步骤模板),
                        flow_param_ids=[int(流程参数记录["id"]) for 流程参数记录 in 店铺流程参数记录],
                        flow_mode=True,
                        merge=bool(首步骤.get("merge")),
                        queue_name=queue_name,
                        批次数据=批次数据,
                        立即投递=False,
                    )
                    待投递任务列表.append(投递结果["signature"])
                    continue

                if not 店铺流程参数记录:
                    投递结果 = await self.投递单步任务(
                        batch_id=batch_id,
                        shop_id=店铺ID,
                        shop_name=店铺名称,
                        task_name=首步骤["task"],
                        on_fail=首步骤["on_fail"],
                        step_index=1,
                        total_steps=len(步骤模板),
                        flow_mode=True,
                        queue_name=queue_name,
                        批次数据=批次数据,
                        立即投递=False,
                    )
                    待投递任务列表.append(投递结果["signature"])
                    continue

                for 流程参数记录 in 店铺流程参数记录:
                    投递结果 = await self.投递单步任务(
                        batch_id=batch_id,
                        shop_id=店铺ID,
                        shop_name=店铺名称,
                        task_name=首步骤["task"],
                        on_fail=首步骤["on_fail"],
                        step_index=1,
                        total_steps=len(步骤模板),
                        flow_param_id=int(流程参数记录["id"]),
                        flow_mode=True,
                        queue_name=queue_name,
                        批次数据=批次数据,
                        立即投递=False,
                    )
                    待投递任务列表.append(投递结果["signature"])
            else:
                投递结果 = await self.投递单步任务(
                    batch_id=batch_id,
                    shop_id=店铺ID,
                    shop_name=店铺名称,
                    task_name=首步骤["task"],
                    on_fail=首步骤["on_fail"],
                    step_index=1,
                    total_steps=len(步骤模板),
                    flow_param_id=None,
                    queue_name=queue_name,
                    批次数据=批次数据,
                    立即投递=False,
                )
                待投递任务列表.append(投递结果["signature"])

        await self._写入批次状态(计算批次汇总(批次数据))

        # 先写入批次状态，再投递首步任务，避免 Worker 抢先启动后查不到批次元数据。
        for 任务签名 in 待投递任务列表:
            投递方法 = getattr(任务签名, "apply_async", None)
            if callable(投递方法):
                投递方法()

        return {
            "batch_id": batch_id,
            "total": 批次数据["total"],
            "status": 批次数据["status"],
        }

    async def 停止批次(self, batch_id: Optional[str] = None) -> Dict[str, Any]:
        """停止当前批次或指定批次。"""
        批次数据 = await self.获取最新批次状态(batch_id=batch_id)
        if not 批次数据:
            raise ValueError("没有可停止的批次")

        await 设置取消标记(str(批次数据["batch_id"]))

        for 任务ID in 批次数据.get("task_ids", []):
            if 任务ID:
                celery应用.control.revoke(任务ID, terminate=False)

        批次数据["stopped"] = True
        for 店铺状态 in 批次数据.get("shops", {}).values():
            if 店铺状态.get("status") in {"waiting", "running"}:
                店铺状态["status"] = "stopped"
                店铺状态["current_task"] = None

        await self._写入批次状态(计算批次汇总(批次数据))

        return {
            "batch_id": 批次数据["batch_id"],
            "total": 批次数据["total"],
            "status": 批次数据["status"],
        }

    async def 订阅批次状态(self, batch_id: Optional[str] = None) -> AsyncIterator[Dict[str, Any]]:
        """订阅执行状态更新。"""
        事件循环 = asyncio.get_running_loop()
        上次输出时间 = 事件循环.time()
        初始状态 = await self.获取最新批次状态(batch_id=batch_id)
        if 初始状态:
            yield 初始状态
            上次输出时间 = 事件循环.time()

        客户端 = await self._获取异步Redis客户端()
        pubsub = 客户端.pubsub()
        await pubsub.subscribe(执行状态频道)

        try:
            while True:
                消息 = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not 消息:
                    if 事件循环.time() - 上次输出时间 >= 执行状态心跳间隔秒:
                        yield {执行状态心跳标记: True}
                        上次输出时间 = 事件循环.time()
                    await asyncio.sleep(0.2)
                    continue

                try:
                    批次数据 = json.loads(消息["data"])
                except Exception:
                    continue

                if batch_id and 批次数据.get("batch_id") != batch_id:
                    continue

                yield 批次数据
                上次输出时间 = 事件循环.time()
        finally:
            await pubsub.unsubscribe(执行状态频道)
            await pubsub.close()
            await self._关闭异步Redis客户端(客户端)


执行服务实例 = 执行服务()


__all__ = [
    "执行服务实例",
    "执行状态频道",
    "当前批次键",
    "批次状态键",
    "执行状态心跳标记",
    "批次已完成可回调",
    "获取批次回调地址",
    "构建批次回调载荷",
    "发送批次完成回调",
    "尝试发送批次完成回调",
    "获取队列名称",
    "批次取消键",
    "同步读取批次状态",
    "同步设置取消标记",
    "同步检查取消标记",
    "同步清除取消标记",
    "同步写入批次状态",
    "同步更新批次店铺状态",
    "设置取消标记",
    "检查取消标记",
    "清除取消标记",
]
