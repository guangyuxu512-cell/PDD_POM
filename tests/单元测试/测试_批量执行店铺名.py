"""
批量执行店铺名显示回归测试
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services import 执行服务 as 执行服务模块
from backend.services.任务服务 import 任务服务实例
from tasks.执行任务 import 执行任务 as 执行任务对象


执行任务函数 = 执行任务对象.run.__func__
仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_批次创建店铺名:
    """验证批次快照与 Celery 参数中的店铺名。"""

    @pytest.mark.asyncio
    async def test_创建批次_写入真实店铺名并传给子任务(self):
        服务 = 执行服务模块.执行服务()
        已写入批次 = {}
        投递调用列表 = []
        步骤列表 = [
            {"task": "登录", "on_fail": "continue"},
            {"task": "采集商品", "on_fail": "abort"},
        ]
        店铺映射 = {
            "shop-1": {"id": "shop-1", "name": "MyCookLab"},
            "shop-2": {"id": "shop-2", "name": "Huanyu"},
        }

        async def 假写入批次状态(批次数据):
            已写入批次.clear()
            已写入批次.update(批次数据)
            return 批次数据

        async def 假投递单步任务(**kwargs):
            投递调用列表.append(kwargs)
            记录标识 = kwargs.get("flow_param_ids") or [kwargs.get("flow_param_id")]
            task_id = f"{kwargs['shop_id']}-{'-'.join(str(标识) for 标识 in 记录标识)}"
            kwargs["批次数据"]["shops"][kwargs["shop_id"]]["task_ids"].append(task_id)
            kwargs["批次数据"]["task_ids"].append(task_id)
            return {
                "task_id": task_id,
                "signature": SimpleNamespace(apply_async=lambda: None),
                "batch": kwargs["批次数据"],
            }

        with patch.object(执行服务模块.配置实例, "AGENT_MACHINE_ID", "machine-1"), \
                patch("backend.services.执行服务.初始化任务注册表"), \
                patch("backend.services.执行服务.获取任务类", side_effect=lambda 名称: object()), \
                patch(
                    "backend.services.执行服务.店铺服务实例.根据ID获取",
                    new=AsyncMock(side_effect=lambda 店铺ID: 店铺映射[店铺ID]),
                ), \
                patch(
                    "backend.services.执行服务.流程服务实例.根据ID获取",
                    new=AsyncMock(return_value={"id": "flow-1", "steps": 步骤列表}),
                ), \
                patch(
                    "backend.services.执行服务.流程参数服务实例.获取待执行列表",
                    new=AsyncMock(side_effect=[
                        [{"id": 301}],
                        [{"id": 302}],
                    ]),
                ), \
                patch("backend.services.执行服务.流程参数服务实例.更新", new=AsyncMock()), \
                patch.object(服务, "_写入运行实例快照", new=AsyncMock()), \
                patch.object(服务, "投递单步任务", new=AsyncMock(side_effect=假投递单步任务)), \
                patch.object(服务, "_写入批次状态", new=AsyncMock(side_effect=假写入批次状态)):
            结果 = await 服务.创建批次(
                flow_id="flow-1",
                task_name=None,
                shop_ids=["shop-1", "shop-2"],
                concurrency=2,
            )

        assert 结果["status"] == "running"
        assert 已写入批次["shops"]["shop-1"]["shop_name"] == "MyCookLab"
        assert 已写入批次["shops"]["shop-2"]["shop_name"] == "Huanyu"
        assert 投递调用列表[0]["shop_name"] == "MyCookLab"
        assert 投递调用列表[1]["shop_name"] == "Huanyu"
        assert 投递调用列表[0]["flow_param_id"] == 301
        assert 投递调用列表[1]["flow_param_id"] == 302
        assert 投递调用列表[0]["flow_mode"] is True
        assert 投递调用列表[1]["flow_mode"] is True

    @pytest.mark.asyncio
    async def test_创建批次_店铺缺少名称时回退店铺ID(self):
        服务 = 执行服务模块.执行服务()
        已写入批次 = {}
        投递调用列表 = []

        async def 假写入批次状态(批次数据):
            已写入批次.clear()
            已写入批次.update(批次数据)
            return 批次数据

        async def 假投递单步任务(**kwargs):
            投递调用列表.append(kwargs)
            kwargs["批次数据"]["shops"][kwargs["shop_id"]]["task_ids"].append("task-1")
            kwargs["批次数据"]["task_ids"].append("task-1")
            return {
                "task_id": "task-1",
                "signature": SimpleNamespace(apply_async=lambda: None),
                "batch": kwargs["批次数据"],
            }

        with patch.object(执行服务模块.配置实例, "AGENT_MACHINE_ID", "machine-1"), \
                patch("backend.services.执行服务.初始化任务注册表"), \
                patch("backend.services.执行服务.获取任务类", side_effect=lambda 名称: object()), \
                patch(
                    "backend.services.执行服务.店铺服务实例.根据ID获取",
                    new=AsyncMock(return_value={"id": "shop-1", "name": ""}),
                ), \
                patch.object(服务, "_写入运行实例快照", new=AsyncMock()), \
                patch.object(服务, "投递单步任务", new=AsyncMock(side_effect=假投递单步任务)), \
                patch.object(服务, "_写入批次状态", new=AsyncMock(side_effect=假写入批次状态)):
            await 服务.创建批次(
                flow_id=None,
                task_name="登录",
                shop_ids=["shop-1"],
                concurrency=1,
            )

        assert 已写入批次["shops"]["shop-1"]["shop_name"] == "shop-1"
        assert 投递调用列表[0]["shop_name"] == "shop-1"


class 测试_Worker店铺名日志:
    """验证 Worker 层日志与返回值使用展示名。"""

    def test_执行任务_日志和返回优先使用_shop_name(self):
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-1", retries=0),
            retry=MagicMock(),
        )
        响应数据 = {
            "code": 0,
            "data": {
                "task_id": "task-log-1",
                "status": "completed",
                "result": "成功",
            },
        }
        客户端 = MagicMock()
        客户端.post.return_value.json.return_value = 响应数据
        客户端.post.return_value.raise_for_status.return_value = None
        客户端上下文 = MagicMock()
        客户端上下文.__enter__.return_value = 客户端
        客户端上下文.__exit__.return_value = False

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
                patch("tasks.执行任务.同步更新批次店铺状态"), \
                patch("builtins.print") as 模拟打印:
            结果 = 执行任务函数(
                假任务对象,
                batch_id="batch-1",
                shop_id="shop-1",
                shop_name="MyCookLab",
                task_name="登录",
                on_fail="abort",
                step_index=1,
                total_steps=2,
            )

        assert 结果["shop_name"] == "MyCookLab"
        assert 客户端.post.call_args.kwargs["json"]["params"]["shop_name"] == "MyCookLab"
        assert any("shop_name=MyCookLab" in str(调用) for 调用 in 模拟打印.call_args_list)

    def test_执行任务_shop_name缺失时回退shop_id(self):
        假任务对象 = SimpleNamespace(
            request=SimpleNamespace(id="celery-1", retries=0),
            retry=MagicMock(),
        )
        响应数据 = {
            "code": 0,
            "data": {
                "task_id": "task-log-2",
                "status": "failed",
                "error": "boom",
            },
        }
        客户端 = MagicMock()
        客户端.post.return_value.json.return_value = 响应数据
        客户端.post.return_value.raise_for_status.return_value = None
        客户端上下文 = MagicMock()
        客户端上下文.__enter__.return_value = 客户端
        客户端上下文.__exit__.return_value = False

        with patch("tasks.执行任务.初始化Worker环境"), \
                patch("tasks.执行任务.获取任务类"), \
                patch("tasks.执行任务.httpx.Client", return_value=客户端上下文), \
                patch("tasks.执行任务.同步更新批次店铺状态"), \
                patch("builtins.print") as 模拟打印:
            结果 = 执行任务函数(
                假任务对象,
                batch_id="batch-1",
                shop_id="shop-1",
                shop_name=None,
                task_name="登录",
                on_fail="continue",
                step_index=1,
                total_steps=1,
            )

        assert "shop_name" not in 结果
        assert any("shop_name=shop-1" in str(调用) for 调用 in 模拟打印.call_args_list)


class 测试_任务服务店铺名日志:
    """验证任务服务日志优先输出店铺展示名。"""

    @pytest.mark.asyncio
    async def test_统一执行任务_开始日志优先使用_shop_name(self):
        with patch("backend.services.任务服务.任务服务实例.更新任务状态", new=AsyncMock()), \
                patch("backend.services.店铺服务.店铺服务实例.更新", new=AsyncMock()), \
                patch(
                    "backend.services.浏览器服务.确保已初始化",
                    new=AsyncMock(side_effect=asyncio.TimeoutError()),
                ), \
                patch("backend.services.浏览器服务.管理器实例", None), \
                patch("builtins.print") as 模拟打印:
            结果 = await 任务服务实例.统一执行任务(
                task_id="task-1",
                shop_id="shop-1",
                task_name="登录",
                params={"shop_name": "MyCookLab"},
                来源="batch",
            )

        assert 结果["status"] == "failed"
        assert any(
            "开始执行任务" in str(调用)
            and "shop_name=MyCookLab" in str(调用)
            and "shop_id=shop-1" in str(调用)
            for 调用 in 模拟打印.call_args_list
        )


class 测试_批量执行页店铺名显示:
    """验证前端进度区优先显示快照里的店铺名。"""

    def test_批量执行页_优先显示快照里的店铺名(self):
        类型文件 = 读取文件("frontend/src/api/types.ts")
        页面文件 = 读取文件("frontend/src/views/BatchExecute.vue")

        assert "shop_name?: string | null" in 类型文件
        assert "function getBatchShopName(shop: BatchShopState)" in 页面文件
        assert "shop.shop_name || getShopName(shop.shop_id)" in 页面文件
        assert 页面文件.count("getBatchShopName(shop)") == 3
