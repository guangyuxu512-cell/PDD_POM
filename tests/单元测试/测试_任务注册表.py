"""
任务注册表与可用任务接口单元测试
"""
from __future__ import annotations

from copy import deepcopy
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.路由注册 import 注册所有路由
from tasks.基础任务 import 基础任务
from tasks import 注册表 as 注册表模块


class 测试_基础任务:
    """测试基础任务的安全执行包装。"""

    @pytest.mark.asyncio
    async def test_安全执行_成功(self):
        """执行成功时应返回 success 和 result。"""

        class 成功任务(基础任务):
            async def 执行(self, 页面, 店铺配置) -> str:
                return "执行完成"

        结果 = await 成功任务().安全执行(None, {})

        assert 结果 == {
            "status": "success",
            "result": "执行完成",
        }

    @pytest.mark.asyncio
    async def test_安全执行_失败(self):
        """执行异常时应返回 failed 和错误信息。"""

        class 失败任务(基础任务):
            async def 执行(self, 页面, 店铺配置) -> str:
                raise RuntimeError("执行失败")

        结果 = await 失败任务().安全执行(None, {})

        assert 结果 == {
            "status": "failed",
            "error": "执行失败",
        }


class 测试_任务注册表:
    """测试任务注册与查询能力。"""

    def test_register_task_注册并返回任务信息(self):
        """装饰器应写入名称、描述和任务类。"""
        原注册表 = deepcopy(注册表模块.任务注册表)
        注册表模块.清空任务注册表()

        try:
            @注册表模块.register_task("测试任务", "用于测试注册表")
            class 测试任务(基础任务):
                async def 执行(self, 页面, 店铺配置) -> str:
                    return "ok"

            assert 注册表模块.获取任务类("测试任务") is 测试任务
            assert 注册表模块.获取所有任务() == [
                {
                    "name": "测试任务",
                    "description": "用于测试注册表",
                }
            ]
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)

    def test_获取任务类_未注册时报错(self):
        """未注册任务应抛出 KeyError。"""
        with pytest.raises(KeyError, match="任务未注册"):
            注册表模块.获取任务类("不存在的任务")

    def test_初始化任务注册表_自动导入任务模块(self):
        """初始化时应自动发现并注册现有任务文件。"""
        原注册表 = deepcopy(注册表模块.任务注册表)
        注册表模块.清空任务注册表()

        try:
            注册表模块.初始化任务注册表()
            任务列表 = 注册表模块.获取所有任务()
            assert {
                "name": "登录",
                "description": "打开浏览器并登录店铺后台",
            } in 任务列表
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)


class 测试_可用任务接口:
    """测试可用任务接口。"""

    def test_获取可用任务列表接口_返回注册表结果(self):
        """GET /api/tasks/available 应返回已注册任务列表。"""
        app = FastAPI()
        注册所有路由(app)

        with patch(
            "backend.api.可用任务.获取所有任务",
            return_value=[{"name": "登录", "description": "打开浏览器并登录店铺后台"}],
        ):
            响应 = TestClient(app).get("/api/tasks/available")

        assert 响应.status_code == 200
        assert 响应.json() == {
            "code": 0,
            "msg": "ok",
            "data": {
                "tasks": [
                    {
                        "name": "登录",
                        "description": "打开浏览器并登录店铺后台",
                    }
                ]
            },
        }
