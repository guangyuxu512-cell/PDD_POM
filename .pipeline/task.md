任务目标：修复流程执行时因 flow_params 残留记录导致同一店铺投递多个首步任务的问题

需要修改的文件：
- backend/services/execute_service.py

具体实现：

方案 A（推荐 — 去重 + 清理残留）：

在 创建批次() 方法中，读取完 流程参数记录映射 之后，添加去重逻辑：

    # 在 "if flow_id:" 分支内，读取待执行记录之后
    else:
        for 店铺ID in 标准店铺ID列表:
            待执行记录列表 = await 流程参数服务实例.获取待执行列表(店铺ID, str(flow_id))
            流程参数记录映射[店铺ID] = 待执行记录列表

    # ★ 新增：每个店铺最多保留 1 条待执行记录（取最新一条），
    #   多余的标记为 skipped 避免下次再被拉到
    for 店铺ID in 可执行店铺ID列表:
        记录列表 = 流程参数记录映射.get(店铺ID, [])
        if len(记录列表) > 1:
            # 按 id 降序排列，保留最新一条
            记录列表.sort(key=lambda r: int(r.get("id") or 0), reverse=True)
            保留记录 = 记录列表[0]
            多余记录 = 记录列表[1:]
            for 多余 in 多余记录:
                await 流程参数服务实例.更新(int(多余["id"]), {"status": "skipped"})
            流程参数记录映射[店铺ID] = [保留记录]

    # ★ 无记录的店铺也要能跑（空上下文模式）—— 已有逻辑不变

方案 B（更简单 — 无记录时直接投 1 个任务，有记录时合并投 1 个）：

    把投递循环改为"每店铺只投一个首步任务"：
    
    for 店铺ID in 可执行店铺ID列表:
        店铺流程参数记录 = 流程参数记录映射.get(店铺ID, [])
        所有流程参数ID = [int(r["id"]) for r in 店铺流程参数记录 if r.get("id")]

        投递结果 = await self.投递单步任务(
            batch_id=batch_id,
            shop_id=店铺ID,
            shop_name=...,
            task_name=首步骤["task"],
            on_fail=首步骤["on_fail"],
            step_index=1,
            total_steps=len(步骤模板),
            flow_param_ids=所有流程参数ID if 所有流程参数ID else None,
            flow_mode=True,
            merge=bool(首步骤.get("merge")),
            queue_name=queue_name,
            批次数据=批次数据,
            立即投递=False,
        )
        待投递任务列表.append(投递结果["signature"])
        # ★ 不再循环每条记录各投一个，而是合并为一次投递

验收方式：
- 创建一个 2 步流程（登录 → 发布），步骤 1 设为 "记录并跳过"
- 选一个店铺执行
- 查看执行日志：每个步骤只应出现 1 次 "开始执行" 日志
- 查看 Redis 批次状态：shops.{shop_id}.task_ids 数组长度 == 步骤数
- 连续执行 2 次，第 2 次不应因残留记录导致重复