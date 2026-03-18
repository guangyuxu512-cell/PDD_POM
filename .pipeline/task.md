背景
tasks/执行任务.py 中，当一个流程有多个步骤（total_steps > 1）时，第一步完成后只更新了 Redis 状态为 running，但没有投递第二步的 Celery 任务。导致第二个流程永远不会启动。
根因
执行任务() 函数中，第 125-135 行：
if 执行结果["status"] == "completed":
    if batch_id:
        同步更新批次店铺状态(
            ...,
            shop_status="completed" if step_index >= total_steps else "running",
        )
    return 执行结果  # ← 直接 return，没有投递下一步
​
shop_status 被正确设为 "running"（因为 step_index < total_steps），但没有任何代码去投递 step_index + 1 的任务。
要求
在 执行任务() 函数中，当 执行结果["status"] == "completed" 且 step_index < total_steps 时，投递下一步任务。
修改 tasks/执行任务.py
在 return 执行结果 之前，增加下一步投递逻辑：
if 执行结果["status"] == "completed":
    if batch_id:
        同步更新批次店铺状态(
            batch_id,
            shop_id,
            step_index=step_index,
            task_name=task_name,
            step_status="completed",
            shop_status="completed" if step_index >= total_steps else "running",
            result=执行结果.get("result"),
        )

        # ===== 新增：投递下一步 =====
        if step_index < total_steps:
            批次数据 = 同步读取批次状态(batch_id)
            if 批次数据 and not 批次数据.get("stopped") and not 同步检查取消标记(batch_id):
                店铺状态 = 批次数据.get("shops", {}).get(shop_id, {})
                步骤列表 = 店铺状态.get("steps", [])
                if step_index < len(步骤列表):
                    下一步骤 = 步骤列表[step_index]  # step_index 是 1-based，所以 steps[step_index] 就是下一步
                    下一步任务名 = 下一步骤["task"]
                    下一步失败策略 = 下一步骤.get("on_fail", "abort")
                    下一步合并 = bool(下一步骤.get("merge", False))
                    下一步屏障 = bool(下一步骤.get("barrier", False))

                    # 获取队列名称
                    queue_name = 批次数据.get("queue_name") or 获取队列名称()

                    # 构建流程参数
                    下一步参数 = {
                        "batch_id": batch_id,
                        "shop_id": shop_id,
                        "shop_name": shop_name,
                        "task_name": 下一步任务名,
                        "on_fail": 下一步失败策略,
                        "step_index": step_index + 1,
                        "total_steps": total_steps,
                        "merge": 下一步合并,
                    }

                    # 继承 flow_param_id / flow_param_ids
                    if flow_param_ids:
                        下一步参数["flow_param_ids"] = flow_param_ids
                    elif flow_param_id is not None:
                        下一步参数["flow_param_id"] = flow_param_id

                    # 投递
                    下一步签名 = 执行任务.si(**下一步参数).set(
                        queue=queue_name, routing_key=queue_name
                    )
                    下一步签名.apply_async()
                    print(
                        f"[执行任务] 已投递下一步: shop_id={shop_id}, "
                        f"task={下一步任务名}, step={step_index + 1}/{total_steps}"
                    )
        # ===== 新增结束 =====

    return 执行结果
​
同时在文件顶部增加导入：
from backend.services.执行服务 import 同步读取批次状态, 获取队列名称
​
（同步检查取消标记 已经导入了）
对 on_fail == "continue" 的路径也要同样处理
在 on_fail in {"continue", "log_and_skip"} 的分支（约第 145-160 行），如果 step_index < total_steps，也需要投递下一步。逻辑和上面一样，复用同一个投递代码块（建议提取成内部函数 _投递下一步()）。
测试验收
pytest tests/ 全量通过
创建一个 2 步流程（例如"售后处理" → "售后处理"），执行后日志中应该看到：
[执行任务] 开始执行: ... step=1/2
[执行任务] 已投递下一步: ... step=2/2
[执行任务] 开始执行: ... step=2/2
如果批次已被取消（stopped=True），不应投递下一步