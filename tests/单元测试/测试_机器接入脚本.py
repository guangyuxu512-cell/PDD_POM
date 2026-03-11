"""
machine_worker 脚本单元测试
"""
import os
from argparse import Namespace
from unittest.mock import patch

from scripts.machine_worker import 外部机器执行器, 构建配置, 解析命令行参数


def 构造参数(**覆盖):
    默认参数 = {
        "server_url": "http://localhost:8001",
        "redis_url": "redis://192.168.0.43:6380/0",
        "machine_id": "test-machine-001",
        "machine_name": "",
        "rpa_key": "test-rpa-key",
        "queue_prefix": "worker",
        "simulate_seconds": 3,
        "heartbeat_interval": 30.0,
        "request_timeout": 10.0,
        "retry_delay": 3.0,
    }
    默认参数.update(覆盖)
    return Namespace(**默认参数)


class 测试_机器接入脚本:
    def test_解析命令行参数_默认读取_X_RPA_KEY(self):
        with patch.dict(os.environ, {"X_RPA_KEY": "env-rpa-key"}, clear=True):
            with patch("sys.argv", ["machine_worker.py"]):
                参数 = 解析命令行参数()

        assert 参数.rpa_key == "env-rpa-key"

    def test_构建配置_默认回退机器名称并使用Agent接口(self):
        配置 = 构建配置(构造参数())

        assert 配置.服务端地址 == "http://localhost:8001"
        assert 配置.机器名称 == "test-machine-001"
        assert 配置.注册地址 == "http://localhost:8001/api/workers/register"
        assert 配置.心跳地址 == "http://localhost:8001/api/workers/heartbeat"
        assert 配置.状态更新地址 == "http://localhost:8001/api/workers/test-machine-001/status"

    def test_注册机器_按Agent约定发送machine_id和machine_name(self):
        配置 = 构建配置(构造参数(machine_name="测试机器A"))
        执行器 = 外部机器执行器(配置)

        with patch.object(执行器, "_发送请求", return_value={"code": 0, "data": {"ok": True}}) as 模拟请求:
            执行器.注册机器()

        模拟请求.assert_called_once_with(
            "POST",
            "http://localhost:8001/api/workers/register",
            json={"machine_id": "test-machine-001", "machine_name": "测试机器A"},
            headers={"X-RPA-KEY": "test-rpa-key"},
        )

    def test_发送心跳_运行中上报shadowbot_running_true(self):
        配置 = 构建配置(构造参数())
        执行器 = 外部机器执行器(配置)
        执行器.设置状态("running", "task-1")

        with patch.object(执行器, "_发送请求", return_value={"code": 0, "data": {"ok": True}}) as 模拟请求:
            执行器._发送心跳()

        模拟请求.assert_called_once_with(
            "POST",
            "http://localhost:8001/api/workers/heartbeat",
            json={"machine_id": "test-machine-001", "shadowbot_running": True},
            headers={"X-RPA-KEY": "test-rpa-key"},
        )

    def test_更新机器状态_使用PUT和X_RPA_KEY(self):
        配置 = 构建配置(构造参数())
        执行器 = 外部机器执行器(配置)

        with patch.object(执行器, "_发送请求", return_value={"code": 0, "data": {"ok": True}}) as 模拟请求:
            执行器._更新机器状态("idle")

        模拟请求.assert_called_once_with(
            "PUT",
            "http://localhost:8001/api/workers/test-machine-001/status",
            json={"status": "idle"},
            headers={"X-RPA-KEY": "test-rpa-key"},
        )

    def test_发送心跳_请求异常时静默忽略(self):
        配置 = 构建配置(构造参数())
        执行器 = 外部机器执行器(配置)

        with patch.object(执行器, "_发送请求", side_effect=RuntimeError("network failed")):
            执行器._发送心跳()

    def test_构建配置_X_RPA_KEY为空时抛异常(self):
        try:
            构建配置(构造参数(rpa_key="  "))
        except ValueError as 异常:
            assert str(异常) == "X_RPA_KEY 不能为空"
        else:
            raise AssertionError("期望抛出 ValueError")
