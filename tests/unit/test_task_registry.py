"""
任务注册表与可用任务接口单元测试
"""
from __future__ import annotations

from copy import deepcopy
import builtins
import sys
from types import ModuleType
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.router import 注册所有路由
from tasks.base_task import 基础任务
from tasks import registry as 注册表模块


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
            任务列表 = 注册表模块.获取所有任务()
            assert len(任务列表) == 1
            assert 任务列表[0]["name"] == "测试任务"
            assert 任务列表[0]["description"] == "用于测试注册表"
            assert 任务列表[0]["category"] == "通用"
            assert 任务列表[0]["tags"] == []
            assert 任务列表[0]["input_schema"] is None
            assert 任务列表[0]["timeout"] == 1800
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
            登录任务 = next((任务 for 任务 in 任务列表 if 任务["name"] == "登录"), None)
            assert 登录任务 is not None
            assert 登录任务["description"] == "打开浏览器并登录店铺后台"
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)

    def test_列出任务模块_frozen模式读取自动生成列表(self, monkeypatch):
        """frozen 模式应优先读取 tasks._frozen_modules 中的 MODULES。"""
        模拟模块 = ModuleType("tasks._frozen_modules")
        模拟模块.MODULES = ["foo_task", "bar_task"]

        monkeypatch.setitem(sys.modules, "tasks._frozen_modules", 模拟模块)
        monkeypatch.setattr(sys, "frozen", True, raising=False)

        assert 注册表模块._列出任务模块() == ["foo_task", "bar_task"]

    def test_列出任务模块_frozen模式缺少生成文件时返回空列表(self, monkeypatch):
        """异常路径下，缺少 _frozen_modules.py 应回退为空列表。"""
        真实导入 = builtins.__import__

        def 假导入(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "tasks._frozen_modules":
                raise ImportError("missing")
            return 真实导入(name, globals, locals, fromlist, level)

        monkeypatch.delitem(sys.modules, "tasks._frozen_modules", raising=False)
        monkeypatch.setattr(sys, "frozen", True, raising=False)

        with patch("builtins.__import__", side_effect=假导入), \
                patch.object(注册表模块.logger, "warning") as 模拟告警:
            assert 注册表模块._列出任务模块() == []

        模拟告警.assert_called_once()


class 测试_可用任务接口:
    """测试可用任务接口。"""

    def test_获取可用任务列表接口_返回注册表结果(self):
        """GET /api/tasks/available 应返回已注册任务列表。"""
        app = FastAPI()
        注册所有路由(app)

        with patch(
            "backend.api.available_tasks.获取所有任务",
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
