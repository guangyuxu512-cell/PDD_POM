"""
服务端派发测试脚本。

用途：
1. 调用 POST /api/task-dispatches/echo-test 向指定机器派发测试任务
2. 打印服务端返回内容与任务 ID
3. 可选轮询任务状态直到完成

说明：
- 仓库当前没有 `/api/task-dispatches/*` 的后端源码，
  默认路由按 `.pipeline/task.md` 的任务说明实现。
- 如果真实接口字段或状态查询地址不同，可通过命令行参数或环境变量覆盖。

PowerShell 示例：
    $env:SERVER_URL = "http://127.0.0.1:8000"
    python scripts/dispatch_test.py --machine-id test-machine-001 --poll

补充额外字段：
    python scripts/dispatch_test.py --machine-id test-machine-001 --payload-json '{"callback_url":"/api/callback"}'
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from typing import Any, Optional

import httpx
from dotenv import load_dotenv


load_dotenv()


默认服务端地址 = "http://127.0.0.1:8000"
默认派发路径 = "/api/task-dispatches/echo-test"
默认状态路径模板 = "/api/tasks/{task_id}"
默认请求超时秒数 = 10.0
默认轮询间隔秒数 = 2.0
默认轮询超时秒数 = 120.0
默认消息文本 = "来自 dispatch_test 的 echo-test 任务"
默认模拟执行秒数 = 3


def 当前时间文本() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def 日志(消息: str) -> None:
    print(f"[{当前时间文本()}] {消息}")


def 规范化地址(服务端地址: str, 路径或地址: str) -> str:
    if 路径或地址.startswith("http://") or 路径或地址.startswith("https://"):
        return 路径或地址
    return f"{服务端地址.rstrip('/')}/{路径或地址.lstrip('/')}"


def 解析JSON文本(文本: str) -> dict[str, Any]:
    if not 文本:
        return {}
    数据 = json.loads(文本)
    if not isinstance(数据, dict):
        raise ValueError("payload-json 必须是 JSON 对象")
    return 数据


def 解析JSON响应(响应: httpx.Response) -> Any:
    try:
        return 响应.json()
    except json.JSONDecodeError:
        return {"raw_text": 响应.text}


def 解包业务响应(响应数据: Any) -> tuple[Any, str]:
    if not isinstance(响应数据, dict) or "code" not in 响应数据:
        return 响应数据, ""

    if 响应数据.get("code") != 0:
        raise RuntimeError(响应数据.get("msg") or "服务端返回失败")

    return 响应数据.get("data"), 响应数据.get("msg", "")


def 提取任务ID(响应数据: Any) -> Optional[str]:
    候选 = []
    if isinstance(响应数据, dict):
        候选.extend(
            [
                响应数据.get("task_id"),
                响应数据.get("dispatch_id"),
                响应数据.get("id"),
            ]
        )
        if isinstance(响应数据.get("data"), dict):
            数据区 = 响应数据["data"]
            候选.extend(
                [
                    数据区.get("task_id"),
                    数据区.get("dispatch_id"),
                    数据区.get("id"),
                ]
            )

    for 值 in 候选:
        if 值:
            return str(值)
    return None


def 提取状态地址(
    服务端地址: str,
    状态路径模板: str,
    任务ID: str,
    派发结果: Any,
) -> str:
    if isinstance(派发结果, dict):
        for 键名 in ("status_url", "query_url", "detail_url"):
            值 = 派发结果.get(键名)
            if 值:
                return 规范化地址(服务端地址, str(值))
    return 规范化地址(服务端地址, 状态路径模板.format(task_id=任务ID))


def 提取任务状态(状态数据: Any) -> str:
    if isinstance(状态数据, dict):
        for 键名 in ("status", "state"):
            值 = 状态数据.get(键名)
            if 值:
                return str(值)
        if isinstance(状态数据.get("data"), dict):
            return 提取任务状态(状态数据["data"])
    return "unknown"


def 构建请求头(RPA密钥: str) -> dict[str, str]:
    密钥 = RPA密钥.strip()
    if not 密钥:
        raise ValueError("X_RPA_KEY 不能为空")
    return {"X-RPA-KEY": 密钥}


def 解析命令行参数() -> argparse.Namespace:
    解析器 = argparse.ArgumentParser(description="服务端派发测试脚本")
    解析器.add_argument("--machine-id", required=True, help="目标机器编号")
    解析器.add_argument("--server-url", default=os.getenv("SERVER_URL", 默认服务端地址))
    解析器.add_argument(
        "--rpa-key",
        default=os.getenv("X_RPA_KEY", "").strip(),
        help="派发请求使用的 X-RPA-KEY；默认从 .env 的 X_RPA_KEY 读取",
    )
    解析器.add_argument("--dispatch-path", default=os.getenv("DISPATCH_PATH", 默认派发路径))
    解析器.add_argument(
        "--status-path-template",
        default=os.getenv("TASK_STATUS_PATH_TEMPLATE", 默认状态路径模板),
    )
    解析器.add_argument("--message", default=os.getenv("TEST_MESSAGE", 默认消息文本))
    解析器.add_argument(
        "--sleep-seconds",
        type=int,
        default=int(os.getenv("SLEEP_SECONDS", str(默认模拟执行秒数))),
    )
    解析器.add_argument(
        "--payload-json",
        default=os.getenv("PAYLOAD_JSON", "").strip(),
        help="派发请求附加 JSON 字段",
    )
    解析器.add_argument("--poll", action="store_true", help="派发后轮询任务状态")
    解析器.add_argument(
        "--poll-interval",
        type=float,
        default=float(os.getenv("POLL_INTERVAL_SECONDS", str(默认轮询间隔秒数))),
    )
    解析器.add_argument(
        "--poll-timeout",
        type=float,
        default=float(os.getenv("POLL_TIMEOUT_SECONDS", str(默认轮询超时秒数))),
    )
    解析器.add_argument(
        "--request-timeout",
        type=float,
        default=float(os.getenv("REQUEST_TIMEOUT_SECONDS", str(默认请求超时秒数))),
    )
    return 解析器.parse_args()


def main() -> int:
    参数 = 解析命令行参数()
    派发地址 = 规范化地址(参数.server_url, 参数.dispatch_path)
    请求头 = 构建请求头(参数.rpa_key)
    请求体 = {
        "machine_id": 参数.machine_id,
        "message": 参数.message,
        "sleep_seconds": max(0, 参数.sleep_seconds),
    }
    请求体.update(解析JSON文本(参数.payload_json))

    日志(f"开始派发任务到机器 {参数.machine_id}，地址：{派发地址}")
    with httpx.Client(timeout=max(1.0, 参数.request_timeout)) as 客户端:
        响应 = 客户端.post(派发地址, json=请求体, headers=请求头)
        响应.raise_for_status()
        响应数据 = 解析JSON响应(响应)
        业务数据, 消息 = 解包业务响应(响应数据)

    任务ID = 提取任务ID(响应数据) or 提取任务ID(业务数据)
    日志(f"派发成功，消息：{消息 or 'ok'}")
    日志(f"服务端返回：{json.dumps(业务数据, ensure_ascii=False, default=str)}")
    if 任务ID:
        日志(f"任务 ID：{任务ID}")
    else:
        日志("未从响应中提取到任务 ID")

    if not 参数.poll:
        return 0

    if not 任务ID:
        日志("未开启轮询：缺少任务 ID")
        return 0

    状态地址 = 提取状态地址(参数.server_url, 参数.status_path_template, 任务ID, 业务数据)
    截止时间 = time.monotonic() + max(1.0, 参数.poll_timeout)
    已结束状态 = {"completed", "failed", "success", "cancelled"}

    日志(f"开始轮询任务状态：{状态地址}")
    with httpx.Client(timeout=max(1.0, 参数.request_timeout)) as 客户端:
        while time.monotonic() < 截止时间:
            响应 = 客户端.get(状态地址, headers=请求头)
            响应.raise_for_status()
            响应数据 = 解析JSON响应(响应)
            业务数据, _ = 解包业务响应(响应数据)
            当前状态 = 提取任务状态(业务数据)
            日志(
                f"任务状态：{当前状态}，详情="
                f"{json.dumps(业务数据, ensure_ascii=False, default=str)}",
            )
            if 当前状态 in 已结束状态:
                return 0
            time.sleep(max(0.5, 参数.poll_interval))

    raise TimeoutError(f"轮询超时，{参数.poll_timeout:g} 秒内未结束")


if __name__ == "__main__":
    raise SystemExit(main())
