"""
任务参数接口模块

提供 task_params 的分页查询、CRUD、CSV 导入与条件清空接口。
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, File, Form, Query, UploadFile

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
    任务参数批量操作请求,
    任务参数创建请求,
    任务参数更新请求,
)
from backend.models.数据库 import 获取连接
from backend.services.流程参数服务 import 流程参数服务实例
from backend.services.流程服务 import 流程服务实例
from backend.services.任务参数服务 import 任务参数服务实例


路由 = APIRouter(prefix="/api/task-params", tags=["任务参数"])
执行结果允许状态集合 = {"success", "failed", "running", "cancelled"}
流程步骤元数据字段 = {
    "status",
    "error",
    "merged_to",
    "merged_by",
    "merged_context",
    "merge_members",
    "result_status",
}


def _解析执行结果状态(状态: Optional[str]) -> list[str]:
    if not 状态:
        return []

    状态列表 = [项.strip() for 项 in str(状态).split(",") if 项.strip()]
    for 当前状态 in 状态列表:
        if 当前状态 not in 执行结果允许状态集合:
            raise ValueError(f"不支持的执行结果状态: {当前状态}")
    return 状态列表


def _提取日期部分(时间文本: Optional[str]) -> str:
    return str(时间文本 or "").strip()[:10]


def _提取流程步骤业务结果(步骤结果: dict[str, Any]) -> dict[str, Any]:
    return {
        键: 值
        for 键, 值 in 步骤结果.items()
        if 键 not in 流程步骤元数据字段
    }


def _解析流程执行任务名(记录: dict[str, Any], 流程: Optional[dict[str, Any]]) -> str:
    步骤列表 = list((流程 or {}).get("steps") or [])
    当前步骤 = int(记录.get("current_step") or 0)
    if 1 <= 当前步骤 <= len(步骤列表):
        任务名 = str(步骤列表[当前步骤 - 1].get("task") or "").strip()
        if 任务名:
            return 任务名

    步骤结果 = 记录.get("step_results") or {}
    for 步骤 in reversed(步骤列表):
        步骤任务名 = str(步骤.get("task") or "").strip()
        if 步骤任务名 and 步骤任务名 in 步骤结果:
            return 步骤任务名

    if isinstance(步骤结果, dict) and 步骤结果:
        return str(list(步骤结果.keys())[-1])

    return str((流程 or {}).get("name") or "流程任务")


async def _查询执行结果列表(
    *,
    page: int,
    page_size: int,
    shop_id: Optional[str],
    task_name: Optional[str],
    status: Optional[str],
    batch_id: Optional[str],
    updated_from: Optional[str],
    updated_to: Optional[str],
) -> dict[str, Any]:
    状态列表 = _解析执行结果状态(status)
    任务参数条件: list[str] = []
    流程参数条件: list[str] = []
    任务参数参数: list[Any] = []
    流程参数参数: list[Any] = []

    if shop_id:
        任务参数条件.append("tp.shop_id = ?")
        流程参数条件.append("fp.shop_id = ?")
        任务参数参数.append(shop_id)
        流程参数参数.append(shop_id)
    if task_name:
        任务参数条件.append("tp.task_name = ?")
        任务参数参数.append(task_name)
    if batch_id:
        任务参数条件.append("tp.batch_id = ?")
        流程参数条件.append("fp.batch_id = ?")
        任务参数参数.append(batch_id)
        流程参数参数.append(batch_id)
    if 状态列表:
        任务参数占位符 = ", ".join("?" for _ in 状态列表)
        流程参数占位符 = ", ".join("?" for _ in 状态列表)
        任务参数条件.append(f"tp.status IN ({任务参数占位符})")
        流程参数条件.append(f"fp.status IN ({流程参数占位符})")
        任务参数参数.extend(状态列表)
        流程参数参数.extend(状态列表)
    if updated_from:
        任务参数条件.append("substr(tp.updated_at, 1, 10) >= ?")
        流程参数条件.append("substr(fp.updated_at, 1, 10) >= ?")
        任务参数参数.append(updated_from)
        流程参数参数.append(updated_from)
    if updated_to:
        任务参数条件.append("substr(tp.updated_at, 1, 10) <= ?")
        流程参数条件.append("substr(fp.updated_at, 1, 10) <= ?")
        任务参数参数.append(updated_to)
        流程参数参数.append(updated_to)

    任务参数条件SQL = f"WHERE {' AND '.join(任务参数条件)}" if 任务参数条件 else ""
    流程参数条件SQL = f"WHERE {' AND '.join(流程参数条件)}" if 流程参数条件 else ""

    async with 获取连接() as 连接:
        async with 连接.execute(
            f"""
            SELECT tp.*, s.name AS shop_name
            FROM task_params tp
            LEFT JOIN shops s ON s.id = tp.shop_id
            {任务参数条件SQL}
            """,
            任务参数参数,
        ) as 游标:
            任务参数行列表 = await 游标.fetchall()

        async with 连接.execute(
            f"""
            SELECT fp.*, s.name AS shop_name
            FROM flow_params fp
            LEFT JOIN shops s ON s.id = fp.shop_id
            {流程参数条件SQL}
            """,
            流程参数参数,
        ) as 游标:
            流程参数行列表 = await 游标.fetchall()

    结果列表: list[dict[str, Any]] = []
    for 行 in 任务参数行列表:
        结果列表.append(任务参数服务实例._转换记录(行))

    流程缓存: dict[str, Optional[dict[str, Any]]] = {}
    for 行 in 流程参数行列表:
        记录 = 流程参数服务实例._转换记录(行)
        flow_id = str(记录["flow_id"])
        if flow_id not in 流程缓存:
            流程缓存[flow_id] = await 流程服务实例.根据ID获取(flow_id)
        流程 = 流程缓存[flow_id]
        当前任务名 = _解析流程执行任务名(记录, 流程)
        if task_name and 当前任务名 != task_name:
            continue

        合并参数 = dict(记录.get("params") or {})
        合并结果: dict[str, Any] = {}
        for 步骤 in list((流程 or {}).get("steps") or []):
            步骤任务名 = str(步骤.get("task") or "").strip()
            步骤结果 = (记录.get("step_results") or {}).get(步骤任务名)
            if not isinstance(步骤结果, dict):
                continue
            业务结果 = _提取流程步骤业务结果(步骤结果)
            if 业务结果:
                合并结果.update(业务结果)
                合并参数.update(业务结果)

        结果列表.append(
            {
                "id": int(记录["id"]),
                "shop_id": str(记录["shop_id"]),
                "shop_name": 记录.get("shop_name"),
                "task_name": 当前任务名,
                "params": 合并参数,
                "result": 合并结果,
                "status": str(记录["status"]),
                "error": 记录.get("error"),
                "batch_id": 记录.get("batch_id"),
                "enabled": bool(记录.get("enabled", True)),
                "run_count": int(记录.get("run_count") or 0),
                "created_at": 记录.get("created_at"),
                "updated_at": 记录.get("updated_at"),
            }
        )

    结果列表.sort(
        key=lambda 记录: (
            str(记录.get("updated_at") or ""),
            str(记录.get("created_at") or ""),
            int(记录.get("id") or 0),
        ),
        reverse=True,
    )
    偏移量 = max(page - 1, 0) * page_size
    分页结果 = 结果列表[偏移量:偏移量 + page_size]

    return {
        "list": 分页结果,
        "total": len(结果列表),
        "page": page,
        "page_size": page_size,
    }


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


@路由.get("/results", summary="分页查询执行结果")
async def 获取执行结果列表(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    shop_id: Optional[str] = Query(None, description="店铺ID"),
    task_name: Optional[str] = Query(None, description="任务名称"),
    status: Optional[str] = Query(None, description="状态"),
    batch_id: Optional[str] = Query(None, description="批次ID"),
    updated_from: Optional[str] = Query(None, description="更新时间开始日期"),
    updated_to: Optional[str] = Query(None, description="更新时间结束日期"),
) -> 统一响应:
    """分页查询执行结果，兼容 task_params 与 flow_params。"""
    try:
        数据 = await _查询执行结果列表(
            page=page,
            page_size=page_size,
            shop_id=shop_id,
            task_name=task_name,
            status=status,
            batch_id=batch_id,
            updated_from=updated_from,
            updated_to=updated_to,
        )
        return 成功(data=数据)
    except Exception as e:
        return 失败(f"获取执行结果失败: {str(e)}")


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
