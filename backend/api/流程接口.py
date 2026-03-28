"""
流程接口模块

提供流程模板 CRUD API。
"""
from fastapi import APIRouter

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
    流程创建请求,
    流程预检请求,
    流程运行创建请求,
    流程更新请求,
)
from backend.services.执行服务 import 执行服务实例
from backend.services.流程服务 import 流程服务实例


路由 = APIRouter(prefix="/api/flows", tags=["流程管理"])


@路由.get("", include_in_schema=False)
@路由.get("/", summary="获取流程列表")
async def 获取流程列表() -> 统一响应:
    """获取流程模板列表。"""
    try:
        return 成功(data=await 流程服务实例.获取全部())
    except Exception as e:
        return 失败(f"获取流程列表失败: {str(e)}")


@路由.post("", include_in_schema=False)
@路由.post("/", summary="创建流程")
async def 创建流程(请求: 流程创建请求) -> 统一响应:
    """创建流程模板。"""
    try:
        流程 = await 流程服务实例.创建(请求.model_dump(exclude_none=True))
        return 成功(data=流程, message="创建成功")
    except Exception as e:
        return 失败(f"创建流程失败: {str(e)}")


@路由.put("/{flow_id}", summary="更新流程")
async def 更新流程(flow_id: str, 请求: 流程更新请求) -> 统一响应:
    """更新流程模板。"""
    try:
        流程 = await 流程服务实例.更新(flow_id, 请求.model_dump(exclude_unset=True))
        if not 流程:
            return 失败("流程不存在")
        return 成功(data=流程, message="更新成功")
    except Exception as e:
        return 失败(f"更新流程失败: {str(e)}")


@路由.delete("/{flow_id}", summary="删除流程")
async def 删除流程(flow_id: str) -> 统一响应:
    """删除流程模板。"""
    try:
        成功标志 = await 流程服务实例.删除(flow_id)
        if not 成功标志:
            return 失败("流程不存在")
        return 成功(message="删除成功")
    except Exception as e:
        return 失败(f"删除流程失败: {str(e)}")


@路由.post("/{flow_id}/precheck", summary="预检流程")
async def 预检流程(flow_id: str, 请求: 流程预检请求) -> 统一响应:
    """启动前预检流程输入。"""
    try:
        if not await 流程服务实例.根据ID获取(flow_id):
            return 失败("流程不存在")

        结果 = await 执行服务实例.预检流程(
            flow_id=flow_id,
            shop_ids=请求.shop_ids,
            input_set_id=请求.input_set_id,
            empty_run_policy=请求.empty_run_policy,
        )
        return 成功(data=结果, message="预检完成")
    except Exception as e:
        return 失败(f"预检流程失败: {str(e)}")


@路由.post("/{flow_id}/runs", summary="创建流程运行")
async def 创建流程运行(flow_id: str, 请求: 流程运行创建请求) -> 统一响应:
    """创建一次流程运行。"""
    try:
        if not await 流程服务实例.根据ID获取(flow_id):
            return 失败("流程不存在")

        结果 = await 执行服务实例.创建批次(
            flow_id=flow_id,
            task_name=None,
            shop_ids=请求.shop_ids,
            concurrency=请求.requested_concurrency,
            callback_url=请求.callback_url,
            input_set_id=请求.input_set_id,
            empty_run_policy=请求.empty_run_policy,
        )
        return 成功(
            data={
                "run_id": 结果["batch_id"],
                "status": 结果["status"],
                "total_items": 结果["total"],
            },
            message="流程已启动",
        )
    except Exception as e:
        return 失败(f"创建流程运行失败: {str(e)}")
