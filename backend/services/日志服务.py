"""
日志服务模块

封装操作日志的写入、查询、SSE 推送、清理。
"""
import json
import asyncio
import aiosqlite
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

from backend.配置 import 配置实例
from backend.models.数据库 import 获取连接


class 日志服务:
    """日志业务服务类"""

    def __init__(self):
        """初始化日志服务"""
        self._数据库路径 = Path(配置实例.DATA_DIR) / "ecom.db"
        self._订阅者: List[asyncio.Queue] = []

    async def 写入日志(
        self,
        shop_id: Optional[str],
        level: str,
        source: str,
        message: str,
        shop_name: Optional[str] = None,
        detail: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        写入日志并推送给所有 SSE 订阅者

        参数:
            shop_id: 店铺 ID（可选）
            level: 日志级别（INFO/WARNING/ERROR）
            source: 来源（task/system/browser 等）
            message: 日志消息
            shop_name: 店铺名称（可选）
            detail: 详细信息（可选）

        返回:
            Dict[str, Any]: 日志记录
        """
        当前时间 = datetime.now().isoformat()

        # 插入日志
        async with 获取连接() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                INSERT INTO operation_logs (
                    shop_id, shop_name, level, source, message, detail, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (shop_id, shop_name, level, source, message, detail, 当前时间)
            )
            await db.commit()

            # 获取插入的记录
            log_id = cursor.lastrowid
            async with db.execute(
                "SELECT * FROM operation_logs WHERE id = ?",
                (log_id,)
            ) as cursor:
                row = await cursor.fetchone()
                日志记录 = dict(row)

        # 推送给所有 SSE 订阅者
        for queue in self._订阅者:
            try:
                queue.put_nowait(日志记录)
            except asyncio.QueueFull:
                # 队列满了，跳过（避免阻塞）
                pass

        return 日志记录

    async def 获取日志列表(
        self,
        shop_id: Optional[str] = None,
        level: Optional[str] = None,
        source: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
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
            page_size: 每页大小

        返回:
            Dict[str, Any]: 分页数据 { "list": [...], "total": N, "page": P, "page_size": S }
        """
        # 构建 WHERE 子句
        where_条件 = []
        where_参数 = []

        if shop_id:
            where_条件.append("shop_id = ?")
            where_参数.append(shop_id)

        if level:
            where_条件.append("level = ?")
            where_参数.append(level)

        if source:
            where_条件.append("source = ?")
            where_参数.append(source)

        if keyword:
            where_条件.append("message LIKE ?")
            where_参数.append(f"%{keyword}%")

        if start_time:
            where_条件.append("created_at >= ?")
            where_参数.append(start_time)

        if end_time:
            where_条件.append("created_at <= ?")
            where_参数.append(end_time)

        where_子句 = " WHERE " + " AND ".join(where_条件) if where_条件 else ""

        # 查询总数和分页数据
        async with 获取连接() as db:
            db.row_factory = aiosqlite.Row

            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM operation_logs{where_子句}"
            async with db.execute(count_sql, where_参数) as cursor:
                row = await cursor.fetchone()
                总数 = row["total"]

            # 查询分页数据
            offset = (page - 1) * page_size
            list_sql = f"""
                SELECT * FROM operation_logs{where_子句}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            async with db.execute(list_sql, where_参数 + [page_size, offset]) as cursor:
                rows = await cursor.fetchall()
                日志列表 = [dict(row) for row in rows]

        return {
            "list": 日志列表,
            "total": 总数,
            "page": page,
            "page_size": page_size
        }

    def 订阅(self) -> asyncio.Queue:
        """
        订阅日志推送（用于 SSE）

        返回:
            asyncio.Queue: 日志队列
        """
        queue = asyncio.Queue(maxsize=100)
        self._订阅者.append(queue)
        return queue

    def 取消订阅(self, queue: asyncio.Queue):
        """
        取消订阅日志推送

        参数:
            queue: 日志队列
        """
        if queue in self._订阅者:
            self._订阅者.remove(queue)

    async def 清理旧日志(self, 天数: int = 30) -> int:
        """
        清理旧日志

        参数:
            天数: 保留最近 N 天的日志，删除更早的日志

        返回:
            int: 删除的条数
        """
        # 计算截止时间
        截止时间 = (datetime.now() - timedelta(days=天数)).isoformat()

        # 删除旧日志
        async with 获取连接() as db:
            cursor = await db.execute(
                "DELETE FROM operation_logs WHERE created_at < ?",
                (截止时间,)
            )
            await db.commit()
            return cursor.rowcount

    async def 清空所有日志(self) -> int:
        """
        清空所有日志记录

        返回:
            int: 删除的条数
        """
        async with 获取连接() as db:
            cursor = await db.execute("DELETE FROM operation_logs")
            await db.commit()
            return cursor.rowcount


# 创建单例
日志服务实例 = 日志服务()
