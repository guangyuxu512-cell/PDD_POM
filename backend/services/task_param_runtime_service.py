"""
任务参数运行时服务模块

封装 task_params 任务在执行前后的参数注入与结果回填。
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Set

from backend.services.task_params_service import 任务参数服务实例


class 任务参数运行时服务:
    """处理 task_params 相关的运行时注入与回填。"""

    def __init__(self, 任务参数任务集合: Set[str]) -> None:
        self._任务参数任务集合 = set(任务参数任务集合)

    async def 获取待执行任务参数记录(
        self,
        shop_id: str,
        task_name: str,
    ) -> Optional[Dict[str, Any]]:
        """为依赖 task_params 的任务取一条待执行记录。"""
        if task_name not in self._任务参数任务集合:
            return None

        待执行列表 = await 任务参数服务实例.获取待执行列表(shop_id, task_name)
        if not 待执行列表:
            return None
        return 待执行列表[0]

    async def 准备任务参数(
        self,
        shop_id: str,
        task_name: str,
        店铺配置: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """读取 task_params 并注入到店铺配置。"""
        if isinstance(店铺配置.get("flow_context"), dict):
            店铺配置["task_param"] = dict(店铺配置["flow_context"])
            return None

        if task_name not in self._任务参数任务集合:
            return None

        任务参数记录 = await self.获取待执行任务参数记录(shop_id, task_name)
        if not 任务参数记录:
            from browser.task_callback import 上报

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

    async def 回填任务参数执行结果(
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
