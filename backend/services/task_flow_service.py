"""
任务流程服务模块

封装 flow 模式下的批量执行、步骤回写与下一步推进。
"""
from __future__ import annotations

import asyncio
import random
from typing import Any, Dict, List, Optional

from backend.logging_config import get_logger


logger = get_logger()


class 任务流程服务:
    """处理 flow 模式的步骤推进逻辑。"""

    def __init__(self, 任务服务实例: Any) -> None:
        self._任务服务 = 任务服务实例

    async def 执行流程批量任务(
        self,
        shop_id: str,
        task_name: str,
        页面: Any,
        店铺配置: Dict[str, Any],
    ) -> Dict[str, Any]:
        """同一页面内串行处理多条 flow_params，避免重复投递多个 Celery 任务。"""
        from backend.services.flow_params_service import 流程参数服务实例

        任务服务实例 = self._任务服务
        flow_param_ids = 任务服务实例._标准化流程参数ID列表(店铺配置.get("flow_param_ids"))
        merge = bool(店铺配置.get("merge"))
        step_index = int(店铺配置.get("step_index") or 0)
        total_steps = int(店铺配置.get("total_steps") or 0)
        on_fail = str(店铺配置.get("on_fail") or "abort")
        batch_id = str(店铺配置.get("batch_id") or "")

        if not flow_param_ids:
            return {
                "task_name": task_name,
                "shop_id": shop_id,
                "result": "跳过",
                "result_data": {},
            }

        if await 任务服务实例._已收到批次取消(batch_id):
            logger.info("[任务服务] 收到取消信号，停止执行")
            return 任务服务实例._构建取消结果(task_name, shop_id)

        if merge:
            记录列表 = []
            for flow_param_id in flow_param_ids:
                记录 = await 流程参数服务实例.根据ID获取(flow_param_id)
                if 记录:
                    记录列表.append(记录)

            if not 记录列表:
                raise ValueError("流程参数记录不存在")

            主记录ID = int(记录列表[0]["id"])
            for flow_param_id in flow_param_ids:
                await 流程参数服务实例.更新(
                    flow_param_id,
                    {
                        "status": "running",
                        "current_step": step_index,
                        "error": None,
                        "batch_id": batch_id or None,
                    },
                )

            主记录 = 记录列表[0]
            当前步骤结果 = ((主记录.get("step_results") or {}).get(task_name) or {})
            合并上下文 = 当前步骤结果.get("merged_context") if isinstance(当前步骤结果, dict) else None
            if not isinstance(合并上下文, dict) or not 合并上下文:
                合并上下文 = await 任务服务实例._构建合并参数(记录列表, task_name)

            await 流程参数服务实例.更新步骤结果(
                主记录ID,
                task_name,
                步骤状态="running",
                step_index=step_index,
                当前步骤=step_index,
                附加数据={
                    "merged_context": 合并上下文,
                    "merge_members": flow_param_ids,
                    "merged_by": 主记录ID,
                },
            )
            for flow_param_id in flow_param_ids[1:]:
                await 任务服务实例._标记合并跳过(flow_param_id, task_name, step_index, 主记录ID)

            if await 任务服务实例._已收到批次取消(batch_id):
                logger.info("[任务服务] 收到取消信号，停止执行")
                return 任务服务实例._构建取消结果(task_name, shop_id)

            try:
                单次结果 = await 任务服务实例.执行任务(
                    shop_id=shop_id,
                    task_name=task_name,
                    页面=页面,
                    店铺配置=任务服务实例._构建流程店铺配置(店铺配置, 合并上下文),
                )
                流程回调结果 = 任务服务实例._构建流程回调结果(
                    str(单次结果.get("result") or "失败"),
                    单次结果.get("result_data") or {},
                    None if str(单次结果.get("result") or "") == "成功" else str(单次结果.get("result") or "任务执行失败"),
                )
            except Exception as 异常:
                流程回调结果 = 任务服务实例._构建流程回调结果("失败", {}, str(异常))

            await 任务服务实例.处理流程步骤执行完成(
                flow_param_id=主记录ID,
                task_name=task_name,
                step_index=step_index,
                total_steps=total_steps,
                on_fail=on_fail,
                执行结果=流程回调结果,
            )
            return {
                "task_name": task_name,
                "shop_id": shop_id,
                "result": 流程回调结果["result"],
                "result_data": 流程回调结果["result_data"],
            }

        成功列表: List[int] = []
        失败列表: List[int] = []
        记录结果列表: List[Dict[str, Any]] = []

        for 索引, flow_param_id in enumerate(flow_param_ids):
            if await 任务服务实例._已收到批次取消(batch_id):
                logger.info("[任务服务] 收到取消信号，停止执行")
                return 任务服务实例._构建取消结果(task_name, shop_id)
            try:
                await 流程参数服务实例.更新(
                    flow_param_id,
                    {
                        "status": "running",
                        "current_step": step_index,
                        "error": None,
                        "batch_id": batch_id or None,
                    },
                )
                await 流程参数服务实例.更新步骤结果(
                    flow_param_id,
                    task_name,
                    步骤状态="running",
                    step_index=step_index,
                    当前步骤=step_index,
                )
                flow_context = await 流程参数服务实例.获取步骤上下文(flow_param_id, task_name)
                单次结果 = await 任务服务实例.执行任务(
                    shop_id=shop_id,
                    task_name=task_name,
                    页面=页面,
                    店铺配置=任务服务实例._构建流程店铺配置(店铺配置, flow_context),
                )
                流程回调结果 = 任务服务实例._构建流程回调结果(
                    str(单次结果.get("result") or "失败"),
                    单次结果.get("result_data") or {},
                    None if str(单次结果.get("result") or "") == "成功" else str(单次结果.get("result") or "任务执行失败"),
                )
            except Exception as 异常:
                流程回调结果 = 任务服务实例._构建流程回调结果("失败", {}, str(异常))

            await 任务服务实例.处理流程步骤执行完成(
                flow_param_id=flow_param_id,
                task_name=task_name,
                step_index=step_index,
                total_steps=total_steps,
                on_fail=on_fail,
                执行结果=流程回调结果,
            )

            if 流程回调结果["result"] == "成功":
                成功列表.append(flow_param_id)
            else:
                失败列表.append(flow_param_id)
            记录结果列表.append(
                {
                    "flow_param_id": flow_param_id,
                    "result": 流程回调结果["result"],
                    "error": 流程回调结果.get("error"),
                }
            )

            if 流程回调结果["result"] != "成功" and on_fail not in {"continue", "log_and_skip"}:
                终止信息 = str(流程回调结果.get("error") or 流程回调结果["result"] or "任务执行失败")
                for 剩余ID in flow_param_ids[索引 + 1:]:
                    await 流程参数服务实例.更新(
                        剩余ID,
                        {
                            "status": "failed",
                            "current_step": step_index,
                            "error": f"前序记录失败，按 on_fail 终止: {终止信息}",
                            "batch_id": batch_id or None,
                        },
                    )
                    await 流程参数服务实例.更新步骤结果(
                        剩余ID,
                        task_name,
                        步骤状态="failed",
                        step_index=step_index,
                        当前步骤=step_index,
                        错误信息=f"前序记录失败，按 on_fail 终止: {终止信息}",
                    )
                    await 流程参数服务实例.更新执行状态(
                        剩余ID,
                        "failed",
                        f"前序记录失败，按 on_fail 终止: {终止信息}",
                    )
                    失败列表.append(剩余ID)
                    记录结果列表.append(
                        {
                            "flow_param_id": 剩余ID,
                            "result": "失败",
                            "error": f"前序记录失败，按 on_fail 终止: {终止信息}",
                        }
                    )
                break

            if await 任务服务实例._已收到批次取消(batch_id):
                logger.info("[任务服务] 收到取消信号，停止执行")
                return 任务服务实例._构建取消结果(task_name, shop_id)

            if 索引 < len(flow_param_ids) - 1:
                await asyncio.sleep(random.uniform(2.0, 5.0))

        return {
            "task_name": task_name,
            "shop_id": shop_id,
            "result": "成功" if not 失败列表 else "失败",
            "result_data": {
                "success_ids": 成功列表,
                "failed_ids": 失败列表,
                "results": 记录结果列表,
            },
        }

    async def 获取流程步骤信息(
        self,
        flow_param_id: int,
        task_name: str,
        step_index: int,
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]], int, Dict[str, Any], Optional[Dict[str, Any]]]:
        from backend.services.flow_params_service import 流程参数服务实例
        from backend.services.flow_service import 流程服务实例

        流程参数记录 = await 流程参数服务实例.根据ID获取(flow_param_id)
        if not 流程参数记录:
            raise ValueError("流程参数记录不存在")

        流程 = await 流程服务实例.根据ID获取(str(流程参数记录["flow_id"]))
        if not 流程:
            raise ValueError("流程不存在")

        步骤列表 = list(流程.get("steps") or [])
        if not 步骤列表:
            raise ValueError("流程步骤不能为空")

        实际步骤序号 = step_index
        if not (1 <= 实际步骤序号 <= len(步骤列表)) or 步骤列表[实际步骤序号 - 1].get("task") != task_name:
            for 索引, 步骤 in enumerate(步骤列表, start=1):
                if str(步骤.get("task") or "") == task_name:
                    实际步骤序号 = 索引
                    break
            else:
                raise ValueError(f"流程中不存在步骤任务: {task_name}")

        当前步骤 = 步骤列表[实际步骤序号 - 1]
        下一步骤 = 步骤列表[实际步骤序号] if 实际步骤序号 < len(步骤列表) else None
        return 流程参数记录, 步骤列表, 实际步骤序号, 当前步骤, 下一步骤

    async def 标记下一步等待屏障(
        self,
        flow_param_id: int,
        next_task_name: str,
        当前步骤序号: int,
    ) -> None:
        from backend.services.flow_params_service import 流程参数服务实例

        await 流程参数服务实例.更新步骤结果(
            flow_param_id,
            next_task_name,
            步骤状态="waiting_barrier",
            step_index=当前步骤序号,
            当前步骤=当前步骤序号,
        )

    async def 准备下一步执行(
        self,
        flow_param_id: int,
        next_task_name: str,
        next_step_index: int,
        附加数据: Optional[Dict[str, Any]] = None,
    ) -> bool:
        from backend.services.flow_params_service import 流程参数服务实例

        记录 = await 流程参数服务实例.根据ID获取(flow_param_id)
        if not 记录:
            return False

        现有结果 = (记录.get("step_results") or {}).get(next_task_name)
        现有状态 = 流程参数服务实例._获取步骤状态(现有结果)
        if 现有状态 in {"running", "completed", "merged_skip"}:
            return False

        await 流程参数服务实例.更新步骤结果(
            flow_param_id,
            next_task_name,
            步骤状态="running",
            step_index=next_step_index,
            当前步骤=next_step_index,
            附加数据=附加数据,
        )
        return True

    async def 标记合并跳过(
        self,
        flow_param_id: int,
        task_name: str,
        step_index: int,
        merged_to: int,
    ) -> None:
        from backend.services.flow_params_service import 流程参数服务实例

        await 流程参数服务实例.更新步骤结果(
            flow_param_id,
            task_name,
            步骤状态="merged_skip",
            step_index=step_index,
            当前步骤=step_index,
            附加数据={
                "merged_to": merged_to,
                "result_status": "pending",
            },
        )

    async def 构建合并参数(
        self,
        记录列表: List[Dict[str, Any]],
        next_task_name: str,
    ) -> Dict[str, Any]:
        from backend.services.flow_params_service import 流程参数服务实例

        上下文列表: List[tuple[Dict[str, Any], Dict[str, Any]]] = []
        for 记录 in 记录列表:
            上下文 = await 流程参数服务实例.获取步骤上下文(int(记录["id"]), next_task_name)
            上下文列表.append((记录, 上下文))

        if not 上下文列表:
            return {}

        主上下文 = dict(上下文列表[0][1])
        商品ID列表: List[str] = []
        商品参数映射: Dict[str, Any] = {}

        for 记录, 上下文 in 上下文列表:
            商品ID = str(
                上下文.get("新商品ID")
                or 上下文.get("商品ID")
                or 上下文.get("new_product_id")
                or 上下文.get("product_id")
                or ""
            ).strip()
            if not 商品ID:
                商品ID = str(记录["id"])
            商品ID列表.append(商品ID)
            商品参数映射[商品ID] = {
                **上下文,
                "flow_param_id": int(记录["id"]),
            }

        主上下文["商品ID列表"] = 商品ID列表
        主上下文["商品参数映射"] = 商品参数映射
        return 主上下文

    async def 投递下一步任务(
        self,
        *,
        batch_id: str,
        shop_id: str,
        shop_name: str,
        next_step: Dict[str, Any],
        next_step_index: int,
        total_steps: int,
        record_ids: List[int],
        主执行记录ID: Optional[int] = None,
        合并参数: Optional[Dict[str, Any]] = None,
    ) -> None:
        from backend.services.execute_service import 执行服务实例

        任务服务实例 = self._任务服务
        if not record_ids:
            return

        if next_step.get("merge"):
            主记录ID = int(主执行记录ID or record_ids[0])
            合并成员ID列表: List[int] = []
            if await 任务服务实例._准备下一步执行(
                主记录ID,
                str(next_step["task"]),
                next_step_index,
                附加数据={
                    "merged_context": 合并参数 or {},
                    "merge_members": record_ids,
                    "merged_by": 主记录ID,
                },
            ):
                合并成员ID列表.append(主记录ID)
            else:
                return

            for 记录ID in record_ids:
                if 记录ID == 主记录ID:
                    continue
                await 任务服务实例._标记合并跳过(记录ID, str(next_step["task"]), next_step_index, 主记录ID)
                合并成员ID列表.append(记录ID)

            await 执行服务实例.投递单步任务(
                batch_id=batch_id,
                shop_id=shop_id,
                shop_name=shop_name,
                task_name=str(next_step["task"]),
                on_fail=str(next_step.get("on_fail") or "abort"),
                step_index=next_step_index,
                total_steps=total_steps,
                flow_param_ids=合并成员ID列表,
                merge=True,
            )
            return

        if next_step.get("barrier"):
            已准备记录ID列表: List[int] = []
            for 记录ID in record_ids:
                if await 任务服务实例._准备下一步执行(记录ID, str(next_step["task"]), next_step_index):
                    已准备记录ID列表.append(记录ID)
            if not 已准备记录ID列表:
                return

            await 执行服务实例.投递单步任务(
                batch_id=batch_id,
                shop_id=shop_id,
                shop_name=shop_name,
                task_name=str(next_step["task"]),
                on_fail=str(next_step.get("on_fail") or "abort"),
                step_index=next_step_index,
                total_steps=total_steps,
                flow_param_ids=已准备记录ID列表,
                merge=False,
            )
            return

        for 记录ID in record_ids:
            if not await 任务服务实例._准备下一步执行(记录ID, str(next_step["task"]), next_step_index):
                continue
            await 执行服务实例.投递单步任务(
                batch_id=batch_id,
                shop_id=shop_id,
                shop_name=shop_name,
                task_name=str(next_step["task"]),
                on_fail=str(next_step.get("on_fail") or "abort"),
                step_index=next_step_index,
                total_steps=total_steps,
                flow_param_id=记录ID,
            )

    async def 回写合并步骤结果(
        self,
        *,
        主记录ID: int,
        task_name: str,
        step_index: int,
        执行结果: Dict[str, Any],
        允许继续: bool,
        最终步骤: bool,
    ) -> List[int]:
        from backend.services.flow_params_service import 流程参数服务实例

        主记录 = await 流程参数服务实例.根据ID获取(主记录ID)
        if not 主记录:
            return []

        当前步骤结果 = (主记录.get("step_results") or {}).get(task_name) or {}
        合并上下文 = 当前步骤结果.get("merged_context") or {}
        商品参数映射 = 合并上下文.get("商品参数映射") or {}
        执行结果数据 = dict(执行结果.get("result_data") or {})
        成功列表 = {
            str(商品ID)
            for 商品ID in (执行结果数据.get("成功列表") or [])
            if str(商品ID).strip()
        }
        失败列表 = {
            str(商品ID)
            for 商品ID in (执行结果数据.get("失败列表") or [])
            if str(商品ID).strip()
        }
        错误信息 = str(执行结果.get("error") or 执行结果.get("result") or "任务执行失败")

        可继续记录ID列表: List[int] = []
        for 商品ID, 参数 in 商品参数映射.items():
            if not isinstance(参数, dict) or not 参数.get("flow_param_id"):
                continue
            flow_param_id = int(参数["flow_param_id"])
            商品成功 = 商品ID in 成功列表 if 成功列表 or 失败列表 else self._任务服务._业务执行成功(执行结果)
            步骤状态 = "completed" if flow_param_id == 主记录ID else "merged_skip"
            await 流程参数服务实例.更新步骤结果(
                flow_param_id,
                task_name,
                步骤状态=步骤状态 if 商品成功 or 允许继续 else "failed",
                step_index=step_index,
                当前步骤=step_index,
                结果字典={
                    "商品ID": 商品ID,
                    "result_status": "success" if 商品成功 else "failed",
                },
                错误信息=None if 商品成功 else 错误信息,
                附加数据=(
                    {
                        "merged_by": 主记录ID,
                        "merged_to": 主记录ID if flow_param_id != 主记录ID else None,
                    }
                ),
            )
            if 最终步骤:
                await 流程参数服务实例.更新执行状态(
                    flow_param_id,
                    "success" if 商品成功 else "failed",
                    None if 商品成功 else 错误信息,
                )
            elif 商品成功 or 允许继续:
                可继续记录ID列表.append(flow_param_id)
            else:
                await 流程参数服务实例.更新执行状态(flow_param_id, "failed", 错误信息)

        return 可继续记录ID列表

    async def 处理流程步骤执行完成(
        self,
        *,
        flow_param_id: int,
        task_name: str,
        step_index: int,
        total_steps: int,
        on_fail: str,
        执行结果: Dict[str, Any],
    ) -> None:
        """在 flow 模式下，根据 barrier / merge 决定是否推进下一步。"""
        from backend.services.flow_params_service import 流程参数服务实例

        任务服务实例 = self._任务服务
        流程参数记录, 步骤列表, 实际步骤序号, 当前步骤, 下一步骤 = await 任务服务实例._获取流程步骤信息(
            flow_param_id,
            task_name,
            step_index,
        )

        批次ID = str(流程参数记录.get("batch_id") or "")
        店铺ID = str(流程参数记录.get("shop_id") or "")
        店铺名称 = str(流程参数记录.get("shop_name") or 店铺ID)
        业务成功 = 任务服务实例._业务执行成功(执行结果)
        允许继续 = 业务成功 or on_fail in {"continue", "log_and_skip"}
        错误信息 = str(执行结果.get("error") or 执行结果.get("result") or "任务执行失败")
        最终步骤 = 实际步骤序号 >= len(步骤列表) or not 下一步骤
        当前步骤结果 = (流程参数记录.get("step_results") or {}).get(task_name) or {}
        合并执行当前步 = bool(当前步骤.get("merge")) or isinstance(当前步骤结果.get("merged_context"), dict)

        if 执行结果.get("status") == "cancelled":
            await 流程参数服务实例.更新步骤结果(
                flow_param_id,
                task_name,
                步骤状态="failed",
                step_index=实际步骤序号,
                当前步骤=实际步骤序号,
                错误信息=错误信息,
            )
            await 流程参数服务实例.更新(
                flow_param_id,
                {
                    "error": 错误信息,
                    "current_step": 实际步骤序号,
                },
            )
            return

        if 合并执行当前步:
            可继续记录ID列表 = await 任务服务实例._回写合并步骤结果(
                主记录ID=flow_param_id,
                task_name=task_name,
                step_index=实际步骤序号,
                执行结果=执行结果,
                允许继续=on_fail in {"continue", "log_and_skip"},
                最终步骤=最终步骤,
            )
        else:
            await 流程参数服务实例.更新步骤结果(
                flow_param_id,
                task_name,
                步骤状态="completed" if 业务成功 else "failed",
                step_index=实际步骤序号,
                当前步骤=实际步骤序号,
                结果字典=dict(执行结果.get("result_data") or {}),
                错误信息=None if 业务成功 else 错误信息,
            )
            if 最终步骤:
                await 流程参数服务实例.更新执行状态(
                    flow_param_id,
                    "success" if 业务成功 else "failed",
                    None if 业务成功 else 错误信息,
                )
                return
            if not 允许继续:
                await 流程参数服务实例.更新执行状态(flow_param_id, "failed", 错误信息)
                return
            可继续记录ID列表 = [flow_param_id]

        if 最终步骤 or not 下一步骤:
            return

        if await 任务服务实例._已收到批次取消(批次ID):
            logger.info("[任务服务] 收到取消信号，停止执行")
            return

        当前步骤名 = str(当前步骤["task"])
        需要屏障 = bool(当前步骤.get("barrier")) or bool(下一步骤.get("merge"))
        if not 需要屏障:
            await 任务服务实例._投递下一步任务(
                batch_id=批次ID,
                shop_id=店铺ID,
                shop_name=店铺名称,
                next_step=下一步骤,
                next_step_index=实际步骤序号 + 1,
                total_steps=total_steps,
                record_ids=可继续记录ID列表,
            )
            return

        步骤状态查询 = await 流程参数服务实例.查询同批次步骤状态(
            店铺ID,
            批次ID,
            str(流程参数记录["flow_id"]),
            当前步骤名,
        )
        全部记录 = 步骤状态查询["records"]
        if not all(
            任务服务实例._步骤是否终态(str(记录.get("step_status") or "pending"))
            for 记录 in 全部记录
        ):
            for 记录ID in 可继续记录ID列表:
                await 任务服务实例._标记下一步等待屏障(记录ID, str(下一步骤["task"]), 实际步骤序号)
            return

        候选记录 = [
            记录
            for 记录 in 全部记录
            if 任务服务实例._步骤可继续(str(记录.get("step_status") or "pending"), str(当前步骤.get("on_fail") or on_fail))
        ]
        候选记录ID列表 = [int(记录["id"]) for 记录 in 候选记录]
        if not 候选记录ID列表:
            return

        if 下一步骤.get("merge"):
            主执行记录ID = 候选记录ID列表[0]
            合并参数 = await 任务服务实例._构建合并参数(候选记录, str(下一步骤["task"]))
            await 任务服务实例._投递下一步任务(
                batch_id=批次ID,
                shop_id=店铺ID,
                shop_name=店铺名称,
                next_step=下一步骤,
                next_step_index=实际步骤序号 + 1,
                total_steps=total_steps,
                record_ids=候选记录ID列表,
                主执行记录ID=主执行记录ID,
                合并参数=合并参数,
            )
            return

        await 任务服务实例._投递下一步任务(
            batch_id=批次ID,
            shop_id=店铺ID,
            shop_name=店铺名称,
            next_step=下一步骤,
            next_step_index=实际步骤序号 + 1,
            total_steps=total_steps,
            record_ids=候选记录ID列表,
        )
