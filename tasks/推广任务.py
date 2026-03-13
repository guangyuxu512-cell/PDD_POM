"""推广任务模块。"""
from __future__ import annotations

from typing import Any

from browser.任务回调 import 自动回调, 上报
from pages.推广页 import 推广页
from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task


@register_task("设置推广", "为商品设置全站推广（稳定成本）")
class 推广任务(基础任务):
    """为指定商品设置全站推广。"""

    def __init__(self):
        self._执行结果: dict[str, Any] = {}

    @staticmethod
    def _读取字符串参数(任务参数: dict[str, Any], *键名: str) -> str:
        for 键名项 in 键名:
            值 = 任务参数.get(键名项)
            if isinstance(值, str):
                清理值 = 值.strip()
                if 清理值:
                    return 清理值
        return ""

    @staticmethod
    def _读取商品ID列表(任务参数: dict[str, Any]) -> list[str]:
        原始值 = (
            任务参数.get("商品ID列表")
            or 任务参数.get("商品ID")
            or 任务参数.get("product_ids")
            or 任务参数.get("goods_ids")
        )
        if isinstance(原始值, list):
            return [str(值).strip() for 值 in 原始值 if str(值).strip()]
        if isinstance(原始值, str):
            return [片段.strip() for 片段 in 原始值.split(",") if 片段.strip()]
        return []

    @staticmethod
    def _读取浮点参数(任务参数: dict[str, Any], 默认值: float, *键名: str) -> float:
        for 键名项 in 键名:
            原始值 = 任务参数.get(键名项)
            if 原始值 in (None, ""):
                continue
            try:
                return float(原始值)
            except (TypeError, ValueError):
                continue
        return 默认值

    @自动回调("设置推广")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        任务参数 = 店铺配置.get("task_param") or {}
        商品ID列表 = self._读取商品ID列表(任务参数)
        一阶段投产比 = self._读取浮点参数(任务参数, 5.0, "一阶段投产比", "phase1_roi")
        二阶段投产比 = self._读取浮点参数(任务参数, 5.0, "二阶段投产比", "phase2_roi")
        需要关闭极速起量 = True
        店铺ID = 店铺配置.get("shop_id") or 店铺配置.get("username") or "临时店铺"

        if not 商品ID列表:
            raise ValueError("商品ID列表不能为空")

        页面对象 = 推广页(页面)
        成功列表: list[str] = []
        失败列表: list[str] = []
        self._执行结果 = {}

        try:
            await 上报("打开全站推广页", 店铺ID)
            await 页面对象.导航到全站推广页()

            await 上报("关闭广告弹窗", 店铺ID)
            await 页面对象.关闭广告弹窗()
            await 页面对象.关闭广告弹窗()

            await 上报("点击添加推广商品", 店铺ID)
            if not await 页面对象.点击添加推广商品():
                raise RuntimeError("点击添加推广商品失败")

            await 上报("检查全局优先起量状态", 店铺ID)
            if await 页面对象.获取全局优先起量状态() == "true":
                await 上报("关闭全局优先起量", 店铺ID)
                if not await 页面对象.点击全局优先起量开关():
                    raise RuntimeError("点击全局优先起量开关失败")
                if not await 页面对象.确认关闭优先起量():
                    raise RuntimeError("确认关闭优先起量失败")

            搜索文本 = ",".join(商品ID列表)
            已搜索商品ID列表: list[str] = []
            for 重试次数 in range(1, 6):
                await 上报(f"查询推广商品（第{重试次数}次）", 店铺ID)
                if not await 页面对象.输入商品ID(搜索文本):
                    continue
                if not await 页面对象.点击查询():
                    continue
                已搜索商品ID列表 = await 页面对象.获取列表商品ID()
                if set(商品ID列表).issubset(set(已搜索商品ID列表)):
                    break
            else:
                raise RuntimeError(f"商品查询结果不完整: {已搜索商品ID列表}")

            await 上报("全选推广商品", 店铺ID)
            if not await 页面对象.点击全选():
                raise RuntimeError("点击全选失败")

            for 商品ID in 商品ID列表:
                await 上报(f"设置商品投产比: {商品ID}", 店铺ID)
                if not await 页面对象.点击投产设置按钮(商品ID):
                    失败列表.append(商品ID)
                    continue

                if 需要关闭极速起量 and await 页面对象.获取极速起量状态(商品ID) == "true":
                    await 上报(f"关闭极速起量: {商品ID}", 店铺ID)
                    if not await 页面对象.点击极速起量开关(商品ID):
                        失败列表.append(商品ID)
                        continue
                    await 页面对象.确认关闭极速起量()

                if not await 页面对象.填写一阶段投产比(一阶段投产比):
                    失败列表.append(商品ID)
                    continue

                if await 页面对象.检测投产比限制():
                    await 上报(f"商品受投产比限制，跳过: {商品ID}", 店铺ID)
                    await 页面对象.取消投产设置(商品ID)
                    await 页面对象.取消勾选商品(商品ID)
                    失败列表.append(商品ID)
                    continue

                if not await 页面对象.点击编辑二阶段(商品ID):
                    失败列表.append(商品ID)
                    continue
                if not await 页面对象.填写二阶段投产比(二阶段投产比):
                    失败列表.append(商品ID)
                    continue
                if not await 页面对象.确认二阶段():
                    失败列表.append(商品ID)
                    continue
                if not await 页面对象.确认投产设置(商品ID):
                    失败列表.append(商品ID)
                    continue

                成功列表.append(商品ID)

            self._执行结果 = {
                "推广商品数": len(成功列表),
                "成功列表": 成功列表,
                "失败列表": 失败列表,
                "一阶段投产比": 一阶段投产比,
                "二阶段投产比": 二阶段投产比,
            }

            if not 成功列表:
                await 上报("跳过：无可推广商品", 店铺ID)
                return "跳过：无可推广商品"

            await 上报("点击开启推广", 店铺ID)
            if not await 页面对象.点击开启推广():
                raise RuntimeError("点击开启推广失败")

            await 上报("等待推广成功", 店铺ID)
            if not await 页面对象.等待推广成功():
                await 页面对象.截图("推广失败")
                return "失败"

            await 上报("返回商品列表页", 店铺ID)
            await 页面对象.返回商品列表页()
            await 页面对象.截图("推广成功")
            return "成功"
        except Exception as 异常:
            self._执行结果 = {
                "推广商品数": len(成功列表),
                "成功列表": 成功列表,
                "失败列表": 失败列表,
                "一阶段投产比": 一阶段投产比,
                "二阶段投产比": 二阶段投产比,
            }
            try:
                await 页面对象.截图("推广任务异常")
            except Exception:
                pass
            await 上报(f"[失败] 推广任务异常: {异常}", 店铺ID)
            return "失败"
