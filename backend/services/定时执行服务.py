"""
定时执行服务模块

提供定时计划 CRUD、RedBeat 同步与到点触发批量执行逻辑。
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

import redis.asyncio as aioredis
from celery.schedules import crontab, schedule as 周期调度

from backend.配置 import 配置实例
from backend.models.数据库 import 获取连接
from backend.models.定时任务模型 import 标准化店铺ID列表
from backend.services.店铺服务 import 店铺服务实例
from backend.services.流程服务 import 流程服务实例
from backend.services.执行服务 import 执行服务实例, 获取队列名称
from tasks.celery应用 import celery应用


定时计划任务名 = "执行定时计划"
定时计划名称前缀 = "execution-schedule:"
定时计划批次键前缀 = "schedule:batch"
允许的重叠策略 = {"wait", "skip", "parallel"}
未提供 = object()


def 定时计划批次键(计划ID: str) -> str:
    """生成定时计划关联的批次缓存键。"""
    return f"{定时计划批次键前缀}:{计划ID}"


class 定时执行服务:
    """定时计划业务服务。"""

    def _构建响应数据(self, 列名: list[str], 行数据) -> dict[str, Any]:
        """将数据库记录转换为 API 返回结构。"""
        数据 = dict(zip(列名, 行数据))

        店铺ID原文 = 数据.get("shop_ids")
        if isinstance(店铺ID原文, str):
            try:
                数据["shop_ids"] = json.loads(店铺ID原文)
            except json.JSONDecodeError:
                数据["shop_ids"] = []

        数据["enabled"] = bool(数据.get("enabled"))

        for 字段名 in ("last_run_at", "next_run_at", "created_at", "updated_at"):
            if isinstance(数据.get(字段名), datetime):
                数据[字段名] = self._序列化时间(数据[字段名])

        return 数据

    def _序列化时间(self, 时间值: datetime | str | None) -> str | None:
        """将时间值转换成可写入数据库和可序列化的字符串。"""
        if 时间值 is None:
            return None
        if isinstance(时间值, str):
            return 时间值
        return 时间值.isoformat(sep=" ", timespec="seconds")

    def _标准化Cron表达式(self, Cron表达式: Optional[str]) -> Optional[str]:
        """标准化 Cron 表达式。"""
        if Cron表达式 is None:
            return None

        标准值 = str(Cron表达式).strip()
        return 标准值 or None

    def _解析Cron调度(self, Cron表达式: str):
        """将标准 5 段 Cron 表达式转换为 Celery crontab。"""
        段列表 = Cron表达式.split()
        if len(段列表) != 5:
            raise ValueError("cron_expr 必须是标准 5 段 Cron 表达式")

        return crontab(
            minute=段列表[0],
            hour=段列表[1],
            day_of_month=段列表[2],
            month_of_year=段列表[3],
            day_of_week=段列表[4],
        )

    def _构建调度规则(
        self,
        *,
        间隔秒数: Optional[int],
        Cron表达式: Optional[str],
    ):
        """根据请求配置构建 Celery 调度对象。"""
        if 间隔秒数 is None and not Cron表达式:
            raise ValueError("interval_seconds 和 cron_expr 至少要提供一个")
        if 间隔秒数 is not None and Cron表达式:
            raise ValueError("interval_seconds 和 cron_expr 不能同时提供")

        if 间隔秒数 is not None:
            return 周期调度(run_every=timedelta(seconds=间隔秒数))

        return self._解析Cron调度(str(Cron表达式))

    def _估算下次运行时间(
        self,
        *,
        间隔秒数: Optional[int],
        Cron表达式: Optional[str],
        参考时间: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """按当前调度规则估算下次运行时间。"""
        调度规则 = self._构建调度规则(间隔秒数=间隔秒数, Cron表达式=Cron表达式)
        当前时间 = 参考时间 or 调度规则.now()

        if 参考时间 is not None:
            调度当前时间 = 调度规则.now()
            if (
                getattr(调度当前时间, "tzinfo", None) is not None
                and getattr(当前时间, "tzinfo", None) is None
            ):
                当前时间 = 当前时间.replace(tzinfo=调度当前时间.tzinfo)

        剩余时间 = 调度规则.remaining_estimate(当前时间)
        if 剩余时间 is None:
            return None
        if 剩余时间.total_seconds() < 0:
            return 当前时间
        return 当前时间 + 剩余时间

    def _获取RedBeat条目类(self):
        """延迟导入 RedBeat，避免测试环境未安装时导入即失败。"""
        try:
            from redbeat import RedBeatSchedulerEntry
        except ModuleNotFoundError as 异常:
            raise RuntimeError("未安装 celery-redbeat，无法操作定时计划") from 异常

        return RedBeatSchedulerEntry

    def _生成RedBeat计划名称(self, 计划ID: str) -> str:
        """生成 RedBeat 条目名称。"""
        return f"{定时计划名称前缀}{计划ID}"

    async def _同步RedBeat计划(self, 计划数据: dict[str, Any]) -> Optional[datetime]:
        """创建或覆盖对应的 RedBeat 调度条目。"""
        RedBeatSchedulerEntry = self._获取RedBeat条目类()
        调度规则 = self._构建调度规则(
            间隔秒数=计划数据.get("interval_seconds"),
            Cron表达式=计划数据.get("cron_expr"),
        )
        队列名称 = 获取队列名称()
        条目 = RedBeatSchedulerEntry(
            name=self._生成RedBeat计划名称(计划数据["id"]),
            task=定时计划任务名,
            schedule=调度规则,
            kwargs={"schedule_id": 计划数据["id"]},
            options={"queue": 队列名称, "routing_key": 队列名称},
            enabled=bool(计划数据.get("enabled", True)),
            app=celery应用,
        )
        条目.save()
        return 条目.due_at

    async def _移除RedBeat计划(self, 计划ID: str) -> None:
        """从 RedBeat 中删除调度条目。"""
        RedBeatSchedulerEntry = self._获取RedBeat条目类()
        计划键 = RedBeatSchedulerEntry.generate_key(
            celery应用,
            self._生成RedBeat计划名称(计划ID),
        )

        try:
            条目 = RedBeatSchedulerEntry.from_key(计划键, app=celery应用)
        except KeyError:
            return

        条目.delete()

    async def _获取异步Redis客户端(self):
        """获取异步 Redis 客户端。"""
        return aioredis.from_url(配置实例.REDIS_URL, decode_responses=True)

    async def _关闭异步Redis客户端(self, 客户端) -> None:
        """关闭异步 Redis 客户端。"""
        关闭方法 = getattr(客户端, "aclose", None)
        if callable(关闭方法):
            await 关闭方法()
        else:
            await 客户端.close()

    async def _读取计划批次ID(self, 计划ID: str) -> Optional[str]:
        """读取计划当前关联的批次 ID。"""
        客户端 = await self._获取异步Redis客户端()
        try:
            return await 客户端.get(定时计划批次键(计划ID))
        finally:
            await self._关闭异步Redis客户端(客户端)

    async def _写入计划批次ID(self, 计划ID: str, 批次ID: str) -> None:
        """记录计划最近触发的批次 ID。"""
        客户端 = await self._获取异步Redis客户端()
        try:
            await 客户端.set(定时计划批次键(计划ID), 批次ID)
        finally:
            await self._关闭异步Redis客户端(客户端)

    async def _清理计划批次ID(self, 计划ID: str) -> None:
        """清理计划关联的批次 ID 缓存。"""
        客户端 = await self._获取异步Redis客户端()
        try:
            await 客户端.delete(定时计划批次键(计划ID))
        finally:
            await self._关闭异步Redis客户端(客户端)

    async def _更新运行时间(
        self,
        计划ID: str,
        *,
        上次运行时间: Any = 未提供,
        下次运行时间: Any = 未提供,
    ) -> None:
        """更新计划的运行时间字段。"""
        更新字段: list[str] = []
        更新值: list[Any] = []

        if 上次运行时间 is not 未提供:
            更新字段.append("last_run_at = ?")
            更新值.append(self._序列化时间(上次运行时间))

        if 下次运行时间 is not 未提供:
            更新字段.append("next_run_at = ?")
            更新值.append(self._序列化时间(下次运行时间))

        if not 更新字段:
            return

        更新字段.append("updated_at = CURRENT_TIMESTAMP")
        更新值.append(计划ID)

        async with 获取连接() as 连接:
            await 连接.execute(
                f"UPDATE execution_schedules SET {', '.join(更新字段)} WHERE id = ?",
                更新值,
            )
            await 连接.commit()

    async def _准备计划数据(
        self,
        数据: dict[str, Any],
        *,
        现有计划: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """校验并标准化创建或更新参数。"""
        标准数据 = {
            "name": str(现有计划["name"]).strip() if 现有计划 else None,
            "flow_id": str(现有计划["flow_id"]).strip() if 现有计划 else None,
            "shop_ids": list(现有计划["shop_ids"]) if 现有计划 else None,
            "concurrency": int(现有计划["concurrency"]) if 现有计划 else 1,
            "interval_seconds": 现有计划["interval_seconds"] if 现有计划 else None,
            "cron_expr": self._标准化Cron表达式(现有计划.get("cron_expr")) if 现有计划 else None,
            "overlap_policy": str(现有计划["overlap_policy"]).strip() if 现有计划 else "wait",
        }

        if "name" in 数据 or 现有计划 is None:
            名称 = str(数据.get("name", "")).strip()
            if not 名称:
                raise ValueError("name 不能为空")
            标准数据["name"] = 名称

        if "flow_id" in 数据 or 现有计划 is None:
            流程ID = str(数据.get("flow_id", "")).strip()
            if not 流程ID:
                raise ValueError("flow_id 不能为空")
            标准数据["flow_id"] = 流程ID

        if "shop_ids" in 数据 or 现有计划 is None:
            店铺ID列表 = 数据.get("shop_ids")
            if 店铺ID列表 is None:
                raise ValueError("shop_ids 不能为空")
            标准数据["shop_ids"] = 标准化店铺ID列表(店铺ID列表)

        if "concurrency" in 数据 or 现有计划 is None:
            try:
                并发数 = int(数据.get("concurrency", 标准数据["concurrency"]))
            except (TypeError, ValueError) as 异常:
                raise ValueError("concurrency 必须是大于 0 的整数") from 异常
            if 并发数 <= 0:
                raise ValueError("concurrency 必须大于 0")
            标准数据["concurrency"] = 并发数

        if "interval_seconds" in 数据:
            间隔秒数原值 = 数据.get("interval_seconds")
            if 间隔秒数原值 is None:
                标准数据["interval_seconds"] = None
            else:
                try:
                    间隔秒数 = int(间隔秒数原值)
                except (TypeError, ValueError) as 异常:
                    raise ValueError("interval_seconds 必须是大于 0 的整数") from 异常
                if 间隔秒数 <= 0:
                    raise ValueError("interval_seconds 必须大于 0")
                标准数据["interval_seconds"] = 间隔秒数

        if "cron_expr" in 数据:
            标准数据["cron_expr"] = self._标准化Cron表达式(数据.get("cron_expr"))

        if "overlap_policy" in 数据 or 现有计划 is None:
            重叠策略 = str(
                数据.get("overlap_policy", 标准数据["overlap_policy"])
            ).strip() or "wait"
            if 重叠策略 not in 允许的重叠策略:
                raise ValueError("overlap_policy 仅支持 wait、skip、parallel")
            标准数据["overlap_policy"] = 重叠策略

        if 标准数据["interval_seconds"] is None and not 标准数据["cron_expr"]:
            raise ValueError("interval_seconds 和 cron_expr 至少要提供一个")
        if 标准数据["interval_seconds"] is not None and 标准数据["cron_expr"]:
            raise ValueError("interval_seconds 和 cron_expr 不能同时提供")

        self._构建调度规则(
            间隔秒数=标准数据["interval_seconds"],
            Cron表达式=标准数据["cron_expr"],
        )

        流程 = await 流程服务实例.根据ID获取(标准数据["flow_id"])
        if not 流程:
            raise ValueError("流程不存在")

        for 店铺ID in 标准数据["shop_ids"]:
            if not await 店铺服务实例.根据ID获取(店铺ID):
                raise ValueError(f"店铺不存在: {店铺ID}")

        return 标准数据

    async def 获取全部(self) -> dict[str, Any]:
        """获取全部定时计划。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT COUNT(*) FROM execution_schedules"
            ) as 游标:
                结果 = await 游标.fetchone()
                总数 = 结果[0] if 结果 else 0

            async with 连接.execute(
                "SELECT * FROM execution_schedules ORDER BY created_at DESC"
            ) as 游标:
                列名 = [描述[0] for 描述 in 游标.description]
                行列表 = await 游标.fetchall()
                计划列表 = [self._构建响应数据(列名, 行) for 行 in 行列表]

        return {
            "list": 计划列表,
            "total": 总数,
        }

    async def 根据ID获取(self, 计划ID: str) -> Optional[dict[str, Any]]:
        """根据 ID 获取定时计划。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT * FROM execution_schedules WHERE id = ?",
                (计划ID,),
            ) as 游标:
                行 = await 游标.fetchone()
                if not 行:
                    return None

                列名 = [描述[0] for 描述 in 游标.description]
                return self._构建响应数据(列名, 行)

    async def 创建(self, 数据: dict[str, Any]) -> dict[str, Any]:
        """创建定时计划，并同步写入 RedBeat。"""
        标准数据 = await self._准备计划数据(数据)
        计划ID = uuid.uuid4().hex

        async with 获取连接() as 连接:
            await 连接.execute(
                """
                INSERT INTO execution_schedules (
                    id, name, flow_id, shop_ids, concurrency, interval_seconds,
                    cron_expr, overlap_policy, enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    计划ID,
                    标准数据["name"],
                    标准数据["flow_id"],
                    json.dumps(标准数据["shop_ids"], ensure_ascii=False),
                    标准数据["concurrency"],
                    标准数据["interval_seconds"],
                    标准数据["cron_expr"],
                    标准数据["overlap_policy"],
                    1,
                ),
            )
            await 连接.commit()

        计划数据 = await self.根据ID获取(计划ID)
        if not 计划数据:
            raise RuntimeError("定时计划创建后读取失败")

        try:
            下次运行时间 = await self._同步RedBeat计划(计划数据)
            await self._更新运行时间(计划ID, 下次运行时间=下次运行时间)
        except Exception:
            async with 获取连接() as 连接:
                await 连接.execute(
                    "DELETE FROM execution_schedules WHERE id = ?",
                    (计划ID,),
                )
                await 连接.commit()
            raise

        最新计划 = await self.根据ID获取(计划ID)
        if not 最新计划:
            raise RuntimeError("定时计划创建后读取失败")
        return 最新计划

    async def 更新(self, 计划ID: str, 数据: dict[str, Any]) -> Optional[dict[str, Any]]:
        """更新定时计划。"""
        现有计划 = await self.根据ID获取(计划ID)
        if not 现有计划:
            return None

        标准数据 = await self._准备计划数据(数据, 现有计划=现有计划)

        async with 获取连接() as 连接:
            await 连接.execute(
                """
                UPDATE execution_schedules
                SET name = ?, flow_id = ?, shop_ids = ?, concurrency = ?,
                    interval_seconds = ?, cron_expr = ?, overlap_policy = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    标准数据["name"],
                    标准数据["flow_id"],
                    json.dumps(标准数据["shop_ids"], ensure_ascii=False),
                    标准数据["concurrency"],
                    标准数据["interval_seconds"],
                    标准数据["cron_expr"],
                    标准数据["overlap_policy"],
                    计划ID,
                ),
            )
            await 连接.commit()

        更新后计划 = await self.根据ID获取(计划ID)
        if not 更新后计划:
            return None

        if 更新后计划["enabled"]:
            await self._移除RedBeat计划(计划ID)
            下次运行时间 = await self._同步RedBeat计划(更新后计划)
            await self._更新运行时间(计划ID, 下次运行时间=下次运行时间)

        return await self.根据ID获取(计划ID)

    async def 删除(self, 计划ID: str) -> bool:
        """删除定时计划并移除对应的 RedBeat 条目。"""
        现有计划 = await self.根据ID获取(计划ID)
        if not 现有计划:
            return False

        await self._移除RedBeat计划(计划ID)

        async with 获取连接() as 连接:
            await 连接.execute(
                "DELETE FROM execution_schedules WHERE id = ?",
                (计划ID,),
            )
            await 连接.commit()

        await self._清理计划批次ID(计划ID)
        return True

    async def 暂停(self, 计划ID: str) -> Optional[dict[str, Any]]:
        """暂停定时计划。"""
        现有计划 = await self.根据ID获取(计划ID)
        if not 现有计划:
            return None
        if not 现有计划["enabled"]:
            return 现有计划

        await self._移除RedBeat计划(计划ID)

        async with 获取连接() as 连接:
            await 连接.execute(
                """
                UPDATE execution_schedules
                SET enabled = 0, next_run_at = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (计划ID,),
            )
            await 连接.commit()

        return await self.根据ID获取(计划ID)

    async def 恢复(self, 计划ID: str) -> Optional[dict[str, Any]]:
        """恢复已暂停的定时计划。"""
        现有计划 = await self.根据ID获取(计划ID)
        if not 现有计划:
            return None
        if 现有计划["enabled"]:
            return 现有计划

        async with 获取连接() as 连接:
            await 连接.execute(
                """
                UPDATE execution_schedules
                SET enabled = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (计划ID,),
            )
            await 连接.commit()

        恢复后计划 = await self.根据ID获取(计划ID)
        if not 恢复后计划:
            return None

        try:
            下次运行时间 = await self._同步RedBeat计划(恢复后计划)
            await self._更新运行时间(计划ID, 下次运行时间=下次运行时间)
        except Exception:
            async with 获取连接() as 连接:
                await 连接.execute(
                    """
                    UPDATE execution_schedules
                    SET enabled = 0, next_run_at = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (计划ID,),
                )
                await 连接.commit()
            raise

        return await self.根据ID获取(计划ID)

    async def 触发计划(self, 计划ID: str) -> dict[str, Any]:
        """到点触发计划时，复用批量执行服务创建批次。"""
        计划数据 = await self.根据ID获取(计划ID)
        if not 计划数据:
            raise ValueError("定时计划不存在")
        if not 计划数据["enabled"]:
            raise ValueError("定时计划已暂停")

        if 计划数据["overlap_policy"] != "parallel":
            已有关联批次ID = await self._读取计划批次ID(计划ID)
            if 已有关联批次ID:
                批次状态 = await 执行服务实例.获取最新批次状态(batch_id=已有关联批次ID)
                if 批次状态 and 批次状态.get("status") == "running":
                    return {
                        "schedule_id": 计划ID,
                        "batch_id": 已有关联批次ID,
                        "status": "skipped" if 计划数据["overlap_policy"] == "skip" else "waiting",
                    }
                await self._清理计划批次ID(计划ID)

        批次结果 = await 执行服务实例.创建批次(
            flow_id=计划数据["flow_id"],
            task_name=None,
            shop_ids=list(计划数据["shop_ids"]),
            concurrency=int(计划数据["concurrency"]),
        )
        await self._写入计划批次ID(计划ID, 批次结果["batch_id"])

        调度当前时间 = self._构建调度规则(
            间隔秒数=计划数据.get("interval_seconds"),
            Cron表达式=计划数据.get("cron_expr"),
        ).now()
        上次运行时间 = 调度当前时间
        下次运行时间 = self._估算下次运行时间(
            间隔秒数=计划数据.get("interval_seconds"),
            Cron表达式=计划数据.get("cron_expr"),
            参考时间=上次运行时间,
        )
        await self._更新运行时间(
            计划ID,
            上次运行时间=上次运行时间,
            下次运行时间=下次运行时间,
        )

        return {
            "schedule_id": 计划ID,
            **批次结果,
        }


定时执行服务实例 = 定时执行服务()


__all__ = [
    "定时执行服务",
    "定时执行服务实例",
    "定时计划任务名",
    "定时计划批次键",
]
