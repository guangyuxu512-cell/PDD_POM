"""
流程输入接口模块

提供 flow_input_sets / flow_input_rows 的管理与导入接口。
"""
from __future__ import annotations

from fastapi import APIRouter, File, Query, UploadFile

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
    流程输入行创建请求,
    流程输入行更新请求,
    流程输入集创建请求,
    流程输入集更新请求,
)
from backend.services.流程服务 import 流程服务实例
from backend.services.流程输入服务 import 流程输入服务实例


路由 = APIRouter(tags=["流程输入"])


@路由.get("/api/flows/{flow_id}/input-sets", summary="获取流程输入集列表")
async def 获取输入集列表(flow_id: str) -> 统一响应:
    """获取指定流程下的输入集列表。"""
    try:
        if not await 流程服务实例.根据ID获取(flow_id):
            return 失败("流程不存在")
        return 成功(data=await 流程输入服务实例.获取输入集列表(flow_id))
    except Exception as e:
        return 失败(f"获取输入集列表失败: {str(e)}")


@路由.post("/api/flows/{flow_id}/input-sets", summary="创建流程输入集")
async def 创建输入集(flow_id: str, 请求: 流程输入集创建请求) -> 统一响应:
    """创建流程输入集。"""
    try:
        输入集 = await 流程输入服务实例.创建输入集(
            {
                **请求.model_dump(),
                "flow_id": flow_id,
            }
        )
        return 成功(data=输入集, message="创建成功")
    except Exception as e:
        return 失败(f"创建输入集失败: {str(e)}")


@路由.put("/api/flows/{flow_id}/input-sets/{input_set_id}", summary="更新流程输入集")
async def 更新输入集(
    flow_id: str,
    input_set_id: str,
    请求: 流程输入集更新请求,
) -> 统一响应:
    """更新流程输入集。"""
    try:
        输入集 = await 流程输入服务实例.根据ID获取输入集(input_set_id)
        if not 输入集 or str(输入集.get("flow_id") or "") != flow_id:
            return 失败("输入集不存在")

        更新后输入集 = await 流程输入服务实例.更新输入集(
            input_set_id,
            请求.model_dump(exclude_none=True),
        )
        if not 更新后输入集:
            return 失败("输入集不存在")
        return 成功(data=更新后输入集, message="更新成功")
    except Exception as e:
        return 失败(f"更新输入集失败: {str(e)}")


@路由.delete("/api/flows/{flow_id}/input-sets/{input_set_id}", summary="删除流程输入集")
async def 删除输入集(flow_id: str, input_set_id: str) -> 统一响应:
    """删除流程输入集。"""
    try:
        输入集 = await 流程输入服务实例.根据ID获取输入集(input_set_id)
        if not 输入集 or str(输入集.get("flow_id") or "") != flow_id:
            return 失败("输入集不存在")

        成功标志 = await 流程输入服务实例.删除输入集(input_set_id)
        if not 成功标志:
            return 失败("输入集不存在")
        return 成功(message="删除成功")
    except Exception as e:
        return 失败(f"删除输入集失败: {str(e)}")


@路由.get("/api/input-sets/{input_set_id}/rows", summary="获取输入行列表")
async def 获取输入行列表(
    input_set_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=500, description="每页大小"),
) -> 统一响应:
    """分页获取输入行。"""
    try:
        if not await 流程输入服务实例.根据ID获取输入集(input_set_id):
            return 失败("输入集不存在")
        return 成功(
            data=await 流程输入服务实例.获取输入行列表(
                input_set_id,
                page=page,
                page_size=page_size,
            )
        )
    except Exception as e:
        return 失败(f"获取输入行列表失败: {str(e)}")


@路由.post("/api/input-sets/{input_set_id}/rows/import", summary="导入输入行")
async def 导入输入行(
    input_set_id: str,
    file: UploadFile = File(..., description="CSV/XLSX 文件"),
) -> 统一响应:
    """导入 CSV/XLSX 输入行。"""
    try:
        if not await 流程输入服务实例.根据ID获取输入集(input_set_id):
            return 失败("输入集不存在")

        文件名 = (file.filename or "").strip()
        if 文件名 and not 文件名.lower().endswith((".csv", ".xlsx")):
            return 失败("导入输入行失败: 仅支持 .csv 或 .xlsx 文件")

        文件内容 = await file.read()
        导入结果 = await 流程输入服务实例.批量导入输入行(
            input_set_id,
            文件内容,
            file_name=文件名,
        )
        return 成功(data=导入结果, message="导入完成")
    except Exception as e:
        return 失败(f"导入输入行失败: {str(e)}")


@路由.post("/api/input-sets/{input_set_id}/rows", summary="创建输入行")
async def 创建输入行(input_set_id: str, 请求: 流程输入行创建请求) -> 统一响应:
    """创建单条输入行。"""
    try:
        输入行 = await 流程输入服务实例.创建输入行(
            {
                **请求.model_dump(),
                "input_set_id": input_set_id,
            }
        )
        return 成功(data=输入行, message="创建成功")
    except Exception as e:
        return 失败(f"创建输入行失败: {str(e)}")


@路由.put("/api/input-sets/{input_set_id}/rows/{row_id}", summary="更新输入行")
async def 更新输入行(
    input_set_id: str,
    row_id: int,
    请求: 流程输入行更新请求,
) -> 统一响应:
    """更新单条输入行。"""
    try:
        输入行 = await 流程输入服务实例.根据ID获取输入行(row_id)
        if not 输入行 or str(输入行.get("input_set_id") or "") != input_set_id:
            return 失败("输入行不存在")

        更新后输入行 = await 流程输入服务实例.更新输入行(
            row_id,
            请求.model_dump(exclude_none=True),
        )
        if not 更新后输入行:
            return 失败("输入行不存在")
        return 成功(data=更新后输入行, message="更新成功")
    except Exception as e:
        return 失败(f"更新输入行失败: {str(e)}")


@路由.delete("/api/input-sets/{input_set_id}/rows/{row_id}", summary="删除输入行")
async def 删除输入行(input_set_id: str, row_id: int) -> 统一响应:
    """删除单条输入行。"""
    try:
        输入行 = await 流程输入服务实例.根据ID获取输入行(row_id)
        if not 输入行 or str(输入行.get("input_set_id") or "") != input_set_id:
            return 失败("输入行不存在")

        成功标志 = await 流程输入服务实例.删除输入行(row_id)
        if not 成功标志:
            return 失败("输入行不存在")
        return 成功(message="删除成功")
    except Exception as e:
        return 失败(f"删除输入行失败: {str(e)}")
