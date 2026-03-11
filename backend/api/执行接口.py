"""
执行接口模块

提供批量执行、停止执行与执行状态 SSE。
"""
from __future__ import annotations

import json
import asyncio
from typing import Optional

from fastapi import APIRouter, Body, Query
from fastapi.responses import StreamingResponse

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
    批量执行请求,
    停止执行请求,
)
from backend.services.执行服务 import 执行服务实例, 执行状态心跳标记


路由 = APIRouter(prefix="/api/execute", tags=["批量执行"])


@路由.post("/batch", summary="批量执行")
async def 批量执行(请求: 批量执行请求) -> 统一响应:
    """创建批量执行批次。"""
    try:
        结果 = await 执行服务实例.创建批次(
            flow_id=请求.flow_id,
            task_name=请求.task_name,
            shop_ids=请求.shop_ids,
            concurrency=请求.concurrency,
            callback_url=请求.callback_url,
        )
        return 成功(data=结果)
    except Exception as e:
        return 失败(f"批量执行失败: {str(e)}")


@路由.post("/stop", summary="停止当前批次")
async def 停止批次(
    请求: Optional[停止执行请求] = Body(default=None, description="停止批次请求")
) -> 统一响应:
    """停止当前批次或指定批次。"""
    try:
        结果 = await 执行服务实例.停止批次(batch_id=请求.batch_id if 请求 else None)
        return 成功(data=结果, message="批次已停止")
    except Exception as e:
        return 失败(f"停止批次失败: {str(e)}")


@路由.get("/status", summary="SSE 实时推送执行进度")
async def 执行状态流(batch_id: Optional[str] = Query(None, description="批次 ID（可选）")):
    """SSE 实时推送执行进度。"""

    async def 事件生成器():
        try:
            async for 批次数据 in 执行服务实例.订阅批次状态(batch_id=batch_id):
                if 批次数据.get(执行状态心跳标记):
                    yield ": ping\n\n"
                    continue
                yield f"data: {json.dumps(批次数据, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        事件生成器(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
