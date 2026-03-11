"""
基础任务模块

定义所有任务共享的抽象接口与安全执行包装。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class 基础任务(ABC):
    """所有任务类的抽象基类。"""

    @abstractmethod
    async def 执行(self, 页面, 店铺配置) -> str:
        """
        执行任务核心逻辑。

        参数:
            页面: Playwright 页面对象
            店铺配置: 店铺配置字典

        返回:
            str: 任务执行结果
        """
        raise NotImplementedError

    async def 安全执行(self, 页面, 店铺配置) -> dict[str, Any]:
        """
        安全执行任务，统一包装成功与异常结果。

        返回:
            dict[str, Any]: 包含 status/result 或 status/error 的结果
        """
        try:
            结果 = await self.执行(页面, 店铺配置)
            return {
                "status": "success",
                "result": 结果,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }


__all__ = ["基础任务"]
