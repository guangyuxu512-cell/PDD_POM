"""
执行流程预检服务模块

抽离流程输入、字段规范化与预检相关的低层逻辑。
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from backend.services.flow_input_service import 流程输入服务实例
from backend.services.flow_params_service import 流程参数服务实例


class 执行流程预检服务:
    """封装 execute_service 中与流程输入预检相关的低层能力。"""

    def __init__(
        self,
        *,
        允许空运行策略集合: set[str],
        任务参数字段别名映射: Dict[str, List[str]],
        获取任务元数据函数: Callable[[str], Dict[str, Any]],
    ) -> None:
        self._允许空运行策略集合 = set(允许空运行策略集合)
        self._任务参数字段别名映射 = {
            str(字段名): list(别名列表)
            for 字段名, 别名列表 in 任务参数字段别名映射.items()
        }
        self._获取任务元数据函数 = 获取任务元数据函数

    @staticmethod
    def 字段值有效(值: Any) -> bool:
        """判断字段值是否可视为已提供。"""
        if 值 is None:
            return False
        if isinstance(值, str):
            return bool(值.strip())
        if isinstance(值, (list, tuple, dict, set)):
            return len(值) > 0
        return True

    def 校验空运行策略(self, empty_run_policy: str) -> str:
        """校验并标准化空运行策略。"""
        标准策略 = str(empty_run_policy or "allow_empty").strip() or "allow_empty"
        if 标准策略 not in self._允许空运行策略集合:
            raise ValueError("empty_run_policy 仅支持 allow_empty 或 require_input")
        return 标准策略

    def 获取任务元数据安全(self, task_name: str) -> Dict[str, Any]:
        """兼容未显式标注元数据的任务。"""
        try:
            return self._获取任务元数据函数(task_name)
        except KeyError:
            return {
                "requires_input": False,
                "required_fields": [],
                "supports_empty_context": True,
                "input_schema": None,
                "output_schema": None,
                "category": "通用",
                "tags": [],
                "timeout": 1800,
                "retry_policy": None,
            }

    def 标准化流程上下文(self, 上下文数据: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """统一整理输入上下文字段，并补齐常见别名。"""
        if not isinstance(上下文数据, dict):
            return {}

        标准上下文: Dict[str, Any] = {}
        for 原始键, 原始值 in 上下文数据.items():
            键名 = str(原始键 or "").strip()
            if not 键名:
                continue
            标准上下文[键名] = 原始值

        for 目标字段, 别名列表 in self._任务参数字段别名映射.items():
            for 别名 in 别名列表:
                if 别名 in 标准上下文 and 目标字段 not in 标准上下文:
                    标准上下文[目标字段] = 标准上下文[别名]

        return 标准上下文

    def 获取字段值(self, 上下文数据: Dict[str, Any], 字段名: str) -> Any:
        """按主字段与别名读取上下文字段值。"""
        别名列表 = self._任务参数字段别名映射.get(字段名, [字段名])
        for 当前字段名 in [字段名, *别名列表]:
            if 当前字段名 in 上下文数据 and self.字段值有效(上下文数据[当前字段名]):
                return 上下文数据[当前字段名]
        return None

    def 步骤需要输入(self, task_name: str) -> bool:
        """判断某个任务是否依赖外部输入。"""
        元数据 = self.获取任务元数据安全(task_name)
        return bool(元数据.get("requires_input")) or not bool(元数据.get("supports_empty_context", True))

    def 校验步骤输入(
        self,
        task_name: str,
        上下文数据: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """校验某一步在给定上下文下是否满足输入要求。"""
        元数据 = self.获取任务元数据安全(task_name)
        标准上下文 = self.标准化流程上下文(上下文数据)
        必填字段列表 = [str(字段).strip() for 字段 in (元数据.get("required_fields") or []) if str(字段).strip()]

        缺失字段列表 = [
            字段名
            for 字段名 in 必填字段列表
            if not self.字段值有效(self.获取字段值(标准上下文, 字段名))
        ]
        if 缺失字段列表:
            return f"缺少 {', '.join(缺失字段列表)}"

        需要输入 = bool(元数据.get("requires_input"))
        支持空上下文 = bool(元数据.get("supports_empty_context", True))
        if not 标准上下文 and (需要输入 or not 支持空上下文):
            return "缺少输入数据"

        输入模型 = 元数据.get("input_schema")
        if 输入模型:
            try:
                输入模型.model_validate(标准上下文)
            except Exception as e:
                return f"参数校验失败: {str(e)}"

        return None

    async def 获取流程输入行映射(
        self,
        *,
        flow_id: str,
        input_set_id: str,
        shop_ids: List[str],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """读取输入集，并按店铺聚合启用输入行。"""
        输入集 = await 流程输入服务实例.根据ID获取输入集(input_set_id)
        if not 输入集:
            raise ValueError("输入集不存在")
        if str(输入集.get("flow_id") or "") != str(flow_id):
            raise ValueError("输入集不属于当前流程")

        输入行列表 = await 流程输入服务实例.获取启用输入行(
            input_set_id,
            shop_ids=shop_ids,
        )
        输入行映射: Dict[str, List[Dict[str, Any]]] = {店铺ID: [] for 店铺ID in shop_ids}
        for 输入行 in 输入行列表:
            店铺ID = str(输入行.get("shop_id") or "").strip()
            if not 店铺ID:
                continue
            输入行映射.setdefault(店铺ID, []).append(
                {
                    **dict(输入行),
                    "input_data": self.标准化流程上下文(dict(输入行.get("input_data") or {})),
                }
            )
        return 输入行映射

    async def 创建输入集兼容流程参数(
        self,
        *,
        flow_id: str,
        输入行映射: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """将输入行兼容映射为 flow_params 记录，复用现有流程执行链路。"""
        流程参数记录映射: Dict[str, List[Dict[str, Any]]] = {店铺ID: [] for 店铺ID in 输入行映射}
        for 店铺ID, 输入行列表 in 输入行映射.items():
            for 输入行 in 输入行列表:
                记录 = await 流程参数服务实例.创建(
                    {
                        "shop_id": 店铺ID,
                        "flow_id": flow_id,
                        "params": dict(输入行.get("input_data") or {}),
                        "step_results": {},
                        "current_step": 0,
                        "status": "pending",
                        "error": None,
                        "batch_id": None,
                        "enabled": True,
                    }
                )
                记录["input_row_id"] = 输入行.get("id")
                流程参数记录映射.setdefault(店铺ID, []).append(记录)
        return 流程参数记录映射

    async def 清理店铺残留流程参数记录(
        self,
        *,
        flow_id: str,
        shop_ids: List[str],
        流程参数记录映射: Dict[str, List[Dict[str, Any]]],
        记录跳过日志: Callable[[str, int, List[int]], None],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """每个店铺只保留最新一条待执行 flow_params，避免首步任务重复投递。"""

        def 记录排序键(流程参数记录: Dict[str, Any]) -> int:
            try:
                return int(流程参数记录.get("id") or 0)
            except (TypeError, ValueError):
                return 0

        for 店铺ID in shop_ids:
            记录列表 = list(流程参数记录映射.get(店铺ID) or [])
            if len(记录列表) <= 1:
                流程参数记录映射[店铺ID] = 记录列表
                continue

            记录列表.sort(key=记录排序键, reverse=True)
            保留记录 = 记录列表[0]
            跳过记录列表 = 记录列表[1:]

            for 跳过记录 in 跳过记录列表:
                记录ID = 跳过记录.get("id")
                if 记录ID is None:
                    continue
                await 流程参数服务实例.更新(int(记录ID), {"status": "skipped"})

            流程参数记录映射[店铺ID] = [保留记录]
            记录跳过日志(
                店铺ID,
                int(保留记录.get("id") or 0),
                [int(记录.get("id")) for 记录 in 跳过记录列表 if 记录.get("id") is not None],
            )

        return 流程参数记录映射

    def 构建运行项上下文映射(
        self,
        *,
        flow_id: Optional[str],
        shop_ids: List[str],
        流程参数记录映射: Dict[str, List[Dict[str, Any]]],
        输入行映射: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """为运行快照生成每个店铺的初始上下文。"""
        运行项上下文映射: Dict[str, Dict[str, Any]] = {}
        for 店铺ID in shop_ids:
            当前上下文: Dict[str, Any] = {}
            flow_param_ids = [
                int(流程参数记录["id"])
                for 流程参数记录 in 流程参数记录映射.get(店铺ID, [])
                if 流程参数记录.get("id") is not None
            ]
            if flow_param_ids:
                当前上下文["flow_param_ids"] = flow_param_ids

            输入行列表 = list((输入行映射 or {}).get(店铺ID) or [])
            if 输入行列表:
                输入行ID列表 = [
                    int(输入行["id"])
                    for 输入行 in 输入行列表
                    if 输入行.get("id") is not None
                ]
                if 输入行ID列表:
                    当前上下文["input_row_ids"] = 输入行ID列表
                    if len(输入行ID列表) == 1:
                        当前上下文["input_row_id"] = 输入行ID列表[0]

            if flow_id and not flow_param_ids:
                当前上下文["flow_context"] = {}

            运行项上下文映射[店铺ID] = 当前上下文

        return 运行项上下文映射
