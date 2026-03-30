"""
登录态监控模块

负责检测页面是否被重定向到登录态失效场景，并在失效时发送告警。
"""
from __future__ import annotations

import asyncio
import inspect
import json
import time
from datetime import datetime, timezone
from typing import Any, Optional

import redis.asyncio as aioredis

from backend.config import 配置实例
from backend.logging_config import get_logger
from backend.services.feishu_service import 飞书服务实例
from backend.services.log_service import 日志服务实例


日志记录器 = get_logger()
登录页地址特征 = (
    "/login",
    "/passport",
    "mms.pinduoduo.com/login",
    "fxg.jinritemai.com/login",
)
登录态文案特征 = (
    "登录已过期",
    "请重新登录",
    "账号登录",
    "手机号登录",
    "登录后继续",
)
关键Cookie名称 = ("PASS_ID", "JSESSIONID")


class 登录态监控器:
    """负责登录态检测与告警。"""

    @staticmethod
    def 是否登录页地址(页面地址: str) -> bool:
        标准地址 = str(页面地址 or "").lower()
        return any(特征 in 标准地址 for 特征 in 登录页地址特征)

    async def _读取页面文本(self, 页面: Any) -> str:
        try:
            定位器工厂 = getattr(页面, "locator", None)
            if callable(定位器工厂):
                主体定位器 = 定位器工厂("body")
                if inspect.isawaitable(主体定位器):
                    主体定位器 = await 主体定位器
                读取文本 = getattr(主体定位器, "inner_text", None)
                if callable(读取文本):
                    文本 = 读取文本()
                    if inspect.isawaitable(文本):
                        return str(await 文本)
                    return str(文本)
        except Exception:
            pass

        try:
            读取内容 = getattr(页面, "content", None)
            if callable(读取内容):
                内容 = 读取内容()
                if inspect.isawaitable(内容):
                    内容 = await 内容
                return str(内容 or "")
        except Exception:
            return ""

        return ""

    async def _检查关键Cookie(self, 页面: Any) -> bool:
        上下文 = getattr(页面, "context", None)
        if 上下文 is None:
            return True

        读取Cookie = getattr(上下文, "cookies", None)
        if not callable(读取Cookie):
            return True

        try:
            Cookie列表 = 读取Cookie()
            if asyncio.iscoroutine(Cookie列表):
                Cookie列表 = await Cookie列表
        except Exception:
            return True

        if not isinstance(Cookie列表, list):
            return True

        关键Cookie映射 = {
            str(项.get("name") or ""): 项
            for 项 in Cookie列表
            if isinstance(项, dict)
        }
        当前时间戳 = time.time()

        for Cookie名称 in 关键Cookie名称:
            Cookie = 关键Cookie映射.get(Cookie名称)
            if not Cookie:
                return False
            过期时间 = Cookie.get("expires")
            if isinstance(过期时间, (int, float)) and 过期时间 > 0 and 过期时间 <= 当前时间戳:
                return False

        return True

    async def 检查登录态(self, 页面: Any, 店铺ID: Optional[str]) -> bool:
        """
        检查页面当前登录态是否有效。

        返回 True 表示有效，False 表示需要重新登录。
        """
        当前地址 = str(getattr(页面, "url", "") or "")
        if self.是否登录页地址(当前地址):
            日志记录器.warning(f"检测到登录页地址，判定登录态失效: shop_id={店铺ID}, url={当前地址}")
            return False

        页面文本 = await self._读取页面文本(页面)
        if 页面文本 and any(特征 in 页面文本 for 特征 in 登录态文案特征):
            日志记录器.warning(f"检测到登录态失效文案: shop_id={店铺ID}, url={当前地址}")
            return False

        if not await self._检查关键Cookie(页面):
            日志记录器.warning(f"检测到关键 Cookie 缺失或过期: shop_id={店铺ID}, url={当前地址}")
            return False

        return True

    async def _发布Redis事件(self, 事件数据: dict[str, Any]) -> None:
        Redis地址 = str(配置实例.REDIS_URL or "").strip()
        if not Redis地址:
            return

        客户端 = None
        try:
            客户端 = aioredis.from_url(Redis地址)
            await 客户端.publish("session:expired", json.dumps(事件数据, ensure_ascii=False))
        except Exception as 异常:
            日志记录器.warning(f"发布登录态失效 Redis 事件失败: {异常}")
        finally:
            if 客户端 is not None:
                try:
                    关闭方法 = getattr(客户端, "aclose", None)
                    if callable(关闭方法):
                        await 关闭方法()
                    else:
                        await 客户端.close()
                except Exception:
                    pass

    async def 触发失效告警(self, 店铺ID: Optional[str], 店铺名称: Optional[str], 原因: str) -> None:
        """写入日志、发送飞书并广播 Redis 告警事件。"""
        消息 = f"店铺登录态已失效: {店铺名称 or 店铺ID or '未知店铺'}"
        详情 = str(原因 or "检测到登录态失效")

        try:
            await 日志服务实例.写入日志(
                shop_id=店铺ID,
                shop_name=店铺名称,
                level="ERROR",
                source="session_monitor",
                message=消息,
                detail=详情,
            )
        except Exception as 异常:
            日志记录器.warning(f"写入登录态告警日志失败: {异常}")

        if str(配置实例.FEISHU_WEBHOOK_URL or "").strip():
            try:
                await 飞书服务实例.发送文本通知(
                    f"[登录态失效告警]\n店铺ID: {店铺ID or '-'}\n店铺名称: {店铺名称 or '-'}\n原因: {详情}"
                )
            except Exception as 异常:
                日志记录器.warning(f"发送飞书登录态告警失败: {异常}")

        await self._发布Redis事件(
            {
                "shop_id": 店铺ID,
                "shop_name": 店铺名称,
                "reason": 详情,
                "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
            }
        )


登录态监控实例 = 登录态监控器()
