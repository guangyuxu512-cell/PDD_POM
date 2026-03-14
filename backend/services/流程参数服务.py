"""
流程参数服务模块

提供 flow_params 表的分页查询、CRUD、CSV/XLSX 批量导入与步骤结果回写能力。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from backend.models.数据库 import 获取连接
from backend.services.任务参数服务 import 任务参数服务实例
from backend.services.流程服务 import 流程服务实例


允许状态集合 = {"pending", "running", "success", "failed"}
步骤终态集合 = {"completed", "failed", "merged_skip"}
步骤元数据字段 = {
    "status",
    "error",
    "merged_to",
    "merged_by",
    "merged_context",
    "merge_members",
    "result_status",
}


class 流程参数服务:
    """flow_params 业务服务。"""

    @staticmethod
    def _获取步骤状态(步骤结果: Optional[Dict[str, Any]]) -> str:
        if not isinstance(步骤结果, dict):
            return "pending"
        return str(步骤结果.get("status") or "pending")

    @staticmethod
    def _提取步骤业务结果(步骤结果: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(步骤结果, dict):
            return {}
        return {
            键: 值
            for 键, 值 in 步骤结果.items()
            if 键 not in 步骤元数据字段
        }

    def _校验状态(self, 状态: str) -> None:
        if 状态 not in 允许状态集合:
            raise ValueError(f"不支持的状态: {状态}")

    def _解析状态筛选(self, 状态: Optional[str]) -> List[str]:
        if not 状态:
            return []

        状态列表 = [项.strip() for 项 in str(状态).split(",") if 项.strip()]
        for 当前状态 in 状态列表:
            self._校验状态(当前状态)
        return 状态列表

    def _序列化JSON(self, 数据: Optional[Dict[str, Any]]) -> str:
        return 任务参数服务实例._序列化JSON(数据)

    def _解析JSON(self, 数据: Any) -> Dict[str, Any]:
        return 任务参数服务实例._解析JSON(数据)

    async def _流程是否存在(self, flow_id: str) -> bool:
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT 1 FROM flows WHERE id = ?",
                (flow_id,),
            ) as 游标:
                return await 游标.fetchone() is not None

    def _转换记录(self, 行: Dict[str, Any]) -> Dict[str, Any]:
        记录 = dict(行)
        记录["params"] = self._解析JSON(记录.get("params"))
        记录["step_results"] = self._解析JSON(记录.get("step_results"))
        记录["enabled"] = bool(记录.get("enabled", 1))
        记录["run_count"] = int(记录.get("run_count") or 0)
        记录["current_step"] = int(记录.get("current_step") or 0)
        return 记录

    async def _映射导入行(self, flow_id: str, 行数据: Dict[str, str], 行号: int) -> List[Dict[str, Any]]:
        店铺标识 = str(行数据.get("店铺ID", "")).strip()
        if not 店铺标识:
            raise ValueError(f"第 {行号} 行店铺ID不能为空")

        店铺ID = await 任务参数服务实例._解析店铺标识(店铺标识, 行号)
        发布次数 = 任务参数服务实例._解析发布次数(行数据, 行号)

        排除列 = {"店铺ID", "发布次数"}
        参数: Dict[str, Any] = {}
        for 列名, 值 in 行数据.items():
            if 列名 in 排除列 or not str(列名).strip():
                continue

            清理值 = str(值).strip() if 值 else ""
            if not 清理值:
                continue

            参数键名 = 任务参数服务实例._规范参数键名(列名)
            参数[参数键名] = 任务参数服务实例._转换参数值(参数键名, 清理值)

        记录列表: List[Dict[str, Any]] = []
        for 批次序号 in range(1, 发布次数 + 1):
            当前参数 = dict(参数)
            if 发布次数 > 1:
                当前参数["batch_index"] = 批次序号

            记录列表.append(
                {
                    "shop_id": 店铺ID,
                    "flow_id": flow_id,
                    "params": 当前参数,
                    "step_results": {},
                    "current_step": 0,
                    "status": "pending",
                    "error": None,
                    "batch_id": None,
                    "enabled": True,
                }
            )

        return 记录列表

    def _构建条件SQL(
        self,
        shop_id: Optional[str] = None,
        flow_id: Optional[str] = None,
        status: Optional[str] = None,
        状态集合: Optional[List[str]] = None,
        batch_id: Optional[str] = None,
    ) -> Tuple[str, List[Any], bool]:
        条件列表: List[str] = []
        参数列表: List[Any] = []
        是否包含筛选 = False

        if shop_id:
            条件列表.append("shop_id = ?")
            参数列表.append(shop_id)
            是否包含筛选 = True
        if flow_id:
            条件列表.append("flow_id = ?")
            参数列表.append(flow_id)
            是否包含筛选 = True
        if batch_id:
            条件列表.append("batch_id = ?")
            参数列表.append(batch_id)
            是否包含筛选 = True

        if 状态集合:
            占位符 = ", ".join("?" for _ in 状态集合)
            条件列表.append(f"status IN ({占位符})")
            参数列表.extend(状态集合)
            是否包含筛选 = True
        elif status:
            状态列表 = self._解析状态筛选(status)
            if len(状态列表) == 1:
                条件列表.append("status = ?")
                参数列表.append(状态列表[0])
                是否包含筛选 = True
            elif 状态列表:
                占位符 = ", ".join("?" for _ in 状态列表)
                条件列表.append(f"status IN ({占位符})")
                参数列表.extend(状态列表)
                是否包含筛选 = True

        条件SQL = f"WHERE {' AND '.join(条件列表)}" if 条件列表 else ""
        return 条件SQL, 参数列表, 是否包含筛选

    async def 分页查询(
        self,
        page: int = 1,
        page_size: int = 20,
        shop_id: Optional[str] = None,
        flow_id: Optional[str] = None,
        status: Optional[str] = None,
        batch_id: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """分页查询流程参数记录。"""
        page = max(page, 1)
        page_size = max(page_size, 1)

        条件列表: List[str] = []
        参数列表: List[Any] = []
        状态列表 = self._解析状态筛选(status)

        if shop_id:
            条件列表.append("fp.shop_id = ?")
            参数列表.append(shop_id)
        if flow_id:
            条件列表.append("fp.flow_id = ?")
            参数列表.append(flow_id)
        if batch_id:
            条件列表.append("fp.batch_id = ?")
            参数列表.append(batch_id)
        if len(状态列表) == 1:
            条件列表.append("fp.status = ?")
            参数列表.append(状态列表[0])
        elif 状态列表:
            占位符 = ", ".join("?" for _ in 状态列表)
            条件列表.append(f"fp.status IN ({占位符})")
            参数列表.extend(状态列表)

        条件SQL = f"WHERE {' AND '.join(条件列表)}" if 条件列表 else ""
        排序字段映射 = {
            "created_at": "fp.created_at",
            "updated_at": "fp.updated_at",
            "id": "fp.id",
            "current_step": "fp.current_step",
        }
        排序字段 = 排序字段映射.get(sort_by, "fp.created_at")
        排序方向 = "ASC" if str(sort_order).lower() == "asc" else "DESC"

        async with 获取连接() as 连接:
            async with 连接.execute(
                f"""
                SELECT COUNT(*)
                FROM flow_params fp
                {条件SQL}
                """,
                参数列表,
            ) as 游标:
                总数行 = await 游标.fetchone()
                总数 = 总数行[0] if 总数行 else 0

            偏移量 = (page - 1) * page_size
            查询参数 = [*参数列表, page_size, 偏移量]
            async with 连接.execute(
                f"""
                SELECT fp.*, s.name AS shop_name
                FROM flow_params fp
                LEFT JOIN shops s ON s.id = fp.shop_id
                {条件SQL}
                ORDER BY {排序字段} {排序方向}, fp.id DESC
                LIMIT ? OFFSET ?
                """,
                查询参数,
            ) as 游标:
                行列表 = await 游标.fetchall()

        记录列表 = [self._转换记录(行) for 行 in 行列表]
        return {
            "list": 记录列表,
            "total": 总数,
            "page": page,
            "page_size": page_size,
        }

    async def 创建(self, 数据: Dict[str, Any]) -> Dict[str, Any]:
        """创建单条流程参数记录。"""
        店铺ID = str(数据.get("shop_id", "")).strip()
        flow_id = str(数据.get("flow_id", "")).strip()
        状态 = str(数据.get("status") or "pending").strip()
        当前步骤 = int(数据.get("current_step") or 0)
        是否启用 = bool(数据.get("enabled", True))
        执行次数 = int(数据.get("run_count") or 0)

        if not 店铺ID:
            raise ValueError("shop_id 不能为空")
        if not flow_id:
            raise ValueError("flow_id 不能为空")
        self._校验状态(状态)
        if 当前步骤 < 0:
            raise ValueError("current_step 不能小于 0")
        if 执行次数 < 0:
            raise ValueError("run_count 不能小于 0")

        if not await 任务参数服务实例._店铺是否存在(店铺ID):
            raise ValueError("店铺不存在")
        if not await self._流程是否存在(flow_id):
            raise ValueError("流程不存在")

        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                """
                INSERT INTO flow_params (
                    shop_id, flow_id, params, step_results, current_step,
                    status, error, batch_id, enabled, run_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    店铺ID,
                    flow_id,
                    self._序列化JSON(数据.get("params")),
                    self._序列化JSON(数据.get("step_results")),
                    当前步骤,
                    状态,
                    数据.get("error"),
                    数据.get("batch_id"),
                    1 if 是否启用 else 0,
                    执行次数,
                ),
            )
            await 连接.commit()
            记录ID = 游标.lastrowid

        return await self.根据ID获取(int(记录ID))

    async def 根据ID获取(self, 记录ID: int) -> Optional[Dict[str, Any]]:
        """根据主键获取单条记录。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                """
                SELECT fp.*, s.name AS shop_name
                FROM flow_params fp
                LEFT JOIN shops s ON s.id = fp.shop_id
                WHERE fp.id = ?
                """,
                (记录ID,),
            ) as 游标:
                行 = await 游标.fetchone()

        return self._转换记录(行) if 行 else None

    async def 更新(self, 记录ID: int, 数据: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新单条流程参数记录。"""
        现有记录 = await self.根据ID获取(记录ID)
        if not 现有记录:
            return None

        更新字段: List[str] = []
        更新值: List[Any] = []

        if "shop_id" in 数据 and 数据["shop_id"] is not None:
            店铺ID = str(数据["shop_id"]).strip()
            if not 店铺ID:
                raise ValueError("shop_id 不能为空")
            if not await 任务参数服务实例._店铺是否存在(店铺ID):
                raise ValueError("店铺不存在")
            更新字段.append("shop_id = ?")
            更新值.append(店铺ID)

        if "flow_id" in 数据 and 数据["flow_id"] is not None:
            flow_id = str(数据["flow_id"]).strip()
            if not flow_id:
                raise ValueError("flow_id 不能为空")
            if not await self._流程是否存在(flow_id):
                raise ValueError("流程不存在")
            更新字段.append("flow_id = ?")
            更新值.append(flow_id)

        if "params" in 数据 and 数据["params"] is not None:
            更新字段.append("params = ?")
            更新值.append(self._序列化JSON(数据["params"]))

        if "step_results" in 数据 and 数据["step_results"] is not None:
            更新字段.append("step_results = ?")
            更新值.append(self._序列化JSON(数据["step_results"]))

        if "current_step" in 数据 and 数据["current_step"] is not None:
            当前步骤 = int(数据["current_step"])
            if 当前步骤 < 0:
                raise ValueError("current_step 不能小于 0")
            更新字段.append("current_step = ?")
            更新值.append(当前步骤)

        if "status" in 数据 and 数据["status"] is not None:
            状态 = str(数据["status"]).strip()
            self._校验状态(状态)
            更新字段.append("status = ?")
            更新值.append(状态)

        if "error" in 数据:
            更新字段.append("error = ?")
            更新值.append(数据.get("error"))

        if "batch_id" in 数据:
            更新字段.append("batch_id = ?")
            更新值.append(数据.get("batch_id"))

        if "enabled" in 数据 and 数据["enabled"] is not None:
            更新字段.append("enabled = ?")
            更新值.append(1 if bool(数据["enabled"]) else 0)

        if "run_count" in 数据 and 数据["run_count"] is not None:
            执行次数 = int(数据["run_count"])
            if 执行次数 < 0:
                raise ValueError("run_count 不能小于 0")
            更新字段.append("run_count = ?")
            更新值.append(执行次数)

        if not 更新字段:
            return 现有记录

        更新字段.append("updated_at = CURRENT_TIMESTAMP")
        更新值.append(记录ID)

        async with 获取连接() as 连接:
            await 连接.execute(
                f"UPDATE flow_params SET {', '.join(更新字段)} WHERE id = ?",
                更新值,
            )
            await 连接.commit()

        return await self.根据ID获取(记录ID)

    async def 删除(self, 记录ID: int) -> bool:
        """删除单条流程参数记录。"""
        async with 获取连接() as 连接:
            游标 = await 连接.execute("DELETE FROM flow_params WHERE id = ?", (记录ID,))
            await 连接.commit()
            return 游标.rowcount > 0

    async def 按条件清空(
        self,
        shop_id: Optional[str] = None,
        flow_id: Optional[str] = None,
        status: Optional[str] = None,
        batch_id: Optional[str] = None,
    ) -> int:
        """按条件清空流程参数记录。"""
        条件SQL, 参数列表, _ = self._构建条件SQL(
            shop_id=shop_id,
            flow_id=flow_id,
            status=status,
            batch_id=batch_id,
        )

        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                f"DELETE FROM flow_params {条件SQL}",
                参数列表,
            )
            await 连接.commit()
            return 游标.rowcount

    async def 批量导入(
        self,
        文件内容: bytes,
        flow_id: str,
        file_name: str = "",
    ) -> Dict[str, Any]:
        """解析 CSV/XLSX 并批量导入流程参数。"""
        flow_id = str(flow_id or "").strip()
        if not flow_id:
            raise ValueError("flow_id 不能为空")
        if not await self._流程是否存在(flow_id):
            raise ValueError("流程不存在")

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
                记录列表 = await self._映射导入行(flow_id, 行数据, 行号)
                for 记录 in 记录列表:
                    await self.创建(记录)
                    成功数量 += 1
            except Exception as 异常:
                失败数量 += 1
                错误列表.append(str(异常))

        return {
            "success_count": 成功数量,
            "failed_count": 失败数量,
            "errors": 错误列表,
        }

    async def 获取待执行列表(self, shop_id: str, flow_id: str) -> List[Dict[str, Any]]:
        """获取指定店铺和流程的待执行记录。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                """
                SELECT fp.*, s.name AS shop_name
                FROM flow_params fp
                LEFT JOIN shops s ON s.id = fp.shop_id
                WHERE fp.shop_id = ?
                  AND fp.flow_id = ?
                  AND fp.status = 'pending'
                  AND fp.enabled = 1
                ORDER BY fp.id ASC
                """,
                (shop_id, flow_id),
            ) as 游标:
                行列表 = await 游标.fetchall()

        return [self._转换记录(行) for 行 in 行列表]

    async def 查询同批次步骤状态(
        self,
        shop_id: str,
        batch_id: str,
        flow_id: str,
        step_name: str,
    ) -> Dict[str, Any]:
        """查询同店铺同批次同流程下某一步的执行状态。"""
        async with 获取连接() as 连接:
            async with 连接.execute(
                """
                SELECT fp.*, s.name AS shop_name
                FROM flow_params fp
                LEFT JOIN shops s ON s.id = fp.shop_id
                WHERE fp.shop_id = ?
                  AND fp.batch_id = ?
                  AND fp.flow_id = ?
                ORDER BY fp.id ASC
                """,
                (shop_id, batch_id, flow_id),
            ) as 游标:
                行列表 = await 游标.fetchall()

        记录列表 = [self._转换记录(行) for 行 in 行列表]
        完成列表: List[Dict[str, Any]] = []
        未完成列表: List[Dict[str, Any]] = []
        终态列表: List[Dict[str, Any]] = []

        for 记录 in 记录列表:
            步骤结果 = (记录.get("step_results") or {}).get(step_name)
            步骤状态 = self._获取步骤状态(步骤结果)
            记录["step_status"] = 步骤状态
            if 步骤状态 == "completed":
                完成列表.append(记录)
            else:
                未完成列表.append(记录)
            if 步骤状态 in 步骤终态集合:
                终态列表.append(记录)

        return {
            "records": 记录列表,
            "completed_records": 完成列表,
            "unfinished_records": 未完成列表,
            "terminal_records": 终态列表,
        }

    async def 批量推进到下一步(self, record_ids: List[int]) -> int:
        """将指定记录的 current_step 统一加一，供下一步任务投递前调用。"""
        有效ID列表 = [int(记录ID) for 记录ID in record_ids if int(记录ID) > 0]
        if not 有效ID列表:
            return 0

        占位符 = ", ".join("?" for _ in 有效ID列表)
        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                f"""
                UPDATE flow_params
                SET current_step = current_step + 1,
                    status = 'running',
                    error = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({占位符})
                """,
                有效ID列表,
            )
            await 连接.commit()
            return 游标.rowcount

    async def 更新步骤结果(
        self,
        flow_param_id: int,
        任务名: str,
        *,
        步骤状态: str,
        step_index: int,
        结果字典: Optional[Dict[str, Any]] = None,
        错误信息: Optional[str] = None,
        附加数据: Optional[Dict[str, Any]] = None,
        当前步骤: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新单个步骤的结构化结果。"""
        记录 = await self.根据ID获取(flow_param_id)
        if not 记录:
            return None

        步骤结果表 = dict(记录.get("step_results") or {})
        原步骤结果 = dict(步骤结果表.get(str(任务名)) or {})
        if 结果字典:
            原步骤结果.update(dict(结果字典))
        if 附加数据:
            原步骤结果.update(dict(附加数据))
        原步骤结果["status"] = 步骤状态
        if 错误信息:
            原步骤结果["error"] = 错误信息
        else:
            原步骤结果.pop("error", None)
        步骤结果表[str(任务名)] = 原步骤结果

        更新数据: Dict[str, Any] = {
            "step_results": 步骤结果表,
            "current_step": 当前步骤 if 当前步骤 is not None else step_index,
        }
        if 错误信息 is not None:
            更新数据["error"] = 错误信息
        elif 步骤状态 in {"completed", "merged_skip", "running"}:
            更新数据["error"] = None

        return await self.更新(flow_param_id, 更新数据)

    async def 获取步骤上下文(self, flow_param_id: int, 当前任务名: str) -> Dict[str, Any]:
        """读取流程共享参数并按步骤顺序叠加前序步骤结果。"""
        记录 = await self.根据ID获取(flow_param_id)
        if not 记录:
            raise ValueError("流程参数记录不存在")

        flow_id = str(记录["flow_id"])
        流程 = await 流程服务实例.根据ID获取(flow_id)
        if not 流程:
            raise ValueError("流程不存在")

        上下文 = dict(记录.get("params") or {})
        步骤结果 = 记录.get("step_results") or {}
        当前任务名 = str(当前任务名 or "").strip()

        for 步骤 in 流程.get("steps", []):
            步骤任务名 = str(步骤.get("task") or "").strip()
            if not 步骤任务名:
                continue
            if 当前任务名 and 步骤任务名 == 当前任务名:
                break

            结果数据 = 步骤结果.get(步骤任务名)
            if isinstance(结果数据, dict):
                上下文.update(self._提取步骤业务结果(结果数据))

        当前步骤结果 = 步骤结果.get(当前任务名)
        if isinstance(当前步骤结果, dict):
            合并上下文 = 当前步骤结果.get("merged_context")
            if isinstance(合并上下文, dict):
                上下文.update(合并上下文)

        return 上下文

    async def 回写步骤结果(
        self,
        flow_param_id: int,
        任务名: str,
        结果字典: Dict[str, Any],
        step_index: int,
    ) -> Optional[Dict[str, Any]]:
        """回写单步执行结果。"""
        return await self.更新步骤结果(
            flow_param_id,
            任务名,
            步骤状态="completed",
            step_index=step_index,
            结果字典=结果字典,
            错误信息=None,
        )

    async def 更新执行状态(
        self,
        flow_param_id: int,
        状态: str,
        错误信息: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新流程参数整体执行状态。"""
        self._校验状态(状态)

        更新字段 = [
            "status = ?",
            "error = ?",
            "updated_at = CURRENT_TIMESTAMP",
        ]
        更新参数: List[Any] = [状态, 错误信息]

        if 状态 in {"success", "failed"}:
            更新字段.append("run_count = COALESCE(run_count, 0) + 1")

        async with 获取连接() as 连接:
            await 连接.execute(
                f"""
                UPDATE flow_params
                SET {', '.join(更新字段)}
                WHERE id = ?
                """,
                [*更新参数, flow_param_id],
            )
            await 连接.commit()

        return await self.根据ID获取(flow_param_id)

    async def 批量重置(
        self,
        shop_id: Optional[str] = None,
        flow_id: Optional[str] = None,
        status: Optional[str] = None,
        batch_id: Optional[str] = None,
    ) -> int:
        """按筛选条件批量重置记录。"""
        if status:
            目标状态集合 = self._解析状态筛选(status)
        else:
            目标状态集合 = ["success", "failed"]

        条件SQL, 参数列表, _ = self._构建条件SQL(
            shop_id=shop_id,
            flow_id=flow_id,
            状态集合=目标状态集合,
            batch_id=batch_id,
        )
        if not 条件SQL:
            raise ValueError("批量重置必须至少包含一个筛选条件")

        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                f"""
                UPDATE flow_params
                SET status = 'pending',
                    step_results = '{{}}',
                    current_step = 0,
                    error = NULL,
                    updated_at = CURRENT_TIMESTAMP
                {条件SQL}
                """,
                参数列表,
            )
            await 连接.commit()
            return 游标.rowcount

    async def 批量启用(
        self,
        shop_id: Optional[str] = None,
        flow_id: Optional[str] = None,
        status: Optional[str] = None,
        batch_id: Optional[str] = None,
    ) -> int:
        """按筛选条件批量启用记录。"""
        条件SQL, 参数列表, 是否包含筛选 = self._构建条件SQL(
            shop_id=shop_id,
            flow_id=flow_id,
            status=status,
            batch_id=batch_id,
        )
        if not 是否包含筛选:
            raise ValueError("批量启用必须至少提供一个筛选条件")

        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                f"""
                UPDATE flow_params
                SET enabled = 1,
                    updated_at = CURRENT_TIMESTAMP
                {条件SQL}
                """,
                参数列表,
            )
            await 连接.commit()
            return 游标.rowcount

    async def 批量禁用(
        self,
        shop_id: Optional[str] = None,
        flow_id: Optional[str] = None,
        status: Optional[str] = None,
        batch_id: Optional[str] = None,
    ) -> int:
        """按筛选条件批量禁用记录。"""
        条件SQL, 参数列表, 是否包含筛选 = self._构建条件SQL(
            shop_id=shop_id,
            flow_id=flow_id,
            status=status,
            batch_id=batch_id,
        )
        if not 是否包含筛选:
            raise ValueError("批量禁用必须至少提供一个筛选条件")

        async with 获取连接() as 连接:
            游标 = await 连接.execute(
                f"""
                UPDATE flow_params
                SET enabled = 0,
                    updated_at = CURRENT_TIMESTAMP
                {条件SQL}
                """,
                参数列表,
            )
            await 连接.commit()
            return 游标.rowcount


流程参数服务实例 = 流程参数服务()
