"""
任务注册表扩展能力单元测试
"""
from __future__ import annotations

from copy import deepcopy

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from backend.api.router import 注册所有路由
from tasks import registry as 注册表模块
from tasks.base_task import 基础任务


class 测试_任务注册表扩展:
    """验证任务注册表的扩展元数据能力。"""

    def test_register_task_支持扩展元数据并自动推导必填字段(self):
        """input_schema 应自动推导 required_fields，并写入扩展元数据。"""
        原注册表 = deepcopy(注册表模块.任务注册表)
        注册表模块.清空任务注册表()

        class 测试输入(BaseModel):
            shop_id: str = Field(..., description="店铺 ID")
            shop_name: str = Field(default="", description="店铺名称")

        class 测试输出(BaseModel):
            success: bool = Field(..., description="是否成功")

        try:
            @注册表模块.register_task(
                "扩展任务",
                "用于测试扩展元数据",
                input_schema=测试输入,
                output_schema=测试输出,
                category="测试分类",
                tags=["测试", "注册表"],
                timeout=600,
                retry_policy={"max_retries": 2, "countdown": 30},
            )
            class 扩展任务(基础任务):
                async def 执行(self, 页面, 店铺配置) -> str:
                    return "ok"

            任务列表 = 注册表模块.获取所有任务()
            assert len(任务列表) == 1
            assert 任务列表[0]["name"] == "扩展任务"
            assert 任务列表[0]["category"] == "测试分类"
            assert 任务列表[0]["tags"] == ["测试", "注册表"]
            assert 任务列表[0]["required_fields"] == ["shop_id"]
            assert 任务列表[0]["timeout"] == 600
            assert 任务列表[0]["retry_policy"] == {"max_retries": 2, "countdown": 30}
            assert "shop_id" in 任务列表[0]["input_schema"]["properties"]
            assert "success" in 任务列表[0]["output_schema"]["properties"]

            元数据 = 注册表模块.获取任务元数据("扩展任务")
            assert 元数据["input_schema"] is 测试输入
            assert 元数据["output_schema"] is 测试输出
            assert 元数据["required_fields"] == ["shop_id"]
            assert 元数据["category"] == "测试分类"
            assert 元数据["tags"] == ["测试", "注册表"]
            assert 元数据["timeout"] == 600
            assert 元数据["retry_policy"] == {"max_retries": 2, "countdown": 30}
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)

    def test_register_task_旧式调用仍保持兼容(self):
        """仅传名称和描述时，应保留默认元数据。"""
        原注册表 = deepcopy(注册表模块.任务注册表)
        注册表模块.清空任务注册表()

        try:
            @注册表模块.register_task("兼容任务", "兼容旧式调用")
            class 兼容任务(基础任务):
                async def 执行(self, 页面, 店铺配置) -> str:
                    return "ok"

            元数据 = 注册表模块.获取任务元数据("兼容任务")
            assert 元数据["required_fields"] == []
            assert 元数据["input_schema"] is None
            assert 元数据["output_schema"] is None
            assert 元数据["category"] == "通用"
            assert 元数据["tags"] == []
            assert 元数据["timeout"] == 1800
            assert 元数据["retry_policy"] is None
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)


class 测试_通用任务接口:
    """验证任务注册表 API。"""

    def test_任务注册表接口_返回列表_schema与校验结果(self):
        """任务注册表接口应暴露 Schema，并支持参数校验。"""
        原注册表 = deepcopy(注册表模块.任务注册表)
        注册表模块.清空任务注册表()

        class 接口输入(BaseModel):
            shop_id: str = Field(..., description="店铺 ID")
            retry_count: int = Field(default=0, description="重试次数")

        try:
            @注册表模块.register_task(
                "接口任务",
                "用于测试接口",
                input_schema=接口输入,
                category="接口分类",
                tags=["接口"],
            )
            class 接口任务(基础任务):
                async def 执行(self, 页面, 店铺配置) -> str:
                    return "ok"

            app = FastAPI()
            注册所有路由(app)
            客户端 = TestClient(app)

            列表响应 = 客户端.get("/api/task-registry/")
            assert 列表响应.status_code == 200
            assert 列表响应.json()["code"] == 0
            assert 列表响应.json()["data"][0]["name"] == "接口任务"
            assert 列表响应.json()["data"][0]["category"] == "接口分类"
            assert "shop_id" in 列表响应.json()["data"][0]["input_schema"]["properties"]

            Schema响应 = 客户端.get("/api/task-registry/接口任务/schema")
            assert Schema响应.status_code == 200
            assert Schema响应.json() == {
                "code": 0,
                "msg": "ok",
                "data": {
                    "name": "接口任务",
                    "input_schema": 接口输入.model_json_schema(),
                    "required_fields": ["shop_id"],
                    "requires_input": False,
                },
            }

            校验通过响应 = 客户端.post(
                "/api/task-registry/接口任务/validate",
                json={"shop_id": "shop-1", "retry_count": 2},
            )
            assert 校验通过响应.status_code == 200
            assert 校验通过响应.json() == {
                "code": 0,
                "msg": "ok",
                "data": {"valid": True},
            }

            校验失败响应 = 客户端.post(
                "/api/task-registry/接口任务/validate",
                json={"shop_id": "shop-1", "retry_count": "bad"},
            )
            assert 校验失败响应.status_code == 200
            assert 校验失败响应.json()["code"] == 1
            assert "参数校验失败" in 校验失败响应.json()["msg"]
        finally:
            注册表模块.清空任务注册表()
            注册表模块.任务注册表.update(原注册表)
