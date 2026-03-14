"""限时限量任务模块。"""
from typing import Any

from browser.任务回调 import 自动回调, 上报
from pages.限时限量页 import 限时限量页
from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task


@register_task("限时限量", "批量创建限时折扣活动")
class 限时限量任务(基础任务):
    """根据单条任务参数创建限时折扣活动。"""

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

    def _读取商品折扣列表(self, 任务参数: dict[str, Any]) -> list[tuple[str, float]]:
        """兼容单商品和合并参数格式，返回逐商品折扣列表。"""
        商品参数映射 = 任务参数.get("商品参数映射")
        if isinstance(商品参数映射, dict) and 商品参数映射:
            商品ID列表原始值 = 任务参数.get("商品ID列表") or list(商品参数映射.keys())
            if isinstance(商品ID列表原始值, str):
                商品ID列表 = [片段.strip() for 片段 in 商品ID列表原始值.split(",") if 片段.strip()]
            else:
                商品ID列表 = [str(商品ID).strip() for 商品ID in 商品ID列表原始值 if str(商品ID).strip()]

            商品折扣列表: list[tuple[str, float]] = []
            for 商品ID in 商品ID列表:
                商品参数 = 商品参数映射.get(商品ID)
                if not isinstance(商品参数, dict):
                    continue
                商品折扣列表.append((商品ID, self._读取折扣(商品参数)))
            if 商品折扣列表:
                return 商品折扣列表

        新商品ID = self._读取字符串参数(任务参数, "新商品ID", "new_product_id")
        if not 新商品ID:
            return []
        return [(新商品ID, self._读取折扣(任务参数))]

    async def _安全截图(self, 页面对象: 限时限量页 | None, 名称: str) -> None:
        """在成功或失败场景下尽量保留页面截图。"""
        if 页面对象 is None:
            return

        try:
            await 页面对象.截图(名称)
        except Exception:
            pass

    def _构建执行结果(self, 批次ID: str, 商品折扣列表: list[tuple[str, float]]) -> dict[str, Any]:
        """统一构建任务结果。"""
        结果 = {
            "商品数量": len(商品折扣列表),
            "商品列表": [
                {"商品ID": 商品ID, "折扣": 折扣值}
                for 商品ID, 折扣值 in 商品折扣列表
            ],
        }
        if 商品折扣列表:
            首商品ID, 首折扣值 = 商品折扣列表[0]
            结果["新商品ID"] = 首商品ID
            结果["折扣"] = 首折扣值
        if 批次ID:
            结果["batch_id"] = 批次ID
        return 结果

    @自动回调("限时限量")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        """执行限时限量单商品创建流程。"""
        self._执行结果 = {}
        任务参数 = 店铺配置.get("task_param") or 店铺配置.get("params") or {}
        批次ID = self._读取字符串参数(任务参数, "batch_id", "batchId")
        店铺ID = 店铺配置.get("shop_id") or 店铺配置.get("username") or "临时店铺"
        商品折扣列表 = self._读取商品折扣列表(任务参数)

        if not 商品折扣列表:
            await 上报("跳过：无新商品ID", 店铺ID)
            return "跳过：无新商品ID"

        self._执行结果 = self._构建执行结果(批次ID, 商品折扣列表)

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

            for 商品ID, _ in 商品折扣列表:
                await 上报(f"选择商品: {商品ID}", 店铺ID)
                await 页面对象.弹窗输入商品ID(商品ID)
                await 页面对象.弹窗点击查询()
                await 页面对象.弹窗等待结果()
                await 页面对象.弹窗勾选第一行()

            await 上报("确认选择商品", 店铺ID)
            await 页面对象.弹窗点击确认选择()

            for 商品ID, 折扣值 in 商品折扣列表:
                await 上报(f"输入商品折扣: 商品ID={商品ID}, 折扣={折扣值}", 店铺ID)
                await 页面对象.输入商品折扣(商品ID, 折扣值)

            await 上报("创建限时限量活动", 店铺ID)
            await 页面对象.点击创建()

            await 上报("等待创建成功提示", 店铺ID)
            if await 页面对象.等待创建成功():
                await self._安全截图(页面对象, "限时限量创建成功")
                await 上报(f"[成功] 限时限量创建成功，商品数: {len(商品折扣列表)}", 店铺ID)
                return "成功"

            await self._安全截图(页面对象, "限时限量创建失败")
            await 上报("[失败] 限时限量创建失败", 店铺ID)
            return "失败"
        except Exception as 异常:
            await self._安全截图(页面对象, "限时限量任务异常")
            await 上报(f"[失败] 限时限量任务异常: {异常}", 店铺ID)
            return "失败"
