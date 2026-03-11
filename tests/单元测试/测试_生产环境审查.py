"""
生产环境审查修复回归测试
"""
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.配置 as 配置模块
from backend.api.执行接口 import 路由 as 执行路由
from backend.api.日志接口 import 路由 as 日志路由
from backend.models import 数据库 as 数据库模块
from backend.services import 定时执行服务 as 定时执行服务模块
from backend.services.店铺服务 import 店铺服务, 店铺服务实例
from backend.services.流程服务 import 流程服务实例
from backend.services.日志服务 import 日志服务实例
from tasks.celery应用 import celery应用


@pytest.fixture
def 临时环境(tmp_path: Path):
    """使用临时数据库和数据目录构造隔离环境。"""
    数据目录 = tmp_path / "data"
    数据库文件 = 数据目录 / "ecom.db"

    with patch.object(数据库模块, "数据库路径", 数据库文件), patch.object(
        配置模块.配置实例,
        "DATA_DIR",
        str(数据目录),
    ):
        asyncio.run(数据库模块.初始化数据库())
        yield {
            "data_dir": 数据目录,
            "db_file": 数据库文件,
        }


class 测试_数据库连接与迁移:
    """验证数据库初始化阶段的生产修复。"""

    @pytest.mark.asyncio
    async def test_初始化数据库_补齐日志表字段并应用SQLite配置(self, tmp_path: Path):
        """旧库升级后应补齐 shop_name，并启用 WAL 与 busy_timeout。"""
        数据目录 = tmp_path / "data"
        数据目录.mkdir(parents=True, exist_ok=True)
        数据库文件 = 数据目录 / "ecom.db"

        with sqlite3.connect(数据库文件) as 连接:
            连接.execute(
                """
                CREATE TABLE operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shop_id TEXT,
                    level TEXT NOT NULL,
                    source TEXT,
                    message TEXT NOT NULL,
                    detail TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            连接.commit()

        with patch.object(数据库模块, "数据库路径", 数据库文件), patch.object(
            配置模块.配置实例,
            "DATA_DIR",
            str(数据目录),
        ):
            await 数据库模块.初始化数据库()

            async with 数据库模块.获取连接() as 连接:
                async with 连接.execute("PRAGMA journal_mode") as 游标:
                    日志模式 = (await 游标.fetchone())[0]
                async with 连接.execute("PRAGMA busy_timeout") as 游标:
                    忙等待毫秒 = (await 游标.fetchone())[0]

            await 日志服务实例.写入日志(
                shop_id="shop-1",
                shop_name="演示店铺",
                level="INFO",
                source="system",
                message="初始化完成",
            )

        with sqlite3.connect(数据库文件) as 连接:
            日志字段集合 = {
                行[1] for 行 in 连接.execute("PRAGMA table_info(operation_logs)")
            }

        assert "shop_name" in 日志字段集合
        assert str(日志模式).lower() == "wal"
        assert int(忙等待毫秒) >= 5000


class 测试_店铺服务生产修复:
    """验证店铺加密与定时计划级联删除。"""

    def test_未配置环境密钥时_使用持久化密钥文件保证可解密(self, tmp_path: Path):
        """不同服务实例间应能复用同一持久化密钥。"""
        数据目录 = tmp_path / "data"

        with patch.object(配置模块.配置实例, "DATA_DIR", str(数据目录)), patch.object(
            配置模块.配置实例,
            "ENCRYPTION_KEY",
            None,
        ):
            服务一 = 店铺服务()
            密文 = 服务一._加密("secret-value")

            服务二 = 店铺服务()
            明文 = 服务二._解密(密文)

        assert 明文 == "secret-value"
        assert (数据目录 / ".encryption.key").exists()

    @pytest.mark.asyncio
    async def test_删除店铺_同步删除或更新关联定时计划(self, 临时环境):
        """删除店铺时不应留下引用已删除 shop_id 的计划。"""
        店铺一 = await 店铺服务实例.创建({"name": "店铺一"})
        店铺二 = await 店铺服务实例.创建({"name": "店铺二"})
        流程 = await 流程服务实例.创建(
            {
                "name": "巡检流程",
                "steps": [{"task": "登录", "on_fail": "continue"}],
            }
        )

        with patch.object(
            定时执行服务模块.定时执行服务实例,
            "_同步RedBeat计划",
            new=AsyncMock(return_value=None),
        ), patch.object(
            定时执行服务模块.定时执行服务实例,
            "_移除RedBeat计划",
            new=AsyncMock(),
        ), patch.object(
            定时执行服务模块.定时执行服务实例,
            "_清理计划批次ID",
            new=AsyncMock(),
        ):
            单店计划 = await 定时执行服务模块.定时执行服务实例.创建(
                {
                    "name": "仅店铺一",
                    "flow_id": 流程["id"],
                    "shop_ids": [店铺一["id"]],
                    "interval_seconds": 60,
                }
            )
            多店计划 = await 定时执行服务模块.定时执行服务实例.创建(
                {
                    "name": "双店铺计划",
                    "flow_id": 流程["id"],
                    "shop_ids": [店铺一["id"], 店铺二["id"]],
                    "interval_seconds": 120,
                }
            )

            删除结果 = await 店铺服务实例.删除(店铺一["id"])

        assert 删除结果 is True
        assert await 店铺服务实例.根据ID获取(店铺一["id"]) is None
        assert await 定时执行服务模块.定时执行服务实例.根据ID获取(单店计划["id"]) is None

        更新后计划 = await 定时执行服务模块.定时执行服务实例.根据ID获取(多店计划["id"])
        assert 更新后计划 is not None
        assert 更新后计划["shop_ids"] == [店铺二["id"]]


class 测试_SSE保活:
    """验证长连接空闲期会输出保活心跳。"""

    def test_执行状态流_保活事件输出_ping(self):
        """执行状态 SSE 应将保活标记转换为注释帧。"""
        应用 = FastAPI(redirect_slashes=False)
        应用.include_router(执行路由)

        async def 假订阅批次状态(batch_id=None):
            yield {"__keepalive__": True}
            yield {"batch_id": batch_id or "batch-1", "status": "running", "total": 1}

        with TestClient(应用) as 客户端, patch(
            "backend.api.执行接口.执行服务实例.订阅批次状态",
            new=假订阅批次状态,
        ):
            with 客户端.stream("GET", "/api/execute/status?batch_id=batch-1") as 响应:
                片段列表 = list(响应.iter_text())

        assert 响应.status_code == 200
        assert any(": ping" in 片段 for 片段 in 片段列表)
        assert any('"batch_id": "batch-1"' in 片段 for 片段 in 片段列表)

    def test_日志流推送_空闲时输出_ping(self):
        """日志 SSE 在长时间无消息时应输出保活注释帧。"""
        应用 = FastAPI(redirect_slashes=False)
        应用.include_router(日志路由)

        class 假队列:
            def __init__(self):
                self._次数 = 0

            async def get(self):
                self._次数 += 1
                if self._次数 == 1:
                    await asyncio.sleep(0.05)
                elif self._次数 == 2:
                    return {
                        "shop_id": "shop-1",
                        "level": "INFO",
                        "message": "hello",
                    }
                raise asyncio.CancelledError()

        with TestClient(应用) as 客户端, patch(
            "backend.api.日志接口.日志流心跳间隔秒",
            0.01,
        ), patch(
            "backend.api.日志接口.日志服务实例.订阅",
            return_value=假队列(),
        ), patch(
            "backend.api.日志接口.日志服务实例.取消订阅",
            new=MagicMock(),
        ) as 模拟取消订阅:
            with 客户端.stream("GET", "/api/logs/stream") as 响应:
                片段列表 = list(响应.iter_text())

        assert 响应.status_code == 200
        assert any(": ping" in 片段 for 片段 in 片段列表)
        assert any('"message": "hello"' in 片段 for 片段 in 片段列表)
        模拟取消订阅.assert_called_once()


def test_Celery配置_启用Worker丢失重入队与启动重连():
    """Celery 应启用关键生产配置。"""
    assert celery应用.conf.task_acks_late is True
    assert celery应用.conf.task_reject_on_worker_lost is True
    assert celery应用.conf.broker_connection_retry_on_startup is True
