"""
流程参数接口模块

提供 flow_params 的分页查询、CRUD、CSV/XLSX 导入与批量操作接口。
"""
from typing import Optional

from fastapi import APIRouter, File, Form, Query, UploadFile

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
    流程参数创建请求,
    流程参数更新请求,
    流程参数批量操作请求,
)
from backend.services.流程参数服务 import 流程参数服务实例


路由 = APIRouter(prefix="/api/flow-params", tags=["流程参数"])


@路由.get("", include_in_schema=False)
@路由.get("/", summary="分页查询流程参数")
async def 获取流程参数列表(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    shop_id: Optional[str] = Query(None, description="店铺ID"),
    flow_id: Optional[str] = Query(None, description="流程ID"),
    status: Optional[str] = Query(None, description="状态"),
    batch_id: Optional[str] = Query(None, description="批次ID"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
) -> 统一响应:
    """分页查询流程参数。"""
    try:
        数据 = await 流程参数服务实例.分页查询(
            page=page,
            page_size=page_size,
            shop_id=shop_id,
            flow_id=flow_id,
            status=status,
            batch_id=batch_id,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return 成功(data=数据)
    except Exception as e:
        return 失败(f"获取流程参数列表失败: {str(e)}")


@路由.post("", include_in_schema=False)
@路由.post("/", summary="创建流程参数")
async def 创建流程参数(请求: 流程参数创建请求) -> 统一响应:
    """创建单条流程参数记录。"""
    try:
        记录 = await 流程参数服务实例.创建(请求.model_dump())
        return 成功(data=记录, message="创建成功")
    except Exception as e:
        return 失败(f"创建流程参数失败: {str(e)}")


@路由.post("/import", summary="导入流程参数")
async def 导入流程参数(
    file: UploadFile = File(..., description="CSV/XLSX 文件"),
    flow_id: str = Form(..., description="流程ID"),
) -> 统一响应:
    """上传 CSV/XLSX 并批量导入流程参数。"""
    try:
        if not flow_id.strip():
            return 失败("导入流程参数失败: flow_id 不能为空")

        文件名 = (file.filename or "").strip()
        if 文件名 and not 文件名.lower().endswith((".csv", ".xlsx")):
            return 失败("导入流程参数失败: 仅支持 .csv 或 .xlsx 文件")

        文件内容 = await file.read()
        结果 = await 流程参数服务实例.批量导入(
            文件内容,
            flow_id.strip(),
            file_name=文件名,
        )
        return 成功(data=结果, message="导入完成")
    except Exception as e:
        return 失败(f"导入流程参数失败: {str(e)}")


@路由.delete("/batch-clear", summary="按条件清空流程参数")
async def 清空流程参数(
    shop_id: Optional[str] = Query(None, description="店铺ID"),
    flow_id: Optional[str] = Query(None, description="流程ID"),
    status: Optional[str] = Query(None, description="状态"),
    batch_id: Optional[str] = Query(None, description="批次ID"),
) -> 统一响应:
    """按条件清空流程参数记录。"""
    try:
        删除数量 = await 流程参数服务实例.按条件清空(
            shop_id=shop_id,
            flow_id=flow_id,
            status=status,
            batch_id=batch_id,
        )
        return 成功(data={"deleted_count": 删除数量}, message="清空成功")
    except Exception as e:
        return 失败(f"清空流程参数失败: {str(e)}")


@路由.get("/{record_id}", summary="获取流程参数详情")
async def 获取流程参数详情(record_id: int) -> 统一响应:
    """获取单条流程参数记录。"""
    try:
        记录 = await 流程参数服务实例.根据ID获取(record_id)
        if not 记录:
            return 失败("流程参数不存在")
        return 成功(data=记录)
    except Exception as e:
        return 失败(f"获取流程参数详情失败: {str(e)}")


@路由.put("/{record_id}", summary="更新流程参数")
async def 更新流程参数(record_id: int, 请求: 流程参数更新请求) -> 统一响应:
    """更新单条流程参数记录。"""
    try:
        记录 = await 流程参数服务实例.更新(
            record_id,
            请求.model_dump(exclude_none=True),
        )
        if not 记录:
            return 失败("流程参数不存在")
        return 成功(data=记录, message="更新成功")
    except Exception as e:
        return 失败(f"更新流程参数失败: {str(e)}")


@路由.delete("/{record_id}", summary="删除流程参数")
async def 删除流程参数(record_id: int) -> 统一响应:
    """删除单条流程参数记录。"""
    try:
        成功标志 = await 流程参数服务实例.删除(record_id)
        if not 成功标志:
            return 失败("流程参数不存在")
        return 成功(message="删除成功")
    except Exception as e:
        return 失败(f"删除流程参数失败: {str(e)}")


@路由.post("/batch-reset", summary="按条件批量重置流程参数")
async def 批量重置流程参数(请求: 流程参数批量操作请求) -> 统一响应:
    """按筛选条件批量重置流程参数。"""
    try:
        更新数量 = await 流程参数服务实例.批量重置(
            shop_id=请求.shop_id,
            flow_id=请求.flow_id,
            status=请求.status,
            batch_id=请求.batch_id,
        )
        return 成功(data={"updated_count": 更新数量}, message="批量重置成功")
    except Exception as e:
        return 失败(f"批量重置流程参数失败: {str(e)}")


@路由.post("/batch-enable", summary="按条件批量启用流程参数")
async def 批量启用流程参数(请求: 流程参数批量操作请求) -> 统一响应:
    """按筛选条件批量启用流程参数。"""
    try:
        更新数量 = await 流程参数服务实例.批量启用(
            shop_id=请求.shop_id,
            flow_id=请求.flow_id,
            status=请求.status,
            batch_id=请求.batch_id,
        )
        return 成功(data={"updated_count": 更新数量}, message="批量启用成功")
    except Exception as e:
        return 失败(f"批量启用流程参数失败: {str(e)}")


@路由.post("/batch-disable", summary="按条件批量禁用流程参数")
async def 批量禁用流程参数(请求: 流程参数批量操作请求) -> 统一响应:
    """按筛选条件批量禁用流程参数。"""
    try:
        更新数量 = await 流程参数服务实例.批量禁用(
            shop_id=请求.shop_id,
            flow_id=请求.flow_id,
            status=请求.status,
            batch_id=请求.batch_id,
        )
        return 成功(data={"updated_count": 更新数量}, message="批量禁用成功")
    except Exception as e:
        return 失败(f"批量禁用流程参数失败: {str(e)}")
