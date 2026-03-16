"""售后工作队列表模型。"""
from __future__ import annotations

import aiosqlite


售后队列建表SQL = """
CREATE TABLE IF NOT EXISTS aftersale_queue (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id            TEXT NOT NULL,
    shop_id             TEXT NOT NULL,
    订单号               TEXT NOT NULL,
    售后类型             TEXT,
    售后状态             TEXT,
    退款金额             REAL DEFAULT 0,
    商品名称             TEXT,
    详情数据             TEXT DEFAULT '{}',
    申请原因             TEXT,
    售后申请说明         TEXT,
    发货物流公司         TEXT,
    发货快递单号         TEXT,
    有售后图片           INTEGER DEFAULT 0,
    物流最新状态         TEXT,
    物流最新时间         TEXT,
    收货城市             TEXT,
    剩余处理时间         TEXT,
    平台建议             TEXT,
    可用按钮列表         TEXT DEFAULT '[]',
    协商轮次             INTEGER DEFAULT 0,
    商家已回复           INTEGER DEFAULT 0,
    当前阶段             TEXT DEFAULT '待处理',
    处理次数             INTEGER DEFAULT 0,
    最大处理次数         INTEGER DEFAULT 5,
    下次处理时间         TEXT,
    拒绝次数             INTEGER DEFAULT 0,
    上次拒绝时间         TEXT,
    匹配规则名           TEXT,
    决策动作             TEXT,
    处理结果             TEXT,
    错误信息             TEXT,
    created_at          TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at          TEXT DEFAULT (datetime('now', 'localtime'))
);
"""

售后队列去重索引SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_aftersale_queue_batch_order
ON aftersale_queue (batch_id, 订单号);
"""


async def 初始化售后队列表(连接: aiosqlite.Connection | None = None) -> None:
    """初始化售后工作队列表。"""
    if 连接 is not None:
        await 连接.execute(售后队列建表SQL)
        await 连接.execute(售后队列去重索引SQL)
        return

    from backend.models.数据库 import 获取连接

    async with 获取连接() as 数据库连接:
        await 数据库连接.execute(售后队列建表SQL)
        await 数据库连接.execute(售后队列去重索引SQL)
        await 数据库连接.commit()


__all__ = [
    "售后队列建表SQL",
    "售后队列去重索引SQL",
    "初始化售后队列表",
]
