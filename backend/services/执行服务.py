"""
执行服务模块

提供批量执行、停止执行与执行状态推送能力。
"""
from __future__ import annotations

import asyncio
import json
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit

import httpx
import redis
import redis.asyncio as aioredis
from celery import chain as celery_chain

from backend.配置 import 配置实例
from backend.services.店铺服务 import 店铺服务实例
from backend.services.流程服务 import 流程服务实例
from backend.services.流程参数服务 import 流程参数服务实例
from tasks.注册表 import 获取任务类, 初始化任务注册表
from tasks.celery应用 import celery应用


执行状态频道 = "execute:status"
当前批次键 = "execute:current"
批次键前缀 = "execute:batch"
批次回调键前缀 = "execute:callback"
执行状态心跳标记 = "__keepalive__"
执行状态心跳间隔秒 = 15.0
默认Agent回调地址 = "http://localhost:8001"
批次回调超时秒 = 10.0
批次回调标记过期秒 = 86400


def 批次状态键(batch_id: str) -> str:
    """生成批次状态缓存键。"""
    return f"{批次键前缀}:{batch_id}"


def 批次回调标记键(batch_id: str) -> str:
    """生成批次回调去重键。"""
    return f"{批次回调键前缀}:{batch_id}"


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


class 执行服务:
    """批量执行与执行状态服务。"""

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
            return 批次数据
        finally:
            await self._关闭异步Redis客户端(客户端)

    async def _构建步骤列表(
        self,
        flow_id: Optional[str],
        task_name: Optional[str],
    ) -> List[Dict[str, str]]:
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

        return [{"task": str(task_name), "on_fail": "abort"}]

    async def 创建批次(
        self,
        *,
        flow_id: Optional[str],
        task_name: Optional[str],
        shop_ids: List[str],
        concurrency: int,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建批量执行批次并投递 Celery 队列。"""
        标准店铺ID列表 = [店铺ID.strip() for 店铺ID in shop_ids if isinstance(店铺ID, str) and 店铺ID.strip()]
        if not 标准店铺ID列表:
            raise ValueError("shop_ids 不能为空")

        if concurrency <= 0:
            raise ValueError("concurrency 必须大于 0")

        店铺信息映射: Dict[str, Dict[str, Any]] = {}
        for 店铺ID in 标准店铺ID列表:
            店铺信息 = await 店铺服务实例.根据ID获取(店铺ID)
            if not 店铺信息:
                raise ValueError(f"店铺不存在: {店铺ID}")
            店铺信息映射[店铺ID] = 店铺信息

        步骤模板 = await self._构建步骤列表(flow_id=flow_id, task_name=task_name)
        可执行店铺ID列表 = list(标准店铺ID列表)
        流程参数ID映射: Dict[str, int] = {}

        if flow_id:
            可执行店铺ID列表 = []
            for 店铺ID in 标准店铺ID列表:
                待执行记录列表 = await 流程参数服务实例.获取待执行列表(店铺ID, str(flow_id))
                if not 待执行记录列表:
                    continue

                首条记录 = 待执行记录列表[0]
                流程参数ID映射[店铺ID] = int(首条记录["id"])
                可执行店铺ID列表.append(店铺ID)

        batch_id = uuid.uuid4().hex
        machine_id = 获取默认机器编号()
        queue_name = 获取队列名称(machine_id)
        标准回调地址 = str(callback_url or "").strip() or None

        if flow_id:
            for 店铺ID, flow_param_id in 流程参数ID映射.items():
                await 流程参数服务实例.更新(
                    flow_param_id,
                    {
                        "batch_id": batch_id,
                        "error": None,
                    },
                )

        批次数据: Dict[str, Any] = {
            "batch_id": batch_id,
            "mode": "flow" if flow_id else "task",
            "flow_id": flow_id,
            "task_name": task_name,
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

        from tasks.执行任务 import 执行任务 as 执行Celery任务

        任务链列表 = []
        for 店铺ID in 可执行店铺ID列表:
            店铺名称 = str(店铺信息映射[店铺ID].get("name") or 店铺ID)
            任务链 = celery_chain(
                *[
                    执行Celery任务.si(
                        batch_id=batch_id,
                        shop_id=店铺ID,
                        shop_name=店铺名称,
                        task_name=步骤["task"],
                        on_fail=步骤["on_fail"],
                        step_index=索引,
                        total_steps=len(步骤模板),
                        flow_param_id=流程参数ID映射.get(店铺ID),
                    ).set(queue=queue_name, routing_key=queue_name)
                    for 索引, 步骤 in enumerate(步骤模板, start=1)
                ]
            )

            任务链.freeze()
            店铺任务ID列表 = [任务.options.get("task_id") for 任务 in 任务链.tasks]
            批次数据["shops"][店铺ID]["task_ids"] = 店铺任务ID列表
            批次数据["task_ids"].extend([任务ID for 任务ID in 店铺任务ID列表 if 任务ID])
            任务链列表.append(任务链)

        await self._写入批次状态(计算批次汇总(批次数据))

        # 先写入批次状态，再投递链路，避免 Worker 抢先启动后查不到批次元数据。
        for 任务链 in 任务链列表:
            任务链.apply_async()

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
    "同步读取批次状态",
    "同步写入批次状态",
    "同步更新批次店铺状态",
]
