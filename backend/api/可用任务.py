"""
可用任务接口模块

提供前端可直接读取的任务注册列表。
"""
from fastapi import APIRouter

from backend.models.数据结构 import 统一响应, 成功, 失败
from tasks.注册表 import 获取所有任务


路由 = APIRouter(prefix="/api/tasks", tags=["任务管理"])


@路由.get("/available", summary="获取可用任务列表")
async def 获取可用任务列表() -> 统一响应:
    """
    获取当前已注册的任务列表。

    返回:
        统一响应: 包含任务名称与描述列表
    """
    try:
        return 成功(data={"tasks": 获取所有任务()})
    except Exception as e:
        return 失败(f"获取可用任务列表失败: {str(e)}")
