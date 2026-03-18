### 问题

导航到售后列表页时，浏览器会发出**多个**匹配 `/afterSales` 的 API 请求（投诉预警接口、主列表接口等），数量不固定。之前的"消耗"方案只消耗了其中一个，剩余的仍然被后续拦截器错误捕获。

### 修复方案

用 Playwright 的 `wait_for_load_state("networkidle")` 等待**所有**导航触发的网络请求完成后（500ms 无新请求），再注册拦截器。

### 修改文件

仅修改 `pages/售后页.py`

### 替换 `导航并拦截售后列表` 方法

```python
async def 导航并拦截售后列表(self) -> list[dict]:
    """导航到列表页，等待所有默认请求完成，再拦截待商家处理的请求。"""
    await self.导航到售后列表()

    # 等待所有导航触发的网络请求完成（500ms无新请求即视为idle）
    # 这会等待投诉预警、主列表、统计等所有默认接口返回完毕
    print("[售后页] 等待所有默认请求完成（networkidle）")
    try:
        await self.页面.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        # 超时也没关系，至少等了10秒，大部分请求应该已经完成
        print("[售后页] networkidle 超时，继续执行")
    print("[售后页] 网络已空闲，开始拦截")

    # 现在所有默认请求都已完成，注册全新的拦截器
    拦截任务 = asyncio.create_task(self.拦截售后列表API(超时秒=15))
    await asyncio.sleep(0.1)  # 确保 response 监听器注册完成

    # 点击"待商家处理"触发新的列表请求
    await self.确保待商家处理已选中(强制点击=True)
    结果 = await 拦截任务

    if not 结果:
        print("[售后页] 首次 API 拦截为空，重试")
        拦截任务 = asyncio.create_task(self.拦截售后列表API(超时秒=15))
        await asyncio.sleep(0.1)
        await self.确保待商家处理已选中(强制点击=True)
        结果 = await 拦截任务

    if not 结果:
        print("[售后页] API拦截失败，fallback到JS抓取")

    return 结果
```

### 同时修改 `导航到售后列表` 方法

将 `wait_until="domcontentloaded"` 保持不变（不要改成 `networkidle`，因为我们在 `导航并拦截售后列表` 中单独等待 `networkidle`，这样日志更清晰）。

### 同时修改 `翻页并拦截` 方法

翻页不需要 `networkidle`（翻页前没有多余请求），但把 `asyncio.sleep(0)` 改为 `asyncio.sleep(0.1)`，去掉 `仅待商家处理=True`：

```python
async def 翻页并拦截(self) -> list[dict] | None:
    if not await self._检查有下一页():
        return None

    拦截任务 = asyncio.create_task(self.拦截售后列表API(超时秒=15))
    await asyncio.sleep(0.1)
    翻页成功 = await self.翻页()
    if not 翻页成功:
        拦截任务.cancel()
        return None
    return await 拦截任务
```

### 清理

删除 `导航并拦截售后列表` 中所有旧的时序处理代码，包括：

- 删除 `asyncio.sleep(2)`
- 删除旧的"消耗"拦截调用
- 删除 `仅待商家处理=True` 参数传递（`拦截售后列表API` 方法本身不用改，保留 `仅待商家处理` 参数定义，只是调用时不再传它）

### 不要修改

- `tasks/售后任务.py`
- `selectors/售后页选择器.py`
- `backend/` 下所有文件
- `拦截售后列表API` 方法本身不需要改

### 预期日志

```
[售后页] 售后列表页加载完成: https://mms.pinduoduo.com/...
[售后页] 等待所有默认请求完成（networkidle）
[售后页] 网络已空闲，开始拦截
[售后页] 已点击待商家处理卡片
[售后页] API拦截抓取到 10 条售后单        ← 真正的待处理数据 ✅
[售后页] API拦截抓取到 4 条售后单         ← 翻页 ✅
[任务服务] 任务执行完成，结果: 扫描14单, 写入14单
```

### 验收标准

- [ ] "网络已空闲" 出现在 "已点击待商家处理卡片" **之前**
- [ ] "API拦截抓取到 N 条"（N > 0）出现在 "已点击待商家处理卡片" **之后**
- [ ] 不再出现 DOM fallback 逐行抓取
- [ ] 总扫描数 = 14（而非 24 或 34）