"""
Celery 应用配置模块

配置 Celery 实例，连接群晖 Redis。
"""
import asyncio
import threading
from typing import Any, Optional
from urllib.parse import urlsplit, urlunsplit

from celery import Celery
from celery.signals import worker_init, worker_shutdown
import httpx

from backend.配置 import 配置实例


Worker环境已初始化 = False
Worker事件循环: Optional[asyncio.AbstractEventLoop] = None
Worker线程本地 = threading.local()
Worker事件循环表: dict[int, asyncio.AbstractEventLoop] = {}
Worker事件循环锁 = threading.Lock()
Worker环境初始化锁 = threading.Lock()
默认Agent服务地址 = "http://localhost:8001"
Worker注册地址路径 = "/api/workers/register"
Worker注册超时秒 = 5.0

celery应用 = Celery(
    "抖店自动化",
    broker=配置实例.REDIS_URL,
    backend=配置实例.REDIS_URL,
)

celery应用.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    beat_scheduler="redbeat.RedBeatScheduler",
    redbeat_redis_url=配置实例.REDIS_URL,
    task_track_started=True,        # 让 Agent 能看到 "started" 状态
    worker_concurrency=1,           # 同时只跑一个任务（浏览器资源有限）
    task_acks_late=True,            # 任务完成后才 ack，防止崩溃丢任务
    task_reject_on_worker_lost=True,  # Worker 异常退出后重新入队，避免任务静默丢失
    broker_connection_retry_on_startup=True,  # 启动期等待 Redis 恢复，避免瞬时网络抖动直接退出
    imports=("tasks.桥接任务", "tasks.执行任务", "tasks.定时任务"),
)


def 获取Worker事件循环() -> asyncio.AbstractEventLoop:
    """获取当前线程复用的 Worker 事件循环。"""
    global Worker事件循环

    当前线程事件循环 = getattr(Worker线程本地, "事件循环", None)
    if 当前线程事件循环 is not None and not 当前线程事件循环.is_closed():
        Worker事件循环 = 当前线程事件循环
        return 当前线程事件循环

    当前线程事件循环 = asyncio.new_event_loop()
    Worker线程本地.事件循环 = 当前线程事件循环
    Worker事件循环 = 当前线程事件循环

    with Worker事件循环锁:
        Worker事件循环表[threading.get_ident()] = 当前线程事件循环

    return 当前线程事件循环


def 获取Worker机器编号() -> str:
    """获取 Worker 注册使用的机器编号。"""
    return (配置实例.AGENT_MACHINE_ID or "").strip() or "default"


def 获取Worker机器名称() -> str:
    """获取 Worker 注册使用的机器名称。"""
    return (配置实例.MACHINE_NAME or "").strip() or 获取Worker机器编号()


def 获取Agent服务地址() -> str:
    """从现有配置推导 Agent 服务根地址。"""
    for 原始地址 in (
        str(配置实例.AGENT_HEARTBEAT_URL or "").strip(),
        str(配置实例.AGENT_CALLBACK_URL or "").strip(),
        默认Agent服务地址,
    ):
        if not 原始地址:
            continue

        解析结果 = urlsplit(原始地址)
        if not 解析结果.scheme or not 解析结果.netloc:
            continue

        return urlunsplit((解析结果.scheme, 解析结果.netloc, "", "", ""))

    return 默认Agent服务地址


def 获取Worker注册地址() -> str:
    """构造 Worker 机器注册接口地址。"""
    return f"{获取Agent服务地址().rstrip('/')}{Worker注册地址路径}"


def 构建Worker注册请求头() -> Optional[dict[str, str]]:
    """构造 Worker 注册请求头。"""
    密钥 = str(配置实例.X_RPA_KEY or "").strip()
    if not 密钥:
        return None
    return {"X-RPA-KEY": 密钥}


def 校验业务响应(响应: httpx.Response) -> None:
    """校验 Agent 的统一业务响应。"""
    try:
        响应数据: Any = 响应.json()
    except ValueError:
        return

    if isinstance(响应数据, dict) and 响应数据.get("code") not in (None, 0):
        raise RuntimeError(响应数据.get("msg") or "Agent 返回失败")


def 注册Worker机器() -> None:
    """向 Agent 注册当前 Worker 机器信息。"""
    请求头 = 构建Worker注册请求头()
    if not 请求头:
        print("[Celery] Worker 机器注册已跳过：未配置 X_RPA_KEY")
        return

    注册地址 = 获取Worker注册地址()
    请求体 = {
        "machine_id": 获取Worker机器编号(),
        "machine_name": 获取Worker机器名称(),
    }

    try:
        with httpx.Client(timeout=Worker注册超时秒) as 客户端:
            响应 = 客户端.post(注册地址, json=请求体, headers=请求头)
            响应.raise_for_status()
            校验业务响应(响应)
        print(f"[Celery] Worker 机器注册成功: machine_id={请求体['machine_id']}, url={注册地址}")
    except Exception as e:
        print(f"[Celery] Worker 机器注册失败（忽略）: machine_id={请求体['machine_id']}, error={e}")


def 初始化Worker环境() -> None:
    """
    初始化 Celery Worker 运行环境

    说明:
        Worker 通过 worker_init 信号完成一次性初始化，兼容 threads 等不同池模式。
    """
    global Worker环境已初始化

    事件循环 = 获取Worker事件循环()
    asyncio.set_event_loop(事件循环)

    if Worker环境已初始化:
        return

    with Worker环境初始化锁:
        if Worker环境已初始化:
            return

        from browser.任务回调 import 设置回调地址
        from tasks.任务注册表 import 初始化任务注册表

        初始化任务注册表()

        if 配置实例.AGENT_CALLBACK_URL:
            设置回调地址(配置实例.AGENT_CALLBACK_URL)

        注册Worker机器()
        Worker环境已初始化 = True
        print("[Celery] Worker 环境初始化完成")


def 关闭Worker环境() -> None:
    """关闭 Worker 级事件循环并重置状态"""
    global Worker环境已初始化, Worker事件循环, Worker线程本地

    with Worker事件循环锁:
        事件循环列表 = list(Worker事件循环表.values())
        Worker事件循环表.clear()

    for 待关闭事件循环 in 事件循环列表:
        try:
            # 中文注释：关闭阶段只做资源回收，关闭失败只记录，避免影响 Worker 退出流程。
            if 待关闭事件循环 is not None and not 待关闭事件循环.is_closed() and not 待关闭事件循环.is_running():
                待关闭事件循环.close()
        except Exception as e:
            print(f"[Celery] Worker 事件循环关闭失败（忽略）: {e}")

    Worker线程本地 = threading.local()
    Worker事件循环 = None
    Worker环境已初始化 = False


@worker_init.connect
def Worker启动时初始化(**kwargs) -> None:
    """Celery Worker 启动初始化钩子"""
    try:
        # 中文注释：信号钩子里只做最佳努力初始化，异常只记录，避免 Worker 启动即退出。
        初始化Worker环境()
    except Exception as e:
        print(f"[Celery] Worker 启动初始化失败（忽略）: {e}")


@worker_shutdown.connect
def Worker关闭时清理(**kwargs) -> None:
    """Celery Worker 关闭清理钩子"""
    try:
        # 中文注释：关闭信号属于收尾逻辑，异常不应反向影响 Worker 的退出流程。
        关闭Worker环境()
    except Exception as e:
        print(f"[Celery] Worker 关闭清理失败（忽略）: {e}")
