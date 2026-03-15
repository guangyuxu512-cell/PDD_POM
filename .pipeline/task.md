Task 39：前端停止任务真正生效
一、做什么
让前端点击"停止"后，正在执行的任务在当前页面操作完成后立即停止，不再继续下一个操作。
二、涉及文件
backend/services/执行服务.py — 添加 Redis 取消标记读写
backend/services/任务服务.py — 任务执行循环中检查取消标记
tasks/执行任务.py — HTTP 委托返回后检查取消标记
测试同步更新
三、修改内容
3.1 执行服务.py — 添加取消标记
新增 Redis 键前缀和三个函数：
键前缀: "execute:cancel:{batch_id}"
​
设置取消标记(batch_id) — redis.set(键, "1", ex=3600)
检查取消标记(batch_id) -> bool — redis.get(键) == "1"
清除取消标记(batch_id) — redis.delete(键)
提供同步版本（给 Celery Worker 用）和异步版本（给主进程用）。
修改 停止批次() 方法，在现有 revoke 逻辑之前加一行：调用 设置取消标记(batch_id)。
3.2 任务服务.py — 执行循环中检查
在 统一执行任务() 或 任务执行主入口中，每个商品操作（barrier 循环内）执行前检查：
if 检查取消标记(batch_id):
    print(f"[任务服务] 收到取消信号，停止执行")
    return {"status": "cancelled", "error": "用户手动停止"}
​
关键插入位置：
barrier 模式：循环处理每条记录之前
非 barrier 模式：任务开始执行之前
3.3 执行任务.py — HTTP 返回后检查
在 Celery 任务 执行任务() 中，HTTP 委托返回后、判断是否投递下一步之前，检查取消标记：
from backend.services.执行服务 import 同步检查取消标记

# HTTP 返回后，投递下一步之前
if 同步检查取消标记(batch_id):
    同步更新批次店铺状态(
        batch_id, shop_id,
        step_index=step_index,
        shop_status="stopped",
        error="用户手动停止",
    )
    return {"status": "cancelled", "shop_id": shop_id}
​
四、约束
取消标记用 Redis，不用内存字典（因为主进程和 Worker 是不同进程）
取消标记 TTL 设为 3600 秒，防止残留
不要用 revoke(terminate=True)，因为它会强杀进程，可能导致浏览器僵尸
当前正在执行的页面操作允许完成，只在操作之间检查停止
被取消的记录状态写为 cancelled，已完成的不受影响
测试同步更新，确保 pytest 通过