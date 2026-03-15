"""通用规则引擎：CRUD + 条件匹配。"""
from __future__ import annotations

import json
from typing import Any

from backend.models.数据库 import 获取连接
from backend.models.规则模型 import 规则模型


默认动作列表 = [{"type": "默认", "action": "人工处理"}]
默认售后规则 = [
    {
        "name": "小额自动退款",
        "platform": "pdd",
        "business": "售后",
        "shop_id": "*",
        "priority": 100,
        "conditions": {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "仅退款"},
                {"field": "退款金额", "op": "<=", "value": 10},
            ],
        },
        "actions": [{"type": "页面操作", "action": "同意退款"}],
    },
    {
        "name": "中额退款+微信通知",
        "platform": "pdd",
        "business": "售后",
        "shop_id": "*",
        "priority": 90,
        "conditions": {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "仅退款"},
                {"field": "退款金额", "op": "<=", "value": 50},
            ],
        },
        "actions": [
            {"type": "页面操作", "action": "同意退款"},
            {"type": "微信通知", "action": "发消息", "template": "亲，您的退款 {退款金额} 元已处理~"},
        ],
    },
    {
        "name": "大额人工审核",
        "platform": "pdd",
        "business": "售后",
        "shop_id": "*",
        "priority": 80,
        "conditions": {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "仅退款"},
                {"field": "退款金额", "op": ">", "value": 50},
            ],
        },
        "actions": [
            {"type": "飞书通知", "action": "发工单"},
            {"type": "标记", "action": "人工审核"},
        ],
    },
    {
        "name": "退货退款-已发货",
        "platform": "pdd",
        "business": "售后",
        "shop_id": "*",
        "priority": 70,
        "conditions": {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "退货退款"},
                {"field": "发货状态", "op": "==", "value": "已发货"},
            ],
        },
        "actions": [
            {"type": "页面操作", "action": "同意退货"},
            {"type": "微信通知", "action": "发消息", "template": "亲，退货已同意，请尽快寄回~"},
        ],
    },
    {
        "name": "退货退款-未发货",
        "platform": "pdd",
        "business": "售后",
        "shop_id": "*",
        "priority": 60,
        "conditions": {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "退货退款"},
                {"field": "发货状态", "op": "==", "value": "未发货"},
            ],
        },
        "actions": [{"type": "页面操作", "action": "同意退款"}],
    },
]


class 规则服务:
    """通用规则引擎：CRUD + 条件匹配。"""

    @staticmethod
    def _解析JSON字段(原始值: Any, 默认值: Any) -> Any:
        if isinstance(原始值, (dict, list)):
            return 原始值
        if 原始值 in (None, ""):
            return 默认值
        try:
            return json.loads(str(原始值))
        except json.JSONDecodeError as 异常:
            raise ValueError("规则 JSON 字段格式错误") from 异常

    @staticmethod
    def _序列化JSON字段(值: Any, 默认值: Any) -> str:
        return json.dumps(值 if 值 not in (None, "") else 默认值, ensure_ascii=False)

    @staticmethod
    def _标准化字符串(值: Any) -> str:
        return str(值 if 值 is not None else "").strip().lower()

    @staticmethod
    def _转换数值(值: Any) -> float:
        if isinstance(值, (int, float)):
            return float(值)

        文本 = str(值 if 值 is not None else "").strip()
        if not 文本:
            raise ValueError("空值无法转换为数值")
        文本 = (
            文本.replace("¥", "")
            .replace("￥", "")
            .replace(",", "")
            .replace("元", "")
            .strip()
        )
        return float(文本)

    @staticmethod
    def _规范列表值(值: Any) -> list[Any]:
        if isinstance(值, (list, tuple, set)):
            return list(值)
        if isinstance(值, str) and "," in 值:
            return [片段.strip() for 片段 in 值.split(",") if 片段.strip()]
        return [值]

    def _构建规则数据(self, 行数据: Any) -> dict[str, Any]:
        数据 = dict(行数据)
        数据["conditions"] = self._解析JSON字段(数据.get("conditions"), {})
        数据["actions"] = self._解析JSON字段(数据.get("actions"), [])
        数据["enabled"] = bool(int(数据.get("enabled", 0)))
        数据["priority"] = int(数据.get("priority", 0))
        return 数据

    def _校验规则数据(self, 规则数据: dict[str, Any], *, 更新模式: bool = False) -> dict[str, Any]:
        数据 = dict(规则数据)
        if not 更新模式 or "name" in 数据:
            名称 = str(数据.get("name") or "").strip()
            if not 名称:
                raise ValueError("规则名称不能为空")
            数据["name"] = 名称

        if not 更新模式 or "business" in 数据:
            业务 = str(数据.get("business") or "").strip()
            if not 业务:
                raise ValueError("业务类型不能为空")
            数据["business"] = 业务

        if "platform" in 数据 or not 更新模式:
            数据["platform"] = str(数据.get("platform") or "*").strip() or "*"

        if "shop_id" in 数据 or not 更新模式:
            数据["shop_id"] = str(数据.get("shop_id") or "*").strip() or "*"

        if "priority" in 数据 or not 更新模式:
            数据["priority"] = int(数据.get("priority") or 0)

        if "conditions" in 数据 or not 更新模式:
            数据["conditions"] = self._解析JSON字段(数据.get("conditions"), {})

        if "actions" in 数据 or not 更新模式:
            动作列表 = self._解析JSON字段(数据.get("actions"), [])
            if not isinstance(动作列表, list):
                raise ValueError("actions 必须是数组")
            数据["actions"] = 动作列表

        if "enabled" in 数据 or not 更新模式:
            数据["enabled"] = bool(数据.get("enabled", True))

        return 数据

    async def 创建规则(self, 规则数据: dict) -> dict:
        数据 = self._校验规则数据(规则数据)
        模型 = 规则模型(
            规则ID=None,
            名称=数据["name"],
            平台=数据["platform"],
            业务=数据["business"],
            店铺ID=数据["shop_id"],
            优先级=数据["priority"],
            条件组=数据["conditions"],
            动作列表=数据["actions"],
            是否启用=数据["enabled"],
        )
        记录 = 模型.转数据库记录()

        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                """
                INSERT INTO rules (name, platform, business, shop_id, priority, conditions, actions, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    记录["name"],
                    记录["platform"],
                    记录["business"],
                    记录["shop_id"],
                    记录["priority"],
                    记录["conditions"],
                    记录["actions"],
                    记录["enabled"],
                ),
            )
            await 连接.commit()
            规则ID = int(游标.lastrowid)

        规则 = await self.获取规则(规则ID)
        if not 规则:
            raise RuntimeError("创建规则后读取失败")
        return 规则

    async def 更新规则(self, 规则ID: int, 规则数据: dict) -> dict | None:
        已有规则 = await self.获取规则(规则ID)
        if not 已有规则:
            return None

        数据 = self._校验规则数据(规则数据, 更新模式=True)
        更新字段: list[str] = []
        更新值: list[Any] = []

        if "name" in 数据:
            更新字段.append("name = ?")
            更新值.append(数据["name"])
        if "platform" in 数据:
            更新字段.append("platform = ?")
            更新值.append(数据["platform"])
        if "business" in 数据:
            更新字段.append("business = ?")
            更新值.append(数据["business"])
        if "shop_id" in 数据:
            更新字段.append("shop_id = ?")
            更新值.append(数据["shop_id"])
        if "priority" in 数据:
            更新字段.append("priority = ?")
            更新值.append(数据["priority"])
        if "conditions" in 数据:
            更新字段.append("conditions = ?")
            更新值.append(self._序列化JSON字段(数据["conditions"], {}))
        if "actions" in 数据:
            更新字段.append("actions = ?")
            更新值.append(self._序列化JSON字段(数据["actions"], []))
        if "enabled" in 数据:
            更新字段.append("enabled = ?")
            更新值.append(1 if 数据["enabled"] else 0)

        if not 更新字段:
            return 已有规则

        更新字段.append("updated_at = datetime('now', 'localtime')")
        更新值.append(规则ID)

        async with 获取连接() as 连接:
            await 连接.execute(
                f"UPDATE rules SET {', '.join(更新字段)} WHERE id = ?",
                更新值,
            )
            await 连接.commit()

        return await self.获取规则(规则ID)

    async def 删除规则(self, 规则ID: int) -> bool:
        async with 获取连接() as 连接:
            游标 = await 连接.execute("DELETE FROM rules WHERE id = ?", (规则ID,))
            await 连接.commit()
            return 游标.rowcount > 0

    async def 获取规则(self, 规则ID: int) -> dict | None:
        async with 获取连接() as 连接:
            async with 连接.execute("SELECT * FROM rules WHERE id = ?", (规则ID,)) as 游标:
                行 = await 游标.fetchone()
                if not 行:
                    return None
                return self._构建规则数据(行)

    async def 获取规则列表(
        self,
        platform: str = None,
        business: str = None,
        shop_id: str = None,
    ) -> list[dict]:
        条件列表: list[str] = []
        参数列表: list[Any] = []

        if platform:
            条件列表.append("platform = ?")
            参数列表.append(platform)
        if business:
            条件列表.append("business = ?")
            参数列表.append(business)
        if shop_id:
            条件列表.append("shop_id = ?")
            参数列表.append(shop_id)

        where_sql = f"WHERE {' AND '.join(条件列表)}" if 条件列表 else ""
        sql = f"""
            SELECT * FROM rules
            {where_sql}
            ORDER BY priority DESC, updated_at DESC, id DESC
        """

        async with 获取连接() as 连接:
            async with 连接.execute(sql, 参数列表) as 游标:
                行列表 = await 游标.fetchall()
                return [self._构建规则数据(行) for 行 in 行列表]

    async def 切换启用(self, 规则ID: int, 启用: bool) -> bool:
        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                """
                UPDATE rules
                SET enabled = ?, updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (1 if 启用 else 0, 规则ID),
            )
            await 连接.commit()
            return 游标.rowcount > 0

    def _评估单条(self, 规则: dict, 数据: dict) -> bool:
        字段名 = str(规则.get("field") or "").strip()
        操作符 = str(规则.get("op") or "").strip()
        目标值 = 规则.get("value")
        当前值 = 数据.get(字段名)

        if not 字段名 or not 操作符:
            return False

        if 操作符 == "==":
            return self._标准化字符串(当前值) == self._标准化字符串(目标值)
        if 操作符 == "!=":
            return self._标准化字符串(当前值) != self._标准化字符串(目标值)
        if 操作符 == ">":
            return self._转换数值(当前值) > self._转换数值(目标值)
        if 操作符 == "<":
            return self._转换数值(当前值) < self._转换数值(目标值)
        if 操作符 == ">=":
            return self._转换数值(当前值) >= self._转换数值(目标值)
        if 操作符 == "<=":
            return self._转换数值(当前值) <= self._转换数值(目标值)
        if 操作符 == "in":
            目标列表 = [self._标准化字符串(项) for 项 in self._规范列表值(目标值)]
            if isinstance(当前值, (list, tuple, set)):
                return any(self._标准化字符串(项) in 目标列表 for 项 in 当前值)
            return self._标准化字符串(当前值) in 目标列表
        if 操作符 == "not_in":
            目标列表 = [self._标准化字符串(项) for 项 in self._规范列表值(目标值)]
            if isinstance(当前值, (list, tuple, set)):
                return all(self._标准化字符串(项) not in 目标列表 for 项 in 当前值)
            return self._标准化字符串(当前值) not in 目标列表
        if 操作符 == "contains":
            目标文本 = self._标准化字符串(目标值)
            if isinstance(当前值, (list, tuple, set)):
                return any(目标文本 in self._标准化字符串(项) for 项 in 当前值)
            return 目标文本 in self._标准化字符串(当前值)

        return False

    def _评估条件(self, 条件组: dict, 数据: dict) -> bool:
        if not 条件组:
            return True

        规则列表 = 条件组.get("rules")
        if not isinstance(规则列表, list) or not 规则列表:
            return True

        操作符 = self._标准化字符串(条件组.get("operator") or "and")
        if 操作符 not in {"and", "or"}:
            raise ValueError("条件组 operator 仅支持 and / or")

        结果列表: list[bool] = []
        for 条目 in 规则列表:
            if isinstance(条目, dict) and "rules" in 条目:
                结果列表.append(self._评估条件(条目, 数据))
            else:
                结果列表.append(self._评估单条(dict(条目 or {}), 数据))

        return all(结果列表) if 操作符 == "and" else any(结果列表)

    @staticmethod
    def _排序键(规则数据: dict, shop_id: str, platform: str) -> tuple[int, int, int, int]:
        return (
            0 if str(规则数据.get("shop_id") or "") == shop_id else 1,
            -int(规则数据.get("priority", 0)),
            0 if str(规则数据.get("platform") or "") == platform else 1,
            int(规则数据.get("id", 0)),
        )

    async def _查找命中规则(
        self,
        platform: str,
        business: str,
        shop_id: str,
        数据: dict,
    ) -> dict[str, Any] | None:
        async with 获取连接() as 连接:
            async with 连接.execute(
                """
                SELECT * FROM rules
                WHERE enabled = 1
                  AND business = ?
                  AND platform IN (?, '*')
                  AND shop_id IN (?, '*')
                """,
                (business, platform, shop_id),
            ) as 游标:
                行列表 = await 游标.fetchall()

        候选规则列表 = [self._构建规则数据(行) for 行 in 行列表]
        候选规则列表.sort(key=lambda 项: self._排序键(项, shop_id, platform))

        for 规则数据 in 候选规则列表:
            try:
                if self._评估条件(规则数据.get("conditions") or {}, 数据):
                    return 规则数据
            except Exception as 异常:
                print(f"[规则服务] 跳过非法规则 {规则数据.get('id')}: {异常}")
        return None

    async def 匹配规则(self, platform: str, business: str, shop_id: str, 数据: dict) -> list[dict]:
        """按优先级匹配第一条命中的规则，返回其 actions 列表。"""
        命中规则 = await self._查找命中规则(platform, business, shop_id, 数据)
        if 命中规则:
            return list(命中规则.get("actions") or [])
        return list(默认动作列表)

    async def 初始化默认售后规则(self) -> None:
        """仅当 rules 表为空时插入默认售后规则。"""
        async with 获取连接() as 连接:
            async with 连接.execute("SELECT COUNT(*) FROM rules") as 游标:
                结果 = await 游标.fetchone()
                总数 = int(结果[0] if 结果 else 0)

        if 总数 > 0:
            return

        for 规则数据 in 默认售后规则:
            await self.创建规则(规则数据)


规则服务实例 = 规则服务()


__all__ = [
    "规则服务",
    "规则服务实例",
    "默认动作列表",
    "默认售后规则",
]
