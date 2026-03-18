### Bug 1：API 拦截抓到了错误的数据

**文件**：`pages/售后页.py` 的 `导航并拦截售后列表` 方法

**问题**：当前流程是先导航到页面、再注册拦截、再点击"待商家处理"。但导航本身会触发一次默认的列表API请求，拦截器可能捕获的是这次默认请求的数据（"全部"状态），而不是点击"待商家处理"后的数据。

**修复方案**：改为以下流程：

```
1. 导航到售后列表页（不注册拦截）
2. 等待页面加载完成
3. 注册 API 拦截器（此时默认请求已经完成，不会被误捕获）
4. 点击"待商家处理"卡片（触发新的列表请求）
5. 等待拦截器捕获到新请求的数据
```

具体修改 `导航并拦截售后列表` 方法：

- 先调用 `导航到售后列表()`，等待页面完全加载（`await self.页面加载延迟()` 或额外等待 1-2 秒确保默认请求已返回）
- 然后再创建拦截任务 `asyncio.create_task(self.拦截售后列表API())`
- 紧接着点击"待商家处理" `await self.确保待商家处理已选中(强制点击=True)`
- 等待拦截结果

另外，在 `拦截售后列表API` 的 `_处理响应` 回调中，增加一个保护：忽略掉第一次拦截到的数据（在注册拦截器之后、点击待商家处理之前可能还有残余的默认请求响应），或者通过检查响应 URL 参数中是否包含表示"待商家处理"状态的筛选参数来过滤。

### Bug 2：翻页选择器已过时

**文件**：`selectors/售后页选择器.py`

**问题**：当前翻页选择器使用 `ant-pagination` 类名，但拼多多已更换为 Beast Core 分页组件。

**实际 HTML 结构**（从页面提取）：

```html
<ul data-testid="beast-core-pagination" class="PGT_outerWrapper_5-163-0">
  <li data-testid="beast-core-pagination-prev" class="PGT_prev_5-163-0 PGT_disabled_5-163-0">...</li>
  <li class="PGT_pagerItem_5-163-0 PGT_pagerItemActive_5-163-0">1</li>
  <li class="PGT_pagerItem_5-163-0">2</li>
  <li data-testid="beast-core-pagination-next" class="PGT_next_5-163-0">...</li>
</ul>
```

**修复**：更新 `下一页按钮` 选择器：

```python
下一页按钮 = 选择器配置(
    主选择器='//li[@data-testid="beast-core-pagination-next"]',
    备选选择器=[
        "//li[contains(@class, 'PGT_next')]",
        "//li[contains(@class, 'ant-pagination-next')]",  # 保留旧版兜底
    ],
)
```

同时，`pages/售后页.py` 的 `_检查有下一页` 方法中，判断禁用状态的逻辑需要更新。旧逻辑检查 `aria-disabled` 和 class 中的 `disabled`，但新的 Beast Core 组件使用 `PGT_disabled` 类名表示禁用：

```html
<!-- 禁用状态 -->
<li data-testid="beast-core-pagination-prev" class="PGT_prev_5-163-0 PGT_disabled_5-163-0">

<!-- 可用状态 -->
<li data-testid="beast-core-pagination-next" class="PGT_next_5-163-0">
```

修改 `_检查有下一页` 方法：除了检查 `aria-disabled` 和 `disabled`，还要检查 class 中是否包含 `PGT_disabled`。

### 不要修改的部分

- 保持每页 10 条的默认设置，不改为 100 条
- 不修改 `售后任务.py` 的流程逻辑（此任务只修 POM 层和选择器层）
- 不修改 `售后队列服务.py`

### 验收标准

- [ ] 导航到售后列表后，API 拦截到的数据确实是"待商家处理"状态的售后单
- [ ] 不会误捕获导航时默认加载的"全部"列表数据
- [ ] 翻页按钮能被正确定位到
- [ ] 禁用状态（最后一页）能被正确识别，不会死循环翻页
- [ ] 翻页后能继续拦截下一页的 API 数据