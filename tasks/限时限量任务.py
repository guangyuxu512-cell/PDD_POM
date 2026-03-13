"""限时限量任务模块。"""
import json
from typing import Any

from backend.services.任务参数服务 import 任务参数服务实例
from browser.任务回调 import 自动回调, 上报
from pages.限时限量页 import 限时限量页
from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task


@register_task("限时限量", "批量创建限时折扣活动")
class 限时限量任务(基础任务):
    """根据同批次成功发布商品批量创建限时折扣活动。"""

    def __init__(self):
        self._执行结果: dict[str, Any] = {}

    @staticmethod
    def _读取字符串参数(任务参数: dict[str, Any], *键名: str) -> str:
        """按优先级读取字符串参数。"""
        for 键名项 in 键名:
            值 = str(任务参数.get(键名项) or "").strip()
            if 值:
                return 值
        return ""

    @staticmethod
    def _读取折扣(任务参数: dict[str, Any]) -> float:
        """读取并校验折扣参数。"""
        原始值 = 任务参数.get("折扣")
        if 原始值 in (None, ""):
            原始值 = 任务参数.get("discount")
        if 原始值 in (None, ""):
            raise ValueError("折扣不能为空")

        try:
            折扣值 = float(原始值)
        except (TypeError, ValueError) as 异常:
            raise ValueError("折扣必须是数字") from 异常

        if 折扣值 <= 0:
            raise ValueError("折扣必须大于 0")
        return 折扣值

    @staticmethod
    def _提取新商品ID列表(结果列表: list[Any]) -> list[str]:
        """从成功结果中提取去重后的新商品ID列表。"""
        商品ID列表: list[str] = []
        已存在商品ID: set[str] = set()

        for 结果 in 结果列表:
            记录 = 结果
            if isinstance(结果, str):
                try:
                    记录 = json.loads(结果)
                except (TypeError, json.JSONDecodeError):
                    记录 = {}

            if not isinstance(记录, dict):
                continue

            商品ID = str(记录.get("新商品ID") or 记录.get("new_product_id") or "").strip()
            if not 商品ID or 商品ID in 已存在商品ID:
                continue

            已存在商品ID.add(商品ID)
            商品ID列表.append(商品ID)

        return 商品ID列表

    async def _安全截图(self, 页面对象: 限时限量页 | None, 名称: str) -> None:
        """在成功或失败场景下尽量保留页面截图。"""
        if 页面对象 is None:
            return

        try:
            await 页面对象.截图(名称)
        except Exception:
            pass

    def _构建执行结果(self, 批次ID: str, 折扣值: float, 新商品ID列表: list[str]) -> dict[str, Any]:
        """统一构建任务结果。"""
        return {
            "batch_id": 批次ID,
            "折扣": 折扣值,
            "商品数量": len(新商品ID列表),
            "新商品ID列表": 新商品ID列表,
        }

    @自动回调("限时限量")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        """执行限时限量批量创建流程。"""
        self._执行结果 = {}
        任务参数 = 店铺配置.get("task_param") or 店铺配置.get("params") or {}
        批次ID = self._读取字符串参数(任务参数, "batch_id", "batchId")
        折扣值 = self._读取折扣(任务参数)
        店铺ID = 店铺配置.get("shop_id") or 店铺配置.get("username") or "临时店铺"

        if not 批次ID:
            raise ValueError("batch_id 不能为空")

        await 上报(f"查询批次成功记录: {批次ID}", 店铺ID)
        成功结果列表 = await 任务参数服务实例.查询批次成功记录(
            店铺ID,
            批次ID,
            "发布相似商品",
        )
        新商品ID列表 = self._提取新商品ID列表(成功结果列表)
        self._执行结果 = self._构建执行结果(批次ID, 折扣值, 新商品ID列表)

        if not 新商品ID列表:
            await 上报("跳过：无成功发布的商品", 店铺ID)
            return "跳过：无成功发布的商品"

        页面对象 = 限时限量页(页面)
        try:
            await 上报("打开限时限量创建页", 店铺ID)
            await 页面对象.导航到创建页()

            await 上报("展开更多设置", 店铺ID)
            await 页面对象.点击展开更多设置()

            await 上报("勾选自动创建活动", 店铺ID)
            await 页面对象.勾选自动创建()

            await 上报("打开选择商品弹窗", 店铺ID)
            await 页面对象.点击选择商品()

            for 商品ID in 新商品ID列表:
                await 上报(f"选择商品: {商品ID}", 店铺ID)
                await 页面对象.弹窗输入商品ID(商品ID)
                await 页面对象.弹窗点击查询()
                await 页面对象.弹窗等待结果()
                await 页面对象.弹窗勾选第一行()

            await 上报("确认选择商品", 店铺ID)
            await 页面对象.弹窗点击确认选择()

            await 上报(f"填写统一折扣: {折扣值}", 店铺ID)
            await 页面对象.填写折扣(折扣值)

            await 上报("确认折扣设置", 店铺ID)
            await 页面对象.点击确认设置()

            await 上报("创建限时限量活动", 店铺ID)
            await 页面对象.点击创建()

            await 上报("等待创建成功提示", 店铺ID)
            if await 页面对象.等待创建成功():
                await self._安全截图(页面对象, "限时限量创建成功")
                await 上报(f"[成功] 限时限量创建成功，共 {len(新商品ID列表)} 个商品", 店铺ID)
                return "成功"

            await self._安全截图(页面对象, "限时限量创建失败")
            await 上报("[失败] 限时限量创建失败", 店铺ID)
            return "失败"
        except Exception as 异常:
            await self._安全截图(页面对象, "限时限量任务异常")
            await 上报(f"[失败] 限时限量任务异常: {异常}", 店铺ID)
            return "失败"
