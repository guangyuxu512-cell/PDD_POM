"""
系统服务模块

封装系统配置的读取、更新和健康检查。
"""
import asyncio
import re
from datetime import datetime
from time import perf_counter
from typing import Dict, Any
from pathlib import Path

import redis.asyncio as aioredis

from backend.config import 配置实例, _ENV_PATH
from backend.models.database import 获取连接
from backend.services.metrics_service import 指标服务实例
from tasks.celery_app import celery_app


class 系统服务:
    """系统配置管理服务"""

    # 允许更新的配置白名单
    _配置白名单 = {
        "redis_url": "REDIS_URL",
        "agent_machine_id": "AGENT_MACHINE_ID",
        "feishu_webhook_url": "FEISHU_WEBHOOK_URL",
        "feishu_app_id": "FEISHU_APP_ID",
        "feishu_app_secret": "FEISHU_APP_SECRET",
        "feishu_bitable_app_token": "FEISHU_BITABLE_APP_TOKEN",
        "feishu_bitable_table_id": "FEISHU_BITABLE_TABLE_ID",
        "captcha_provider": "CAPTCHA_PROVIDER",
        "captcha_api_key": "CAPTCHA_API_KEY",
        "default_proxy": "DEFAULT_PROXY",
        "max_browser_instances": "MAX_BROWSER_INSTANCES",
        "chrome_path": "CHROME_PATH",
        "log_level": "LOG_LEVEL",
    }

    def __init__(self):
        """初始化系统服务"""
        self._env文件路径 = _ENV_PATH
        self._数据库路径 = Path(配置实例.DATA_DIR) / "ecom.db"

    @staticmethod
    def _获取版本号() -> str:
        候选文件列表 = [
            Path("version"),
            Path("VERSION"),
        ]
        for 候选文件 in 候选文件列表:
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
        """
        读取当前系统配置

        返回:
            Dict[str, Any]: 系统配置
        """
        配置 = {
            "redis_url": 配置实例.REDIS_URL,
            "agent_machine_id": 配置实例.AGENT_MACHINE_ID or "",
            "captcha_provider": 配置实例.CAPTCHA_PROVIDER,
            "captcha_api_key": 配置实例.CAPTCHA_API_KEY or "",
            "default_proxy": 配置实例.DEFAULT_PROXY or "",
            "max_browser_instances": 配置实例.MAX_BROWSER_INSTANCES,
            "chrome_path": 配置实例.CHROME_PATH or "",
            "log_level": 配置实例.LOG_LEVEL,
            "feishu_webhook_url": 配置实例.FEISHU_WEBHOOK_URL or "",
            "feishu_app_id": 配置实例.FEISHU_APP_ID or "",
            "feishu_app_secret": 配置实例.FEISHU_APP_SECRET or "",
            "feishu_bitable_app_token": 配置实例.FEISHU_BITABLE_APP_TOKEN or "",
            "feishu_bitable_table_id": 配置实例.FEISHU_BITABLE_TABLE_ID or "",
        }
        return 配置

    async def 更新配置(self, 新配置: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新系统配置

        参数:
            新配置: 新的配置项（前端字段名）

        返回:
            Dict[str, Any]: 更新后的配置

        异常:
            ValueError: 如果包含不允许更新的字段
        """
        # 转换为后端字段名，并检查白名单
        更新项 = {}
        for 前端字段, 值 in 新配置.items():
            if 前端字段 not in self._配置白名单:
                raise ValueError(f"不允许更新字段: {前端字段}")
            后端字段 = self._配置白名单[前端字段]
            更新项[后端字段] = 值

        # 读取 .env 文件
        if self._env文件路径.exists():
            行列表 = self._env文件路径.read_text(encoding="utf-8").splitlines()
        else:
            行列表 = []

        # 更新现有行
        已更新的键 = set()
        新行列表 = []
        for 行 in 行列表:
            行 = 行.rstrip()
            # 跳过注释和空行
            if not 行 or 行.startswith("#"):
                新行列表.append(行)
                continue

            # 匹配 KEY=VALUE
            匹配 = re.match(r"^([A-Z_]+)=(.*)$", 行)
            if 匹配:
                键 = 匹配.group(1)
                if 键 in 更新项:
                    # 更新这一行
                    新行列表.append(f"{键}={更新项[键]}")
                    已更新的键.add(键)
                else:
                    # 保留原样
                    新行列表.append(行)
            else:
                # 保留原样
                新行列表.append(行)

        # 追加新的键
        for 键, 值 in 更新项.items():
            if 键 not in 已更新的键:
                新行列表.append(f"{键}={值}")

        # 写回 .env 文件
        self._env文件路径.write_text("\n".join(新行列表) + "\n", encoding="utf-8")

        # 更新运行时配置
        for 键, 值 in 更新项.items():
            # 类型转换
            if 键 == "MAX_BROWSER_INSTANCES":
                值 = int(值)
            setattr(配置实例, 键, 值)

        # 返回更新后的配置
        return await self.获取配置()

    async def 健康检查(self) -> Dict[str, Any]:
        """
        健康检查

        返回:
            Dict[str, Any]: 系统健康状态
        """
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


# 创建单例
系统服务实例 = 系统服务()
