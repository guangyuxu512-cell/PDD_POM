"""售后配置服务。"""
from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, ClassVar

from backend.models.数据库 import 获取连接


class 售后配置服务:
    """售后配置 CRUD、校验与迁移服务。"""

    默认配置: ClassVar[dict[str, Any]] = {
        "启用自动售后": True,
        "不支持自动处理类型": ["补寄", "维修", "换货"],
        "退货物流白名单": [],
        "退货等待时间": {"刚发出": 3, "中途运输": 1, "到达目的市": 0.25},
        "需要入库校验": False,
        "自动退款金额上限": 50.0,
        "仅退款_启用": False,
        "仅退款_自动同意金额上限": 10.0,
        "仅退款_需要拒绝": False,
        "仅退款_最大拒绝次数": 3,
        "仅退款_拒绝后等待分钟": 30,
        "仅退款_有图片转人工": True,
        "仅退款_拒收退回自动同意": True,
        "拒收退款_启用": True,
        "拒收退款_需要检查物流": True,
        "飞书通知_启用": True,
        "飞书通知_webhook": "",
        "微信通知_启用": False,
        "微信通知_群ID": "",
        "通知场景": ["人工审核", "金额超限", "派件人不匹配", "入库校验"],
        "弹窗偏好": {},
        "备注模板": {
            "退货匹配": "退回物流匹配，自动退款",
            "人工": "转人工处理",
            "拒绝": "系统拒绝第{n}次",
        },
        "每批最大处理数": 50,
        "单条超时秒数": 60,
        "失败重试次数": 3,
        "扫描间隔分钟": 30,
        "优先处理类型": ["退货退款", "仅退款"],
        "飞书多维表_启用": False,
        "飞书多维表_app_token": "",
        "飞书多维表_table_id": "",
        "飞书多维表_写入场景": ["已签收", "入库校验"],
    }

    JSON字段: ClassVar[set[str]] = {
        "不支持自动处理类型",
        "退货物流白名单",
        "退货等待时间",
        "通知场景",
        "弹窗偏好",
        "备注模板",
        "优先处理类型",
        "飞书多维表_写入场景",
    }
    布尔字段: ClassVar[set[str]] = {
        "启用自动售后",
        "需要入库校验",
        "仅退款_启用",
        "仅退款_需要拒绝",
        "仅退款_有图片转人工",
        "仅退款_拒收退回自动同意",
        "拒收退款_启用",
        "拒收退款_需要检查物流",
        "飞书通知_启用",
        "微信通知_启用",
        "飞书多维表_启用",
    }
    整数字段: ClassVar[set[str]] = {
        "仅退款_最大拒绝次数",
        "仅退款_拒绝后等待分钟",
        "每批最大处理数",
        "单条超时秒数",
        "失败重试次数",
        "扫描间隔分钟",
    }
    浮点字段: ClassVar[set[str]] = {
        "自动退款金额上限",
        "仅退款_自动同意金额上限",
    }
    文本字段: ClassVar[set[str]] = {
        "飞书通知_webhook",
        "微信通知_群ID",
        "飞书多维表_app_token",
        "飞书多维表_table_id",
    }
    配置字段集合: ClassVar[set[str]] = set(默认配置.keys())
    白名单必填字段: ClassVar[tuple[str, ...]] = ("快递公司", "地区关键词", "派件人")

    @classmethod
    def 获取默认配置(cls) -> dict[str, Any]:
        """返回一份默认配置副本。"""
        return deepcopy(cls.默认配置)

    @staticmethod
    def _标准化店铺ID(shop_id: str) -> str:
        店铺ID = str(shop_id or "").strip()
        if not 店铺ID:
            raise ValueError("shop_id 不能为空")
        return 店铺ID

    @staticmethod
    def _解析JSON值(值: Any, 默认值: Any) -> Any:
        if isinstance(值, type(默认值)):
            return 值
        if 值 in (None, ""):
            return deepcopy(默认值)
        try:
            结果 = json.loads(str(值))
        except (TypeError, json.JSONDecodeError) as 异常:
            raise ValueError("JSON 字段格式错误") from 异常
        if not isinstance(结果, type(默认值)):
            raise ValueError("JSON 字段类型不匹配")
        return 结果

    @staticmethod
    def _序列化JSON值(值: Any) -> str:
        return json.dumps(值, ensure_ascii=False)

    @staticmethod
    def _转布尔值(值: Any) -> bool:
        if isinstance(值, bool):
            return 值
        if isinstance(值, (int, float)):
            return bool(int(值))
        文本 = str(值 or "").strip().lower()
        if 文本 in {"1", "true", "yes", "on"}:
            return True
        if 文本 in {"0", "false", "no", "off", ""}:
            return False
        return bool(值)

    def _校验白名单(self, 白名单: list) -> list[dict[str, Any]]:
        """校验白名单格式，每条必须包含快递公司、地区关键词、派件人。"""
        if not isinstance(白名单, list):
            raise ValueError("退货物流白名单必须是数组")

        校验结果: list[dict[str, Any]] = []
        for 索引, 条目 in enumerate(白名单, start=1):
            if not isinstance(条目, dict):
                raise ValueError(f"白名单第{索引}条必须是对象")
            for 字段名 in self.白名单必填字段:
                if 字段名 not in 条目:
                    raise ValueError(f"白名单第{索引}条缺少字段: {字段名}")

            快递公司 = str(条目.get("快递公司") or "").strip() or "*"
            地区关键词 = 条目.get("地区关键词")
            派件人 = 条目.get("派件人")
            if not isinstance(地区关键词, list) or not all(
                isinstance(项, str) and 项.strip() for 项 in 地区关键词
            ):
                raise ValueError(f"白名单第{索引}条地区关键词格式错误")
            if not isinstance(派件人, list) or not all(
                isinstance(项, str) and 项.strip() for 项 in 派件人
            ):
                raise ValueError(f"白名单第{索引}条派件人格式错误")

            校验结果.append(
                {
                    "名称": str(条目.get("名称") or "").strip(),
                    "快递公司": 快递公司,
                    "地区关键词": [项.strip() for 项 in 地区关键词],
                    "派件人": [项.strip() for 项 in 派件人],
                    "启用": self._转布尔值(条目.get("启用", True)),
                }
            )
        return 校验结果

    def _标准化单字段(self, 字段名: str, 值: Any) -> Any:
        if 字段名 not in self.配置字段集合:
            raise ValueError(f"不支持的配置字段: {字段名}")

        默认值 = deepcopy(self.默认配置[字段名])
        if 字段名 == "退货物流白名单":
            白名单 = self._解析JSON值(值, 默认值) if 值 not in (None, "") else 默认值
            return self._校验白名单(白名单)
        if 字段名 in self.JSON字段:
            return self._解析JSON值(值, 默认值) if 值 not in (None, "") else 默认值
        if 字段名 in self.布尔字段:
            return self._转布尔值(值 if 值 is not None else 默认值)
        if 字段名 in self.整数字段:
            return int(值 if 值 not in (None, "") else 默认值)
        if 字段名 in self.浮点字段:
            return float(值 if 值 not in (None, "") else 默认值)
        if 字段名 in self.文本字段:
            return str(值 or "")
        return 值 if 值 is not None else 默认值

    def _反序列化(self, row: dict) -> dict:
        """将 SQLite 行转为 Python dict。"""
        数据 = dict(row)
        结果 = {
            "id": 数据.get("id"),
            "shop_id": 数据.get("shop_id"),
            "created_at": 数据.get("created_at"),
            "updated_at": 数据.get("updated_at"),
        }
        for 字段名 in self.配置字段集合:
            结果[字段名] = self._标准化单字段(字段名, 数据.get(字段名))
        return 结果

    def _准备完整配置(self, 数据: dict[str, Any] | None) -> dict[str, Any]:
        配置 = self.获取默认配置()
        for 字段名, 值 in dict(数据 or {}).items():
            if 字段名 in {"id", "shop_id", "created_at", "updated_at"}:
                continue
            配置[字段名] = self._标准化单字段(字段名, 值)
        return 配置

    async def 初始化默认配置(self, shop_id: str) -> dict:
        """为指定店铺创建默认配置。"""
        店铺ID = self._标准化店铺ID(shop_id)
        配置 = self.获取默认配置()
        字段列表 = list(self.配置字段集合)
        占位符 = ", ".join("?" for _ in 字段列表)
        列名 = ", ".join(f'"{字段}"' for 字段 in 字段列表)

        async with 获取连接() as 连接:
            await 连接.execute(
                f"""
                INSERT OR IGNORE INTO aftersale_config (shop_id, {列名})
                VALUES (?, {占位符})
                """,
                [
                    店铺ID,
                    *[
                        self._序列化JSON值(配置[字段])
                        if 字段 in self.JSON字段
                        else 1 if 字段 in self.布尔字段 and 配置[字段]
                        else 0 if 字段 in self.布尔字段
                        else 配置[字段]
                        for 字段 in 字段列表
                    ],
                ],
            )
            await 连接.commit()
        return await self.获取配置(店铺ID)

    async def 获取配置(self, shop_id: str) -> dict:
        """读取指定店铺配置，不存在时自动创建默认配置。"""
        店铺ID = self._标准化店铺ID(shop_id)
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT * FROM aftersale_config WHERE shop_id = ?",
                (店铺ID,),
            ) as 游标:
                行 = await 游标.fetchone()
        if not 行:
            return await self.初始化默认配置(店铺ID)
        return self._反序列化(dict(行))

    async def 更新配置(self, shop_id: str, data: dict) -> dict:
        """部分更新配置，自动处理 JSON 字段序列化。"""
        店铺ID = self._标准化店铺ID(shop_id)
        当前配置 = await self.获取配置(店铺ID)
        待更新数据 = dict(data or {})
        for 字段名 in 待更新数据:
            if 字段名 not in self.配置字段集合:
                raise ValueError(f"不支持的配置字段: {字段名}")

        合并配置 = dict(当前配置)
        合并配置.update(待更新数据)
        标准化配置 = self._准备完整配置(合并配置)

        更新片段: list[str] = []
        参数列表: list[Any] = []
        for 字段名 in self.配置字段集合:
            更新片段.append(f'"{字段名}" = ?')
            值 = 标准化配置[字段名]
            if 字段名 in self.JSON字段:
                参数列表.append(self._序列化JSON值(值))
            elif 字段名 in self.布尔字段:
                参数列表.append(1 if 值 else 0)
            else:
                参数列表.append(值)

        async with 获取连接() as 连接:
            await 连接.execute(
                f"""
                UPDATE aftersale_config
                SET {", ".join(更新片段)},
                    updated_at = datetime('now', 'localtime')
                WHERE shop_id = ?
                """,
                [*参数列表, 店铺ID],
            )
            await 连接.commit()
        return await self.获取配置(店铺ID)

    async def 获取所有配置(self) -> list[dict]:
        """返回所有店铺配置。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT * FROM aftersale_config ORDER BY shop_id ASC"
            ) as 游标:
                行列表 = await 游标.fetchall()
        return [self._反序列化(dict(行)) for 行 in 行列表]

    async def 删除配置(self, shop_id: str) -> bool:
        """删除指定店铺配置。"""
        店铺ID = self._标准化店铺ID(shop_id)
        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                "DELETE FROM aftersale_config WHERE shop_id = ?",
                (店铺ID,),
            )
            await 连接.commit()
            return 游标.rowcount > 0

    async def _获取全部店铺ID(self) -> list[str]:
        async with 获取连接() as 连接:
            async with 连接.execute("SELECT id FROM shops ORDER BY id ASC") as 游标:
                行列表 = await 游标.fetchall()
        return [str(行[0]) for 行 in 行列表 if 行 and 行[0]]

    def _提取规则配置(self, 动作列表: list[dict[str, Any]]) -> dict[str, Any]:
        提取结果: dict[str, Any] = {}
        for 动作 in 动作列表:
            if not isinstance(动作, dict):
                continue
            if 动作.get("action") == "拒绝":
                提取结果["仅退款_启用"] = True
                提取结果["仅退款_需要拒绝"] = True
            if 动作.get("自动同意金额上限") not in (None, ""):
                提取结果["仅退款_启用"] = True
                提取结果["仅退款_自动同意金额上限"] = 动作.get("自动同意金额上限")
            if 动作.get("自动退款金额上限") not in (None, ""):
                提取结果["自动退款金额上限"] = 动作.get("自动退款金额上限")
            if 动作.get("弹窗偏好") not in (None, ""):
                提取结果["弹窗偏好"] = 动作.get("弹窗偏好")
            if 动作.get("退货物流白名单") not in (None, ""):
                提取结果["退货物流白名单"] = 动作.get("退货物流白名单")
            if 动作.get("退货等待时间") not in (None, ""):
                提取结果["退货等待时间"] = 动作.get("退货等待时间")
            if 动作.get("需要入库校验") is not None:
                提取结果["需要入库校验"] = 动作.get("需要入库校验")
        return 提取结果

    async def 从规则服务迁移(self) -> int:
        """
        将售后规则 actions 中的配置迁移到 aftersale_config，并禁用旧规则。
        """
        async with 获取连接() as 连接:
            async with 连接.execute(
                """
                SELECT id, shop_id, actions
                FROM rules
                WHERE business = '售后' AND enabled = 1
                ORDER BY id ASC
                """
            ) as 游标:
                规则列表 = await 游标.fetchall()

        if not 规则列表:
            return 0

        全部店铺ID = await self._获取全部店铺ID()
        迁移数量 = 0

        for 行 in 规则列表:
            规则ID = int(行["id"])
            店铺ID = str(行["shop_id"] or "").strip() or "*"
            try:
                动作列表 = json.loads(str(行["actions"] or "[]"))
            except json.JSONDecodeError:
                动作列表 = []

            提取配置 = self._提取规则配置(list(动作列表 or []))
            目标店铺列表 = 全部店铺ID if 店铺ID == "*" else [店铺ID]

            for 目标店铺ID in 目标店铺列表:
                if not 目标店铺ID:
                    continue
                await self.获取配置(目标店铺ID)
                if 提取配置:
                    await self.更新配置(目标店铺ID, 提取配置)

            async with 获取连接() as 连接:
                await 连接.execute(
                    """
                    UPDATE rules
                    SET enabled = 0, updated_at = datetime('now', 'localtime')
                    WHERE id = ?
                    """,
                    (规则ID,),
                )
                await 连接.commit()
            迁移数量 += 1

        return 迁移数量


售后配置服务实例 = 售后配置服务()


__all__ = ["售后配置服务", "售后配置服务实例"]
