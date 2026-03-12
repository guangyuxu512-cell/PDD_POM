"""
任务参数接口模块

提供 task_params 的分页查询、CRUD、CSV 导入与条件清空接口。
"""
from typing import Optional

from fastapi import APIRouter, File, Form, Query, UploadFile

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
    任务参数批量操作请求,
    任务参数创建请求,
    任务参数更新请求,
)
from backend.services.任务参数服务 import 任务参数服务实例


路由 = APIRouter(prefix="/api/task-params", tags=["任务参数"])


@路由.get("", include_in_schema=False)
@路由.get("/", summary="分页查询任务参数")
async def 获取任务参数列表(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    shop_id: Optional[str] = Query(None, description="店铺ID"),
    task_name: Optional[str] = Query(None, description="任务名称"),
    status: Optional[str] = Query(None, description="状态"),
    batch_id: Optional[str] = Query(None, description="批次ID"),
    updated_from: Optional[str] = Query(None, description="更新时间开始日期"),
    updated_to: Optional[str] = Query(None, description="更新时间结束日期"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
) -> 统一响应:
    """分页查询任务参数。"""
    try:
        数据 = await 任务参数服务实例.分页查询(
            page=page,
            page_size=page_size,
            shop_id=shop_id,
            task_name=task_name,
            status=status,
            batch_id=batch_id,
            updated_from=updated_from,
            updated_to=updated_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return 成功(data=数据)
    except Exception as e:
        return 失败(f"获取任务参数列表失败: {str(e)}")


@路由.get("/batch-options", summary="获取批次筛选选项")
async def 获取批次筛选选项(
    shop_id: Optional[str] = Query(None, description="店铺ID"),
    task_name: Optional[str] = Query(None, description="任务名称"),
    status: Optional[str] = Query(None, description="状态"),
) -> 统一响应:
    """返回批次下拉所需的聚合选项。"""
    try:
        数据 = await 任务参数服务实例.获取批次选项(
            shop_id=shop_id,
            task_name=task_name,
            status=status,
        )
        return 成功(data=数据)
    except Exception as e:
        return 失败(f"获取批次筛选选项失败: {str(e)}")


@路由.post("", include_in_schema=False)
@路由.post("/", summary="创建任务参数")
async def 创建任务参数(请求: 任务参数创建请求) -> 统一响应:
    """创建单条任务参数记录。"""
    try:
        记录 = await 任务参数服务实例.创建(请求.model_dump())
        return 成功(data=记录, message="创建成功")
    except Exception as e:
        return 失败(f"创建任务参数失败: {str(e)}")


@路由.delete("/clear", summary="按条件清空任务参数")
async def 清空任务参数(
    shop_id: Optional[str] = Query(None, description="店铺ID"),
    task_name: Optional[str] = Query(None, description="任务名称"),
    status: Optional[str] = Query(None, description="状态"),
    batch_id: Optional[str] = Query(None, description="批次ID"),
) -> 统一响应:
    """按条件清空任务参数记录。"""
    try:
        删除数量 = await 任务参数服务实例.按条件清空(
            shop_id=shop_id,
            task_name=task_name,
            status=status,
            batch_id=batch_id,
        )
        return 成功(data={"deleted_count": 删除数量}, message="清空成功")
    except Exception as e:
        return 失败(f"清空任务参数失败: {str(e)}")


@路由.post("/import-csv", summary="导入任务参数 CSV")
async def 导入任务参数CSV(
    file: UploadFile = File(..., description="CSV 文件"),
    task_name: str = Form(..., description="任务名称"),
) -> 统一响应:
    """上传 CSV 或 XLSX 并批量导入任务参数。"""
    try:
        if not task_name.strip():
            return 失败("导入任务参数失败: task_name 不能为空")
        文件名 = (file.filename or "").strip()
        if 文件名 and not 文件名.lower().endswith((".csv", ".xlsx")):
            return 失败("导入任务参数失败: 仅支持 .csv 或 .xlsx 文件")
        文件内容 = await file.read()
        结果 = await 任务参数服务实例.批量导入(
            文件内容,
            task_name.strip(),
            file_name=文件名,
        )
        return 成功(data=结果, message="导入完成")
    except Exception as e:
        return 失败(f"导入任务参数失败: {str(e)}")


@路由.put("/batch-reset", summary="按条件批量重置任务参数")
async def 批量重置任务参数(请求: 任务参数批量操作请求) -> 统一响应:
    """按筛选条件批量重置为 pending。"""
    try:
        更新数量 = await 任务参数服务实例.批量重置(
            shop_id=请求.shop_id,
            task_name=请求.task_name,
            status=请求.status,
            batch_id=请求.batch_id,
        )
        return 成功(data={"updated_count": 更新数量}, message="批量重置成功")
    except Exception as e:
        return 失败(f"批量重置任务参数失败: {str(e)}")


@路由.put("/batch-enable", summary="按条件批量启用任务参数")
async def 批量启用任务参数(请求: 任务参数批量操作请求) -> 统一响应:
    """按筛选条件批量启用任务参数。"""
    try:
        更新数量 = await 任务参数服务实例.批量启用(
            shop_id=请求.shop_id,
            task_name=请求.task_name,
            status=请求.status,
            batch_id=请求.batch_id,
        )
        return 成功(data={"updated_count": 更新数量}, message="批量启用成功")
    except Exception as e:
        return 失败(f"批量启用任务参数失败: {str(e)}")


@路由.put("/batch-disable", summary="按条件批量禁用任务参数")
async def 批量禁用任务参数(请求: 任务参数批量操作请求) -> 统一响应:
    """按筛选条件批量禁用任务参数。"""
    try:
        更新数量 = await 任务参数服务实例.批量禁用(
            shop_id=请求.shop_id,
            task_name=请求.task_name,
            status=请求.status,
            batch_id=请求.batch_id,
        )
        return 成功(data={"updated_count": 更新数量}, message="批量禁用成功")
    except Exception as e:
        return 失败(f"批量禁用任务参数失败: {str(e)}")


@路由.put("/{record_id}/enable", summary="启用单条任务参数")
async def 启用任务参数(record_id: int) -> 统一响应:
    """启用单条任务参数记录。"""
    try:
        记录 = await 任务参数服务实例.启用(record_id)
        if not 记录:
            return 失败("任务参数不存在")
        return 成功(data=记录, message="启用成功")
    except Exception as e:
        return 失败(f"启用任务参数失败: {str(e)}")


@路由.put("/{record_id}/disable", summary="禁用单条任务参数")
async def 禁用任务参数(record_id: int) -> 统一响应:
    """禁用单条任务参数记录。"""
    try:
        记录 = await 任务参数服务实例.禁用(record_id)
        if not 记录:
            return 失败("任务参数不存在")
        return 成功(data=记录, message="禁用成功")
    except Exception as e:
        return 失败(f"禁用任务参数失败: {str(e)}")


@路由.put("/{record_id}/reset", summary="重置单条任务参数")
async def 重置任务参数(record_id: int) -> 统一响应:
    """重置单条任务参数记录。"""
    try:
        记录 = await 任务参数服务实例.重置(record_id)
        if not 记录:
            return 失败("任务参数不存在")
        return 成功(data=记录, message="重置成功")
    except Exception as e:
        return 失败(f"重置任务参数失败: {str(e)}")


@路由.put("/{record_id}", summary="更新任务参数")
async def 更新任务参数(record_id: int, 请求: 任务参数更新请求) -> 统一响应:
    """更新单条任务参数记录。"""
    try:
        记录 = await 任务参数服务实例.更新(
            record_id,
            请求.model_dump(exclude_none=True),
        )
        if not 记录:
            return 失败("任务参数不存在")
        return 成功(data=记录, message="更新成功")
    except Exception as e:
        return 失败(f"更新任务参数失败: {str(e)}")


@路由.delete("/{record_id}", summary="删除任务参数")
async def 删除任务参数(record_id: int) -> 统一响应:
    """删除单条任务参数记录。"""
    try:
        成功标志 = await 任务参数服务实例.删除(record_id)
        if not 成功标志:
            return 失败("任务参数不存在")
        return 成功(message="删除成功")
    except Exception as e:
        return 失败(f"删除任务参数失败: {str(e)}")
