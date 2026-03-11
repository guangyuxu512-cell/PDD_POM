"""
日志接口模块

提供日志管理的 REST API 接口，包含 SSE 实时推送。
"""
import json
import asyncio
from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
)
from backend.services.日志服务 import 日志服务实例


# 创建路由
路由 = APIRouter(prefix="/api/logs", tags=["日志管理"])
日志流心跳间隔秒 = 15.0


@路由.get("/", summary="获取日志列表")
async def 获取日志列表(
    shop_id: Optional[str] = Query(None, description="店铺 ID"),
    level: Optional[str] = Query(None, description="日志级别"),
    source: Optional[str] = Query(None, description="来源"),
    keyword: Optional[str] = Query(None, description="关键词（模糊匹配）"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页大小")
) -> 统一响应:
    """
    获取日志列表（分页 + 筛选）

    参数:
        shop_id: 店铺 ID（可选）
        level: 日志级别（可选）
        source: 来源（可选）
        keyword: 关键词（模糊匹配 message）（可选）
        start_time: 开始时间（可选）
        end_time: 结束时间（可选）
        page: 页码（从 1 开始）
        page_size: 每页大小（1-200）

    返回:
        统一响应: 包含分页数据的响应
    """
    try:
        结果 = await 日志服务实例.获取日志列表(
            shop_id=shop_id,
            level=level,
            source=source,
            keyword=keyword,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        return 成功(data=结果)
    except Exception as e:
        return 失败(f"获取日志列表失败: {str(e)}")


@路由.get("/stream", summary="SSE 实时日志推送")
async def 日志流推送(
    shop_id: Optional[str] = Query(None, description="店铺 ID（过滤）")
):
    """
    SSE 实时日志推送

    参数:
        shop_id: 店铺 ID（可选，用于过滤）

    返回:
        StreamingResponse: SSE 流
    """
    async def 事件生成器():
        """SSE 事件生成器"""
        # 订阅日志推送
        queue = 日志服务实例.订阅()

        try:
            while True:
                try:
                    日志 = await asyncio.wait_for(queue.get(), timeout=日志流心跳间隔秒)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue

                # 如果指定了 shop_id，进行过滤
                if shop_id and 日志.get("shop_id") != shop_id:
                    continue

                # 格式化为 SSE 格式
                data = json.dumps(日志, ensure_ascii=False)
                yield f"data: {data}\n\n"

        except asyncio.CancelledError:
            # 客户端断开连接
            pass
        finally:
            # 取消订阅
            日志服务实例.取消订阅(queue)

    return StreamingResponse(
        事件生成器(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )


@路由.delete("/clean", summary="清理旧日志")
async def 清理旧日志(
    days: int = Query(30, ge=1, le=365, description="保留最近 N 天的日志")
) -> 统一响应:
    """
    清理旧日志

    参数:
        days: 保留最近 N 天的日志，删除更早的日志（1-365）

    返回:
        统一响应: 删除结果
    """
    try:
        删除数 = await 日志服务实例.清理旧日志(天数=days)
        return 成功(data={"deleted": 删除数}, message=f"已清理 {删除数} 条旧日志")
    except Exception as e:
        return 失败(f"清理旧日志失败: {str(e)}")


@路由.delete("/", summary="清空所有日志")
async def 清空所有日志() -> 统一响应:
    """
    清空所有日志记录

    返回:
        统一响应: 删除结果
    """
    try:
        删除数 = await 日志服务实例.清空所有日志()
        return 成功(data={"deleted": 删除数}, message=f"已清空 {删除数} 条日志")
    except Exception as e:
        return 失败(f"清空日志失败: {str(e)}")
