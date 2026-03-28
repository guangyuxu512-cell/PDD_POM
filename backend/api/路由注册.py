"""
路由注册模块

汇总所有 API 路由。
"""
from fastapi import FastAPI

from backend.api.店铺接口 import 路由 as 店铺路由
from backend.api.流程接口 import 路由 as 流程路由
from backend.api.流程输入接口 import 路由 as 流程输入路由
from backend.api.浏览器接口 import 路由 as 浏览器路由
from backend.api.可用任务 import 路由 as 可用任务路由
from backend.api.执行接口 import 路由 as 执行路由
from backend.api.运行接口 import 路由 as 运行路由
from backend.api.定时执行接口 import 路由 as 定时执行路由
from backend.api.任务接口 import 路由 as 任务路由
from backend.api.任务参数接口 import 路由 as 任务参数路由
from backend.api.流程参数接口 import 路由 as 流程参数路由
from backend.api.日志接口 import 路由 as 日志路由
from backend.api.系统接口 import 路由 as 系统路由
from backend.api.飞书接口 import 路由 as 飞书路由
from backend.api.规则接口 import 路由 as 规则路由
from backend.api.售后配置接口 import 路由 as 售后配置路由


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
