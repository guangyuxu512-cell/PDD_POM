"""售后工作队列表模型。"""
from __future__ import annotations

import aiosqlite


售后队列建表SQL = """
CREATE TABLE IF NOT EXISTS aftersale_queue (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id            TEXT NOT NULL,
    shop_id             TEXT NOT NULL,
    shop_name           TEXT,
    退货快递公司         TEXT,
    退货快递单号         TEXT,
    退货物流状态         TEXT,
    退货物流全文         TEXT,
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

售后队列店铺订单去重清理SQL = """
DELETE FROM aftersale_queue
WHERE id NOT IN (
    SELECT MIN(id) FROM aftersale_queue GROUP BY shop_id, 订单号
);
"""

售后队列店铺订单去重索引SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_aftersale_queue_shop_order_unique
ON aftersale_queue (shop_id, 订单号);
"""

售后队列新增字段定义 = {
    "shop_name": "ALTER TABLE aftersale_queue ADD COLUMN shop_name TEXT",
    "退货快递公司": "ALTER TABLE aftersale_queue ADD COLUMN 退货快递公司 TEXT",
    "退货快递单号": "ALTER TABLE aftersale_queue ADD COLUMN 退货快递单号 TEXT",
    "退货物流状态": "ALTER TABLE aftersale_queue ADD COLUMN 退货物流状态 TEXT",
    "退货物流全文": "ALTER TABLE aftersale_queue ADD COLUMN 退货物流全文 TEXT",
}


async def _补齐售后队列表字段(连接: aiosqlite.Connection) -> None:
    async with 连接.execute("PRAGMA table_info(aftersale_queue)") as 游标:
        字段集合 = {行[1] for 行 in await 游标.fetchall()}

    if not 字段集合:
        return

    for 字段名, SQL in 售后队列新增字段定义.items():
        if 字段名 not in 字段集合:
            await 连接.execute(SQL)


async def 初始化售后队列表(连接: aiosqlite.Connection | None = None) -> None:
    """初始化售后工作队列表。"""
    if 连接 is not None:
        await 连接.execute(售后队列建表SQL)
        await _补齐售后队列表字段(连接)
        await 连接.execute(售后队列去重索引SQL)
        await 连接.execute(售后队列店铺订单去重清理SQL)
        await 连接.execute(售后队列店铺订单去重索引SQL)
        return

    from backend.models.数据库 import 获取连接

    async with 获取连接() as 数据库连接:
        await 数据库连接.execute(售后队列建表SQL)
        await _补齐售后队列表字段(数据库连接)
        await 数据库连接.execute(售后队列去重索引SQL)
        await 数据库连接.execute(售后队列店铺订单去重清理SQL)
        await 数据库连接.execute(售后队列店铺订单去重索引SQL)
        await 数据库连接.commit()


__all__ = [
    "售后队列建表SQL",
    "售后队列去重索引SQL",
    "售后队列店铺订单去重索引SQL",
    "初始化售后队列表",
]
