"""
运行服务模块

提供 execution_runs / execution_run_items / execution_run_steps 的查询能力。
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from backend.models.数据库 import 获取连接
from backend.services.任务服务 import 任务服务


class 运行服务:
    """运行实例查询服务。"""

    @staticmethod
    def _解析JSON字段(值: Any, 默认值: Any) -> Any:
        if isinstance(值, str):
            try:
                return json.loads(值)
            except json.JSONDecodeError:
                return 默认值
        return 默认值 if 值 is None else 值

    def _转换运行记录(self, 行数据) -> Dict[str, Any]:
        记录 = dict(行数据)
        记录["flow_snapshot"] = self._解析JSON字段(记录.get("flow_snapshot"), [])
        记录["shop_ids"] = self._解析JSON字段(记录.get("shop_ids"), [])
        return 记录

    def _转换运行项记录(self, 行数据) -> Dict[str, Any]:
        记录 = dict(行数据)
        记录["context_data"] = self._解析JSON字段(记录.get("context_data"), {})
        记录["result_data"] = self._解析JSON字段(记录.get("result_data"), {})
        return 记录

    def _转换运行步骤记录(self, 行数据) -> Dict[str, Any]:
        记录 = dict(行数据)
        记录["params_snapshot"] = self._解析JSON字段(记录.get("params_snapshot"), {})
        记录["result_data"] = self._解析JSON字段(记录.get("result_data"), {})
        return 记录

    @staticmethod
    def _提取流程上下文(上下文数据: Dict[str, Any]) -> Dict[str, Any]:
        流程上下文 = 上下文数据.get("flow_context")
        if isinstance(流程上下文, dict):
            return dict(流程上下文)
        return {}

    async def 获取运行列表(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """分页获取运行列表。"""
        条件列表: list[str] = []
        参数列表: list[Any] = []

        if status:
            条件列表.append("status = ?")
            参数列表.append(status)
        if mode:
            条件列表.append("mode = ?")
            参数列表.append(mode)

        条件SQL = f"WHERE {' AND '.join(条件列表)}" if 条件列表 else ""
        偏移量 = (page - 1) * page_size

        async with 获取连接() as 连接:
            async with 连接.execute(
                f"SELECT COUNT(*) FROM execution_runs {条件SQL}",
                参数列表,
            ) as 游标:
                结果 = await 游标.fetchone()
                总数 = int(结果[0] if 结果 else 0)

            async with 连接.execute(
                f"""
                SELECT * FROM execution_runs
                {条件SQL}
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                [*参数列表, page_size, 偏移量],
            ) as 游标:
                行列表 = await 游标.fetchall()

        return {
            "list": [self._转换运行记录(行) for 行 in 行列表],
            "total": 总数,
            "page": page,
            "page_size": page_size,
        }

    async def 根据ID获取(self, run_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取运行详情。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT * FROM execution_runs WHERE id = ?",
                (run_id,),
            ) as 游标:
                行 = await 游标.fetchone()
                if not 行:
                    return None
        return self._转换运行记录(行)

    async def 获取运行项(self, run_id: str, shop_id: str) -> Optional[Dict[str, Any]]:
        """根据运行 ID 和店铺 ID 获取运行项。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                """
                SELECT * FROM execution_run_items
                WHERE run_id = ? AND shop_id = ?
                """,
                (run_id, shop_id),
            ) as 游标:
                行 = await 游标.fetchone()
                if not 行:
                    return None
        return self._转换运行项记录(行)

    async def 获取运行项流程上下文(self, run_id: str, shop_id: str) -> Dict[str, Any]:
        """读取无流程参数运行项当前累积的流程上下文。"""
        运行项 = await self.获取运行项(run_id, shop_id)
        if not 运行项:
            return {}
        return self._提取流程上下文(dict(运行项.get("context_data") or {}))

    async def 回写无流程参数步骤结果(
        self,
        *,
        run_id: str,
        shop_id: str,
        task_name: str,
        step_index: int,
        请求参数: Optional[Dict[str, Any]],
        执行结果: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """为无 flow_param 的运行项累积上下文，并返回下一步信息。"""
        运行 = await self.根据ID获取(run_id)
        if not 运行:
            return None

        运行项 = await self.获取运行项(run_id, shop_id)
        if not 运行项:
            return None

        步骤快照 = list(运行.get("flow_snapshot") or [])
        总步骤数 = int(运行项.get("total_steps") or len(步骤快照) or 0)
        上下文数据 = dict(运行项.get("context_data") or {})
        当前流程上下文 = self._提取流程上下文(上下文数据)

        if not 当前流程上下文 and isinstance((请求参数 or {}).get("flow_context"), dict):
            当前流程上下文 = dict((请求参数 or {}).get("flow_context") or {})

        新流程上下文 = dict(当前流程上下文)
        if 任务服务._业务执行成功(执行结果):
            新流程上下文.update(dict(执行结果.get("result_data") or {}))

        上下文数据["flow_context"] = 新流程上下文

        当前时间 = datetime.now().isoformat()
        当前步骤记录ID = f"{run_id}:{shop_id}:{step_index}"

        async with 获取连接() as 连接:
            await 连接.execute(
                """
                UPDATE execution_run_items
                SET context_data = ?,
                    current_step = ?,
                    last_task_name = ?,
                    error = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    json.dumps(上下文数据, ensure_ascii=False),
                    step_index,
                    task_name,
                    执行结果.get("error"),
                    当前时间,
                    f"{run_id}:{shop_id}",
                ),
            )
            await 连接.execute(
                """
                UPDATE execution_run_steps
                SET params_snapshot = ?,
                    result_data = ?,
                    error = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    json.dumps(dict(请求参数 or {}), ensure_ascii=False),
                    json.dumps(dict(执行结果.get("result_data") or {}), ensure_ascii=False),
                    执行结果.get("error"),
                    当前时间,
                    当前步骤记录ID,
                ),
            )
            await 连接.commit()

        下一步骤 = None
        if 0 < step_index < len(步骤快照):
            候选步骤 = 步骤快照[step_index]
            if isinstance(候选步骤, dict):
                下一步骤 = dict(候选步骤)

        return {
            "run": 运行,
            "flow_context": 新流程上下文,
            "next_step": 下一步骤,
            "total_steps": 总步骤数,
        }

    async def 获取运行项列表(
        self,
        run_id: str,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """分页获取运行项列表。"""
        偏移量 = (page - 1) * page_size

        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT COUNT(*) FROM execution_run_items WHERE run_id = ?",
                (run_id,),
            ) as 游标:
                结果 = await 游标.fetchone()
                总数 = int(结果[0] if 结果 else 0)

            async with 连接.execute(
                """
                SELECT * FROM execution_run_items
                WHERE run_id = ?
                ORDER BY shop_id ASC, created_at ASC, id ASC
                LIMIT ? OFFSET ?
                """,
                (run_id, page_size, 偏移量),
            ) as 游标:
                行列表 = await 游标.fetchall()

        return {
            "list": [self._转换运行项记录(行) for 行 in 行列表],
            "total": 总数,
            "page": page,
            "page_size": page_size,
        }

    async def 获取运行步骤列表(self, run_id: str) -> Dict[str, Any]:
        """获取运行下全部步骤记录。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                """
                SELECT 步骤.*, 运行项.shop_id
                FROM execution_run_steps AS 步骤
                INNER JOIN execution_run_items AS 运行项
                    ON 运行项.id = 步骤.run_item_id
                WHERE 运行项.run_id = ?
                ORDER BY 运行项.shop_id ASC, 步骤.step_index ASC
                """,
                (run_id,),
            ) as 游标:
                行列表 = await 游标.fetchall()

        return {
            "list": [self._转换运行步骤记录(行) for 行 in 行列表],
            "total": len(行列表),
        }


运行服务实例 = 运行服务()
