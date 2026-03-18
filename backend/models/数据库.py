"""
数据库模块

使用 aiosqlite 提供异步 SQLite 数据库操作，并基于模型定义统一建表。
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import aiosqlite

from backend.models.店铺模型 import 店铺表定义
from backend.models.流程模型 import 流程表定义
from backend.models.定时任务模型 import 定时任务表定义
from backend.models.售后配置模型 import 初始化售后配置表, 售后配置建表SQL
from backend.models.售后队列模型 import 初始化售后队列表, 售后队列建表SQL


数据库路径 = Path("data/ecom.db")
数据库忙等待毫秒 = 5000
数据库日志模式 = "WAL"
数据库同步模式 = "NORMAL"

任务日志建表SQL = """
    CREATE TABLE IF NOT EXISTS task_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        shop_id TEXT,
        task_name TEXT NOT NULL,
        status TEXT NOT NULL,
        params TEXT,
        result TEXT,
        error TEXT,
        screenshot TEXT,
        started_at DATETIME,
        finished_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
"""

操作日志建表SQL = """
    CREATE TABLE IF NOT EXISTS operation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_id TEXT,
        shop_name TEXT,
        level TEXT NOT NULL,
        source TEXT,
        message TEXT NOT NULL,
        detail TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
"""

任务参数建表SQL = """
    CREATE TABLE IF NOT EXISTS task_params (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_id TEXT NOT NULL,
        task_name TEXT NOT NULL,
        params TEXT DEFAULT '{}',
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'running', 'success', 'failed', 'skipped')),
        result TEXT DEFAULT '{}',
        error TEXT,
        batch_id TEXT,
        enabled INTEGER NOT NULL DEFAULT 1,
        run_count INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
    )
"""

流程参数建表SQL = """
    CREATE TABLE IF NOT EXISTS flow_params (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_id TEXT NOT NULL,
        flow_id TEXT NOT NULL,
        params TEXT DEFAULT '{}',
        step_results TEXT DEFAULT '{}',
        current_step INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'running', 'success', 'failed')),
        error TEXT,
        batch_id TEXT,
        enabled INTEGER NOT NULL DEFAULT 1,
        run_count INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
        FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE
    )
"""

售后队列店铺订单索引SQL = """
    CREATE INDEX IF NOT EXISTS idx_aftersale_queue_shop_order
    ON aftersale_queue (shop_id, 订单号, 当前阶段)
"""


def 获取建表语句列表() -> list[str]:
    """返回数据库初始化需要执行的全部建表语句。"""
    return [
        店铺表定义.生成建表SQL(),
        流程表定义.生成建表SQL(),
        定时任务表定义.生成建表SQL(),
        任务日志建表SQL,
        操作日志建表SQL,
        任务参数建表SQL,
        流程参数建表SQL,
        售后配置建表SQL,
        售后队列建表SQL,
        售后队列店铺订单索引SQL,
    ]


async def 配置SQLite连接(连接: aiosqlite.Connection) -> None:
    """统一配置 SQLite 连接参数，提升长时间运行时的稳定性。"""
    连接.row_factory = aiosqlite.Row
    await 连接.execute("PRAGMA foreign_keys = ON")
    await 连接.execute(f"PRAGMA journal_mode = {数据库日志模式}")
    await 连接.execute(f"PRAGMA synchronous = {数据库同步模式}")
    await 连接.execute(f"PRAGMA busy_timeout = {数据库忙等待毫秒}")


async def _补齐旧版表结构(连接: aiosqlite.Connection) -> None:
    """为旧数据库补齐新增字段，保证升级后可直接运行。"""
    async with 连接.execute("PRAGMA table_info(operation_logs)") as 游标:
        字段集合 = {行[1] for 行 in await 游标.fetchall()}

    if 字段集合 and "shop_name" not in 字段集合:
        await 连接.execute("ALTER TABLE operation_logs ADD COLUMN shop_name TEXT")

    async with 连接.execute("PRAGMA table_info(task_params)") as 游标:
        任务参数字段集合 = {行[1] for 行 in await 游标.fetchall()}

    if 任务参数字段集合 and "enabled" not in 任务参数字段集合:
        await 连接.execute(
            "ALTER TABLE task_params ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1"
        )

    if 任务参数字段集合 and "run_count" not in 任务参数字段集合:
        await 连接.execute(
            "ALTER TABLE task_params ADD COLUMN run_count INTEGER NOT NULL DEFAULT 0"
        )

    async with 连接.execute("PRAGMA table_info(flow_params)") as 游标:
        流程参数字段集合 = {行[1] for 行 in await 游标.fetchall()}

    if 流程参数字段集合 and "step_results" not in 流程参数字段集合:
        await 连接.execute(
            "ALTER TABLE flow_params ADD COLUMN step_results TEXT DEFAULT '{}'"
        )

    if 流程参数字段集合 and "current_step" not in 流程参数字段集合:
        await 连接.execute(
            "ALTER TABLE flow_params ADD COLUMN current_step INTEGER NOT NULL DEFAULT 0"
        )

    if 流程参数字段集合 and "batch_id" not in 流程参数字段集合:
        await 连接.execute(
            "ALTER TABLE flow_params ADD COLUMN batch_id TEXT"
        )

    if 流程参数字段集合 and "enabled" not in 流程参数字段集合:
        await 连接.execute(
            "ALTER TABLE flow_params ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1"
        )

    if 流程参数字段集合 and "run_count" not in 流程参数字段集合:
        await 连接.execute(
            "ALTER TABLE flow_params ADD COLUMN run_count INTEGER NOT NULL DEFAULT 0"
        )

    await 初始化售后配置表(连接)


async def 初始化数据库() -> None:
    """
    初始化数据库，创建所有表

    如果 data 目录不存在，会自动创建。
    如果表已存在，不会重复创建。
    """
    数据库路径.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(数据库路径, timeout=数据库忙等待毫秒 / 1000) as 连接:
        await 配置SQLite连接(连接)

        for 建表SQL in 获取建表语句列表():
            await 连接.execute(建表SQL)

        from backend.models.规则模型 import 初始化规则表

        await 初始化规则表(连接)
        await 初始化售后配置表(连接)
        await 初始化售后队列表(连接)
        await _补齐旧版表结构(连接)
        await 连接.commit()

    try:
        from backend.services.规则服务 import 规则服务实例

        await 规则服务实例.初始化默认售后规则()
    except Exception as 异常:
        print(f"[数据库初始化] 默认规则初始化失败（忽略）: {异常}")

    try:
        from backend.services.售后配置服务 import 售后配置服务实例

        await 售后配置服务实例.从规则服务迁移()
    except Exception as 异常:
        print(f"[数据库初始化] 售后配置迁移失败（忽略）: {异常}")


async def 关闭数据库() -> None:
    """
    关闭数据库连接

    注意：SQLite 使用连接池，每次操作通过上下文管理器自动管理连接，
    因此不需要显式关闭全局连接。此函数保留用于生命周期管理的一致性。
    """
    pass


@asynccontextmanager
async def 获取连接() -> AsyncIterator[aiosqlite.Connection]:
    """
    获取数据库连接

    返回:
        AsyncIterator[aiosqlite.Connection]: 数据库连接上下文管理器

    使用示例:
        async with 获取连接() as 连接:
            async with 连接.execute("SELECT * FROM shops") as 游标:
                结果 = await 游标.fetchall()
    """
    async with aiosqlite.connect(数据库路径, timeout=数据库忙等待毫秒 / 1000) as 连接:
        await 配置SQLite连接(连接)
        yield 连接
