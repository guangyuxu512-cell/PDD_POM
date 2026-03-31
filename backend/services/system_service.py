"""
系统服务模块

封装系统配置兼容读取、设置转译与健康检查。
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from time import perf_counter
from typing import Any, Dict

import redis.asyncio as aioredis

from backend.config import 配置实例
from backend.models.database import 获取连接
from backend.services.metrics_service import 指标服务实例
from backend.utils.settings import batch_update_settings
from tasks.celery_app import celery_app


class 系统服务:
    """系统配置管理服务。"""

    _配置白名单 = {
        "redis_url": "celery_broker_url",
        "agent_machine_id": "agent_machine_id",
        "machine_name": "machine_name",
        "agent_callback_url": "agent_callback_url",
        "agent_heartbeat_url": "agent_heartbeat_url",
        "x_rpa_key": "x_rpa_key",
        "feishu_webhook_url": "feishu_webhook_url",
        "feishu_secret": "feishu_secret",
        "feishu_app_id": "feishu_app_id",
        "feishu_app_secret": "feishu_app_secret",
        "feishu_bitable_app_token": "feishu_bitable_app_token",
        "feishu_bitable_table_id": "feishu_bitable_table_id",
        "captcha_provider": "captcha_provider",
        "captcha_api_key": "captcha_api_key",
        "default_proxy": "default_proxy",
        "max_browser_instances": "max_concurrency",
        "chrome_path": "chrome_path",
        "log_level": "log_level",
        "app_port": "app_port",
    }

    @staticmethod
    def _获取版本号() -> str:
        for 候选文件名 in ("version", "VERSION"):
            from pathlib import Path

            候选文件 = Path(候选文件名)
            if 候选文件.exists():
                内容 = 候选文件.read_text(encoding="utf-8").strip()
                if 内容:
                    return 内容
        return "0.1.0"

    @staticmethod
    async def _关闭Redis客户端(客户端: Any) -> None:
        if 客户端 is None:
            return
        关闭方法 = getattr(客户端, "aclose", None)
        if callable(关闭方法):
            await 关闭方法()
            return
        await 客户端.close()

    async def _检查Redis(self) -> Dict[str, Any]:
        Redis地址 = str(配置实例.REDIS_URL or "").strip()
        if not Redis地址:
            return {"status": "error", "latency_ms": None}

        客户端 = None
        try:
            客户端 = aioredis.from_url(Redis地址)
            开始时间 = perf_counter()
            await asyncio.wait_for(客户端.ping(), timeout=2)
            return {
                "status": "ok",
                "latency_ms": round((perf_counter() - 开始时间) * 1000, 2),
            }
        except Exception:
            return {"status": "error", "latency_ms": None}
        finally:
            try:
                await self._关闭Redis客户端(客户端)
            except Exception:
                pass

    async def _检查SQLite(self) -> Dict[str, Any]:
        try:
            开始时间 = perf_counter()
            async with 获取连接() as db:
                await db.execute("SELECT 1")
            return {
                "status": "ok",
                "latency_ms": round((perf_counter() - 开始时间) * 1000, 2),
            }
        except Exception:
            return {"status": "error", "latency_ms": None}

    async def _检查浏览器池(self) -> Dict[str, Any]:
        try:
            from backend.services import browser_service as 浏览器服务模块

            管理器实例 = 浏览器服务模块.获取当前管理器实例()
            活跃数 = len(getattr(管理器实例, "实例集", {}) or {})
            最大值 = int(配置实例.MAX_BROWSER_INSTANCES)
            return {
                "status": "ok" if 活跃数 <= 最大值 else "warning",
                "active": 活跃数,
                "max": 最大值,
            }
        except Exception:
            return {
                "status": "error",
                "active": 0,
                "max": int(配置实例.MAX_BROWSER_INSTANCES),
            }

    async def _检查CeleryWorkers(self) -> Dict[str, Any]:
        try:
            响应列表 = celery_app.control.ping(timeout=2) or []
            return {
                "status": "ok" if 响应列表 else "warning",
                "count": len(响应列表),
            }
        except Exception:
            return {"status": "error", "count": 0}

    async def _获取Redis内存使用MB(self) -> float | None:
        Redis地址 = str(配置实例.REDIS_URL or "").strip()
        if not Redis地址:
            return None

        客户端 = None
        try:
            客户端 = aioredis.from_url(Redis地址)
            信息 = await asyncio.wait_for(客户端.info(section="memory"), timeout=2)
            已用字节 = float(信息.get("used_memory", 0) or 0)
            return round(已用字节 / 1024 / 1024, 2)
        except Exception:
            return None
        finally:
            try:
                await self._关闭Redis客户端(客户端)
            except Exception:
                pass

    async def 获取配置(self) -> Dict[str, Any]:
        """返回兼容旧页面的扁平配置结构。"""
        return {
            "redis_url": 配置实例.REDIS_URL,
            "agent_machine_id": 配置实例.AGENT_MACHINE_ID or "",
            "machine_name": 配置实例.MACHINE_NAME or "",
            "agent_callback_url": 配置实例.AGENT_CALLBACK_URL or "",
            "agent_heartbeat_url": 配置实例.AGENT_HEARTBEAT_URL or "",
            "x_rpa_key": "",
            "captcha_provider": 配置实例.CAPTCHA_PROVIDER,
            "captcha_api_key": "",
            "default_proxy": 配置实例.DEFAULT_PROXY or "",
            "max_browser_instances": 配置实例.MAX_BROWSER_INSTANCES,
            "chrome_path": 配置实例.CHROME_PATH or "",
            "log_level": 配置实例.LOG_LEVEL,
            "app_port": 配置实例.BACKEND_PORT,
            "feishu_webhook_url": "",
            "feishu_secret": "",
            "feishu_app_id": 配置实例.FEISHU_APP_ID or "",
            "feishu_app_secret": "",
            "feishu_bitable_app_token": "",
            "feishu_bitable_table_id": 配置实例.FEISHU_BITABLE_TABLE_ID or "",
        }

    async def 更新配置(self, 新配置: Dict[str, Any]) -> Dict[str, Any]:
        """将旧接口提交的配置更新到 settings 表。"""
        更新项: list[dict[str, Any]] = []
        for 前端字段, 值 in 新配置.items():
            if 前端字段 not in self._配置白名单:
                raise ValueError(f"不允许更新字段: {前端字段}")

            设置键名 = self._配置白名单[前端字段]
            if isinstance(值, bool):
                规范值: str | None = "true" if 值 else "false"
            elif 值 is None:
                规范值 = None
            else:
                规范值 = str(值)

            更新项.append({"key": 设置键名, "value": 规范值})

        batch_update_settings(更新项)
        return await self.获取配置()

    async def 健康检查(self) -> Dict[str, Any]:
        """返回结构化健康检查结果。"""
        Redis检查, SQLite检查, 浏览器池检查, Celery检查 = await asyncio.gather(
            self._检查Redis(),
            self._检查SQLite(),
            self._检查浏览器池(),
            self._检查CeleryWorkers(),
        )

        检查结果 = {
            "redis": Redis检查,
            "sqlite": SQLite检查,
            "browser_pool": 浏览器池检查,
            "celery_workers": Celery检查,
        }
        状态集合 = {项.get("status") for 项 in 检查结果.values()}

        if SQLite检查.get("status") == "error":
            整体状态 = "unhealthy"
        elif 状态集合 <= {"ok"}:
            整体状态 = "healthy"
        else:
            整体状态 = "degraded"

        return {
            "status": 整体状态,
            "version": self._获取版本号(),
            "uptime_seconds": 指标服务实例.获取运行秒数(),
            "checks": 检查结果,
            "timestamp": datetime.now().astimezone().isoformat(),
        }

    async def 获取指标(self) -> Dict[str, Any]:
        """返回基础运行指标。"""
        指标快照 = 指标服务实例.获取快照()
        浏览器池检查 = await self._检查浏览器池()
        Redis内存 = await self._获取Redis内存使用MB()
        指标快照.update(
            {
                "browser_instances_active": 浏览器池检查.get("active", 0),
                "browser_instances_max": 浏览器池检查.get("max", int(配置实例.MAX_BROWSER_INSTANCES)),
                "redis_memory_used_mb": Redis内存,
            }
        )
        return 指标快照


系统服务实例 = 系统服务()
