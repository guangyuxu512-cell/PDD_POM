"""
Models 模块

按需导出常用模型与工具，避免初始化阶段产生循环导入。
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


_导出映射 = {
    "初始化数据库": ("backend.models.database", "初始化数据库"),
    "获取连接": ("backend.models.database", "获取连接"),
    "店铺模型": ("backend.models.shop_model", "店铺模型"),
    "店铺表定义": ("backend.models.shop_model", "店铺表定义"),
    "流程步骤": ("backend.models.flow_model", "流程步骤"),
    "流程模型": ("backend.models.flow_model", "流程模型"),
    "流程表定义": ("backend.models.flow_model", "流程表定义"),
    "定时任务模型": ("backend.models.scheduled_task_model", "定时任务模型"),
    "定时任务表定义": ("backend.models.scheduled_task_model", "定时任务表定义"),
    "设置模型": ("backend.models.settings_model", "设置模型"),
    "设置表定义": ("backend.models.settings_model", "设置表定义"),
    "统一响应": ("backend.models.data_structure", "统一响应"),
    "成功": ("backend.models.data_structure", "成功"),
    "失败": ("backend.models.data_structure", "失败"),
    "分页响应": ("backend.models.data_structure", "分页响应"),
    "店铺创建请求": ("backend.models.data_structure", "店铺创建请求"),
    "店铺更新请求": ("backend.models.data_structure", "店铺更新请求"),
    "店铺响应": ("backend.models.data_structure", "店铺响应"),
    "任务执行请求": ("backend.models.data_structure", "任务执行请求"),
    "任务日志响应": ("backend.models.data_structure", "任务日志响应"),
    "定时任务创建请求": ("backend.models.data_structure", "定时任务创建请求"),
    "定时任务更新请求": ("backend.models.data_structure", "定时任务更新请求"),
    "定时任务响应": ("backend.models.data_structure", "定时任务响应"),
    "Cookie导入请求": ("backend.models.data_structure", "Cookie导入请求"),
    "浏览器初始化配置": ("backend.models.data_structure", "浏览器初始化配置"),
    "浏览器实例响应": ("backend.models.data_structure", "浏览器实例响应"),
    "操作日志响应": ("backend.models.data_structure", "操作日志响应"),
    "系统配置请求": ("backend.models.data_structure", "系统配置请求"),
    "系统配置响应": ("backend.models.data_structure", "系统配置响应"),
    "健康检查响应": ("backend.models.data_structure", "健康检查响应"),
}


def __getattr__(名称: str) -> Any:
    if 名称 not in _导出映射:
        raise AttributeError(名称)

    模块路径, 属性名 = _导出映射[名称]
    模块 = import_module(模块路径)
    值 = getattr(模块, 属性名)
    globals()[名称] = 值
    return 值


__all__ = list(_导出映射)
