"""
任务服务模块

封装任务日志的 CRUD 和任务触发逻辑。
"""
import json
import uuid
import asyncio
import random
import aiosqlite
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from backend.配置 import 配置实例
from backend.models.数据库 import 获取连接
from backend.services.任务参数服务 import 任务参数服务实例

浏览器初始化超时秒 = 60
打开浏览器超时秒 = 120
任务执行超时秒 = 1800
任务参数任务集合 = {"发布相似商品", "发布换图商品", "限时限量", "设置推广"}
任务链映射 = {
    "发布相似商品": "限时限量",
}


class 任务服务:
    """任务业务服务类"""

    def __init__(self):
        """初始化任务服务"""
        self._数据库路径 = Path(配置实例.DATA_DIR) / "ecom.db"

    @staticmethod
    def _页面已关闭(页面: Any) -> bool:
        """兼容真实 Page 与测试替身，判断页面是否关闭。"""
        if 页面 is None:
            return True

        检查方法 = getattr(页面, "is_closed", None)
        if not callable(检查方法):
            return False

        try:
            检查结果 = 检查方法()
        except Exception:
            return False

        return 检查结果 if isinstance(检查结果, bool) else False

    async def _确保页面可用(self, 管理器实例: Any, shop_id: str):
        """确保任务执行前拿到一个可用页面。"""
        页面 = None
        try:
            页面 = 管理器实例.获取页面(shop_id)
        except RuntimeError as 异常:
            if "所有页面已关闭" not in str(异常):
                raise

        if 页面 is not None and not self._页面已关闭(页面):
            return 页面

        if shop_id not in 管理器实例.实例集:
            raise RuntimeError(f"店铺 {shop_id} 未启动，请先调用 打开店铺() 方法")

        实例 = 管理器实例.实例集[shop_id]
        浏览器上下文 = 实例["浏览器"]
        现有页面 = [
            当前页面
            for 当前页面 in getattr(浏览器上下文, "pages", [])
            if not self._页面已关闭(当前页面)
        ]

        if 现有页面:
            页面 = 现有页面[0]
        else:
            页面 = await 浏览器上下文.new_page()

        实例["页面"] = 页面
        实例["page"] = 页面
        print(f"[任务服务] 页面已刷新: {页面}")
        return 页面

    async def _获取待执行任务参数记录(
        self,
        shop_id: str,
        task_name: str,
    ) -> Optional[Dict[str, Any]]:
        """为依赖 task_params 的任务取一条待执行记录。"""
        if task_name not in 任务参数任务集合:
            return None

        待执行列表 = await 任务参数服务实例.获取待执行列表(shop_id, task_name)
        if not 待执行列表:
            return None
        return 待执行列表[0]

    async def _准备任务参数(
        self,
        shop_id: str,
        task_name: str,
        店铺配置: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """读取 task_params 并注入到店铺配置。"""
        if isinstance(店铺配置.get("flow_context"), dict):
            店铺配置["task_param"] = dict(店铺配置["flow_context"])
            return None

        if task_name not in 任务参数任务集合:
            return None

        任务参数记录 = await self._获取待执行任务参数记录(shop_id, task_name)
        if not 任务参数记录:
            from browser.任务回调 import 上报

            await 上报("没有待执行的任务参数", shop_id)
            return None

        任务参数 = dict(任务参数记录.get("params") or {})
        任务参数["task_param_id"] = 任务参数记录["id"]
        店铺配置["task_param"] = 任务参数

        await 任务参数服务实例.更新执行结果(
            任务参数记录["id"],
            "running",
            结果=任务参数记录.get("result") or {},
            错误信息=None,
        )
        return 任务参数记录

    async def _回填任务参数执行结果(
        self,
        任务参数记录: Optional[Dict[str, Any]],
        状态: str,
        结果: Optional[Dict[str, Any]] = None,
        错误信息: Optional[str] = None,
    ) -> None:
        """按执行结果回填 task_params 记录。"""
        if not 任务参数记录:
            return

        await 任务参数服务实例.更新执行结果(
            任务参数记录["id"],
            状态,
            结果=结果 or {},
            错误信息=错误信息,
        )

    @staticmethod
    def _标准化流程参数ID列表(原始值: Any) -> List[int]:
        """将任意输入统一转换为流程参数ID列表。"""
        if isinstance(原始值, list):
            结果: List[int] = []
            for 记录ID in 原始值:
                if 记录ID in (None, ""):
                    continue
                结果.append(int(记录ID))
            return 结果
        if 原始值 in (None, "", ()):
            return []
        return [int(原始值)]

    @staticmethod
    def _构建流程回调结果(
        结果: str,
        结果数据: Optional[Dict[str, Any]] = None,
        错误信息: Optional[str] = None,
    ) -> Dict[str, Any]:
        """构造供 flow 推进逻辑消费的执行结果结构。"""
        return {
            "status": "completed",
            "result": 结果,
            "result_data": dict(结果数据 or {}),
            "error": 错误信息,
        }

    @staticmethod
    def _构建流程店铺配置(
        基础配置: Dict[str, Any],
        flow_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """为单条 flow 记录构造可直接执行的店铺配置。"""
        店铺配置 = dict(基础配置)
        店铺配置.pop("flow_param_ids", None)
        店铺配置.pop("merge", None)
        店铺配置["flow_context"] = dict(flow_context)
        店铺配置["task_param"] = dict(flow_context)
        return 店铺配置

    async def _执行流程批量任务(
        self,
        shop_id: str,
        task_name: str,
        页面: Any,
        店铺配置: Dict[str, Any],
    ) -> Dict[str, Any]:
        """同一页面内串行处理多条 flow_params，避免重复投递多个 Celery 任务。"""
        from backend.services.流程参数服务 import 流程参数服务实例

        flow_param_ids = self._标准化流程参数ID列表(店铺配置.get("flow_param_ids"))
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
                合并上下文 = await self._构建合并参数(记录列表, task_name)

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
                await self._标记合并跳过(flow_param_id, task_name, step_index, 主记录ID)

            try:
                单次结果 = await self.执行任务(
                    shop_id=shop_id,
                    task_name=task_name,
                    页面=页面,
                    店铺配置=self._构建流程店铺配置(店铺配置, 合并上下文),
                )
                流程回调结果 = self._构建流程回调结果(
                    str(单次结果.get("result") or "失败"),
                    单次结果.get("result_data") or {},
                    None if str(单次结果.get("result") or "") == "成功" else str(单次结果.get("result") or "任务执行失败"),
                )
            except Exception as 异常:
                流程回调结果 = self._构建流程回调结果("失败", {}, str(异常))

            await self.处理流程步骤执行完成(
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
                单次结果 = await self.执行任务(
                    shop_id=shop_id,
                    task_name=task_name,
                    页面=页面,
                    店铺配置=self._构建流程店铺配置(店铺配置, flow_context),
                )
                流程回调结果 = self._构建流程回调结果(
                    str(单次结果.get("result") or "失败"),
                    单次结果.get("result_data") or {},
                    None if str(单次结果.get("result") or "") == "成功" else str(单次结果.get("result") or "任务执行失败"),
                )
            except Exception as 异常:
                流程回调结果 = self._构建流程回调结果("失败", {}, str(异常))

            await self.处理流程步骤执行完成(
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

    @staticmethod
    def _步骤是否终态(步骤状态: str) -> bool:
        return 步骤状态 in {"completed", "failed", "merged_skip"}

    @staticmethod
    def _步骤可继续(步骤状态: str, on_fail: str) -> bool:
        if 步骤状态 in {"completed", "merged_skip"}:
            return True
        return 步骤状态 == "failed" and on_fail in {"continue", "log_and_skip"}

    @staticmethod
    def _业务执行成功(执行结果: Dict[str, Any]) -> bool:
        return 执行结果.get("status") == "completed" and 执行结果.get("result") == "成功"

    async def _获取流程步骤信息(
        self,
        flow_param_id: int,
        task_name: str,
        step_index: int,
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]], int, Dict[str, Any], Optional[Dict[str, Any]]]:
        from backend.services.流程参数服务 import 流程参数服务实例
        from backend.services.流程服务 import 流程服务实例

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

    async def _标记下一步等待屏障(
        self,
        flow_param_id: int,
        next_task_name: str,
        当前步骤序号: int,
    ) -> None:
        from backend.services.流程参数服务 import 流程参数服务实例

        await 流程参数服务实例.更新步骤结果(
            flow_param_id,
            next_task_name,
            步骤状态="waiting_barrier",
            step_index=当前步骤序号,
            当前步骤=当前步骤序号,
        )

    async def _准备下一步执行(
        self,
        flow_param_id: int,
        next_task_name: str,
        next_step_index: int,
        附加数据: Optional[Dict[str, Any]] = None,
    ) -> bool:
        from backend.services.流程参数服务 import 流程参数服务实例

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

    async def _标记合并跳过(
        self,
        flow_param_id: int,
        task_name: str,
        step_index: int,
        merged_to: int,
    ) -> None:
        from backend.services.流程参数服务 import 流程参数服务实例

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

    async def _构建合并参数(
        self,
        记录列表: List[Dict[str, Any]],
        next_task_name: str,
    ) -> Dict[str, Any]:
        from backend.services.流程参数服务 import 流程参数服务实例

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

    async def _投递下一步任务(
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
        from backend.services.执行服务 import 执行服务实例
        from backend.services.流程参数服务 import 流程参数服务实例

        if not record_ids:
            return

        if next_step.get("merge"):
            主记录ID = int(主执行记录ID or record_ids[0])
            合并成员ID列表: List[int] = []
            if await self._准备下一步执行(
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
                await self._标记合并跳过(记录ID, str(next_step["task"]), next_step_index, 主记录ID)
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
                if await self._准备下一步执行(记录ID, str(next_step["task"]), next_step_index):
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
            if not await self._准备下一步执行(记录ID, str(next_step["task"]), next_step_index):
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

    async def _回写合并步骤结果(
        self,
        *,
        主记录ID: int,
        task_name: str,
        step_index: int,
        执行结果: Dict[str, Any],
        允许继续: bool,
        最终步骤: bool,
    ) -> List[int]:
        from backend.services.流程参数服务 import 流程参数服务实例

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
            商品成功 = 商品ID in 成功列表 if 成功列表 or 失败列表 else self._业务执行成功(执行结果)
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
        from backend.services.流程参数服务 import 流程参数服务实例

        流程参数记录, 步骤列表, 实际步骤序号, 当前步骤, 下一步骤 = await self._获取流程步骤信息(
            flow_param_id,
            task_name,
            step_index,
        )

        批次ID = str(流程参数记录.get("batch_id") or "")
        店铺ID = str(流程参数记录.get("shop_id") or "")
        店铺名称 = str(流程参数记录.get("shop_name") or 店铺ID)
        业务成功 = self._业务执行成功(执行结果)
        允许继续 = 业务成功 or on_fail in {"continue", "log_and_skip"}
        错误信息 = str(执行结果.get("error") or 执行结果.get("result") or "任务执行失败")
        最终步骤 = 实际步骤序号 >= len(步骤列表) or not 下一步骤
        当前步骤结果 = (流程参数记录.get("step_results") or {}).get(task_name) or {}
        合并执行当前步 = bool(当前步骤.get("merge")) or isinstance(当前步骤结果.get("merged_context"), dict)

        if 合并执行当前步:
            可继续记录ID列表 = await self._回写合并步骤结果(
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

        当前步骤名 = str(当前步骤["task"])
        需要屏障 = bool(当前步骤.get("barrier")) or bool(下一步骤.get("merge"))
        if not 需要屏障:
            await self._投递下一步任务(
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
            self._步骤是否终态(str(记录.get("step_status") or "pending"))
            for 记录 in 全部记录
        ):
            for 记录ID in 可继续记录ID列表:
                await self._标记下一步等待屏障(记录ID, str(下一步骤["task"]), 实际步骤序号)
            return

        候选记录 = [
            记录
            for 记录 in 全部记录
            if self._步骤可继续(str(记录.get("step_status") or "pending"), str(当前步骤.get("on_fail") or on_fail))
        ]
        候选记录ID列表 = [int(记录["id"]) for 记录 in 候选记录]
        if not 候选记录ID列表:
            return

        if 下一步骤.get("merge"):
            主执行记录ID = 候选记录ID列表[0]
            合并参数 = await self._构建合并参数(候选记录, str(下一步骤["task"]))
            await self._投递下一步任务(
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

        await self._投递下一步任务(
            batch_id=批次ID,
            shop_id=店铺ID,
            shop_name=店铺名称,
            next_step=下一步骤,
            next_step_index=实际步骤序号 + 1,
            total_steps=total_steps,
            record_ids=候选记录ID列表,
        )

    async def 获取任务列表(
        self,
        shop_id: Optional[str] = None,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取任务列表（分页 + 筛选）

        参数:
            shop_id: 店铺 ID（可选）
            status: 任务状态（可选）
            task_name: 任务名称（可选）
            page: 页码（从 1 开始）
            page_size: 每页大小

        返回:
            Dict[str, Any]: 分页数据 { "list": [...], "total": N, "page": P, "page_size": S }
        """
        # 构建 WHERE 子句
        where_条件 = []
        where_参数 = []

        if shop_id:
            where_条件.append("shop_id = ?")
            where_参数.append(shop_id)

        if status:
            where_条件.append("status = ?")
            where_参数.append(status)

        if task_name:
            where_条件.append("task_name = ?")
            where_参数.append(task_name)

        where_子句 = " WHERE " + " AND ".join(where_条件) if where_条件 else ""

        # 查询总数
        async with 获取连接() as db:
            db.row_factory = aiosqlite.Row

            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM task_logs{where_子句}"
            async with db.execute(count_sql, where_参数) as cursor:
                row = await cursor.fetchone()
                总数 = row["total"]

            # 查询分页数据
            offset = (page - 1) * page_size
            list_sql = f"""
                SELECT * FROM task_logs{where_子句}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            async with db.execute(list_sql, where_参数 + [page_size, offset]) as cursor:
                rows = await cursor.fetchall()
                任务列表 = [dict(row) for row in rows]

        return {
            "list": 任务列表,
            "total": 总数,
            "page": page,
            "page_size": page_size
        }

    async def 获取任务详情(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务详情

        参数:
            task_id: 任务 ID

        返回:
            Optional[Dict[str, Any]]: 任务详情，不存在返回 None
        """
        async with 获取连接() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM task_logs WHERE task_id = ?",
                (task_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def 创建任务记录(
        self,
        shop_id: str,
        task_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建任务记录

        参数:
            shop_id: 店铺 ID
            task_name: 任务名称
            params: 任务参数（可选）

        返回:
            Dict[str, Any]: 新建任务记录
        """
        task_id = uuid.uuid4().hex
        当前时间 = datetime.now().isoformat()
        params_json = json.dumps(params, ensure_ascii=False) if params else None

        async with 获取连接() as db:
            await db.execute(
                """
                INSERT INTO task_logs (
                    task_id, shop_id, task_name, status, params,
                    started_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, shop_id, task_name, "pending", params_json, 当前时间, 当前时间)
            )
            await db.commit()

        return {
            "task_id": task_id,
            "shop_id": shop_id,
            "task_name": task_name,
            "status": "pending",
            "params": params_json,
            "started_at": 当前时间,
            "created_at": 当前时间
        }

    async def 触发任务(
        self,
        shop_id: str,
        task_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        触发任务

        参数:
            shop_id: 店铺 ID
            task_name: 任务名称
            params: 任务参数（可选）

        返回:
            Dict[str, Any]: 任务信息
        """
        任务记录 = await self.创建任务记录(shop_id=shop_id, task_name=task_name, params=params)

        # 后台异步执行任务（不阻塞 API 返回）
        asyncio.create_task(
            self.统一执行任务(
                task_id=任务记录["task_id"],
                shop_id=shop_id,
                task_name=task_name,
                params=params,
                来源="http"
            )
        )

        return 任务记录

    async def _后台执行任务(
        self,
        task_id: str,
        shop_id: str,
        task_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        后台执行任务

        参数:
            task_id: 任务 ID
            shop_id: 店铺 ID
            task_name: 任务名称
            params: 任务参数（可选）
        """
        await self.统一执行任务(
            task_id=task_id,
            shop_id=shop_id,
            task_name=task_name,
            params=params,
            来源="http"
        )

    async def 统一执行任务(
        self,
        task_id: str,
        shop_id: str,
        task_name: str,
        params: Optional[Dict[str, Any]] = None,
        来源: str = "http"
    ) -> Dict[str, Any]:
        """
        统一执行任务链路

        参数:
            task_id: 任务 ID
            shop_id: 店铺 ID
            task_name: 任务名称
            params: 任务参数（可选）
            来源: 触发来源，仅用于日志记录

        返回:
            Dict[str, Any]: 执行结果
        """
        展示店铺名 = shop_id
        if isinstance(params, dict):
            展示店铺名 = str(params.get("shop_name") or shop_id)

        try:
            print(
                f"[任务服务] 开始执行任务: 来源={来源}, task_id={task_id}, "
                f"shop_name={展示店铺名}, shop_id={shop_id}, task_name={task_name}"
            )

            # 如果是登录任务，更新店铺状态为 logging_in
            if task_name == "登录":
                from backend.services.店铺服务 import 店铺服务实例
                await 店铺服务实例.更新(shop_id, {"status": "logging_in"})
                print(f"[任务服务] 店铺状态已更新为 logging_in")

            # 更新状态为 running
            await self.更新任务状态(task_id, "running")
            print(f"[任务服务] 任务状态已更新为 running")

            # 获取浏览器页面
            from backend.services import 浏览器服务 as 浏览器服务模块

            # 中文注释：浏览器初始化依赖 Playwright，必须加超时和异常包装，避免任务一直卡在启动阶段。
            try:
                await asyncio.wait_for(
                    浏览器服务模块.确保已初始化(),
                    timeout=浏览器初始化超时秒
                )
            except asyncio.TimeoutError as e:
                raise TimeoutError(f"浏览器初始化超时（{浏览器初始化超时秒}秒）") from e
            except Exception as e:
                raise RuntimeError(f"浏览器初始化失败: {e}") from e

            管理器实例 = 浏览器服务模块.获取当前管理器实例()
            if 管理器实例 is None:
                raise RuntimeError("浏览器初始化失败: 管理器实例为空")

            print(f"[任务服务] 浏览器管理器实例: {管理器实例}")

            # 检查店铺浏览器是否已打开
            if shop_id not in 管理器实例.实例集:
                print(f"[任务服务] 店铺浏览器未打开，开始自动初始化...")
                # 自动初始化浏览器
                from backend.services.店铺服务 import 店铺服务实例
                店铺 = await 店铺服务实例.根据ID获取(shop_id)
                if not 店铺:
                    raise Exception(f"店铺不存在: {shop_id}")

                # 打开浏览器
                from backend.services.浏览器服务 import 打开店铺浏览器
                店铺配置 = {
                    "name": 店铺.get("name"),
                    "proxy": 店铺.get("proxy")
                }
                # 中文注释：打开浏览器属于外部 IO，这里单独加超时兜底，避免任务长时间挂起。
                try:
                    await asyncio.wait_for(
                        打开店铺浏览器(shop_id, 店铺配置),
                        timeout=打开浏览器超时秒
                    )
                except asyncio.TimeoutError as e:
                    raise TimeoutError(f"打开店铺浏览器超时（{打开浏览器超时秒}秒）") from e
                except Exception as e:
                    raise RuntimeError(f"打开店铺浏览器失败: {e}") from e

                管理器实例 = 浏览器服务模块.获取当前管理器实例()
                if 管理器实例 is None:
                    raise RuntimeError("浏览器打开失败: 管理器实例为空")
                print(f"[任务服务] 浏览器已自动打开")
            else:
                print(f"[任务服务] 店铺浏览器已打开，复用现有实例")

            # 获取页面
            页面 = await self._确保页面可用(管理器实例, shop_id)
            if 页面 is None:
                raise RuntimeError("浏览器页面获取失败: 页面对象为空")
            print(f"[任务服务] 获取到页面对象: {页面}")

            # 获取店铺配置（包含解密后的密码）
            from backend.services.店铺服务 import 店铺服务实例

            店铺完整信息 = await 店铺服务实例.根据ID获取完整信息(shop_id)
            if not 店铺完整信息:
                raise Exception(f"店铺不存在: {shop_id}")
            展示店铺名 = str(店铺完整信息.get("name") or 展示店铺名)

            print(f"[任务服务] 获取到店铺完整信息，用户名: {店铺完整信息.get('username')}")

            # 构建店铺配置
            店铺配置 = {
                "shop_id": shop_id,  # 添加 shop_id 用于 Cookie 文件命名
                "username": 店铺完整信息.get("username"),
                "password": 店铺完整信息.get("password")
            }

            # 边界检查：密码不能为空
            if not 店铺配置.get("username"):
                raise Exception("店铺用户名为空，请先在店铺管理中设置用户名")

            if not 店铺配置.get("password"):
                raise Exception("店铺密码为空，请先在店铺管理中设置密码")

            print(f"[任务服务] 店铺配置验证通过，密码长度: {len(店铺配置.get('password', ''))}")

            # 添加邮箱配置（用于邮箱验证码功能）
            if 店铺完整信息.get("smtp_host"):
                店铺配置["smtp_host"] = 店铺完整信息.get("smtp_host")
            if 店铺完整信息.get("smtp_port"):
                店铺配置["smtp_port"] = 店铺完整信息.get("smtp_port")
            if 店铺完整信息.get("smtp_user"):
                店铺配置["smtp_user"] = 店铺完整信息.get("smtp_user")
            if 店铺完整信息.get("smtp_pass"):
                店铺配置["smtp_pass"] = 店铺完整信息.get("smtp_pass")
            if 店铺完整信息.get("smtp_protocol"):
                店铺配置["smtp_protocol"] = 店铺完整信息.get("smtp_protocol")

            if isinstance(params, dict):
                if params.get("batch_id") is not None:
                    店铺配置["batch_id"] = params.get("batch_id")
                if params.get("step_index") is not None:
                    店铺配置["step_index"] = params.get("step_index")
                if params.get("total_steps") is not None:
                    店铺配置["total_steps"] = params.get("total_steps")
                if params.get("on_fail") is not None:
                    店铺配置["on_fail"] = params.get("on_fail")
                if params.get("flow_param_ids") is not None:
                    店铺配置["flow_param_ids"] = self._标准化流程参数ID列表(params.get("flow_param_ids"))
                if params.get("merge") is not None:
                    店铺配置["merge"] = bool(params.get("merge"))

            print(f"[任务服务] 开始执行任务...")
            # 中文注释：任务执行过程可能包含页面交互和网络等待，设置超时可避免任务永久占用 Worker。
            try:
                执行结果 = await asyncio.wait_for(
                    self.执行任务(
                        shop_id=shop_id,
                        task_name=task_name,
                        页面=页面,
                        店铺配置=店铺配置
                    ),
                    timeout=任务执行超时秒
                )
            except asyncio.TimeoutError as e:
                raise TimeoutError(f"任务执行超时（{任务执行超时秒}秒）") from e

            结果 = 执行结果["result"]
            print(f"[任务服务] 任务执行完成，结果: {结果}")

            # 更新任务状态为 completed
            await self.更新任务状态(task_id, "completed", result=str(结果))
            print(f"[任务服务] 任务状态已更新为 completed")

            # 如果是登录任务，根据结果更新店铺状态
            if task_name == "登录":
                from backend.services.店铺服务 import 店铺服务实例
                if 结果 == "成功":
                    await 店铺服务实例.更新(shop_id, {"status": "online"})
                    print(f"[任务服务] 登录成功，店铺状态已更新为 online")
                else:
                    await 店铺服务实例.更新(shop_id, {"status": "offline"})
                    print(f"[任务服务] 登录失败，店铺状态已更新为 offline")

            return {
                "task_id": task_id,
                "shop_id": shop_id,
                "shop_name": 展示店铺名,
                "task_name": task_name,
                "status": "completed",
                "result": str(结果),
                "result_data": 执行结果.get("result_data", {}),
                "error": None
            }

        except Exception as e:
            print(f"[任务服务] 任务执行失败: shop_name={展示店铺名}, shop_id={shop_id}, error={e}")
            import traceback
            traceback.print_exc()

            # 更新任务状态为 failed
            await self.更新任务状态(task_id, "failed", error=str(e))

            # 如果是登录任务，更新店铺状态为 offline
            if task_name == "登录":
                from backend.services.店铺服务 import 店铺服务实例
                await 店铺服务实例.更新(shop_id, {"status": "offline"})
                print(f"[任务服务] 登录异常，店铺状态已更新为 offline")

            return {
                "task_id": task_id,
                "shop_id": shop_id,
                "shop_name": 展示店铺名,
                "task_name": task_name,
                "status": "failed",
                "result": None,
                "error": str(e)
            }

    async def 取消任务(self, task_id: str) -> bool:
        """
        取消任务（仅限 pending 状态）

        参数:
            task_id: 任务 ID

        返回:
            bool: 是否取消成功
        """
        # 查询任务状态
        任务 = await self.获取任务详情(task_id)
        if not 任务:
            return False

        # 只能取消 pending 状态的任务
        if 任务["status"] != "pending":
            return False

        # TODO: 集成 Celery revoke 逻辑（Phase 7）
        # 示例代码：
        # from tasks.celery应用 import celery应用
        # celery应用.control.revoke(task_id, terminate=True)

        # 更新状态为 cancelled
        async with 获取连接() as db:
            await db.execute(
                """
                UPDATE task_logs
                SET status = ?, finished_at = ?
                WHERE task_id = ?
                """,
                ("cancelled", datetime.now().isoformat(), task_id)
            )
            await db.commit()

        return True

    async def 删除任务(self, task_id: str) -> bool:
        """
        删除任务记录

        参数:
            task_id: 任务 ID

        返回:
            bool: 是否删除成功
        """
        # 查询任务是否存在
        任务 = await self.获取任务详情(task_id)
        if not 任务:
            return False

        # 删除任务记录
        async with 获取连接() as db:
            await db.execute(
                "DELETE FROM task_logs WHERE task_id = ?",
                (task_id,)
            )
            await db.commit()

        return True

    async def 清空历史记录(self) -> int:
        """
        删除所有已完成和已失败的任务记录

        返回:
            int: 删除的记录数量
        """
        async with 获取连接() as db:
            # 查询要删除的记录数量
            async with db.execute(
                "SELECT COUNT(*) FROM task_logs WHERE status IN ('completed', 'failed', 'cancelled')"
            ) as cursor:
                result = await cursor.fetchone()
                删除数量 = result[0] if result else 0

            # 删除记录
            await db.execute(
                "DELETE FROM task_logs WHERE status IN ('completed', 'failed', 'cancelled')"
            )
            await db.commit()

        return 删除数量

    async def 更新任务状态(
        self,
        task_id: str,
        status: str,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        更新任务状态（供回调装饰器内部调用）

        参数:
            task_id: 任务 ID
            status: 任务状态
            result: 执行结果（可选）
            error: 错误信息（可选）

        返回:
            bool: 是否更新成功
        """
        # 构建更新字段
        更新字段 = ["status = ?"]
        更新参数 = [status]

        if result is not None:
            更新字段.append("result = ?")
            更新参数.append(result)

        if error is not None:
            更新字段.append("error = ?")
            更新参数.append(error)

        # 如果是完成或失败状态，更新 finished_at
        if status in ("completed", "failed", "cancelled"):
            更新字段.append("finished_at = ?")
            更新参数.append(datetime.now().isoformat())

        # 执行更新
        async with 获取连接() as db:
            cursor = await db.execute(
                f"""
                UPDATE task_logs
                SET {", ".join(更新字段)}
                WHERE task_id = ?
                """,
                更新参数 + [task_id]
            )
            await db.commit()
            return cursor.rowcount > 0

    async def 执行任务(
        self,
        shop_id: str,
        task_name: str,
        页面,
        店铺配置: dict
    ) -> Dict[str, Any]:
        """
        执行已注册任务

        参数:
            shop_id: 店铺 ID
            task_name: 任务名称
            页面: Playwright page 对象
            店铺配置: 店铺配置字典

        返回:
            Dict[str, Any]: 执行结果
        """
        from tasks.任务注册表 import 获取任务

        流程参数ID列表 = self._标准化流程参数ID列表(店铺配置.get("flow_param_ids"))
        if len(流程参数ID列表) > 1 or (bool(店铺配置.get("merge")) and 流程参数ID列表):
            return await self._执行流程批量任务(
                shop_id=shop_id,
                task_name=task_name,
                页面=页面,
                店铺配置=店铺配置,
            )

        任务参数记录 = await self._准备任务参数(shop_id, task_name, 店铺配置)
        使用流程上下文 = isinstance(店铺配置.get("flow_context"), dict)
        if task_name in 任务参数任务集合 and not 任务参数记录 and not 使用流程上下文:
            return {
                "task_name": task_name,
                "shop_id": shop_id,
                "result": "跳过",
            }

        # 获取任务实例
        任务实例 = 获取任务(task_name)

        try:
            # 执行任务
            结果 = await 任务实例.执行(页面, 店铺配置)
        except Exception as e:
            await self._回填任务参数执行结果(
                任务参数记录,
                "failed",
                结果=getattr(任务实例, "_执行结果", {}) or {},
                错误信息=str(e),
            )
            raise

        执行结果数据 = getattr(任务实例, "_执行结果", {}) or {}
        if 任务参数记录:
            if 结果 == "成功":
                await self._回填任务参数执行结果(
                    任务参数记录,
                    "success",
                    结果=执行结果数据,
                )
                下一步任务名 = 任务链映射.get(task_name)
                if 下一步任务名 and 任务参数记录:
                    try:
                        await 任务参数服务实例.创建后续任务(
                            源记录=任务参数记录,
                            执行结果=执行结果数据,
                            下一步任务名=下一步任务名,
                        )
                    except Exception as e:
                        print(f"[任务服务] 自动创建后续任务失败（忽略）: {e}")
            elif 结果 != "跳过":
                await self._回填任务参数执行结果(
                    任务参数记录,
                    "failed",
                    结果=执行结果数据,
                    错误信息=str(结果 or "任务执行失败"),
                )

        return {
            "task_name": task_name,
            "shop_id": shop_id,
            "result": 结果,
            "result_data": 执行结果数据,
        }


# 创建单例
任务服务实例 = 任务服务()
