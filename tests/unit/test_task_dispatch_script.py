"""
dispatch_test 脚本单元测试
"""
import os
from argparse import Namespace
from unittest.mock import MagicMock, patch

from scripts import dispatch_test


def 构造参数(**覆盖):
    默认参数 = {
        "machine_id": "test-machine-001",
        "server_url": "http://localhost:8001",
        "rpa_key": "test-rpa-key",
        "dispatch_path": "/api/task-dispatches/echo-test",
        "status_path_template": "/api/tasks/{task_id}",
        "message": "hello",
        "sleep_seconds": 3,
        "payload_json": "",
        "poll": False,
        "poll_interval": 2.0,
        "poll_timeout": 120.0,
        "request_timeout": 10.0,
    }
    默认参数.update(覆盖)
    return Namespace(**默认参数)


def 构造响应(响应数据):
    响应 = MagicMock()
    响应.json.return_value = 响应数据
    响应.raise_for_status.return_value = None
    return 响应


class 测试_任务派发脚本:
    def test_解析命令行参数_默认读取_X_RPA_KEY(self):
        with patch.dict(os.environ, {"X_RPA_KEY": "env-rpa-key"}, clear=True):
            with patch("sys.argv", ["dispatch_test.py", "--machine-id", "machine-1"]):
                参数 = dispatch_test.解析命令行参数()

        assert 参数.rpa_key == "env-rpa-key"

    def test_解析命令行参数_不回退_RPA_KEY(self):
        with patch.dict(os.environ, {"RPA_KEY": "legacy-rpa-key"}, clear=True):
            with patch("sys.argv", ["dispatch_test.py", "--machine-id", "machine-1"]):
                参数 = dispatch_test.解析命令行参数()

        assert 参数.rpa_key == ""

    def test_构建请求头_返回_X_RPA_KEY(self):
        assert dispatch_test.构建请求头(" test-rpa-key ") == {"X-RPA-KEY": "test-rpa-key"}

    def test_构建请求头_为空时抛异常(self):
        try:
            dispatch_test.构建请求头("   ")
        except ValueError as 异常:
            assert str(异常) == "X_RPA_KEY 不能为空"
        else:
            raise AssertionError("期望抛出 ValueError")

    def test_main_派发请求携带_X_RPA_KEY(self):
        参数 = 构造参数()
        派发响应 = 构造响应({"code": 0, "msg": "ok", "data": {"task_id": "task-1"}})
        客户端上下文 = MagicMock()
        客户端 = 客户端上下文.__enter__.return_value
        客户端.post.return_value = 派发响应

        with patch.object(dispatch_test, "解析命令行参数", return_value=参数):
            with patch("scripts.dispatch_test.httpx.Client", return_value=客户端上下文):
                assert dispatch_test.main() == 0

        客户端.post.assert_called_once_with(
            "http://localhost:8001/api/task-dispatches/echo-test",
            json={"machine_id": "test-machine-001", "message": "hello", "sleep_seconds": 3},
            headers={"X-RPA-KEY": "test-rpa-key"},
        )

    def test_main_轮询请求也携带_X_RPA_KEY(self):
        参数 = 构造参数(poll=True)
        派发响应 = 构造响应({"code": 0, "msg": "ok", "data": {"task_id": "task-1"}})
        状态响应 = 构造响应({"code": 0, "msg": "ok", "data": {"status": "success"}})

        派发上下文 = MagicMock()
        派发客户端 = 派发上下文.__enter__.return_value
        派发客户端.post.return_value = 派发响应

        轮询上下文 = MagicMock()
        轮询客户端 = 轮询上下文.__enter__.return_value
        轮询客户端.get.return_value = 状态响应

        with patch.object(dispatch_test, "解析命令行参数", return_value=参数):
            with patch(
                "scripts.dispatch_test.httpx.Client",
                side_effect=[派发上下文, 轮询上下文],
            ):
                assert dispatch_test.main() == 0

        轮询客户端.get.assert_called_once_with(
            "http://localhost:8001/api/tasks/task-1",
            headers={"X-RPA-KEY": "test-rpa-key"},
        )
