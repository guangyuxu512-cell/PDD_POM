Task 37：屏障模式单任务投递修复 — 同店铺合并为1个Celery任务
一、做什么
修复 barrier 模式下同店铺同批次投递多个独立 Celery 任务的问题。改为只投递1个任务，任务内部循环处理所有 flow_params 记录。
二、涉及文件
backend/services/执行服务.py — 投递逻辑：barrier 步骤同店铺只投递1个 Celery 任务
backend/services/任务服务.py — 执行逻辑：支持接收多条 flow_params 参数，内部循环执行
tasks/执行任务.py — Celery 任务签名支持 flow_param_ids: list[int]（多条记录）
tasks/发布相似商品任务.py — 无需改动（框架层循环调用）
tasks/限时限量任务.py — 无需改动（框架层循环调用）
tasks/推广任务.py — merge 模式已支持合并参数，无需改动
测试同步更新
三、核心改动
3.1 投递逻辑（执行服务.py）
当前步骤推进时的投递逻辑改为：
推进到下一步(shop_id, batch_id, flow_id, step_name):
    下一步配置 = 获取下一步(flow_id, current_step)
    同店铺记录 = 查(shop_id, batch_id, flow_id, 当前步骤已完成)
    
    如果下一步 barrier == true 或 merge == true:
        只投递1个 Celery 任务，参数为：
            flow_param_ids = [所有记录的ID列表]
            merge = 下一步的merge配置
    否则:
        每条记录各投递1个 Celery 任务（现有逻辑不变）
​
3.2 执行逻辑（任务服务.py）
执行任务() / 统一执行任务() 入口支持两种模式：
如果 flow_param_ids 是列表且长度 > 1:
    如果 merge == true:
        合并所有记录参数 → 商品ID列表 + 商品参数映射
        调用任务.执行() 一次
        逐条回写结果到每条 flow_params
    如果 merge == false (barrier only):
        循环每条记录：
            读取该记录的参数
            调用任务.执行()
            回写该记录的 step_results
            随机延时（避免操作过快）
否则:
    单条执行（现有逻辑不变）
​
3.3 Celery 任务签名（执行任务.py）
当前签名：
执行任务(batch_id, shop_id, shop_name, task_name, on_fail, step_index, total_steps, flow_param_id)
​
改为兼容：
执行任务(batch_id, shop_id, shop_name, task_name, on_fail, step_index, total_steps, flow_param_id=None, flow_param_ids=None, merge=False)
​
flow_param_id：单条模式（向后兼容）
flow_param_ids：多条模式（barrier/merge）
merge：是否合并执行
如果传了 flow_param_ids，忽略 flow_param_id。
如果传了 flow_param_id（旧模式），自动包装成 flow_param_ids = [flow_param_id]。
3.4 循环执行时的浏览器复用
barrier only（merge=false）模式下，框架层循环调用任务：
打开浏览器页面（1次）
for 记录 in 所有记录:
    读取该记录参数
    调用 任务.执行(页面, 店铺配置)  # 复用同一个页面对象
    回写该记录 step_results
    随机延时 2-5 秒
​
关键：页面对象在循环外创建，循环内复用。每个商品操作完后，任务内部会自动导航回起始页（现有任务已有"返回商品列表页"逻辑），下一个商品操作时再导航到目标页面。
3.5 错误处理
循环模式下某个商品失败不影响其他商品：
for 记录 in 所有记录:
    try:
        执行并回写(记录, "completed")
    except Exception as e:
        回写(记录, "failed", error=str(e))
        根据 on_fail 策略决定是否继续
​
四、约束
向后兼容：flow_param_id 单条模式保持不变
barrier 步骤同店铺同批次只投递1个 Celery 任务，不投递多个
循环执行时复用同一个浏览器页面对象，不重复打开
每个商品操作之间加随机延时 2-5 秒
单个商品失败不影响其他商品的执行
merge 模式逻辑不变（Task 36 已实现）
测试同步更新，确保 pytest 通过