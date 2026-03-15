"""售后任务模块。"""
from __future__ import annotations

import asyncio
from enum import Enum
from typing import Any

from browser.任务回调 import 自动回调, 上报
from backend.services.规则服务 import 规则服务
from backend.services.飞书服务 import 飞书服务
from pages.售后页 import 售后页
from pages.微信页 import 微信页
from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task


class 售后状态(Enum):
    初始化 = "初始化"
    打开售后列表 = "打开售后列表"
    读取售后单 = "读取售后单"
    匹配规则 = "匹配规则"
    执行页面操作 = "执行页面操作"
    处理弹窗 = "处理弹窗"
    发送微信 = "发送微信"
    发送飞书 = "发送飞书"
    记录结果 = "记录结果"
    处理下一单 = "处理下一单"
    完成 = "完成"
    失败 = "失败"


状态转移表 = {
    售后状态.初始化: 售后状态.打开售后列表,
    售后状态.打开售后列表: 售后状态.读取售后单,
    售后状态.读取售后单: 售后状态.匹配规则,
    售后状态.匹配规则: 售后状态.执行页面操作,
    售后状态.执行页面操作: 售后状态.处理弹窗,
    售后状态.处理弹窗: 售后状态.发送微信,
    售后状态.发送微信: 售后状态.发送飞书,
    售后状态.发送飞书: 售后状态.记录结果,
    售后状态.记录结果: 售后状态.处理下一单,
    售后状态.处理下一单: 售后状态.读取售后单,
}


@register_task("售后处理", "根据规则自动处理售后单（退款/退货/通知）")
class 售后任务(基础任务):
    """状态机驱动的售后处理任务。"""

    def __init__(self):
        self._当前状态 = 售后状态.初始化
        self._售后页: 售后页 | None = None
        self._规则服务 = 规则服务()
        self._飞书服务 = 飞书服务()
        self._处理结果列表: list[dict[str, Any]] = []
        self._当前行号 = 1
        self._当前订单数据: dict[str, Any] = {}
        self._当前动作列表: list[dict[str, Any]] = []
        self._执行结果: dict[str, Any] = {}

    async def _转移状态(self, 下一状态: 售后状态):
        """记录状态转移日志。"""
        print(f"[售后状态机] {self._当前状态.value} -> {下一状态.value}")
        self._当前状态 = 下一状态

    async def _执行状态(self, 页面, 店铺配置: dict) -> 售后状态:
        """根据当前状态执行对应逻辑，返回下一状态。"""
        match self._当前状态:
            case 售后状态.初始化:
                self._售后页 = 售后页(页面)
                return 售后状态.打开售后列表

            case 售后状态.打开售后列表:
                await self._售后页.导航到售后列表()
                await self._售后页.切换待处理()
                return 售后状态.读取售后单

            case 售后状态.读取售后单:
                总数 = await self._售后页.获取售后单数量()
                if self._当前行号 > 总数:
                    return 售后状态.完成
                self._当前订单数据 = await self._售后页.获取第N行信息(self._当前行号)
                return 售后状态.匹配规则

            case 售后状态.匹配规则:
                shop_id = str(店铺配置.get("shop_id") or "*").strip() or "*"
                self._当前动作列表 = await self._规则服务.匹配规则(
                    platform="pdd",
                    business="售后",
                    shop_id=shop_id,
                    数据=self._当前订单数据,
                )
                for 动作 in self._当前动作列表:
                    if 动作.get("action") in {"人工处理", "人工审核"}:
                        return 售后状态.发送飞书
                return 售后状态.执行页面操作

            case 售后状态.执行页面操作:
                for 动作 in self._当前动作列表:
                    if 动作.get("type") != "页面操作":
                        continue
                    操作 = str(动作.get("action") or "").strip()
                    if 操作 == "同意退款":
                        await self._售后页.点击第N行操作(self._当前行号, "同意退款")
                    elif 操作 == "同意退货":
                        await self._售后页.点击第N行操作(self._当前行号, "同意退货")
                    elif 操作 == "拒绝":
                        await self._售后页.点击第N行操作(self._当前行号, "拒绝")
                return 售后状态.处理弹窗

            case 售后状态.处理弹窗:
                await self._售后页.处理确认弹窗()
                return 售后状态.发送微信

            case 售后状态.发送微信:
                微信动作列表 = [动作 for 动作 in self._当前动作列表 if 动作.get("type") == "微信通知"]
                if 微信动作列表:
                    try:
                        任务参数 = 店铺配置.get("task_param", {}) or {}
                        联系人 = str(任务参数.get("客户微信") or "").strip()
                        if 联系人:
                            模板 = str(微信动作列表[0].get("template") or "您的售后已处理")
                            消息 = self._渲染模板(模板, self._当前订单数据)
                            微信 = 微信页()
                            发送结果 = await asyncio.to_thread(微信.发送消息, 联系人, 消息)
                            if not 发送结果:
                                await 上报("[警告] 微信通知发送失败", 店铺配置.get("shop_id", ""))
                        else:
                            await 上报("[警告] 缺少客户微信，跳过微信通知", 店铺配置.get("shop_id", ""))
                    except Exception as 异常:
                        await 上报(f"[警告] 微信通知异常: {异常}", 店铺配置.get("shop_id", ""))
                return 售后状态.发送飞书

            case 售后状态.发送飞书:
                飞书动作列表 = [动作 for 动作 in self._当前动作列表 if 动作.get("type") == "飞书通知"]
                if 飞书动作列表:
                    try:
                        发送结果 = await self._飞书服务.发送售后通知(
                            self._当前订单数据,
                            str(飞书动作列表[0].get("action") or "通知"),
                        )
                        if not 发送结果.get("success"):
                            await 上报(
                                f"[警告] 飞书通知发送失败: {发送结果.get('error', '未知错误')}",
                                店铺配置.get("shop_id", ""),
                            )
                    except Exception as 异常:
                        await 上报(f"[警告] 飞书通知异常: {异常}", 店铺配置.get("shop_id", ""))
                return 售后状态.记录结果

            case 售后状态.记录结果:
                self._处理结果列表.append(
                    {
                        "订单号": self._当前订单数据.get("订单号", ""),
                        "售后类型": self._当前订单数据.get("售后类型", ""),
                        "处理方式": [动作.get("action") for 动作 in self._当前动作列表],
                        "状态": "已处理",
                    }
                )
                self._执行结果 = {
                    "处理数量": len(self._处理结果列表),
                    "处理结果列表": list(self._处理结果列表),
                }
                return 售后状态.处理下一单

            case 售后状态.处理下一单:
                self._当前行号 += 1
                return 售后状态.读取售后单

        return 售后状态.失败

    def _渲染模板(self, 模板: str, 数据: dict) -> str:
        """简单模板渲染，把 {字段名} 替换为数据值。"""
        结果 = str(模板)
        for 键, 值 in 数据.items():
            结果 = 结果.replace(f"{{{键}}}", str(值))
        return 结果

    @自动回调("售后处理")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        """状态机主循环。"""
        self._当前状态 = 售后状态.初始化
        self._当前行号 = 1
        self._处理结果列表 = []
        self._当前订单数据 = {}
        self._当前动作列表 = []
        self._执行结果 = {}
        店铺ID = 店铺配置.get("shop_id", "")

        最大迭代 = 500
        迭代次数 = 0

        while self._当前状态 not in (售后状态.完成, 售后状态.失败):
            迭代次数 += 1
            if 迭代次数 > 最大迭代:
                await 上报("[失败] 状态机迭代超限", 店铺ID)
                return "失败"

            try:
                下一状态 = await self._执行状态(页面, 店铺配置)
                await self._转移状态(下一状态)
                await 上报(f"[{下一状态.value}]", 店铺ID)
            except Exception as 异常:
                await 上报(f"[失败] 状态={self._当前状态.value} 异常={异常}", 店铺ID)
                if self._售后页:
                    try:
                        await self._售后页.截图(f"售后异常_{self._当前状态.value}")
                    except Exception:
                        pass
                return "失败"

        self._执行结果 = {
            "处理数量": len(self._处理结果列表),
            "处理结果列表": list(self._处理结果列表),
        }
        await 上报(f"[完成] 处理了 {len(self._处理结果列表)} 单", 店铺ID)
        return f"成功处理 {len(self._处理结果列表)} 单"
