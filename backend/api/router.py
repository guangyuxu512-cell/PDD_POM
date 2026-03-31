"""
路由注册模块

汇总所有 API 路由。
"""
from fastapi import FastAPI

from backend.api.shop_api import 路由 as 店铺路由
from backend.api.flow_api import 路由 as 流程路由
from backend.api.flow_input_api import 路由 as 流程输入路由
from backend.api.browser_api import 路由 as 浏览器路由
from backend.api.available_tasks import 路由 as 可用任务路由
from backend.api.execute_api import 路由 as 执行路由
from backend.api.run_api import 路由 as 运行路由
from backend.api.scheduled_execute_api import 路由 as 定时执行路由
from backend.api.task_api import 路由 as 任务路由
from backend.api.task_params_api import 路由 as 任务参数路由
from backend.api.generic_task_api import 路由 as 通用任务路由
from backend.api.flow_params_api import 路由 as 流程参数路由
from backend.api.log_api import 路由 as 日志路由
from backend.api.system_api import 路由 as 系统路由
from backend.api.feishu_api import 路由 as 飞书路由
from backend.api.rule_api import 路由 as 规则路由
from backend.api.after_sale_config_api import 路由 as 售后配置路由


# 所有路由列表
所有路由 = [
    店铺路由,
    流程路由,
    流程输入路由,
    浏览器路由,
    可用任务路由,
    执行路由,
    运行路由,
    定时执行路由,
    任务路由,
    任务参数路由,
    通用任务路由,
    流程参数路由,
    日志路由,
    系统路由,
    飞书路由,
    规则路由,
    售后配置路由,
]


def 注册所有路由(app: FastAPI) -> None:
    """
    注册所有 API 路由到 FastAPI 应用实例

    参数:
        app: FastAPI 应用实例
    """
    for 路由 in 所有路由:
        app.include_router(路由)
