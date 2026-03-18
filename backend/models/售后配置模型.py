"""售后配置模型。"""
from __future__ import annotations

import aiosqlite


售后配置建表SQL = """
CREATE TABLE IF NOT EXISTS aftersale_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id TEXT NOT NULL UNIQUE,
    启用自动售后 INTEGER DEFAULT 1,
    不支持自动处理类型 TEXT DEFAULT '["补寄","维修","换货"]',
    退货物流白名单 TEXT DEFAULT '[]',
    退货等待时间 TEXT DEFAULT '{"刚发出":3,"中途运输":1,"到达目的市":0.25}',
    需要入库校验 INTEGER DEFAULT 0,
    自动退款金额上限 REAL DEFAULT 50.0,
    仅退款_启用 INTEGER DEFAULT 0,
    仅退款_自动同意金额上限 REAL DEFAULT 10.0,
    仅退款_需要拒绝 INTEGER DEFAULT 0,
    仅退款_最大拒绝次数 INTEGER DEFAULT 3,
    仅退款_拒绝后等待分钟 INTEGER DEFAULT 30,
    仅退款_有图片转人工 INTEGER DEFAULT 1,
    仅退款_拒收退回自动同意 INTEGER DEFAULT 1,
    拒收退款_启用 INTEGER DEFAULT 1,
    拒收退款_需要检查物流 INTEGER DEFAULT 1,
    飞书通知_启用 INTEGER DEFAULT 1,
    飞书通知_webhook TEXT DEFAULT '',
    微信通知_启用 INTEGER DEFAULT 0,
    微信通知_群ID TEXT DEFAULT '',
    通知场景 TEXT DEFAULT '["人工审核","金额超限","派件人不匹配","入库校验"]',
    弹窗偏好 TEXT DEFAULT '{}',
    备注模板 TEXT DEFAULT '{"退货匹配":"退回物流匹配，自动退款","人工":"转人工处理","拒绝":"系统拒绝第{n}次"}',
    每批最大处理数 INTEGER DEFAULT 50,
    单条超时秒数 INTEGER DEFAULT 60,
    失败重试次数 INTEGER DEFAULT 3,
    扫描间隔分钟 INTEGER DEFAULT 30,
    优先处理类型 TEXT DEFAULT '["退货退款","仅退款"]',
    飞书多维表_启用 INTEGER DEFAULT 0,
    飞书多维表_app_token TEXT DEFAULT '',
    飞书多维表_table_id TEXT DEFAULT '',
    飞书多维表_写入场景 TEXT DEFAULT '["已签收","入库校验"]',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime'))
)
"""

售后配置字段补齐SQL = {
    "启用自动售后": "ALTER TABLE aftersale_config ADD COLUMN 启用自动售后 INTEGER DEFAULT 1",
    "不支持自动处理类型": (
        "ALTER TABLE aftersale_config ADD COLUMN 不支持自动处理类型 "
        "TEXT DEFAULT '[\"补寄\",\"维修\",\"换货\"]'"
    ),
    "退货物流白名单": "ALTER TABLE aftersale_config ADD COLUMN 退货物流白名单 TEXT DEFAULT '[]'",
    "退货等待时间": (
        "ALTER TABLE aftersale_config ADD COLUMN 退货等待时间 "
        "TEXT DEFAULT '{\"刚发出\":3,\"中途运输\":1,\"到达目的市\":0.25}'"
    ),
    "需要入库校验": "ALTER TABLE aftersale_config ADD COLUMN 需要入库校验 INTEGER DEFAULT 0",
    "自动退款金额上限": "ALTER TABLE aftersale_config ADD COLUMN 自动退款金额上限 REAL DEFAULT 50.0",
    "仅退款_启用": "ALTER TABLE aftersale_config ADD COLUMN 仅退款_启用 INTEGER DEFAULT 0",
    "仅退款_自动同意金额上限": (
        "ALTER TABLE aftersale_config ADD COLUMN 仅退款_自动同意金额上限 REAL DEFAULT 10.0"
    ),
    "仅退款_需要拒绝": "ALTER TABLE aftersale_config ADD COLUMN 仅退款_需要拒绝 INTEGER DEFAULT 0",
    "仅退款_最大拒绝次数": (
        "ALTER TABLE aftersale_config ADD COLUMN 仅退款_最大拒绝次数 INTEGER DEFAULT 3"
    ),
    "仅退款_拒绝后等待分钟": (
        "ALTER TABLE aftersale_config ADD COLUMN 仅退款_拒绝后等待分钟 INTEGER DEFAULT 30"
    ),
    "仅退款_有图片转人工": (
        "ALTER TABLE aftersale_config ADD COLUMN 仅退款_有图片转人工 INTEGER DEFAULT 1"
    ),
    "仅退款_拒收退回自动同意": (
        "ALTER TABLE aftersale_config ADD COLUMN 仅退款_拒收退回自动同意 INTEGER DEFAULT 1"
    ),
    "拒收退款_启用": "ALTER TABLE aftersale_config ADD COLUMN 拒收退款_启用 INTEGER DEFAULT 1",
    "拒收退款_需要检查物流": (
        "ALTER TABLE aftersale_config ADD COLUMN 拒收退款_需要检查物流 INTEGER DEFAULT 1"
    ),
    "飞书通知_启用": "ALTER TABLE aftersale_config ADD COLUMN 飞书通知_启用 INTEGER DEFAULT 1",
    "飞书通知_webhook": "ALTER TABLE aftersale_config ADD COLUMN 飞书通知_webhook TEXT DEFAULT ''",
    "微信通知_启用": "ALTER TABLE aftersale_config ADD COLUMN 微信通知_启用 INTEGER DEFAULT 0",
    "微信通知_群ID": "ALTER TABLE aftersale_config ADD COLUMN 微信通知_群ID TEXT DEFAULT ''",
    "通知场景": (
        "ALTER TABLE aftersale_config ADD COLUMN 通知场景 "
        "TEXT DEFAULT '[\"人工审核\",\"金额超限\",\"派件人不匹配\",\"入库校验\"]'"
    ),
    "弹窗偏好": "ALTER TABLE aftersale_config ADD COLUMN 弹窗偏好 TEXT DEFAULT '{}'",
    "备注模板": (
        "ALTER TABLE aftersale_config ADD COLUMN 备注模板 "
        "TEXT DEFAULT '{\"退货匹配\":\"退回物流匹配，自动退款\",\"人工\":\"转人工处理\",\"拒绝\":\"系统拒绝第{n}次\"}'"
    ),
    "每批最大处理数": "ALTER TABLE aftersale_config ADD COLUMN 每批最大处理数 INTEGER DEFAULT 50",
    "单条超时秒数": "ALTER TABLE aftersale_config ADD COLUMN 单条超时秒数 INTEGER DEFAULT 60",
    "失败重试次数": "ALTER TABLE aftersale_config ADD COLUMN 失败重试次数 INTEGER DEFAULT 3",
    "扫描间隔分钟": "ALTER TABLE aftersale_config ADD COLUMN 扫描间隔分钟 INTEGER DEFAULT 30",
    "优先处理类型": (
        "ALTER TABLE aftersale_config ADD COLUMN 优先处理类型 "
        "TEXT DEFAULT '[\"退货退款\",\"仅退款\"]'"
    ),
    "飞书多维表_启用": "ALTER TABLE aftersale_config ADD COLUMN 飞书多维表_启用 INTEGER DEFAULT 0",
    "飞书多维表_app_token": "ALTER TABLE aftersale_config ADD COLUMN 飞书多维表_app_token TEXT DEFAULT ''",
    "飞书多维表_table_id": "ALTER TABLE aftersale_config ADD COLUMN 飞书多维表_table_id TEXT DEFAULT ''",
    "飞书多维表_写入场景": (
        "ALTER TABLE aftersale_config ADD COLUMN 飞书多维表_写入场景 "
        "TEXT DEFAULT '[\"已签收\",\"入库校验\"]'"
    ),
    "created_at": "ALTER TABLE aftersale_config ADD COLUMN created_at TEXT",
    "updated_at": "ALTER TABLE aftersale_config ADD COLUMN updated_at TEXT",
}


async def _补齐售后配置表字段(连接: aiosqlite.Connection) -> None:
    async with 连接.execute("PRAGMA table_info(aftersale_config)") as 游标:
        字段集合 = {行[1] for 行 in await 游标.fetchall()}

    if not 字段集合:
        return

    for 字段名, SQL in 售后配置字段补齐SQL.items():
        if 字段名 not in 字段集合:
            await 连接.execute(SQL)


async def 初始化售后配置表(连接: aiosqlite.Connection | None = None) -> None:
    """初始化售后配置表。"""
    if 连接 is not None:
        await 连接.execute(售后配置建表SQL)
        await _补齐售后配置表字段(连接)
        return

    from backend.models.数据库 import 获取连接

    async with 获取连接() as 数据库连接:
        await 数据库连接.execute(售后配置建表SQL)
        await _补齐售后配置表字段(数据库连接)
        await 数据库连接.commit()


__all__ = [
    "售后配置建表SQL",
    "初始化售后配置表",
]
