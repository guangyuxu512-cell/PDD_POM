### 问题

`翻页并拦截` 点击下一页按钮后，`批量抓取当前页` 立即执行 `wait_for_selector('div[class*="after-sales-table_order_item"]')`，但旧页面的行还在 DOM 里，所以 `wait_for_selector` 立刻通过，`sleep(0.5)` 不够等新数据渲染，导致抓到的仍然是上一页的数据。

### 修改文件

仅修改 `pages/售后页.py`

### 修改方法：`翻页并拦截`

翻页前先记录当前页第一行的订单号，翻页后轮询等待第一行订单号变化（说明新数据已渲染），再调用批量抓取：

```python
async def 翻页并拦截(self) -> list[dict] | None:
    """翻到下一页，等待DOM刷新，再批量抓取。返回 None 表示没有下一页。"""
    if not await self._检查有下一页():
        return None

    # 记录翻页前第一行的订单号
    旧首行订单号 = await self.页面.evaluate(
        """
        () => {
            const 首行 = document.querySelector('div[class*="after-sales-table_order_item"]');
            if (!首行) return '';
            const 订单节点 = 首行.querySelector('[class*="table-item-header_sn__"]');
            return 订单节点 ? 订单节点.textContent.trim() : '';
        }
        """
    )

    翻页成功 = await self.翻页()
    if not 翻页成功:
        return None

    # 等待DOM刷新：轮询直到第一行订单号变化，或超时5秒
    for _ in range(25):  # 25次 × 0.2秒 = 5秒
        await asyncio.sleep(0.2)
        当前首行订单号 = await self.页面.evaluate(
            """
            () => {
                const 首行 = document.querySelector('div[class*="after-sales-table_order_item"]');
                if (!首行) return '';
                const 订单节点 = 首行.querySelector('[class*="table-item-header_sn__"]');
                return 订单节点 ? 订单节点.textContent.trim() : '';
            }
            """
        )
        if 当前首行订单号 and 当前首行订单号 != 旧首行订单号:
            print(f"[售后页] 翻页DOM已刷新: {旧首行订单号} → {当前首行订单号}")
            break
    else:
        print("[售后页] 翻页DOM刷新超时，可能已到最后一页")
        return None

    return await self.批量抓取当前页()
```

### 不要修改

- `导航并拦截售后列表` 方法 — 不改（第一页不需要等刷新）
- `批量抓取当前页` 方法 — 不改
- `tasks/售后任务.py` — 不改
- `selectors/售后页选择器.py` — 不改
- `backend/` 下所有文件 — 不改

### 预期日志

```
[售后页] 已点击待商家处理卡片
[售后页] DOM批量抓取到 10 条售后单
[售后页] 翻页DOM已刷新: 260315-201662164532207 → 260319-xxxxxxxxx
[售后页] DOM批量抓取到 4 条售后单
[任务服务] 任务执行完成，结果: 扫描14单, 写入14单
```

如果待商家处理只有 1 页（≤10条），翻页后 DOM 不会变化，5 秒超时后返回 None，循环正常结束。

### 验收标准

- [ ] 翻页后不再抓到与上一页相同的数据
- [ ] 日志显示 "翻页DOM已刷新" 及新旧订单号变化
- [ ] 如果是最后一页，显示 "翻页DOM刷新超时" 并正常结束
- [ ] 总扫描数 = 实际待处理售后单数