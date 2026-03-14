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
    def _读取商品ID列表(任务参数: dict[str, Any]) -> list[str]:
        原始值 = (
            任务参数.get("商品ID列表")
            or 任务参数.get("商品ID")
            or 任务参数.get("新商品ID")
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

    @staticmethod
    def _读取布尔参数(任务参数: dict[str, Any], 默认值: bool, *键名: str) -> bool:
        for 键名项 in 键名:
            原始值 = 任务参数.get(键名项)
            if 原始值 in (None, ""):
                continue
            if isinstance(原始值, bool):
                return 原始值
            if isinstance(原始值, str):
                标准值 = 原始值.strip().lower()
                if 标准值 in {"true", "1", "yes", "y", "是", "开启"}:
                    return True
                if 标准值 in {"false", "0", "no", "n", "否", "关闭"}:
                    return False
        return 默认值

    @staticmethod
    def _读取商品参数映射(任务参数: dict[str, Any]) -> dict[str, dict[str, Any]]:
        原始值 = 任务参数.get("商品参数映射")
        if not isinstance(原始值, dict):
            return {}
        return {
            str(商品ID).strip(): dict(参数)
            for 商品ID, 参数 in 原始值.items()
            if str(商品ID).strip() and isinstance(参数, dict)
        }

    @自动回调("设置推广")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        任务参数 = 店铺配置.get("task_param") or {}
        商品ID列表 = self._读取商品ID列表(任务参数)
        商品参数映射 = self._读取商品参数映射(任务参数)
        默认投产比 = self._读取浮点参数(任务参数, 5.0, "投产比", "phase1_roi", "一阶段投产比")
        默认日限额 = self._读取浮点参数(任务参数, 0.0, "日限额")
        关闭极速起量 = self._读取布尔参数(任务参数, True, "关闭极速起量", "close_fast_boost")
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

            搜索文本 = ",".join(商品ID列表)
            await 上报("输入商品ID并查询", 店铺ID)
            if not await 页面对象.输入商品ID(搜索文本):
                raise RuntimeError("输入商品ID失败")
            if not await 页面对象.点击查询():
                raise RuntimeError("点击查询失败")

            for 商品ID in 商品ID列表:
                if not await 页面对象.商品行是否存在(商品ID):
                    raise RuntimeError(f"商品行不存在: {商品ID}")

            await 上报("检查全局优先起量状态", 店铺ID)
            if await 页面对象.获取全局优先起量状态() == "true":
                await 上报("关闭全局优先起量", 店铺ID)
                if not await 页面对象.点击全局优先起量开关():
                    raise RuntimeError("点击全局优先起量开关失败")
                if not await 页面对象.确认关闭全局起量():
                    raise RuntimeError("确认关闭全局起量失败")

            for 商品ID in 商品ID列表:
                try:
                    商品参数 = 商品参数映射.get(商品ID, {})
                    商品投产比 = self._读取浮点参数(
                        商品参数,
                        默认投产比,
                        "投产比",
                        "phase1_roi",
                        "一阶段投产比",
                    )
                    商品日限额 = self._读取浮点参数(商品参数, 默认日限额, "日限额")

                    if 商品日限额 > 0:
                        await 上报(f"设置日限额: {商品ID}", 店铺ID)
                        if not await 页面对象.点击更多设置(商品ID):
                            raise RuntimeError("点击更多设置失败")
                        if not await 页面对象.点击预算日限额():
                            raise RuntimeError("点击预算日限额失败")
                        if not await 页面对象.输入日限额(商品日限额):
                            raise RuntimeError("输入日限额失败")
                        if not await 页面对象.确认日限额():
                            raise RuntimeError("确认日限额失败")

                    await 上报(f"设置投产比: {商品ID}", 店铺ID)
                    if not await 页面对象.点击修改投产铅笔按钮(商品ID):
                        raise RuntimeError("点击修改投产铅笔按钮失败")
                    if not await 页面对象.等待投产弹窗():
                        raise RuntimeError("等待投产弹窗失败")

                    极速起量状态 = await 页面对象.获取极速起量高级版状态(商品ID)
                    if 极速起量状态 == "true" and 关闭极速起量:
                        await 上报(f"关闭极速起量高级版: {商品ID}", 店铺ID)
                        if not await 页面对象.点击极速起量高级版开关(商品ID):
                            raise RuntimeError("点击极速起量高级版开关失败")
                        if not await 页面对象.确认关闭极速起量(商品ID):
                            raise RuntimeError("确认关闭极速起量失败")
                    elif 极速起量状态 == "false" and not 关闭极速起量:
                        await 上报(f"开启极速起量高级版: {商品ID}", 店铺ID)
                        if not await 页面对象.点击极速起量高级版开关(商品ID):
                            raise RuntimeError("点击极速起量高级版开关失败")

                    if not await 页面对象.输入投产比(商品投产比):
                        raise RuntimeError("输入投产比失败")
                    if not await 页面对象.确认投产比设置(商品ID):
                        raise RuntimeError("确认投产比设置失败")

                    成功列表.append(商品ID)
                except Exception as 异常:
                    失败列表.append(商品ID)
                    await 上报(f"[失败] 商品推广设置失败: {商品ID}, error={异常}", 店铺ID)

            self._执行结果 = {
                "推广商品数": len(成功列表),
                "成功列表": 成功列表,
                "失败列表": 失败列表,
                "投产比": 默认投产比,
                "日限额": 默认日限额 if 默认日限额 > 0 else None,
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
                "投产比": 默认投产比,
                "日限额": 默认日限额 if 默认日限额 > 0 else None,
            }
            try:
                await 页面对象.截图("推广任务异常")
            except Exception:
                pass
            await 上报(f"[失败] 推广任务异常: {异常}", 店铺ID)
            return "失败"
