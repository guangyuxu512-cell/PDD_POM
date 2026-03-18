Codex 任务 1（修订版）：售后列表抓包抓取 + 编排第二步修复
Part A：售后列表改用 API 拦截
1) pages/售后页.py — 新增 拦截售后列表API() 方法
async def 拦截售后列表API(self, 超时秒: int = 15) -> list[dict]:
    """
    拦截 PDD 后台售后列表 API 响应，直接获取结构化数据。
    
    原理：PDD 后台切换 tab / 翻页时会发 XHR 请求，响应中包含 result.list。
    用 page.expect_response() 或 page.on("response") 拦截。
    
    返回: list[dict]，每个 dict 包含清洗后的售后单信息
    """
    import asyncio
    
    结果容器: list[dict] = []
    捕获事件 = asyncio.Event()
    
    async def _响应处理(response):
        try:
            if "/afterSales" not in response.url and "/after-sales" not in response.url and "/refund" not in response.url:
                return
            if response.status != 200:
                return
            try:
                数据 = await response.json()
            except Exception:
                return
            if not isinstance(数据, dict):
                return
            result = 数据.get("result") or {}
            列表数据 = result.get("list") or result.get("pageItems") or []
            if not isinstance(列表数据, list) or not 列表数据:
                return
            for 项 in 列表数据:
                if not isinstance(项, dict):
                    continue
                订单号 = str(项.get("orderSn") or "").strip()
                if not 订单号:
                    continue
                结果容器.append({
                    "订单号": 订单号,
                    "售后单ID": str(项.get("id") or ""),
                    "退款金额": round(float(项.get("refundAmount") or 0) / 100, 2),
                    "实收金额": round(float(项.get("receiveAmount") or 0) / 100, 2),
                    "售后类型": str(项.get("afterSalesTypeName") or ""),
                    "售后类型码": int(项.get("afterSalesType") or 0),
                    "售后状态": str(项.get("afterSalesTitle") or ""),
                    "售后状态码": int(项.get("afterSalesStatus") or 0),
                    "申请原因": str(项.get("afterSalesReasonDesc") or ""),
                    "商品名称": str(项.get("goodsName") or ""),
                    "发货状态": str(项.get("sellerAfterSalesShippingStatusDesc") or ""),
                    "操作码列表": list(项.get("actions") or []),
                    "剩余处理秒数": int(项.get("expireRemainTime") or 0),
                })
            if 结果容器:
                捕获事件.set()
        except Exception:
            pass
    
    self.页面.on("response", _响应处理)
    try:
        # 等待已有的响应或即将触发的响应
        await asyncio.wait_for(捕获事件.wait(), timeout=超时秒)
    except asyncio.TimeoutError:
        pass
    finally:
        self.页面.remove_listener("response", _响应处理)
    
    print(f"[售后页] API拦截抓取到 {len(结果容器)} 条售后单")
    return 结果容器
​
关键点：
金额字段从分转元（refundAmount: 460 → 4.60）
actions 保留操作码列表，后续决策引擎可以直接用操作码判断而不是抓按钮文本
URL 匹配用多个关键词兜底（afterSales、after-sales、refund），防止 PDD 改路径
超时 15 秒兜底，拦截不到就返回空列表（fallback 到旧的 JS 抓取）
2) pages/售后页.py — 新增 导航并拦截售后列表() 组合方法
async def 导航并拦截售后列表(self) -> list[dict]:
    """导航到售后列表页，同时拦截 API 响应获取数据。"""
    import asyncio

    拦截任务 = asyncio.create_task(self.拦截售后列表API(超时秒=15))
    await self.导航到售后列表()
    await self.确保待商家处理已选中()
    结果 = await 拦截任务

    if not 结果:
        # fallback: 点击切换 tab 触发新请求
        拦截任务2 = asyncio.create_task(self.拦截售后列表API(超时秒=10))
        await self.确保待商家处理已选中()
        结果 = await 拦截任务2

    return 结果
​
3) pages/售后页.py — 新增 翻页并拦截() 方法
async def 翻页并拦截(self) -> list[dict] | None:
    """点击下一页，同时拦截 API 响应。返回 None 表示没有下一页。"""
    import asyncio
    
    # 先检查是否有下一页
    有下一页 = await self._检查有下一页()
    if not 有下一页:
        return None
    
    拦截任务 = asyncio.create_task(self.拦截售后列表API(超时秒=10))
    翻页成功 = await self.翻页()
    if not 翻页成功:
        拦截任务.cancel()
        return None
    结果 = await 拦截任务
    return 结果
​
需要新增 _检查有下一页() 私有方法（从现有 翻页() 中提取判断逻辑）。
4) tasks/售后任务.py — 改用 API 拦截
在 执行() 方法中：
替换现有的扫描循环（导航 + 逐行抓取 + 翻页）为：
# ===== 扫描阶段：API 拦截 =====
await self._售后页.导航到售后列表()
# 先注册拦截，再点击 tab 触发请求
import asyncio
拦截任务 = asyncio.create_task(self._售后页.拦截售后列表API(超时秒=15))
await self._售后页.确保待商家处理已选中()
当前页数据 = await 拦截任务

达到处理上限 = False

while not 达到处理上限:
    if not 当前页数据:
        await 上报("[扫描] 当前页未拦截到数据，尝试 JS fallback", 店铺ID)
        # fallback 到旧方法（保留兼容）
        break

    当前页记录 = []
    当前页订单号集合 = set()
    
    for 信息 in 当前页数据:
        if not 信息 or not 信息.get("订单号"):
            continue
        # 立即过滤不支持的类型
        售后类型 = str(信息.get("售后类型", ""))
        if any(类型 in 售后类型 for 类型 in 不支持自动处理类型):
            # 直接写入队列标记人工，不进详情页
            队列记录 = self._构建队列记录(信息, 批次ID, 店铺ID, 店铺名称)
            已有记录 = ...  # 去重检查
            if not 已有记录:
                记录ID = await self._队列服务.写入队列(队列记录)
                if 记录ID > 0:
                    await self._队列服务.标记人工(记录ID, f"{售后类型}不支持自动处理")
                    if bool(售后配置.get("飞书通知_启用", True)):
                        # 发飞书
                        ...
                    人工数 += 1
                    已处理总数 += 1
            continue
        
        队列记录 = self._构建队列记录(信息, 批次ID, 店铺ID, 店铺名称)
        当前页记录.append(队列记录)
        当前页订单号集合.add(str(队列记录["订单号"]))
    
    # 写入队列 + 处理（和现在逻辑一样）
    if 当前页记录:
        写入数 = await self._队列服务.批量写入队列(当前页记录)
        # ... 后续处理逻辑不变 ...
    
    if 达到处理上限:
        break
    
    # 翻页并拦截
    下一页数据 = await self._售后页.翻页并拦截()
    if 下一页数据 is None:
        break
    当前页数据 = 下一页数据
​
5) _构建队列记录() 适配
API 返回的字段名和之前 DOM 抓取的不同，需要兼容：
def _构建队列记录(self, 摘要, 批次ID, 店铺ID, 店铺名称):
    return {
        "batch_id": 批次ID,
        "shop_id": 店铺ID,
        "shop_name": 店铺名称,
        "订单号": 摘要.get("订单号", ""),
        "售后类型": 摘要.get("售后类型", ""),
        "售后状态": 摘要.get("售后状态", ""),
        "退款金额": self._提取金额(摘要.get("退款金额", "")),
        "商品名称": 摘要.get("商品名称", ""),
    }
​
由于 API 拦截已经把 退款金额 从分转成了元（float），_提取金额() 要兼容直接传入 float 的情况（现有代码已经支持）。
Part B：流程编排第二步投递修复
（和上一条消息中的 Codex 任务 2 完全一致，不重复了）
核心改动：tasks/执行任务.py 中，执行结果["status"] == "completed" 且 step_index < total_steps 时，投递 step_index + 1 的 Celery 任务。同样在 on_fail == "continue" 分支也要投递下一步。
测试验收
pytest tests/ 全量通过
启动售后任务，日志中应该看到 [售后页] API拦截抓取到 N 条售后单，而不是逐行的 [售后页] 第X行: ...
如果 API 拦截失败（比如 PDD 改接口），应该有 fallback 日志并走旧路径
2 步流程应该能自动推进到第二步