"""
流程服务模块

提供流程模板 CRUD 与步骤校验逻辑。
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from backend.models.数据库 import 获取连接
from backend.models.流程模型 import 流程模型, 标准化步骤列表
from tasks.注册表 import 获取任务类, 初始化任务注册表


class 流程服务:
    """流程模板业务服务。"""

    def _构建响应数据(self, 列名: List[str], 行数据) -> Dict[str, Any]:
        """将数据库记录转换为 API 返回结构。"""
        数据 = dict(zip(列名, 行数据))
        步骤原文 = 数据.get("steps")

        if isinstance(步骤原文, str):
            try:
                数据["steps"] = json.loads(步骤原文)
            except json.JSONDecodeError:
                数据["steps"] = []

        return 数据

    def _解析步骤(self, 步骤配置: Any) -> List[Dict[str, Any]]:
        """解析并验证 steps 配置。"""
        if isinstance(步骤配置, str):
            try:
                步骤配置 = json.loads(步骤配置)
            except json.JSONDecodeError as e:
                raise ValueError("steps JSON 格式错误") from e

        if not isinstance(步骤配置, list):
            raise ValueError("steps 必须是 JSON 数组")

        初始化任务注册表()
        步骤列表 = 标准化步骤列表(步骤配置)

        for 步骤 in 步骤列表:
            try:
                获取任务类(步骤.任务)
            except KeyError as e:
                raise ValueError(f"步骤任务未注册: {步骤.任务}") from e

        return [步骤.转字典() for 步骤 in 步骤列表]

    async def 获取全部(self) -> Dict[str, Any]:
        """获取全部流程模板。"""
        async with 获取连接() as 连接:
            async with 连接.execute("SELECT COUNT(*) FROM flows") as 游标:
                结果 = await 游标.fetchone()
                总数 = 结果[0] if 结果 else 0

            async with 连接.execute(
                "SELECT * FROM flows ORDER BY created_at DESC"
            ) as 游标:
                列名 = [描述[0] for 描述 in 游标.description]
                行列表 = await 游标.fetchall()
                流程列表 = [self._构建响应数据(列名, 行) for 行 in 行列表]

        return {
            "list": 流程列表,
            "total": 总数,
        }

    async def 根据ID获取(self, 流程ID: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取流程模板。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT * FROM flows WHERE id = ?",
                (流程ID,),
            ) as 游标:
                行 = await 游标.fetchone()
                if not 行:
                    return None
                列名 = [描述[0] for 描述 in 游标.description]
                return self._构建响应数据(列名, 行)

    async def 创建(self, 数据: Dict[str, Any]) -> Dict[str, Any]:
        """创建流程模板。"""
        流程名称 = str(数据.get("name", "")).strip()
        if not 流程名称:
            raise ValueError("流程名称不能为空")

        步骤列表 = self._解析步骤(数据.get("steps"))
        流程ID = str(uuid.uuid4())
        模型 = 流程模型(
            流程ID=流程ID,
            名称=流程名称,
            步骤=步骤列表,
            描述=(str(数据["description"]).strip() if 数据.get("description") is not None else None),
        )
        记录 = 模型.转数据库记录()

        async with 获取连接() as 连接:
            await 连接.execute(
                """
                INSERT INTO flows (id, name, steps, description)
                VALUES (?, ?, ?, ?)
                """,
                (
                    记录["id"],
                    记录["name"],
                    记录["steps"],
                    记录["description"],
                ),
            )
            await 连接.commit()

        return await self.根据ID获取(流程ID)

    async def 更新(self, 流程ID: str, 数据: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新流程模板。"""
        流程 = await self.根据ID获取(流程ID)
        if not 流程:
            return None

        更新字段: List[str] = []
        更新值: List[Any] = []

        if "name" in 数据 and 数据["name"] is not None:
            流程名称 = str(数据["name"]).strip()
            if not 流程名称:
                raise ValueError("流程名称不能为空")
            更新字段.append("name = ?")
            更新值.append(流程名称)

        if "steps" in 数据 and 数据["steps"] is not None:
            步骤列表 = self._解析步骤(数据["steps"])
            更新字段.append("steps = ?")
            更新值.append(json.dumps(步骤列表, ensure_ascii=False))

        if "description" in 数据:
            描述 = 数据["description"]
            if 描述 is not None:
                描述 = str(描述).strip()
            更新字段.append("description = ?")
            更新值.append(描述)

        if not 更新字段:
            return 流程

        更新字段.append("updated_at = CURRENT_TIMESTAMP")
        更新值.append(流程ID)

        async with 获取连接() as 连接:
            await 连接.execute(
                f"UPDATE flows SET {', '.join(更新字段)} WHERE id = ?",
                更新值,
            )
            await 连接.commit()

        return await self.根据ID获取(流程ID)

    async def 删除(self, 流程ID: str) -> bool:
        """删除流程模板。"""
        async with 获取连接() as 连接:
            游标 = await 连接.execute("DELETE FROM flows WHERE id = ?", (流程ID,))
            await 连接.commit()
            return 游标.rowcount > 0


流程服务实例 = 流程服务()
