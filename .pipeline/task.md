Codex 任务：售后列表全部改为 DOM 批量抓取，废弃 API 拦截
背景
API 拦截方案因为导航时多个默认请求的时序问题，始终无法可靠工作。DOM 抓取每次都正确。现在改为全部使用 DOM 批量抓取（一次 JS evaluate 抓取当前页所有行），不再使用 API 拦截。
修改文件
pages/售后页.py
tasks/售后任务.py
一、pages/售后页.py 修改
1) 新增方法：批量抓取当前页
在 确保待商家处理已选中 方法之后，新增以下方法。用一次 page.evaluate 调用抓取当前页所有售后单行：
async def 批量抓取当前页(self) -> list[dict]:
    """一次 JS evaluate 批量抓取当前页所有售后单行。"""
    await self.操作前延迟()

    # 先等待至少一行渲染出来
    try:
        await self.页面.wait_for_selector(
            'div[class*="after-sales-table_order_item"]',
            timeout=8000,
        )
    except Exception:
        print("[售后页] 未检测到售后单行，当前页可能为空")
        return []

    # 额外等待确保所有行渲染完成（翻页后 DOM 可能还在更新）
    await asyncio.sleep(0.5)

    结果 = await self.页面.evaluate(
        """
        () => {
            const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
            const 所有行 = document.querySelectorAll(
                'div[class*="after-sales-table_order_item"]'
            );
            const 结果列表 = [];
            for (let i = 0; i < 所有行.length; i++) {
                const 行 = 所有行[i];

                const 订单号节点 = 行.querySelector('[class*="table-item-header_sn__"]');
                const 订单号 = 清洗(订单号节点 ? 订单号节点.textContent : '');
                if (!订单号) continue;

                const 申请时间节点 = 行.querySelector(
                    '[class*="table-item-header_apply_time"] span'
                );
                const 剩余时间节点 = 行.querySelector('[class*="table-item-header_time__"]');

                const 所有列 = 行.querySelectorAll('[class*="after-sales-table_item_cell"]');
                const 读列 = (索引) => {
                    if (索引 >= 所有列.length) return '';
                    return 清洗(所有列[索引].textContent);
                };

                const 商品名节点 = 所有列[0]
                    ? 所有列[0].querySelector('[class*="order-info_main"]')
                    : null;
                const 规格节点 = 所有列[0]
                    ? 所有列[0].querySelector('[class*="order-info_sub"]')
                    : null;
                const 实收节点 = 所有列[1]
                    ? 所有列[1].querySelector('[class*="amount_dotted"]')
                    : null;
                const 退款节点 = 所有列[1]
                    ? 所有列[1].querySelector('[class*="amount_refund"]')
                    : null;
                const 售后状态节点 = 所有列[4] ? 所有列[4].querySelector('div') : null;
                const 操作按钮 = 所有列[7]
                    ? Array.from(所有列[7].querySelectorAll('a span, button span'))
                          .map((节点) => 清洗(节点.textContent))
                          .filter((文本) => 文本.length > 0)
                    : [];

                结果列表.push({
                    订单号: 订单号,
                    申请时间: 清洗(申请时间节点 ? 申请时间节点.textContent : ''),
                    剩余处理时间: 清洗(剩余时间节点 ? 剩余时间节点.textContent : ''),
                    商品名称: 清洗(商品名节点 ? 商品名节点.textContent : ''),
                    商品规格: 清洗(规格节点 ? 规格节点.textContent : ''),
                    实收金额: 清洗(实收节点 ? 实收节点.textContent : ''),
                    退款金额: 清洗(退款节点 ? 退款节点.textContent : ''),
                    发货状态: 清洗(读列(2)),
                    售后类型: 清洗(读列(3)),
                    售后状态: 清洗(售后状态节点 ? 售后状态节点.textContent : ''),
                    售后协商: 清洗(读列(5)),
                    售后原因: 清洗(读列(6)),
                    操作按钮: 操作按钮,
                });
            }
            return 结果列表;
        }
        """
    )
    await self.操作后延迟()

    列表 = list(结果 or [])
    print(f"[售后页] DOM批量抓取到 {len(列表)} 条售后单")
    return 列表
​
2) 替换 导航并拦截售后列表 方法
async def 导航并拦截售后列表(self) -> list[dict]:
    """导航到售后列表页，点击待商家处理，批量抓取第一页。"""
    await self.导航到售后列表()
    await self.确保待商家处理已选中(强制点击=True)
    return await self.批量抓取当前页()
​
3) 替换 翻页并拦截 方法
不再用 API 拦截，改为翻页后 DOM 批量抓取：
async def 翻页并拦截(self) -> list[dict] | None:
    """翻到下一页并批量抓取。返回 None 表示没有下一页。"""
    if not await self._检查有下一页():
        return None

    翻页成功 = await self.翻页()
    if not 翻页成功:
        return None

    return await self.批量抓取当前页()
​
4) 可选清理
以下方法不再被调用，可以删除（或保留备用，但建议删除以减少混淆）：
拦截售后列表API — 不再使用
_响应URL是否待商家处理 — 不再使用
_列表数据是否待商家处理 — 不再使用
_转换分转元 — 不再使用（API 数据转换用的）
_转换整数 — 不再使用
切换待处理 — 从未使用
扫描所有待处理 — 旧方法，已废弃
不要删除 获取第N行信息 和 获取售后单数量，后续 Step 可能还会用。
二、tasks/售后任务.py 修改
因为 导航并拦截售后列表 和 翻页并拦截 现在都直接返回 DOM 数据，不再需要 DOM fallback 逻辑。
替换 执行 方法中的 while 循环部分：
@自动回调("售后处理")
async def 执行(self, 页面, 店铺配置: dict) -> str:
    店铺ID = str(店铺配置.get("shop_id", "") or "").strip()
    店铺名称 = str(店铺配置.get("shop_name", "") or "").strip()
    self._售后页 = 售后页(页面)

    try:
        await 上报("[扫描] 开始扫描售后列表", 店铺ID)
        批次ID = await self._队列服务.创建批次(店铺ID)

        # 导航 + 点击待商家处理 + 抓取第一页
        当前页数据 = await self._售后页.导航并拦截售后列表()

        页码 = 1
        总扫描数 = 0
        总写入数 = 0

        while True:
            队列记录列表 = self._构建当前页队列记录列表(
                当前页数据,
                批次ID,
                店铺ID,
                店铺名称,
            )
            if not 队列记录列表:
                if 页码 == 1:
                    await 上报("[完成] 无待处理售后单", 店铺ID)
                    return "无待处理售后单"
                break

            写入数 = await self._队列服务.批量写入队列(队列记录列表)
            总扫描数 += len(队列记录列表)
            总写入数 += 写入数
            await 上报(
                f"[扫描] 第{页码}页 扫描{len(队列记录列表)}单，写入{写入数}单",
                店铺ID,
            )

            下一页数据 = await self._售后页.翻页并拦截()
            if 下一页数据 is None:
                break
            当前页数据 = 下一页数据
            页码 += 1

        汇总 = f"扫描{总扫描数}单, 写入{总写入数}单"
        await 上报(f"[完成] {汇总}", 店铺ID)
        return 汇总
    except Exception as 异常:
        await 上报(f"[失败] 售后任务异常: {异常}", 店铺ID)
        return f"失败: {异常}"
​
同时删除 _收集当前页DOM摘要 方法，因为不再需要了。
不要修改
selectors/售后页选择器.py
backend/ 下所有文件
预期日志
[售后页] 售后列表页加载完成: https://mms.pinduoduo.com/...
[售后页] 已点击待商家处理卡片
[售后页] DOM批量抓取到 10 条售后单
[扫描] 第1页 扫描10单，写入10单
[售后页] DOM批量抓取到 4 条售后单
[扫描] 第2页 扫描4单，写入4单
[任务服务] 任务执行完成，结果: 扫描14单, 写入14单
​
验收标准
[ ] 不再出现 "API拦截抓取到" 的日志
[ ] 不再出现逐行 "第X行: 订单=..." 的日志
[ ] 每页只有一条 "DOM批量抓取到 N 条售后单" 的汇总日志
[ ] 总扫描数 = 14（10 + 4）
[ ] 没有重复扫描