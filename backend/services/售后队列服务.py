"""售后工作队列 CRUD 与批次管理服务。"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import aiosqlite

from backend.models.数据库 import 获取连接


class 售后队列服务:
    """售后工作队列 CRUD + 批次管理。"""

    待到期阶段集合 = ("待处理", "等待退回", "等待验货", "待退款")
    活跃阶段集合 = ("待处理", "处理中", "等待退回", "等待验货", "待退款")

    @staticmethod
    def _解析JSON字段(原始值: Any, 默认值: Any) -> Any:
        if isinstance(原始值, (dict, list)):
            return 原始值
        if 原始值 in (None, ""):
            return 默认值
        try:
            return json.loads(str(原始值))
        except (TypeError, json.JSONDecodeError):
            return 默认值

    @staticmethod
    def _序列化JSON字段(值: Any, 默认值: Any) -> str:
        if 值 in (None, ""):
            return json.dumps(默认值, ensure_ascii=False)
        if isinstance(值, (dict, list)):
            return json.dumps(值, ensure_ascii=False)
        try:
            json.loads(str(值))
            return str(值)
        except (TypeError, json.JSONDecodeError):
            return json.dumps(默认值, ensure_ascii=False)

    @staticmethod
    def _标准化文本(值: Any) -> str:
        return str(值 or "").strip()

    @staticmethod
    def _转换金额(值: Any) -> float:
        if 值 in (None, ""):
            return 0.0
        if isinstance(值, (int, float)):
            return float(值)
        文本 = (
            str(值)
            .replace("¥", "")
            .replace("￥", "")
            .replace(",", "")
            .replace("元", "")
            .strip()
        )
        if not 文本:
            return 0.0
        return float(文本)

    def _转换记录(self, 行数据: Any) -> dict[str, Any]:
        数据 = dict(行数据)
        数据["详情数据"] = self._解析JSON字段(数据.get("详情数据"), {})
        数据["可用按钮列表"] = self._解析JSON字段(数据.get("可用按钮列表"), [])
        数据["决策动作"] = self._解析JSON字段(数据.get("决策动作"), {})
        数据["退款金额"] = float(数据.get("退款金额") or 0)
        数据["有售后图片"] = bool(int(数据.get("有售后图片") or 0))
        数据["商家已回复"] = bool(int(数据.get("商家已回复") or 0))
        数据["协商轮次"] = int(数据.get("协商轮次") or 0)
        数据["处理次数"] = int(数据.get("处理次数") or 0)
        数据["最大处理次数"] = int(数据.get("最大处理次数") or 0)
        数据["拒绝次数"] = int(数据.get("拒绝次数") or 0)
        return 数据

    def _校验基础记录(self, 记录: dict[str, Any]) -> dict[str, Any]:
        批次ID = self._标准化文本(记录.get("batch_id"))
        店铺ID = self._标准化文本(记录.get("shop_id"))
        订单号 = self._标准化文本(记录.get("订单号"))
        if not 批次ID:
            raise ValueError("batch_id 不能为空")
        if not 店铺ID:
            raise ValueError("shop_id 不能为空")
        if not 订单号:
            raise ValueError("订单号不能为空")

        return {
            "batch_id": 批次ID,
            "shop_id": 店铺ID,
            "shop_name": self._标准化文本(记录.get("shop_name")) or None,
            "退货快递公司": self._标准化文本(记录.get("退货快递公司")),
            "退货快递单号": self._标准化文本(记录.get("退货快递单号")),
            "退货物流状态": self._标准化文本(记录.get("退货物流状态")),
            "退货物流全文": self._标准化文本(记录.get("退货物流全文")),
            "订单号": 订单号,
            "售后类型": self._标准化文本(记录.get("售后类型")),
            "售后状态": self._标准化文本(记录.get("售后状态")),
            "退款金额": self._转换金额(记录.get("退款金额")),
            "商品名称": self._标准化文本(记录.get("商品名称")),
            "详情数据": self._序列化JSON字段(记录.get("详情数据"), {}),
            "申请原因": self._标准化文本(记录.get("申请原因")),
            "售后申请说明": self._标准化文本(记录.get("售后申请说明")),
            "发货物流公司": self._标准化文本(记录.get("发货物流公司")),
            "发货快递单号": self._标准化文本(记录.get("发货快递单号")),
            "有售后图片": 1 if bool(记录.get("有售后图片")) else 0,
            "物流最新状态": self._标准化文本(记录.get("物流最新状态")),
            "物流最新时间": self._标准化文本(记录.get("物流最新时间")),
            "收货城市": self._标准化文本(记录.get("收货城市")),
            "剩余处理时间": self._标准化文本(记录.get("剩余处理时间")),
            "平台建议": self._标准化文本(记录.get("平台建议")),
            "可用按钮列表": self._序列化JSON字段(记录.get("可用按钮列表"), []),
            "协商轮次": int(记录.get("协商轮次") or 0),
            "商家已回复": 1 if bool(记录.get("商家已回复")) else 0,
            "当前阶段": self._标准化文本(记录.get("当前阶段")) or "待处理",
            "处理次数": int(记录.get("处理次数") or 0),
            "最大处理次数": int(记录.get("最大处理次数") or 5),
            "下次处理时间": self._标准化文本(记录.get("下次处理时间")) or None,
            "拒绝次数": int(记录.get("拒绝次数") or 0),
            "上次拒绝时间": self._标准化文本(记录.get("上次拒绝时间")) or None,
            "匹配规则名": self._标准化文本(记录.get("匹配规则名")) or None,
            "决策动作": self._序列化JSON字段(记录.get("决策动作"), {}),
            "处理结果": self._标准化文本(记录.get("处理结果")) or None,
            "错误信息": self._标准化文本(记录.get("错误信息")) or None,
        }

    @staticmethod
    def _提取物流最新时间(详情数据: dict[str, Any]) -> str:
        候选键 = ("物流最新时间", "最新物流时间", "物流时间")
        for 键名 in 候选键:
            值 = str(详情数据.get(键名) or "").strip()
            if 值:
                return 值
        return ""

    def _构建详情更新字段(self, 详情数据: dict[str, Any]) -> dict[str, Any]:
        退货物流信息 = dict(详情数据.get("退货物流信息") or {})
        最新轨迹 = dict(退货物流信息.get("最新轨迹") or {})
        return {
            "售后类型": self._标准化文本(详情数据.get("售后类型")),
            "售后状态": self._标准化文本(详情数据.get("售后状态")),
            "退款金额": self._转换金额(详情数据.get("退款金额")),
            "商品名称": self._标准化文本(详情数据.get("商品名称")),
            "详情数据": self._序列化JSON字段(详情数据, {}),
            "退货快递公司": self._标准化文本(退货物流信息.get("退货快递公司")),
            "退货快递单号": self._标准化文本(退货物流信息.get("退货快递单号")),
            "退货物流状态": self._标准化文本(
                退货物流信息.get("退货物流状态") or 最新轨迹.get("描述")
            ),
            "退货物流全文": self._标准化文本(退货物流信息.get("轨迹全文")),
            "申请原因": self._标准化文本(详情数据.get("申请原因")),
            "售后申请说明": self._标准化文本(详情数据.get("售后申请说明")),
            "发货物流公司": self._标准化文本(详情数据.get("发货物流公司")),
            "发货快递单号": self._标准化文本(详情数据.get("发货快递单号")),
            "有售后图片": 1 if bool(详情数据.get("有售后图片")) else 0,
            "物流最新状态": self._标准化文本(详情数据.get("物流最新状态")),
            "物流最新时间": self._提取物流最新时间(详情数据),
            "收货城市": self._标准化文本(详情数据.get("收货城市")),
            "剩余处理时间": self._标准化文本(详情数据.get("剩余处理时间")),
            "平台建议": self._标准化文本(详情数据.get("平台建议")),
            "可用按钮列表": self._序列化JSON字段(详情数据.get("可用按钮列表"), []),
            "协商轮次": int(详情数据.get("协商轮次") or 0),
            "商家已回复": 1 if bool(详情数据.get("商家已回复")) else 0,
        }

    async def _执行标准化写入(
        self,
        连接: aiosqlite.Connection,
        数据: dict[str, Any],
    ) -> int:
        游标 = await 连接.execute(
            """
            INSERT INTO aftersale_queue (
                batch_id, shop_id, shop_name, 退货快递公司, 退货快递单号, 退货物流状态, 退货物流全文,
                订单号, 售后类型, 售后状态, 退款金额, 商品名称, 详情数据,
                申请原因, 售后申请说明, 发货物流公司, 发货快递单号, 有售后图片, 物流最新状态,
                物流最新时间, 收货城市, 剩余处理时间, 平台建议, 可用按钮列表, 协商轮次,
                商家已回复, 当前阶段, 处理次数, 最大处理次数, 下次处理时间, 拒绝次数,
                上次拒绝时间, 匹配规则名, 决策动作, 处理结果, 错误信息
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                数据["batch_id"],
                数据["shop_id"],
                数据["shop_name"],
                数据["退货快递公司"],
                数据["退货快递单号"],
                数据["退货物流状态"],
                数据["退货物流全文"],
                数据["订单号"],
                数据["售后类型"],
                数据["售后状态"],
                数据["退款金额"],
                数据["商品名称"],
                数据["详情数据"],
                数据["申请原因"],
                数据["售后申请说明"],
                数据["发货物流公司"],
                数据["发货快递单号"],
                数据["有售后图片"],
                数据["物流最新状态"],
                数据["物流最新时间"],
                数据["收货城市"],
                数据["剩余处理时间"],
                数据["平台建议"],
                数据["可用按钮列表"],
                数据["协商轮次"],
                数据["商家已回复"],
                数据["当前阶段"],
                数据["处理次数"],
                数据["最大处理次数"],
                数据["下次处理时间"],
                数据["拒绝次数"],
                数据["上次拒绝时间"],
                数据["匹配规则名"],
                数据["决策动作"],
                数据["处理结果"],
                数据["错误信息"],
            ),
        )
        return int(游标.lastrowid or 0)

    async def _执行写入(self, 连接: aiosqlite.Connection, 记录: dict[str, Any]) -> int:
        数据 = self._校验基础记录(记录)
        return await self._执行标准化写入(连接, 数据)

    async def _查询活跃记录(
        self,
        连接: aiosqlite.Connection,
        shop_id: str,
        订单号: str,
    ) -> aiosqlite.Row | None:
        占位符 = ", ".join("?" for _ in self.活跃阶段集合)
        async with 连接.execute(
            f"""
            SELECT id, 当前阶段
            FROM aftersale_queue
            WHERE shop_id = ? AND 订单号 = ?
              AND 当前阶段 IN ({占位符})
            ORDER BY id DESC
            LIMIT 1
            """,
            [shop_id, 订单号, *self.活跃阶段集合],
        ) as 游标:
            return await 游标.fetchone()

    async def 创建批次(self, shop_id: str) -> str:
        """生成新的 batch_id（格式: AS-{shop_id}-{时间戳}）。"""
        店铺ID = self._标准化文本(shop_id)
        if not 店铺ID:
            raise ValueError("shop_id 不能为空")
        时间戳 = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        return f"AS-{店铺ID}-{时间戳}"

    async def 写入队列(self, 记录: dict) -> int:
        """写入一条售后单到队列（从列表页扫描阶段调用）。"""
        async with 获取连接() as 连接:
            try:
                记录ID = await self._执行写入(连接, dict(记录 or {}))
            except aiosqlite.IntegrityError:
                await 连接.rollback()
                return 0
            await 连接.commit()
            return 记录ID

    async def 批量写入队列(self, 记录列表: list[dict]) -> int:
        """批量写入。返回实际写入条数。"""
        if not 记录列表:
            return 0

        已处理键集合: set[tuple[str, str]] = set()
        写入数量 = 0
        async with 获取连接() as 连接:
            for 原始记录 in 记录列表:
                记录 = dict(原始记录 or {})
                数据 = self._校验基础记录(记录)
                去重键 = (
                    数据["batch_id"],
                    数据["订单号"],
                )
                if 去重键 in 已处理键集合:
                    continue
                已处理键集合.add(去重键)

                已有记录 = await self._查询活跃记录(
                    连接,
                    数据["shop_id"],
                    数据["订单号"],
                )
                if 已有记录:
                    continue
                try:
                    记录ID = await self._执行标准化写入(连接, 数据)
                except aiosqlite.IntegrityError:
                    continue
                if 记录ID > 0:
                    写入数量 += 1
            await 连接.commit()
        return 写入数量

    async def 更新详情(self, id: int, 详情数据: dict) -> bool:
        """从详情页抓取后更新完整信息。"""
        if not isinstance(详情数据, dict):
            raise ValueError("详情数据必须是 dict")

        数据 = self._构建详情更新字段(详情数据)
        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                """
                UPDATE aftersale_queue
                SET 售后类型 = ?,
                    售后状态 = ?,
                    退款金额 = ?,
                    商品名称 = ?,
                    详情数据 = ?,
                    退货快递公司 = ?,
                    退货快递单号 = ?,
                    退货物流状态 = ?,
                    退货物流全文 = ?,
                    申请原因 = ?,
                    售后申请说明 = ?,
                    发货物流公司 = ?,
                    发货快递单号 = ?,
                    有售后图片 = ?,
                    物流最新状态 = ?,
                    物流最新时间 = ?,
                    收货城市 = ?,
                    剩余处理时间 = ?,
                    平台建议 = ?,
                    可用按钮列表 = ?,
                    协商轮次 = ?,
                    商家已回复 = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (
                    数据["售后类型"],
                    数据["售后状态"],
                    数据["退款金额"],
                    数据["商品名称"],
                    数据["详情数据"],
                    数据["退货快递公司"],
                    数据["退货快递单号"],
                    数据["退货物流状态"],
                    数据["退货物流全文"],
                    数据["申请原因"],
                    数据["售后申请说明"],
                    数据["发货物流公司"],
                    数据["发货快递单号"],
                    数据["有售后图片"],
                    数据["物流最新状态"],
                    数据["物流最新时间"],
                    数据["收货城市"],
                    数据["剩余处理时间"],
                    数据["平台建议"],
                    数据["可用按钮列表"],
                    数据["协商轮次"],
                    数据["商家已回复"],
                    id,
                ),
            )
            await 连接.commit()
            return 游标.rowcount > 0

    async def 更新退货物流(
        self,
        id: int,
        退货快递公司: str,
        退货快递单号: str,
        退货物流全文: str,
        退货物流状态: str = "",
    ) -> bool:
        """回写退货物流摘要字段。"""
        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                """
                UPDATE aftersale_queue
                SET 退货快递公司 = ?,
                    退货快递单号 = ?,
                    退货物流状态 = ?,
                    退货物流全文 = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (
                    self._标准化文本(退货快递公司),
                    self._标准化文本(退货快递单号),
                    self._标准化文本(退货物流状态),
                    self._标准化文本(退货物流全文),
                    id,
                ),
            )
            await 连接.commit()
            return 游标.rowcount > 0

    async def 更新阶段(
        self,
        id: int,
        阶段: str,
        下次处理时间: str = None,
        拒绝次数: int = None,
        处理结果: str = None,
        错误信息: str = None,
    ) -> bool:
        """更新售后单的处理阶段和相关字段。"""
        目标阶段 = self._标准化文本(阶段)
        if not 目标阶段:
            raise ValueError("阶段不能为空")

        更新字段 = [
            "当前阶段 = ?",
            "处理次数 = COALESCE(处理次数, 0) + 1",
            "updated_at = datetime('now', 'localtime')",
        ]
        参数列表: list[Any] = [目标阶段]

        if 下次处理时间 is not None:
            更新字段.append("下次处理时间 = ?")
            参数列表.append(self._标准化文本(下次处理时间) or None)
        if 拒绝次数 is not None:
            更新字段.append("拒绝次数 = ?")
            参数列表.append(int(拒绝次数))
            更新字段.append("上次拒绝时间 = datetime('now', 'localtime')")
        if 处理结果 is not None:
            更新字段.append("处理结果 = ?")
            参数列表.append(self._标准化文本(处理结果) or None)
        if 错误信息 is not None:
            更新字段.append("错误信息 = ?")
            参数列表.append(self._标准化文本(错误信息) or None)

        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                f"UPDATE aftersale_queue SET {', '.join(更新字段)} WHERE id = ?",
                [*参数列表, id],
            )
            await 连接.commit()
            return 游标.rowcount > 0

    async def 获取待处理列表(
        self,
        batch_id: str = None,
        shop_id: str = None,
    ) -> list[dict]:
        """获取当前阶段为'待处理'的记录。"""
        条件列表 = ["当前阶段 = '待处理'"]
        参数列表: list[Any] = []
        if batch_id:
            条件列表.append("batch_id = ?")
            参数列表.append(self._标准化文本(batch_id))
        if shop_id:
            条件列表.append("shop_id = ?")
            参数列表.append(self._标准化文本(shop_id))

        async with 获取连接() as 连接:
            async with 连接.execute(
                f"""
                SELECT *
                FROM aftersale_queue
                WHERE {' AND '.join(条件列表)}
                ORDER BY id ASC
                """,
                参数列表,
            ) as 游标:
                行列表 = await 游标.fetchall()
        return [self._转换记录(行) for 行 in 行列表]

    async def 获取到期记录(self) -> list[dict]:
        """获取 下次处理时间 <= now 且 当前阶段处于待处理集合中的记录。"""
        占位符 = ", ".join("?" for _ in self.待到期阶段集合)
        async with 获取连接() as 连接:
            async with 连接.execute(
                f"""
                SELECT *
                FROM aftersale_queue
                WHERE 当前阶段 IN ({占位符})
                  AND COALESCE(下次处理时间, '') != ''
                  AND datetime(下次处理时间) <= datetime('now', 'localtime')
                ORDER BY datetime(下次处理时间) ASC, id ASC
                """,
                list(self.待到期阶段集合),
            ) as 游标:
                行列表 = await 游标.fetchall()
        return [self._转换记录(行) for 行 in 行列表]

    async def 查询拒绝次数(self, 订单号: str) -> int:
        """查询某订单的累计拒绝次数。"""
        订单编号 = self._标准化文本(订单号)
        if not 订单编号:
            return 0

        async with 获取连接() as 连接:
            async with 连接.execute(
                """
                SELECT MAX(COALESCE(拒绝次数, 0))
                FROM aftersale_queue
                WHERE 订单号 = ?
                """,
                (订单编号,),
            ) as 游标:
                结果 = await 游标.fetchone()
        return int((结果[0] if 结果 else 0) or 0)

    async def 标记已完成(self, id: int, 处理结果: str = "成功") -> bool:
        """标记当前售后单已完成。"""
        return await self.更新阶段(id, "已完成", 处理结果=处理结果, 错误信息="")

    async def 标记已被处理(self, id: int) -> bool:
        """人工已处理，跳过。"""
        return await self.更新阶段(id, "跳过", 处理结果="人工已处理", 错误信息="")

    async def 标记人工(self, id: int, 原因: str = "") -> bool:
        """标记当前售后单进入人工审核。"""
        return await self.更新阶段(
            id,
            "人工审核",
            处理结果=self._标准化文本(原因) or "人工审核",
        )

    async def 获取批次统计(self, batch_id: str) -> dict:
        """返回批次统计：总数/已完成/失败/人工/待处理。"""
        批次ID = self._标准化文本(batch_id)
        if not 批次ID:
            raise ValueError("batch_id 不能为空")

        async with 获取连接() as 连接:
            async with 连接.execute(
                """
                SELECT
                    COUNT(*) AS 总数,
                    SUM(CASE WHEN 当前阶段 = '已完成' THEN 1 ELSE 0 END) AS 已完成,
                    SUM(CASE WHEN 当前阶段 = '失败' THEN 1 ELSE 0 END) AS 失败,
                    SUM(CASE WHEN 当前阶段 = '人工审核' THEN 1 ELSE 0 END) AS 人工,
                    SUM(CASE WHEN 当前阶段 = '待处理' THEN 1 ELSE 0 END) AS 待处理
                FROM aftersale_queue
                WHERE batch_id = ?
                """,
                (批次ID,),
            ) as 游标:
                行 = await 游标.fetchone()

        if not 行:
            return {"总数": 0, "已完成": 0, "失败": 0, "人工": 0, "待处理": 0}
        return {
            "总数": int(行["总数"] or 0),
            "已完成": int(行["已完成"] or 0),
            "失败": int(行["失败"] or 0),
            "人工": int(行["人工"] or 0),
            "待处理": int(行["待处理"] or 0),
        }


售后队列服务实例 = 售后队列服务()


__all__ = [
    "售后队列服务",
    "售后队列服务实例",
]
