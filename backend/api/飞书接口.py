"""
飞书接口模块

提供飞书 Webhook 测试接口。
"""
from typing import Any, Dict

from fastapi import APIRouter, Body

from backend.models.数据结构 import 统一响应, 成功, 失败
from backend.services.飞书服务 import 飞书服务


路由 = APIRouter(prefix="/api/feishu", tags=["飞书配置"])


@路由.post("/test-webhook", summary="测试飞书 Webhook")
async def 测试飞书Webhook(
    请求体: Dict[str, Any] = Body(..., description="Webhook 配置")
) -> 统一响应:
    """测试飞书机器人 Webhook 连通性。"""
    webhook_url = str(请求体.get("webhook_url") or "").strip()
    if not webhook_url:
        return 失败("webhook_url 不能为空", data={"success": False, "message": "webhook_url 不能为空"})

    服务 = 飞书服务(webhook_url=webhook_url)
    成功标志 = await 服务.测试webhook()
    if 成功标志:
        return 成功(data={"success": True, "message": "发送成功"})
    return 失败("发送失败", data={"success": False, "message": "发送失败"})
