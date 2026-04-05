"""
执行状态仓储模块

抽离 execute_service 中批次状态读写与取消标记处理的低层逻辑。
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional


def 同步读取批次状态(
    batch_id: str,
    *,
    获取同步Redis客户端: Callable[[], Any],
    批次状态键: Callable[[str], str],
    读取内存批次状态: Callable[[str], Optional[Dict[str, Any]]],
    记录Redis降级: Callable[[str, Exception], None],
) -> Optional[Dict[str, Any]]:
    """供 Celery Worker 读取批次状态。"""
    客户端 = 获取同步Redis客户端()
    try:
        原始数据 = 客户端.get(批次状态键(batch_id))
        if not 原始数据:
            return 读取内存批次状态(batch_id)
        return json.loads(原始数据)
    except Exception as e:
        记录Redis降级("读取批次状态", e)
        return 读取内存批次状态(batch_id)
    finally:
        客户端.close()


def 同步写入批次状态(
    批次数据: Dict[str, Any],
    *,
    获取同步Redis客户端: Callable[[], Any],
    批次状态键: Callable[[str], str],
    当前批次键: str,
    执行状态频道: str,
    记录Redis降级: Callable[[str, Exception], None],
    写入内存批次状态: Callable[[Dict[str, Any]], None],
    同步写入运行实例状态: Callable[[Dict[str, Any]], bool],
    尝试发送批次完成回调: Callable[[Dict[str, Any]], None],
) -> Dict[str, Any]:
    """供 Celery Worker 写入批次状态并推送事件。"""
    客户端 = 获取同步Redis客户端()
    序列化数据 = json.dumps(批次数据, ensure_ascii=False)
    try:
        客户端.set(批次状态键(批次数据["batch_id"]), 序列化数据)
        客户端.set(当前批次键, 批次数据["batch_id"])
        客户端.publish(执行状态频道, 序列化数据)
    except Exception as e:
        记录Redis降级("写入批次状态", e)
        写入内存批次状态(批次数据)
    finally:
        客户端.close()

    同步写入运行实例状态(批次数据)
    尝试发送批次完成回调(批次数据)
    return 批次数据


def 同步更新批次店铺状态(
    batch_id: str,
    shop_id: str,
    *,
    step_index: Optional[int],
    task_name: Optional[str],
    step_status: Optional[str],
    shop_status: Optional[str],
    error: Optional[str],
    result: Optional[str],
    读取批次状态: Callable[[str], Optional[Dict[str, Any]]],
    更新店铺步骤状态: Callable[..., Dict[str, Any]],
    写入批次状态: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """供 Celery Worker 更新批次状态。"""
    批次数据 = 读取批次状态(batch_id)
    if not 批次数据:
        return None

    更新后数据 = 更新店铺步骤状态(
        批次数据,
        shop_id,
        step_index=step_index,
        task_name=task_name,
        step_status=step_status,
        shop_status=shop_status,
        error=error,
        result=result,
    )
    return 写入批次状态(更新后数据)


def 同步设置取消标记(
    batch_id: str,
    *,
    批次取消键: Callable[[str], str],
    批次取消标记过期秒: int,
    内存取消标记缓存: set[str],
    获取同步Redis客户端: Callable[[], Any],
    记录Redis降级: Callable[[str, Exception], None],
) -> bool:
    """为批次写入取消标记，供 Worker 与主进程跨进程读取。"""
    if not str(batch_id or "").strip():
        return False

    内存取消标记缓存.add(str(batch_id))
    客户端 = 获取同步Redis客户端()
    try:
        return bool(
            客户端.set(
                批次取消键(batch_id),
                "1",
                ex=批次取消标记过期秒,
            )
        )
    except Exception as e:
        记录Redis降级("设置取消标记", e)
        return True
    finally:
        客户端.close()


def 同步检查取消标记(
    batch_id: str,
    *,
    批次取消键: Callable[[str], str],
    内存取消标记缓存: set[str],
    获取同步Redis客户端: Callable[[], Any],
    记录Redis降级: Callable[[str, Exception], None],
) -> bool:
    """同步检查批次是否已被标记为取消。"""
    if not str(batch_id or "").strip():
        return False

    客户端 = 获取同步Redis客户端()
    try:
        return 客户端.get(批次取消键(batch_id)) == "1" or str(batch_id) in 内存取消标记缓存
    except Exception as e:
        记录Redis降级("检查取消标记", e)
        return str(batch_id) in 内存取消标记缓存
    finally:
        客户端.close()


def 同步清除取消标记(
    batch_id: str,
    *,
    批次取消键: Callable[[str], str],
    内存取消标记缓存: set[str],
    获取同步Redis客户端: Callable[[], Any],
    记录Redis降级: Callable[[str, Exception], None],
) -> bool:
    """同步清理批次取消标记。"""
    if not str(batch_id or "").strip():
        return False

    已存在 = str(batch_id) in 内存取消标记缓存
    内存取消标记缓存.discard(str(batch_id))
    客户端 = 获取同步Redis客户端()
    try:
        return bool(客户端.delete(批次取消键(batch_id))) or 已存在
    except Exception as e:
        记录Redis降级("清除取消标记", e)
        return 已存在
    finally:
        客户端.close()


async def 设置取消标记(
    batch_id: str,
    *,
    批次取消键: Callable[[str], str],
    批次取消标记过期秒: int,
    内存取消标记缓存: set[str],
    获取异步Redis客户端: Callable[[], Any],
    关闭异步Redis客户端: Callable[[Any], Any],
    记录Redis降级: Callable[[str, Exception], None],
) -> bool:
    """异步设置批次取消标记。"""
    if not str(batch_id or "").strip():
        return False

    内存取消标记缓存.add(str(batch_id))
    客户端 = await 获取异步Redis客户端()
    try:
        return bool(
            await 客户端.set(
                批次取消键(batch_id),
                "1",
                ex=批次取消标记过期秒,
            )
        )
    except Exception as e:
        记录Redis降级("设置取消标记", e)
        return True
    finally:
        await 关闭异步Redis客户端(客户端)


async def 检查取消标记(
    batch_id: str,
    *,
    批次取消键: Callable[[str], str],
    内存取消标记缓存: set[str],
    获取异步Redis客户端: Callable[[], Any],
    关闭异步Redis客户端: Callable[[Any], Any],
    记录Redis降级: Callable[[str, Exception], None],
) -> bool:
    """异步检查批次是否已被标记为取消。"""
    if not str(batch_id or "").strip():
        return False

    客户端 = await 获取异步Redis客户端()
    try:
        return await 客户端.get(批次取消键(batch_id)) == "1" or str(batch_id) in 内存取消标记缓存
    except Exception as e:
        记录Redis降级("检查取消标记", e)
        return str(batch_id) in 内存取消标记缓存
    finally:
        await 关闭异步Redis客户端(客户端)


async def 清除取消标记(
    batch_id: str,
    *,
    批次取消键: Callable[[str], str],
    内存取消标记缓存: set[str],
    获取异步Redis客户端: Callable[[], Any],
    关闭异步Redis客户端: Callable[[Any], Any],
    记录Redis降级: Callable[[str, Exception], None],
) -> bool:
    """异步清理批次取消标记。"""
    if not str(batch_id or "").strip():
        return False

    已存在 = str(batch_id) in 内存取消标记缓存
    内存取消标记缓存.discard(str(batch_id))
    客户端 = await 获取异步Redis客户端()
    try:
        return bool(await 客户端.delete(批次取消键(batch_id))) or 已存在
    except Exception as e:
        记录Redis降级("清除取消标记", e)
        return 已存在
    finally:
        await 关闭异步Redis客户端(客户端)


async def 获取批次状态(
    batch_id: str,
    *,
    获取异步Redis客户端: Callable[[], Any],
    关闭异步Redis客户端: Callable[[Any], Any],
    批次状态键: Callable[[str], str],
    读取内存批次状态: Callable[[str], Optional[Dict[str, Any]]],
    记录Redis降级: Callable[[str, Exception], None],
) -> Optional[Dict[str, Any]]:
    """读取单个批次状态。"""
    客户端 = await 获取异步Redis客户端()
    try:
        原始数据 = await 客户端.get(批次状态键(batch_id))
        if not 原始数据:
            return 读取内存批次状态(batch_id)
        return json.loads(原始数据)
    except Exception as e:
        记录Redis降级("读取批次状态", e)
        return 读取内存批次状态(batch_id)
    finally:
        await 关闭异步Redis客户端(客户端)


async def 获取最新批次状态(
    batch_id: Optional[str],
    *,
    获取异步Redis客户端: Callable[[], Any],
    关闭异步Redis客户端: Callable[[Any], Any],
    当前批次键: str,
    批次状态键: Callable[[str], str],
    读取内存批次状态: Callable[[str], Optional[Dict[str, Any]]],
    获取内存当前批次ID: Callable[[], Optional[str]],
    记录Redis降级: Callable[[str, Exception], None],
) -> Optional[Dict[str, Any]]:
    """获取当前批次或指定批次的状态快照。"""
    客户端 = await 获取异步Redis客户端()
    try:
        目标批次ID = batch_id or await 客户端.get(当前批次键)
        if not 目标批次ID:
            目标批次ID = 获取内存当前批次ID()
        if not 目标批次ID:
            return None
        原始数据 = await 客户端.get(批次状态键(目标批次ID))
        if not 原始数据:
            return 读取内存批次状态(str(目标批次ID))
        return json.loads(原始数据)
    except Exception as e:
        记录Redis降级("读取最新批次状态", e)
        目标批次ID = str(batch_id or 获取内存当前批次ID() or "").strip()
        if not 目标批次ID:
            return None
        return 读取内存批次状态(目标批次ID)
    finally:
        await 关闭异步Redis客户端(客户端)


async def 写入批次状态(
    批次数据: Dict[str, Any],
    *,
    获取异步Redis客户端: Callable[[], Any],
    关闭异步Redis客户端: Callable[[Any], Any],
    批次状态键: Callable[[str], str],
    当前批次键: str,
    执行状态频道: str,
    写入内存批次状态: Callable[[Dict[str, Any]], None],
    记录Redis降级: Callable[[str, Exception], None],
    同步写入运行实例状态: Callable[[Dict[str, Any]], bool],
) -> Dict[str, Any]:
    """异步写入批次状态并推送事件。"""
    客户端 = await 获取异步Redis客户端()
    try:
        序列化数据 = json.dumps(批次数据, ensure_ascii=False)
        await 客户端.set(批次状态键(批次数据["batch_id"]), 序列化数据)
        await 客户端.set(当前批次键, 批次数据["batch_id"])
        await 客户端.publish(执行状态频道, 序列化数据)
    except Exception as e:
        记录Redis降级("写入批次状态", e)
        写入内存批次状态(批次数据)
    finally:
        await 关闭异步Redis客户端(客户端)

    同步写入运行实例状态(批次数据)
    return 批次数据
