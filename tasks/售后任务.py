"""售后任务模块。"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from browser.任务回调 import 自动回调, 上报
from backend.services.规则服务 import 规则服务
from backend.services.售后决策引擎 import 售后决策引擎
from backend.services.售后队列服务 import 售后队列服务
from backend.services.飞书服务 import 飞书服务
from pages.售后页 import 售后页
from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task


@register_task("售后处理", "扫描待商家处理售后单，根据规则自动处理")
class 售后任务(基础任务):
    """基于工作队列和决策引擎的售后处理任务。"""

    def __init__(self):
        self._售后页: 售后页 | None = None
        self._队列服务 = 售后队列服务()
        self._决策引擎 = 售后决策引擎()
        self._规则服务 = 规则服务()
        self._飞书服务 = 飞书服务()
        self._执行结果: dict[str, Any] = {}

    @staticmethod
    def _提取金额(文本: Any) -> float:
        if isinstance(文本, (int, float)):
            return float(文本)
        匹配 = re.search(r"(\d+(?:\.\d+)?)", str(文本 or ""))
        return float(匹配.group(1)) if 匹配 else 0.0

    def _组装规则配置(self, 规则结果: list[dict]) -> dict:
        配置 = {
            "自动同意金额上限": 10,
            "自动退款金额上限": 50,
            "需要拒绝": False,
            "需要入库校验": False,
            "弹窗偏好": {},
            "退货物流白名单": [],
            "退货等待时间": {"刚发出": 3, "中途运输": 1, "到达目的市": 0.25},
        }
        for 动作 in 规则结果 or []:
            if 动作.get("action") == "拒绝":
                配置["需要拒绝"] = True
            if 动作.get("自动同意金额上限") not in (None, ""):
                配置["自动同意金额上限"] = self._提取金额(动作.get("自动同意金额上限"))
            if 动作.get("自动退款金额上限") not in (None, ""):
                配置["自动退款金额上限"] = self._提取金额(动作.get("自动退款金额上限"))
            if 动作.get("弹窗偏好"):
                配置["弹窗偏好"] = dict(动作.get("弹窗偏好") or {})
            if 动作.get("退货物流白名单") is not None:
                配置["退货物流白名单"] = list(动作.get("退货物流白名单") or [])
            if 动作.get("退货等待时间"):
                配置["退货等待时间"] = dict(动作.get("退货等待时间") or {})
            if 动作.get("需要入库校验") is not None:
                配置["需要入库校验"] = bool(动作.get("需要入库校验"))
        return 配置

    async def _发送飞书通知(self, 详情: dict, 店铺配置: dict, 通知内容: str) -> None:
        数据 = dict(详情 or {})
        数据["shop_name"] = 店铺配置.get("shop_name", "")
        try:
            await self._飞书服务.发送售后通知(数据, 通知内容)
        except Exception:
            pass

    async def _执行详情页转人工(
        self,
        记录: dict,
        详情: dict,
        店铺配置: dict,
        决策: dict,
    ) -> str:
        订单号 = str(详情.get("订单编号") or 详情.get("订单号") or 记录.get("订单号") or "")
        await self._售后页.详情页截图(f"人工{订单号}")
        if 决策.get("需要备注") and 决策.get("备注内容"):
            try:
                await self._售后页.详情页添加备注(决策["备注内容"])
            except Exception:
                pass
        if 决策.get("需要飞书通知"):
            await self._发送飞书通知(
                详情,
                店铺配置,
                决策.get("飞书通知内容", "需人工处理"),
            )
        await self._队列服务.标记人工(记录["id"], 决策.get("人工原因", "需人工处理"))
        await self._售后页.关闭详情标签()
        return "人工"

    async def _处理单条(self, 记录: dict, 店铺配置: dict) -> str:
        店铺ID = str(店铺配置.get("shop_id", ""))
        订单号 = str(记录.get("订单号", ""))
        await 上报(f"[处理] 订单 {订单号}", 店铺ID)
        await self._队列服务.更新阶段(记录["id"], "处理中")

        try:
            await self._售后页.点击订单详情并切换标签(订单号)
        except Exception:
            await self._队列服务.标记已被处理(记录["id"])
            return "跳过"

        try:
            详情 = await self._售后页.抓取详情页完整信息()
            售后类型 = str(详情.get("售后类型") or 记录.get("售后类型") or "")

            if "退货退款" in 售后类型:
                退货物流 = await self._售后页.抓取退货物流信息()
                详情["退货物流信息"] = 退货物流

            await self._队列服务.更新详情(记录["id"], 详情)

            退货物流信息 = dict(详情.get("退货物流信息") or {})
            if 退货物流信息.get("有退货物流"):
                await self._队列服务.更新退货物流(
                    记录["id"],
                    str(退货物流信息.get("退货快递公司", "")),
                    str(退货物流信息.get("退货快递单号", "")),
                    str(退货物流信息.get("轨迹全文", ""))[:2000],
                    str(
                        退货物流信息.get("退货物流状态")
                        or dict(退货物流信息.get("最新轨迹") or {}).get("描述", "")
                    ),
                )

            if not await self._售后页.检查是否需要处理():
                await self._队列服务.标记已被处理(记录["id"])
                await self._售后页.关闭详情标签()
                return "跳过"

            规则结果 = await self._规则服务.匹配规则(
                platform="pdd",
                business="售后",
                shop_id=店铺ID,
                数据=详情,
            )
            规则配置 = self._组装规则配置(规则结果)
            决策 = await self._决策引擎.决策(详情, 规则配置, 记录)
            await 上报(f"[决策] {订单号}: {决策['操作']}", 店铺ID)

            if 决策["操作"] == "跳过":
                await self._队列服务.标记已被处理(记录["id"])
                await self._售后页.关闭详情标签()
                return "跳过"

            if 决策["操作"] == "等待":
                天数 = float(决策.get("下次处理天数", 1) or 1)
                显示天数 = int(天数) if 天数.is_integer() else 天数
                下次时间 = (datetime.now() + timedelta(days=天数)).strftime("%Y-%m-%d %H:%M:%S")
                await self._队列服务.更新阶段(
                    记录["id"],
                    "等待退回",
                    下次处理时间=下次时间,
                    处理结果=f"等待{显示天数}天后复查",
                )
                await self._售后页.关闭详情标签()
                return "跳过"

            if 决策["操作"] == "等待验货":
                await self._队列服务.更新阶段(
                    记录["id"],
                    "等待验货",
                    处理结果="待入库校验",
                )
                if 决策.get("需要备注") and 决策.get("备注内容"):
                    try:
                        await self._售后页.详情页添加备注(决策["备注内容"])
                    except Exception:
                        pass
                if 决策.get("需要飞书通知"):
                    await self._发送飞书通知(
                        详情,
                        店铺配置,
                        决策.get("飞书通知内容", "待人工验货"),
                    )
                await self._售后页.关闭详情标签()
                return "人工"

            if 决策["操作"] == "人工处理":
                return await self._执行详情页转人工(记录, 详情, 店铺配置, 决策)

            点击成功 = await self._售后页.点击指定按钮(str(决策.get("目标按钮", "")))
            if not 点击成功:
                for 备选按钮 in 决策.get("备选按钮", []):
                    点击成功 = await self._售后页.点击指定按钮(str(备选按钮))
                    if 点击成功:
                        break
            if not 点击成功:
                return await self._执行详情页转人工(
                    记录,
                    详情,
                    店铺配置,
                    {
                        "人工原因": f"按钮未找到: {决策.get('目标按钮', '')}",
                        "需要备注": False,
                        "备注内容": "",
                        "需要飞书通知": False,
                        "飞书通知内容": "",
                    },
                )

            弹窗结果 = await self._售后页.弹窗扫描循环(决策.get("弹窗偏好", {}))
            if 弹窗结果 == "人工处理":
                return await self._执行详情页转人工(
                    记录,
                    详情,
                    店铺配置,
                    {
                        "人工原因": "弹窗无法自动处理",
                        "需要备注": False,
                        "备注内容": "",
                        "需要飞书通知": False,
                        "飞书通知内容": "",
                    },
                )

            if 决策["操作"] == "拒绝":
                新拒绝次数 = int(记录.get("拒绝次数", 0) or 0) + 1
                下次时间 = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                await self._队列服务.更新阶段(
                    记录["id"],
                    "待处理",
                    拒绝次数=新拒绝次数,
                    下次处理时间=下次时间,
                    处理结果=f"拒绝第{新拒绝次数}次",
                )
            else:
                await self._队列服务.标记已完成(记录["id"], f"{决策['操作']}成功")

            if 决策.get("需要备注") and 决策.get("备注内容"):
                try:
                    await self._售后页.详情页添加备注(决策["备注内容"])
                except Exception:
                    pass

            await self._售后页.关闭详情标签()
            return "已处理"
        except Exception:
            if self._售后页 and self._售后页._详情页:
                await self._售后页.详情页截图(f"异常{订单号}")
                await self._售后页.关闭详情标签()
            raise

    @自动回调("售后处理")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        店铺ID = str(店铺配置.get("shop_id", ""))
        店铺名称 = str(店铺配置.get("shop_name", ""))
        self._售后页 = 售后页(页面)
        self._执行结果 = {}
        try:
            await 上报("[扫描] 开始扫描售后列表", 店铺ID)
            批次ID = await self._队列服务.创建批次(店铺ID)

            await self._售后页.导航到售后列表()
            await self._售后页.确保待商家处理已选中()
            摘要列表 = await self._售后页.扫描所有待处理()
            if not 摘要列表:
                await 上报("[完成] 无待处理售后单", 店铺ID)
                self._执行结果 = {"总数": 0, "已完成": 0, "失败": 0, "人工": 0, "待处理": 0}
                return "无待处理售后单"

            记录列表 = [
                {
                    "batch_id": 批次ID,
                    "shop_id": 店铺ID,
                    "shop_name": 店铺名称,
                    "订单号": 摘要.get("订单号", ""),
                    "售后类型": 摘要.get("售后类型", ""),
                    "售后状态": 摘要.get("售后状态", ""),
                    "退款金额": self._提取金额(摘要.get("退款金额", "")),
                    "商品名称": 摘要.get("商品名称", ""),
                }
                for 摘要 in 摘要列表
                if 摘要.get("订单号")
            ]
            写入数 = await self._队列服务.批量写入队列(记录列表)
            await 上报(f"[扫描] 扫描到 {len(摘要列表)} 单，写入 {写入数} 单", 店铺ID)

            待处理列表 = await self._队列服务.获取待处理列表(batch_id=批次ID)
            已处理数 = 0
            人工数 = 0
            跳过数 = 0

            需要详情列表: list[dict] = []
            不需要进详情的类型 = ["补寄", "维修", "换货"]
            for 记录 in 待处理列表:
                售后类型 = str(记录.get("售后类型", ""))
                if any(类型 in 售后类型 for 类型 in 不需要进详情的类型):
                    订单号 = str(记录.get("订单号", ""))
                    备注内容 = f"【系统】{售后类型}暂不支持自动处理，转人工"
                    try:
                        await self._售后页.列表页添加备注(订单号, 备注内容)
                    except Exception:
                        pass
                    await self._发送飞书通知(记录, 店铺配置, f"{售后类型}转人工处理")
                    await self._队列服务.标记人工(记录["id"], f"{售后类型}不支持自动处理")
                    人工数 += 1
                    continue
                需要详情列表.append(记录)

            for 记录 in 需要详情列表:
                try:
                    结果 = await self._处理单条(记录, 店铺配置)
                    if 结果 == "已处理":
                        已处理数 += 1
                    elif 结果 == "人工":
                        人工数 += 1
                    else:
                        跳过数 += 1
                except Exception as 异常:
                    await 上报(f"[失败] 订单{记录.get('订单号')} 异常: {异常}", 店铺ID)
                    await self._队列服务.更新阶段(记录["id"], "失败", 错误信息=str(异常))
                    if self._售后页 and self._售后页._详情页:
                        await self._售后页.详情页截图(f"异常{记录.get('订单号')}")
                        await self._售后页.关闭详情标签()

            汇总 = f"处理{已处理数}单, 人工{人工数}单, 跳过{跳过数}单"
            await 上报(f"[完成] {汇总}", 店铺ID)
            self._执行结果 = await self._队列服务.获取批次统计(批次ID)
            return 汇总
        except Exception as 异常:
            await 上报(f"[失败] 售后任务异常: {异常}", 店铺ID)
            return f"失败: {异常}"
