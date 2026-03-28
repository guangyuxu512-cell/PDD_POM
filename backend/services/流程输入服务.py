"""
流程输入服务模块

提供 flow_input_sets / flow_input_rows 的 CRUD、查询与导入能力。
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from backend.models.数据库 import 获取连接
from backend.services.任务参数服务 import 任务参数服务实例
from backend.services.流程服务 import 流程服务实例


允许来源类型集合 = {"manual", "csv", "xlsx", "api"}


class 流程输入服务:
    """流程输入层服务。"""

    @staticmethod
    def _序列化JSON(数据: Optional[Dict[str, Any]]) -> str:
        return 任务参数服务实例._序列化JSON(数据)

    @staticmethod
    def _解析JSON(数据: Any) -> Dict[str, Any]:
        return 任务参数服务实例._解析JSON(数据)

    @staticmethod
    def _解析布尔值(原始值: Any, 默认值: bool = True) -> bool:
        if 原始值 is None:
            return 默认值
        if isinstance(原始值, bool):
            return 原始值
        文本值 = str(原始值).strip().lower()
        if 文本值 in {"1", "true", "yes", "y", "是", "启用"}:
            return True
        if 文本值 in {"0", "false", "no", "n", "否", "禁用"}:
            return False
        return 默认值

    @staticmethod
    def _解析整数值(原始值: Any, 默认值: int = 0) -> int:
        if 原始值 in (None, ""):
            return 默认值
        return int(原始值)

    @staticmethod
    def _清理文本(原始值: Any) -> Optional[str]:
        if 原始值 is None:
            return None
        文本值 = str(原始值).strip()
        return 文本值 or None

    def _校验来源类型(self, 来源类型: str) -> str:
        标准来源类型 = str(来源类型 or "manual").strip().lower() or "manual"
        if 标准来源类型 not in 允许来源类型集合:
            raise ValueError("source_type 仅支持 manual/csv/xlsx/api")
        return 标准来源类型

    @staticmethod
    def _转换输入集记录(行数据) -> Dict[str, Any]:
        记录 = dict(行数据)
        记录["enabled"] = bool(记录.get("enabled", 1))
        return 记录

    def _转换输入行记录(self, 行数据) -> Dict[str, Any]:
        记录 = dict(行数据)
        记录["input_data"] = self._解析JSON(记录.get("input_data"))
        记录["enabled"] = bool(记录.get("enabled", 1))
        记录["sort_order"] = int(记录.get("sort_order") or 0)
        return 记录

    async def 根据ID获取输入集(self, input_set_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取输入集。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT * FROM flow_input_sets WHERE id = ?",
                (input_set_id,),
            ) as 游标:
                行 = await 游标.fetchone()
                if not 行:
                    return None
        return self._转换输入集记录(行)

    async def 获取输入集列表(self, flow_id: str) -> Dict[str, Any]:
        """获取指定流程的输入集列表。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT COUNT(*) FROM flow_input_sets WHERE flow_id = ?",
                (flow_id,),
            ) as 游标:
                结果 = await 游标.fetchone()
                总数 = int(结果[0] if 结果 else 0)

            async with 连接.execute(
                """
                SELECT * FROM flow_input_sets
                WHERE flow_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (flow_id,),
            ) as 游标:
                行列表 = await 游标.fetchall()

        return {
            "list": [self._转换输入集记录(行) for 行 in 行列表],
            "total": 总数,
        }

    async def 创建输入集(self, 数据: Dict[str, Any]) -> Dict[str, Any]:
        """创建输入集。"""
        flow_id = str(数据.get("flow_id") or "").strip()
        if not flow_id:
            raise ValueError("flow_id 不能为空")
        if not await 流程服务实例.根据ID获取(flow_id):
            raise ValueError("流程不存在")

        名称 = str(数据.get("name") or "").strip()
        if not 名称:
            raise ValueError("name 不能为空")

        输入集ID = str(uuid.uuid4())
        来源类型 = self._校验来源类型(str(数据.get("source_type") or "manual"))
        描述 = self._清理文本(数据.get("description"))
        是否启用 = 1 if self._解析布尔值(数据.get("enabled"), True) else 0

        async with 获取连接() as 连接:
            await 连接.execute(
                """
                INSERT INTO flow_input_sets (id, flow_id, name, description, source_type, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (输入集ID, flow_id, 名称, 描述, 来源类型, 是否启用),
            )
            await 连接.commit()

        return await self.根据ID获取输入集(输入集ID)

    async def 更新输入集(self, input_set_id: str, 数据: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新输入集。"""
        现有记录 = await self.根据ID获取输入集(input_set_id)
        if not 现有记录:
            return None

        更新字段: List[str] = []
        更新值: List[Any] = []

        if "name" in 数据 and 数据["name"] is not None:
            名称 = str(数据["name"]).strip()
            if not 名称:
                raise ValueError("name 不能为空")
            更新字段.append("name = ?")
            更新值.append(名称)

        if "description" in 数据:
            更新字段.append("description = ?")
            更新值.append(self._清理文本(数据.get("description")))

        if "source_type" in 数据 and 数据["source_type"] is not None:
            更新字段.append("source_type = ?")
            更新值.append(self._校验来源类型(str(数据["source_type"])))

        if "enabled" in 数据 and 数据["enabled"] is not None:
            更新字段.append("enabled = ?")
            更新值.append(1 if self._解析布尔值(数据["enabled"]) else 0)

        if not 更新字段:
            return 现有记录

        更新字段.append("updated_at = CURRENT_TIMESTAMP")
        更新值.append(input_set_id)

        async with 获取连接() as 连接:
            await 连接.execute(
                f"UPDATE flow_input_sets SET {', '.join(更新字段)} WHERE id = ?",
                更新值,
            )
            await 连接.commit()

        return await self.根据ID获取输入集(input_set_id)

    async def 删除输入集(self, input_set_id: str) -> bool:
        """删除输入集。"""
        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                "DELETE FROM flow_input_sets WHERE id = ?",
                (input_set_id,),
            )
            await 连接.commit()
            return 游标.rowcount > 0

    async def 根据ID获取输入行(self, row_id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 获取输入行。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                """
                SELECT 行.*, 店铺.name AS shop_name
                FROM flow_input_rows AS 行
                LEFT JOIN shops AS 店铺 ON 店铺.id = 行.shop_id
                WHERE 行.id = ?
                """,
                (row_id,),
            ) as 游标:
                行 = await 游标.fetchone()
                if not 行:
                    return None
        return self._转换输入行记录(行)

    async def 获取输入行列表(
        self,
        input_set_id: str,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """分页获取输入行列表。"""
        偏移量 = max(page - 1, 0) * page_size

        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT COUNT(*) FROM flow_input_rows WHERE input_set_id = ?",
                (input_set_id,),
            ) as 游标:
                结果 = await 游标.fetchone()
                总数 = int(结果[0] if 结果 else 0)

            async with 连接.execute(
                """
                SELECT 行.*, 店铺.name AS shop_name
                FROM flow_input_rows AS 行
                LEFT JOIN shops AS 店铺 ON 店铺.id = 行.shop_id
                WHERE 行.input_set_id = ?
                ORDER BY 行.sort_order ASC, 行.id ASC
                LIMIT ? OFFSET ?
                """,
                (input_set_id, page_size, 偏移量),
            ) as 游标:
                行列表 = await 游标.fetchall()

        return {
            "list": [self._转换输入行记录(行) for 行 in 行列表],
            "total": 总数,
            "page": page,
            "page_size": page_size,
        }

    async def 获取启用输入行(
        self,
        input_set_id: str,
        *,
        shop_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """获取输入集下启用的输入行。"""
        条件列表 = ["行.input_set_id = ?", "行.enabled = 1"]
        参数列表: List[Any] = [input_set_id]

        标准店铺ID列表 = [str(店铺ID).strip() for 店铺ID in (shop_ids or []) if str(店铺ID).strip()]
        if 标准店铺ID列表:
            条件列表.append(f"行.shop_id IN ({', '.join('?' for _ in 标准店铺ID列表)})")
            参数列表.extend(标准店铺ID列表)

        async with 获取连接() as 连接:
            async with 连接.execute(
                f"""
                SELECT 行.*, 店铺.name AS shop_name
                FROM flow_input_rows AS 行
                LEFT JOIN shops AS 店铺 ON 店铺.id = 行.shop_id
                WHERE {' AND '.join(条件列表)}
                ORDER BY 行.sort_order ASC, 行.id ASC
                """,
                参数列表,
            ) as 游标:
                行列表 = await 游标.fetchall()

        return [self._转换输入行记录(行) for 行 in 行列表]

    async def 创建输入行(self, 数据: Dict[str, Any]) -> Dict[str, Any]:
        """创建输入行。"""
        input_set_id = str(数据.get("input_set_id") or "").strip()
        if not input_set_id:
            raise ValueError("input_set_id 不能为空")
        if not await self.根据ID获取输入集(input_set_id):
            raise ValueError("输入集不存在")

        shop_id = str(数据.get("shop_id") or "").strip()
        if not shop_id:
            raise ValueError("shop_id 不能为空")
        if not await 任务参数服务实例._店铺是否存在(shop_id):
            raise ValueError("店铺不存在")

        sort_order = self._解析整数值(数据.get("sort_order"), 0)

        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                """
                INSERT INTO flow_input_rows (
                    input_set_id, shop_id, input_data, enabled, sort_order, source_key
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    input_set_id,
                    shop_id,
                    self._序列化JSON(dict(数据.get("input_data") or {})),
                    1 if self._解析布尔值(数据.get("enabled"), True) else 0,
                    sort_order,
                    self._清理文本(数据.get("source_key")),
                ),
            )
            await 连接.commit()
            记录ID = int(游标.lastrowid)

        return await self.根据ID获取输入行(记录ID)

    async def 更新输入行(self, row_id: int, 数据: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新输入行。"""
        现有记录 = await self.根据ID获取输入行(row_id)
        if not 现有记录:
            return None

        更新字段: List[str] = []
        更新值: List[Any] = []

        if "shop_id" in 数据 and 数据["shop_id"] is not None:
            shop_id = str(数据["shop_id"]).strip()
            if not shop_id:
                raise ValueError("shop_id 不能为空")
            if not await 任务参数服务实例._店铺是否存在(shop_id):
                raise ValueError("店铺不存在")
            更新字段.append("shop_id = ?")
            更新值.append(shop_id)

        if "input_data" in 数据 and 数据["input_data"] is not None:
            更新字段.append("input_data = ?")
            更新值.append(self._序列化JSON(dict(数据["input_data"] or {})))

        if "enabled" in 数据 and 数据["enabled"] is not None:
            更新字段.append("enabled = ?")
            更新值.append(1 if self._解析布尔值(数据["enabled"]) else 0)

        if "sort_order" in 数据 and 数据["sort_order"] is not None:
            更新字段.append("sort_order = ?")
            更新值.append(self._解析整数值(数据["sort_order"], 0))

        if "source_key" in 数据:
            更新字段.append("source_key = ?")
            更新值.append(self._清理文本(数据.get("source_key")))

        if not 更新字段:
            return 现有记录

        更新字段.append("updated_at = CURRENT_TIMESTAMP")
        更新值.append(row_id)

        async with 获取连接() as 连接:
            await 连接.execute(
                f"UPDATE flow_input_rows SET {', '.join(更新字段)} WHERE id = ?",
                更新值,
            )
            await 连接.commit()

        return await self.根据ID获取输入行(row_id)

    async def 删除输入行(self, row_id: int) -> bool:
        """删除输入行。"""
        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                "DELETE FROM flow_input_rows WHERE id = ?",
                (row_id,),
            )
            await 连接.commit()
            return 游标.rowcount > 0

    async def _映射导入行(self, input_set_id: str, 行数据: Dict[str, str], 行号: int) -> List[Dict[str, Any]]:
        店铺标识 = str(行数据.get("店铺ID", "")).strip()
        if not 店铺标识:
            raise ValueError(f"第 {行号} 行店铺ID不能为空")

        店铺ID = await 任务参数服务实例._解析店铺标识(店铺标识, 行号)
        发布次数 = 任务参数服务实例._解析发布次数(行数据, 行号)
        是否启用 = self._解析布尔值(
            行数据.get("enabled", 行数据.get("启用")),
            True,
        )
        排序值 = self._解析整数值(
            行数据.get("sort_order", 行数据.get("排序")),
            0,
        )
        source_key = self._清理文本(
            行数据.get("source_key", 行数据.get("幂等键")),
        )

        排除列 = {
            "店铺ID",
            "发布次数",
            "enabled",
            "启用",
            "sort_order",
            "排序",
            "source_key",
            "幂等键",
        }
        输入数据: Dict[str, Any] = {}
        for 列名, 原始值 in 行数据.items():
            if 列名 in 排除列 or not str(列名).strip():
                continue

            清理值 = str(原始值).strip() if 原始值 else ""
            if not 清理值:
                continue

            参数键名 = 任务参数服务实例._规范参数键名(列名)
            输入数据[参数键名] = 任务参数服务实例._转换参数值(参数键名, 清理值)

        记录列表: List[Dict[str, Any]] = []
        for 批次序号 in range(1, 发布次数 + 1):
            当前输入数据 = dict(输入数据)
            if 发布次数 > 1:
                当前输入数据["batch_index"] = 批次序号

            当前source_key = source_key
            if 当前source_key and 发布次数 > 1:
                当前source_key = f"{当前source_key}:{批次序号}"

            记录列表.append(
                {
                    "input_set_id": input_set_id,
                    "shop_id": 店铺ID,
                    "input_data": 当前输入数据,
                    "enabled": 是否启用,
                    "sort_order": 排序值,
                    "source_key": 当前source_key,
                }
            )

        return 记录列表

    async def 批量导入输入行(
        self,
        input_set_id: str,
        文件内容: bytes,
        file_name: str = "",
    ) -> Dict[str, Any]:
        """批量导入输入行。"""
        if not await self.根据ID获取输入集(input_set_id):
            raise ValueError("输入集不存在")

        文件后缀 = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
        if 文件后缀 == "xlsx":
            行列表 = 任务参数服务实例._解析XLSX内容(文件内容)
        else:
            行列表 = 任务参数服务实例._解析CSV内容(文件内容)

        成功数量 = 0
        失败数量 = 0
        错误列表: List[str] = []

        for 行号, 行数据 in enumerate(行列表, start=2):
            try:
                记录列表 = await self._映射导入行(input_set_id, 行数据, 行号)
                for 记录 in 记录列表:
                    await self.创建输入行(记录)
                    成功数量 += 1
            except Exception as 异常:
                失败数量 += 1
                错误列表.append(str(异常))

        return {
            "success_count": 成功数量,
            "failed_count": 失败数量,
            "errors": 错误列表,
        }


流程输入服务实例 = 流程输入服务()

