"""
浏览器服务模块

封装浏览器实例的生命周期管理，集成真实的 Playwright 管理器。
"""
import asyncio
import threading
from typing import Optional, Dict, List, Any
from datetime import datetime

from browser.管理器 import 浏览器管理器


# 模块级单例
管理器实例: Optional[浏览器管理器] = None
初始化锁: Optional[asyncio.Lock] = None
初始化锁所属事件循环: Optional[asyncio.AbstractEventLoop] = None
初始化超时秒 = 60
线程本地状态 = threading.local()


def 运行在线程池中() -> bool:
    """判断当前是否运行在 Worker 线程池线程中。"""
    return threading.current_thread() is not threading.main_thread()


def 获取当前管理器实例() -> Optional[浏览器管理器]:
    """获取当前线程绑定的浏览器管理器。"""
    if not 运行在线程池中():
        return 管理器实例
    return getattr(线程本地状态, "管理器实例", None)


def 设置当前管理器实例(实例: Optional[浏览器管理器]) -> None:
    """设置当前线程绑定的浏览器管理器。"""
    global 管理器实例
    if not 运行在线程池中():
        管理器实例 = 实例
        return
    线程本地状态.管理器实例 = 实例


def 获取当前初始化锁状态() -> tuple[Optional[asyncio.Lock], Optional[asyncio.AbstractEventLoop]]:
    """获取当前线程的初始化锁状态。"""
    if not 运行在线程池中():
        return 初始化锁, 初始化锁所属事件循环
    return (
        getattr(线程本地状态, "初始化锁", None),
        getattr(线程本地状态, "初始化锁所属事件循环", None),
    )


def 设置当前初始化锁状态(
    锁: Optional[asyncio.Lock],
    所属事件循环: Optional[asyncio.AbstractEventLoop],
) -> None:
    """设置当前线程的初始化锁状态。"""
    global 初始化锁, 初始化锁所属事件循环
    if not 运行在线程池中():
        初始化锁 = 锁
        初始化锁所属事件循环 = 所属事件循环
        return
    线程本地状态.初始化锁 = 锁
    线程本地状态.初始化锁所属事件循环 = 所属事件循环


def 获取初始化锁() -> asyncio.Lock:
    """获取与当前事件循环绑定的初始化锁"""
    当前事件循环 = asyncio.get_running_loop()
    当前锁, 当前锁所属事件循环 = 获取当前初始化锁状态()
    if (
        当前锁 is None
        or 当前锁所属事件循环 is None
        or 当前锁所属事件循环.is_closed()
        or 当前锁所属事件循环 is not 当前事件循环
    ):
        当前锁 = asyncio.Lock()
        设置当前初始化锁状态(当前锁, 当前事件循环)

    return 当前锁


async def 确保已初始化() -> None:
    """
    确保浏览器管理器已初始化

    如果管理器实例还没创建或 Playwright 未启动，自动初始化。
    """
    async with 获取初始化锁():
        当前管理器实例 = 获取当前管理器实例()
        # 中文注释：并发场景下做二次检查，避免多个协程重复创建或启动 Playwright。
        if 当前管理器实例 is None:
            print("浏览器服务: 管理器实例不存在，自动创建...")
            当前管理器实例 = 浏览器管理器()
            设置当前管理器实例(当前管理器实例)

        # 中文注释：Playwright 启动属于外部 IO，这里加超时兜底，避免初始化卡死。
        if 当前管理器实例.playwright实例 is None:
            print("浏览器服务: Playwright 未初始化，自动初始化...")
            try:
                await asyncio.wait_for(当前管理器实例.初始化(), timeout=初始化超时秒)
            except asyncio.TimeoutError as e:
                raise TimeoutError(f"浏览器初始化超时（{初始化超时秒}秒）") from e
            except Exception as e:
                raise RuntimeError(f"浏览器初始化失败: {e}") from e
            print("浏览器服务: 自动初始化完成")


async def 初始化浏览器(配置: dict) -> None:
    """
    真正启动 Playwright，创建管理器单例

    参数:
        配置: 浏览器配置字典，包含 chrome_path, max_instances, default_proxy 等
    """
    async with 获取初始化锁():
        当前管理器实例 = 获取当前管理器实例()
        # 中文注释：初始化接口和自动初始化共用同一把锁，避免并发时重复启动浏览器内核。
        if 当前管理器实例 is not None and 当前管理器实例.playwright实例 is not None:
            print(f"浏览器服务: 管理器已完全初始化，跳过")
            return

        print(f"浏览器服务: 开始初始化管理器...")

        if 当前管理器实例 is None:
            当前管理器实例 = 浏览器管理器()
            设置当前管理器实例(当前管理器实例)
            print(f"浏览器服务: 管理器对象已创建")

        # 中文注释：显式限制初始化耗时，防止 Playwright 启动异常时长期阻塞调用方。
        try:
            await asyncio.wait_for(当前管理器实例.初始化(配置), timeout=初始化超时秒)
        except asyncio.TimeoutError as e:
            raise TimeoutError(f"浏览器初始化超时（{初始化超时秒}秒）") from e
        except Exception as e:
            raise RuntimeError(f"浏览器初始化失败: {e}") from e

        print(f"浏览器服务: 管理器初始化完成，playwright实例 = {当前管理器实例.playwright实例}")


async def 打开店铺浏览器(店铺ID: str, 店铺配置: dict, headless: bool = False) -> Dict[str, Any]:
    """
    调用管理器为指定店铺启动独立 Chrome 实例

    参数:
        店铺ID: 店铺 ID
        店铺配置: 店铺配置字典，包含 proxy 等信息
        headless: 是否使用 headless 模式（默认 False）

    返回:
        Dict[str, Any]: 浏览器实例信息

    异常:
        Exception: 如果浏览器未初始化或启动失败
    """
    # 确保浏览器已初始化
    await 确保已初始化()
    当前管理器实例 = 获取当前管理器实例()

    # 详细日志：检查管理器和 Playwright 状态
    playwright状态 = 当前管理器实例.playwright实例 if 当前管理器实例 else None
    print(f"浏览器服务: 打开店铺浏览器 (headless={headless})")
    print(f"  - 管理器实例 = {当前管理器实例}")
    print(f"  - playwright实例 = {playwright状态}")

    # 将 headless 参数添加到店铺配置
    店铺配置_副本 = {**店铺配置, "headless": headless}

    # 调用管理器打开店铺浏览器
    if 当前管理器实例 is None:
        raise RuntimeError("浏览器管理器未初始化")
    实例信息 = await 当前管理器实例.打开店铺(店铺ID, 店铺配置_副本)

    # 返回格式化的实例信息
    return {
        "shop_id": 店铺ID,
        "shop_name": 店铺配置.get("name", ""),
        "status": "running",
        "opened_at": datetime.now().isoformat(),
        "page": 实例信息.get("page"),  # 返回 page 对象供检查状态使用
    }


async def 关闭店铺浏览器(店铺ID: str) -> bool:
    """
    关闭指定店铺的浏览器实例

    参数:
        店铺ID: 店铺 ID

    返回:
        bool: 是否关闭成功
    """
    # 确保浏览器已初始化
    await 确保已初始化()
    当前管理器实例 = 获取当前管理器实例()

    if 当前管理器实例 is None:
        return False

    try:
        await 当前管理器实例.关闭店铺(店铺ID)
        return True
    except KeyError:
        # 实例可能已被自动清理，忽略错误
        print(f"⚠ 店铺 {店铺ID} 实例不存在或已关闭")
        return False
    except Exception as e:
        print(f"✗ 关闭店铺 {店铺ID} 浏览器失败: {e}")
        return False


async def 关闭所有浏览器() -> int:
    """
    关闭所有浏览器实例

    返回:
        int: 关闭的实例数量
    """
    当前管理器实例 = 获取当前管理器实例()
    if 当前管理器实例 is None:
        return 0

    # 获取当前实例数量
    实例列表 = 当前管理器实例.获取实例列表()
    关闭数量 = len(实例列表)

    # 关闭所有实例
    await 当前管理器实例.关闭全部()

    return 关闭数量


async def 获取实例列表() -> List[Dict[str, Any]]:
    """
    获取所有运行中的浏览器实例

    返回:
        List[Dict[str, Any]]: 浏览器实例列表
    """
    当前管理器实例 = 获取当前管理器实例()
    if 当前管理器实例 is None:
        return []

    # 获取实例字典
    实例字典 = 当前管理器实例.获取实例列表()

    # 转换为列表格式
    实例列表 = []
    for 店铺ID, 实例信息 in 实例字典.items():
        实例列表.append({
            "shop_id": 店铺ID,
            "status": 实例信息.get("状态", "运行中"),
            "opened_at": datetime.now().isoformat(),  # 这里可以从实例信息中获取实际时间
        })

    return 实例列表


async def 检查状态(店铺ID: str) -> Optional[Dict[str, Any]]:
    """
    检查指定店铺的浏览器状态

    参数:
        店铺ID: 店铺 ID

    返回:
        Optional[Dict[str, Any]]: 浏览器状态，不存在返回 None
    """
    当前管理器实例 = 获取当前管理器实例()
    if 当前管理器实例 is None:
        return None

    实例字典 = 当前管理器实例.获取实例列表()

    if 店铺ID not in 实例字典:
        return None

    实例信息 = 实例字典[店铺ID]
    return {
        "shop_id": 店铺ID,
        "status": 实例信息.get("状态", "运行中"),
        "opened_at": datetime.now().isoformat(),
    }
