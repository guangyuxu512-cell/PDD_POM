"""售后任务模块。"""
from __future__ import annotations

import re
from typing import Any

from browser.任务回调 import 自动回调, 上报
from backend.services.售后队列服务 import 售后队列服务
from pages.售后页 import 售后页
from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task


@register_task("售后处理", "扫描待商家处理售后单，写入售后队列")
class 售后任务(基础任务):
    """仅负责扫描售后列表并写入工作队列。"""

    def __init__(self):
        self._售后页: 售后页 | None = None
        self._队列服务 = 售后队列服务()

    @staticmethod
    def _提取金额(文本: Any) -> float:
        if isinstance(文本, (int, float)):
            return float(文本)
        匹配 = re.search(r"(\d+(?:\.\d+)?)", str(文本 or ""))
        return float(匹配.group(1)) if 匹配 else 0.0

    @staticmethod
    def _判断售后类型(原始类型: str) -> str:
        文本 = str(原始类型 or "").strip()
        if "退货" in 文本 and "退款" in 文本:
            return "退货退款"
        if "退款" in 文本:
            return "退款"
        if "补寄" in 文本:
            return "补寄"
        if "换货" in 文本:
            return "换货"
        if "维修" in 文本:
            return "维修"
        return 文本

    def _构建队列记录(
        self,
        摘要: dict[str, Any],
        批次ID: str,
        店铺ID: str,
        店铺名称: str,
    ) -> dict[str, Any]:
        原始类型 = str(摘要.get("售后类型", "") or "").strip()
        标准售后类型 = self._判断售后类型(原始类型)
        需要人工 = 标准售后类型 in {"补寄", "换货", "维修"}
        return {
            "batch_id": 批次ID,
            "shop_id": 店铺ID,
            "shop_name": 店铺名称,
            "订单号": 摘要.get("订单号", ""),
            "售后类型": 标准售后类型,
            "售后类型_原始": 原始类型,
            "售后状态": 摘要.get("售后状态", ""),
            "退款金额": self._提取金额(摘要.get("退款金额", "")),
            "商品名称": 摘要.get("商品名称", ""),
            "需要人工": 需要人工,
        }

    def _构建当前页队列记录列表(
        self,
        摘要列表: list[dict[str, Any]],
        批次ID: str,
        店铺ID: str,
        店铺名称: str,
    ) -> list[dict[str, Any]]:
        当前页记录映射: dict[str, dict[str, Any]] = {}
        for 摘要 in 摘要列表:
            if not isinstance(摘要, dict):
                continue
            队列记录 = self._构建队列记录(摘要, 批次ID, 店铺ID, 店铺名称)
            订单号 = str(队列记录.get("订单号", "") or "").strip()
            if not 订单号:
                continue
            当前页记录映射[订单号] = 队列记录
        return list(当前页记录映射.values())

    @自动回调("售后处理")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        店铺ID = str(店铺配置.get("shop_id", "") or "").strip()
        店铺名称 = str(店铺配置.get("shop_name", "") or "").strip()
        self._售后页 = 售后页(页面)

        try:
            await 上报("[扫描] 开始扫描售后列表", 店铺ID)
            批次ID = await self._队列服务.创建批次(店铺ID)
            当前页数据 = await self._售后页.导航并拦截售后列表()

            页码 = 1
            总扫描数 = 0
            总写入数 = 0
            已扫描订单号集合: set[str] = set()

            while True:
                队列记录列表 = self._构建当前页队列记录列表(
                    当前页数据,
                    批次ID,
                    店铺ID,
                    店铺名称,
                )
                if not 队列记录列表:
                    if 页码 == 1:
                        await 上报("[完成] 无待处理售后单", 店铺ID)
                        return "无待处理售后单"
                    await 上报(f"[扫描] 第{页码}页无有效售后单，结束扫描", 店铺ID)
                    break

                当前页订单号集合 = {
                    str(记录.get("订单号", "") or "").strip()
                    for 记录 in 队列记录列表
                    if str(记录.get("订单号", "") or "").strip()
                }
                新订单数 = len(当前页订单号集合 - 已扫描订单号集合)
                if 新订单数 == 0:
                    await 上报(f"[扫描] 第{页码}页全部为已扫描订单，停止翻页", 店铺ID)
                    break
                已扫描订单号集合.update(当前页订单号集合)

                写入数 = await self._队列服务.批量写入队列(队列记录列表)
                总扫描数 += len(队列记录列表)
                总写入数 += 写入数
                await 上报(
                    f"[扫描] 第{页码}页 扫描{len(队列记录列表)}单(新{新订单数}单)，写入{写入数}单",
                    店铺ID,
                )

                下一页数据 = await self._售后页.翻页并拦截()
                if 下一页数据 is None:
                    break
                当前页数据 = 下一页数据
                页码 += 1

            汇总 = f"扫描{总扫描数}单, 写入{总写入数}单"
            await 上报(f"[完成] {汇总}", 店铺ID)
            return 汇总
        except Exception as 异常:
            await 上报(f"[失败] 售后任务异常: {异常}", 店铺ID)
            return f"失败: {异常}"


# Step 1 ✅ 扫描 + 写入（当前版本）
# Step 2 → 打开详情页 + 抓取详情信息
# Step 3 → 恢复决策引擎（基于5种售后类型）
# Step 4 → 按钮点击 + 弹窗处理
# Step 5 → 飞书通知 + 备注
