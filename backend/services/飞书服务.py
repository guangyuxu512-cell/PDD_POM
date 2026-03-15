"""
飞书服务模块

封装飞书机器人 Webhook 通知与多维表格回写能力。
"""
from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from backend.配置 import 配置实例


class 飞书服务:
    """飞书 API 封装：Webhook 通知 + 多维表格回写。"""

    def __init__(
        self,
        webhook_url: str = "",
        app_id: str = "",
        app_secret: str = "",
        bitable_app_token: str = "",
        bitable_table_id: str = "",
    ):
        self.webhook_url = str(webhook_url or getattr(配置实例, "FEISHU_WEBHOOK_URL", "") or "").strip()
        self.app_id = str(app_id or getattr(配置实例, "FEISHU_APP_ID", "") or "").strip()
        self.app_secret = str(app_secret or getattr(配置实例, "FEISHU_APP_SECRET", "") or "").strip()
        self.bitable_app_token = str(
            bitable_app_token or getattr(配置实例, "FEISHU_BITABLE_APP_TOKEN", "") or ""
        ).strip()
        self.bitable_table_id = str(
            bitable_table_id or getattr(配置实例, "FEISHU_BITABLE_TABLE_ID", "") or ""
        ).strip()
        self._tenant_access_token = ""
        self._tenant_access_token_过期时间 = 0.0

    @staticmethod
    def _成功响应(data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        return {"success": True, "data": data or {}}

    @staticmethod
    def _失败响应(错误信息: str) -> dict[str, Any]:
        return {"success": False, "error": 错误信息}

    async def _发送webhook请求(self, 载荷: dict[str, Any]) -> dict[str, Any]:
        if not self.webhook_url:
            return self._失败响应("未配置飞书 Webhook 地址")

        try:
            async with httpx.AsyncClient(timeout=10.0) as 客户端:
                响应 = await 客户端.post(self.webhook_url, json=载荷)
                响应.raise_for_status()
                return self._成功响应(响应.json())
        except Exception as 异常:
            return self._失败响应(str(异常))

    async def 发送文本通知(self, 内容: str) -> dict[str, Any]:
        """发送飞书文本通知。"""
        return await self._发送webhook请求(
            {
                "msg_type": "text",
                "content": {"text": 内容},
            }
        )

    async def 发送卡片通知(self, 标题: str, 内容列表: list[dict]) -> dict[str, Any]:
        """发送飞书交互卡片通知。"""
        元素列表: list[dict[str, Any]] = []
        for 内容项 in 内容列表:
            if not isinstance(内容项, dict):
                continue

            if 内容项.get("tag"):
                元素列表.append(dict(内容项))
                continue

            markdown = "\n".join(
                f"**{键}**: {值}"
                for 键, 值 in 内容项.items()
                if 值 not in (None, "")
            )
            if markdown:
                元素列表.append(
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": markdown,
                        },
                    }
                )

        return await self._发送webhook请求(
            {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": 标题,
                        }
                    },
                    "elements": 元素列表,
                },
            }
        )

    async def 发送售后通知(self, 订单数据: dict, 处理结果: str) -> dict[str, Any]:
        """发送售后处理结果通知。"""
        订单号 = (
            订单数据.get("订单号")
            or 订单数据.get("order_no")
            or 订单数据.get("order_id")
            or "-"
        )
        金额 = (
            订单数据.get("金额")
            or 订单数据.get("退款金额")
            or 订单数据.get("amount")
            or "-"
        )
        类型 = (
            订单数据.get("售后类型")
            or 订单数据.get("类型")
            or 订单数据.get("type")
            or "-"
        )
        店铺 = 订单数据.get("店铺") or 订单数据.get("shop_name") or "-"

        return await self.发送卡片通知(
            "售后处理通知",
            [
                {
                    "订单号": 订单号,
                    "金额": 金额,
                    "售后类型": 类型,
                    "店铺": 店铺,
                    "处理结果": 处理结果,
                }
            ],
        )

    async def _获取tenant_access_token(self) -> str:
        """获取并缓存 tenant_access_token。"""
        当前时间 = time.time()
        if (
            self._tenant_access_token
            and 当前时间 < self._tenant_access_token_过期时间 - 300
        ):
            return self._tenant_access_token

        if not self.app_id or not self.app_secret:
            return ""

        try:
            async with httpx.AsyncClient(timeout=10.0) as 客户端:
                响应 = await 客户端.post(
                    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                    json={
                        "app_id": self.app_id,
                        "app_secret": self.app_secret,
                    },
                )
                响应.raise_for_status()
                数据 = 响应.json()
        except Exception:
            return ""

        token = str(数据.get("tenant_access_token") or "").strip()
        if not token:
            return ""

        过期秒数 = int(数据.get("expire", 7200) or 7200)
        self._tenant_access_token = token
        self._tenant_access_token_过期时间 = 当前时间 + 过期秒数
        return token

    async def 写入多维表格(self, app_token: str, table_id: str, 记录: dict) -> dict:
        """写入单条多维表格记录。"""
        token = await self._获取tenant_access_token()
        if not token:
            return self._失败响应("获取 tenant_access_token 失败")

        try:
            async with httpx.AsyncClient(timeout=10.0) as 客户端:
                响应 = await 客户端.post(
                    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"fields": 记录},
                )
                响应.raise_for_status()
                return self._成功响应(响应.json())
        except Exception as 异常:
            return self._失败响应(str(异常))

    async def 批量写入多维表格(self, app_token: str, table_id: str, 记录列表: list[dict]) -> dict:
        """批量写入多维表格记录。"""
        token = await self._获取tenant_access_token()
        if not token:
            return self._失败响应("获取 tenant_access_token 失败")

        try:
            async with httpx.AsyncClient(timeout=10.0) as 客户端:
                响应 = await 客户端.post(
                    f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"records": [{"fields": 记录} for 记录 in 记录列表]},
                )
                响应.raise_for_status()
                return self._成功响应(响应.json())
        except Exception as 异常:
            return self._失败响应(str(异常))

    async def 测试webhook(self) -> bool:
        """测试 Webhook 连通性。"""
        结果 = await self.发送文本通知("飞书 Webhook 连通性测试")
        return bool(结果.get("success"))


飞书服务实例 = 飞书服务()
