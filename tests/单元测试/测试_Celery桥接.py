"""
Celery 桥接相关回归测试
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from tasks import celery应用 as celery应用模块
from tasks.桥接任务 import 桥接执行任务, _运行异步任务


def 清理Worker状态():
    """清理测试过程中创建的 Worker 全局状态"""
    celery应用模块.关闭Worker环境()


class 测试_Celery桥接:
    """测试 Worker 初始化与桥接执行链路"""

    def teardown_method(self):
        清理Worker状态()

    def test_初始化Worker环境_创建复用事件循环并设置回调(self):
        """Worker 初始化时创建复用事件循环并完成回调配置"""
        celery应用模块.Worker环境已初始化 = False
        celery应用模块.Worker事件循环 = None

        with patch("tasks.任务注册表.初始化任务注册表") as 模拟初始化任务注册表, \
                patch("browser.任务回调.设置回调地址") as 模拟设置回调地址, \
                patch("tasks.celery应用.注册Worker机器") as 模拟注册Worker机器, \
                patch.object(celery应用模块.配置实例, "AGENT_CALLBACK_URL", "http://agent/callback"):
            celery应用模块.初始化Worker环境()
            事件循环 = celery应用模块.获取Worker事件循环()

        assert 事件循环 is celery应用模块.Worker事件循环
        assert not 事件循环.is_closed()
        模拟初始化任务注册表.assert_called_once()
        模拟设置回调地址.assert_called_once_with("http://agent/callback")
        模拟注册Worker机器.assert_called_once()
        assert celery应用模块.Worker环境已初始化 is True

    def test_初始化Worker环境_向Agent注册机器(self):
        """Worker 初始化时按 Agent 约定发送机器注册。"""
        celery应用模块.Worker环境已初始化 = False
        celery应用模块.Worker事件循环 = None
        模拟响应 = MagicMock()

        with patch("tasks.任务注册表.初始化任务注册表"), \
                patch("browser.任务回调.设置回调地址"), \
                patch.object(celery应用模块.配置实例, "AGENT_CALLBACK_URL", "http://agent/callback"), \
                patch.object(celery应用模块.配置实例, "AGENT_HEARTBEAT_URL", "http://agent-host:8001/api/workers/heartbeat"), \
                patch.object(celery应用模块.配置实例, "AGENT_MACHINE_ID", "office-pc-001"), \
                patch.object(celery应用模块.配置实例, "MACHINE_NAME", "办公电脑A"), \
                patch.object(celery应用模块.配置实例, "X_RPA_KEY", "test-rpa-key"), \
                patch("tasks.celery应用.httpx.Client") as 模拟客户端类:
            模拟客户端 = 模拟客户端类.return_value.__enter__.return_value
            模拟客户端.post.return_value = 模拟响应
            模拟响应.json.return_value = {"code": 0, "msg": "ok", "data": {"ok": True}}
            celery应用模块.初始化Worker环境()

        模拟客户端.post.assert_called_once_with(
            "http://agent-host:8001/api/workers/register",
            json={"machine_id": "office-pc-001", "machine_name": "办公电脑A"},
            headers={"X-RPA-KEY": "test-rpa-key"},
        )
        模拟响应.raise_for_status.assert_called_once()
        assert celery应用模块.Worker环境已初始化 is True

    def test_初始化Worker环境_注册失败时只记录不阻塞启动(self):
        """机器注册失败时应继续完成 Worker 初始化。"""
        celery应用模块.Worker环境已初始化 = False
        celery应用模块.Worker事件循环 = None

        with patch("tasks.任务注册表.初始化任务注册表"), \
                patch("browser.任务回调.设置回调地址"), \
                patch.object(celery应用模块.配置实例, "AGENT_MACHINE_ID", "office-pc-001"), \
                patch.object(celery应用模块.配置实例, "X_RPA_KEY", "test-rpa-key"), \
                patch("tasks.celery应用.httpx.Client") as 模拟客户端类:
            模拟客户端 = 模拟客户端类.return_value.__enter__.return_value
            模拟客户端.post.side_effect = RuntimeError("agent offline")
            celery应用模块.初始化Worker环境()

        assert celery应用模块.Worker环境已初始化 is True

    def test_桥接执行任务_复用Worker事件循环调用统一入口(self):
        """桥接函数复用 Worker 事件循环，不再为每个任务新建循环"""
        假循环 = asyncio.new_event_loop()

        try:
            with patch("tasks.桥接任务.初始化Worker环境") as 模拟初始化Worker环境, \
                    patch("tasks.桥接任务.获取Worker事件循环", return_value=假循环), \
                    patch("tasks.桥接任务.asyncio.get_running_loop", side_effect=RuntimeError), \
                    patch("tasks.桥接任务.asyncio.set_event_loop") as 模拟设置事件循环, \
                    patch("tasks.桥接任务.任务服务实例.统一执行任务", new=AsyncMock(return_value={"status": "completed", "task_id": "task-1"})) as 模拟统一执行任务:
                结果 = 桥接执行任务(
                    shop_id="shop-1",
                    task_name="登录",
                    params={"foo": "bar"},
                    task_id="task-1"
                )

            assert 结果 == {"status": "completed", "task_id": "task-1"}
            模拟初始化Worker环境.assert_called_once()
            模拟设置事件循环.assert_called_once_with(假循环)
            模拟统一执行任务.assert_awaited_once_with(
                task_id="task-1",
                shop_id="shop-1",
                task_name="登录",
                params={"foo": "bar"},
                来源="celery"
            )
        finally:
            假循环.close()

    def test_运行异步任务_获取Worker事件循环失败时回退临时事件循环(self):
        """获取 Worker 事件循环失败时回退到 asyncio.run，避免桥接直接崩溃"""

        async def 假协程():
            return "ok"

        def 假运行(协程对象):
            协程对象.close()
            return "ok"

        with patch("tasks.桥接任务.asyncio.get_running_loop", side_effect=RuntimeError), \
                patch("tasks.桥接任务.获取Worker事件循环", side_effect=RuntimeError("loop failed")), \
                patch("tasks.桥接任务.asyncio.run", side_effect=假运行) as 模拟临时运行:
            结果 = _运行异步任务(假协程())

        assert 结果 == "ok"
        模拟临时运行.assert_called_once()

    def test_Worker信号钩子_初始化异常时只记录不抛出(self):
        """Worker 信号钩子出现异常时不应让调用方崩溃"""
        with patch("tasks.celery应用.初始化Worker环境", side_effect=RuntimeError("init failed")):
            celery应用模块.Worker启动时初始化()

        with patch("tasks.celery应用.关闭Worker环境", side_effect=RuntimeError("shutdown failed")):
            celery应用模块.Worker关闭时清理()
