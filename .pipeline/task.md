#### **Step 1：`selectors/售后页选择器.py` — 新增待处理数量选择器**

**文件**：`selectors/售后页选择器.py`

**具体修改**：在 `待商家处理卡片` 下方新增：

```python
# 新增：待商家处理数量 span（卡片内的数字 badge）
待商家处理数量 = 选择器配置(
    主选择器='//span[text()="待商家处理"]/following-sibling::span[contains(@class, "count")]',
    备选选择器=[
        '//span[text()="待商家处理"]/parent::div//span[contains(@class, "MmsUiQuickFilter___count")]',
        '//div[@data-testid="beast-core-card"]//span[text()="待商家处理"]/following-sibling::span',
    ],
)

# 新增：投诉预警卡片（用于判断当前是否在投诉预警 tab）
投诉预警卡片 = 选择器配置(
    主选择器='//span[text()="投诉预警"]/ancestor::div[@data-testid="beast-core-card"]',
    备选选择器=[
        '//span[contains(., "投诉预警")]/ancestor::div[@data-testid="beast-core-card"]',
    ],
)

投诉预警选中类名片段 = "CAD_beastCardChecked"
```

**验收**：`售后页选择器.待商家处理数量.所有选择器()` 返回 3 个选择器字符串。

---

#### **Step 2：`pages/售后页.py` — 新增 `获取待处理数量从卡片()`**

**文件**：`pages/售后页.py`

**新增方法**（放在 `确保待商家处理已选中` 之前）：

```python
async def 获取待处理数量从卡片(self) -> int:
    """从「待商家处理」卡片上的数字 badge 读取待处理总数。"""
    await self.操作前延迟()
    数量 = await self.页面.evaluate(
        """
        () => {
            // 策略1: 找到 "待商家处理" 文本节点的兄弟 span
            const allSpans = Array.from(document.querySelectorAll('span'));
            const label = allSpans.find(s => s.textContent.trim() === '待商家处理');
            if (label) {
                const parent = label.parentElement;
                if (parent) {
                    const countSpan = parent.querySelector('span[class*="count"]');
                    if (countSpan) {
                        const num = parseInt(countSpan.textContent.trim(), 10);
                        if (!isNaN(num)) return num;
                    }
                }
                // 策略2: 紧邻的下一个兄弟 span
                const sibling = label.nextElementSibling;
                if (sibling && sibling.tagName === 'SPAN') {
                    const num = parseInt(sibling.textContent.trim(), 10);
                    if (!isNaN(num)) return num;
                }
            }
            // 策略3: 遍历所有 beast-core-card
            const cards = document.querySelectorAll('div[data-testid="beast-core-card"]');
            for (const card of cards) {
                if (card.textContent.includes('待商家处理')) {
                    const countSpan = card.querySelector('span[class*="count"]');
                    if (countSpan) {
                        const num = parseInt(countSpan.textContent.trim(), 10);
                        if (!isNaN(num)) return num;
                    }
                }
            }
            return 0;
        }
        """
    )
    结果 = int(数量 or 0)
    print(f"[售后页] 待商家处理数量: {结果}")
    return 结果
```

**验收**：在页面有 14 条待处理时，返回 `14`。

---

#### **Step 3：`pages/售后页.py` — 重写 `确保待商家处理已选中()`**

**问题**：当前方法只判断「待商家处理」是否选中，但默认可能落在「投诉预警」，需要先判断投诉预警是否选中再决定是否点击。

**替换整个方法**：

```python
async def 确保待商家处理已选中(self, 强制点击: bool = False) -> None:
    """确保「待商家处理」卡片处于选中态。默认页面可能在「投诉预警」。"""
    await self.操作前延迟()

    # 第一步: 用 JS 一次性检查当前选中的是哪个卡片
    当前状态 = await self.页面.evaluate(
        """
        () => {
            const cards = Array.from(
                document.querySelectorAll('div[data-testid="beast-core-card"]')
            );
            let 待商家处理卡片 = null;
            let 待商家处理已选中 = false;

            for (const card of cards) {
                const text = card.textContent || '';
                if (text.includes('待商家处理')) {
                    待商家处理卡片 = card;
                    待商家处理已选中 = (card.className || '').includes('CAD_beastCardChecked');
                    break;
                }
            }
            return {
                找到卡片: Boolean(待商家处理卡片),
                已选中: 待商家处理已选中,
            };
        }
        """
    )

    if not 当前状态 or not 当前状态.get("找到卡片"):
        raise RuntimeError("未找到「待商家处理」卡片，页面可能未正确加载")

    if 当前状态.get("已选中") and not 强制点击:
        print("[售后页] 待商家处理卡片已选中，无需操作")
        return

    # 需要点击：用 JS 直接点击，避免选择器漂移
    点击成功 = await self.页面.evaluate(
        """
        () => {
            const cards = Array.from(
                document.querySelectorAll('div[data-testid="beast-core-card"]')
            );
            for (const card of cards) {
                if ((card.textContent || '').includes('待商家处理')) {
                    card.click();
                    return true;
                }
            }
            return false;
        }
        """
    )

    if not 点击成功:
        raise RuntimeError("点击「待商家处理」卡片失败")

    await self.页面加载延迟()

    # 验证点击后确实选中了
    验证 = await self.页面.evaluate(
        """
        () => {
            const cards = Array.from(
                document.querySelectorAll('div[data-testid="beast-core-card"]')
            );
            for (const card of cards) {
                if ((card.textContent || '').includes('待商家处理')) {
                    return (card.className || '').includes('CAD_beastCardChecked');
                }
            }
            return false;
        }
        """
    )

    if not 验证:
        print("[售后页] 警告: 点击后「待商家处理」仍未选中，可能需要重试")
    else:
        print("[售后页] 已成功切换到「待商家处理」")
```

---

#### **Step 4：`pages/售后页.py` — 重写 `批量抓取当前页()`**

**问题**：

- `wait_for_selector` 超时即返回空，没有重试
- 列索引硬编码 `所有列[4]`、`所有列[7]` 等可能因 DOM 结构变化偏移

**替换整个方法**：

```python
async def 批量抓取当前页(self, 最大重试: int = 3) -> list[dict]:
    """一次 JS evaluate 批量抓取当前页所有售后单行，带重试。"""
    await self.操作前延迟()

    for 尝试次数 in range(最大重试):
        try:
            await self.页面.wait_for_selector(
                'div[class*="after-sales-table_order_item"]',
                timeout=8000,
            )
            break
        except Exception:
            if 尝试次数 < 最大重试 - 1:
                print(f"[售后页] 第{尝试次数+1}次等待售后单行超时，重试...")
                await asyncio.sleep(1)
            else:
                print("[售后页] 未检测到售后单行，当前页可能为空")
                return []

    await asyncio.sleep(0.8)  # 等待渲染完整

    结果 = await self.页面.evaluate(
        """
        () => {
            const 清洗 = (v) => String(v || '').replace(/\\s+/g, ' ').trim();
            const 所有行 = document.querySelectorAll(
                'div[class*="after-sales-table_order_item"]'
            );
            const 结果列表 = [];

            for (let i = 0; i < 所有行.length; i++) {
                const 行 = 所有行[i];

                // === 头部信息 ===
                const 订单号节点 = 行.querySelector('[class*="table-item-header_sn"]');
                const 订单号 = 清洗(订单号节点 ? 订单号节点.textContent : '');
                if (!订单号) continue;

                const 申请时间节点 = 行.querySelector(
                    '[class*="table-item-header_apply_time"] span'
                );
                const 剩余时间节点 = 行.querySelector('[class*="table-item-header_time"]');

                // === 列单元格 ===
                const 所有列 = Array.from(
                    行.querySelectorAll('[class*="after-sales-table_item_cell"]')
                );

                // 用语义化方式读取列，而非硬编码索引
                // 遍历所有列，按内容特征识别
                let 商品名称 = '', 商品规格 = '', 实收金额 = '', 退款金额 = '';
                let 发货状态 = '', 售后类型 = '', 售后状态 = '';
                let 售后协商 = '', 售后原因 = '';
                let 操作按钮 = [];

                // 第0列: 商品信息
                if (所有列[0]) {
                    const main = 所有列[0].querySelector('[class*="order-info_main"]');
                    const sub = 所有列[0].querySelector('[class*="order-info_sub"]');
                    商品名称 = 清洗(main ? main.textContent : '');
                    商品规格 = 清洗(sub ? sub.textContent : '');
                }

                // 第1列: 金额
                if (所有列[1]) {
                    const dotted = 所有列[1].querySelector('[class*="amount_dotted"]');
                    const refund = 所有列[1].querySelector('[class*="amount_refund"]');
                    实收金额 = 清洗(dotted ? dotted.textContent : '');
                    退款金额 = 清洗(refund ? refund.textContent : '');
                }

                // 第2-6列: 纯文本列
                const 读列 = (idx) => idx < 所有列.length ? 清洗(所有列[idx].textContent) : '';
                发货状态 = 读列(2);
                售后类型 = 读列(3);

                // 第4列: 售后状态（取第一个 div）
                if (所有列[4]) {
                    const div = 所有列[4].querySelector('div');
                    售后状态 = 清洗(div ? div.textContent : 读列(4));
                }

                售后协商 = 读列(5);
                售后原因 = 读列(6);

                // 最后一列: 操作按钮
                const 操作列 = 所有列[所有列.length - 1];
                if (操作列) {
                    操作按钮 = Array.from(
                        操作列.querySelectorAll('a span, button span')
                    )
                        .map(n => 清洗(n.textContent))
                        .filter(t => t.length > 0 && t.length < 20);
                }

                结果列表.push({
                    订单号,
                    申请时间: 清洗(申请时间节点 ? 申请时间节点.textContent : ''),
                    剩余处理时间: 清洗(剩余时间节点 ? 剩余时间节点.textContent : ''),
                    商品名称,
                    商品规格,
                    实收金额,
                    退款金额,
                    发货状态,
                    售后类型,
                    售后状态,
                    售后协商,
                    售后原因,
                    操作按钮,
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
```

---

#### **Step 5：`pages/售后页.py` — 重写 `翻页并拦截()` → 重命名为 `翻页并抓取()`**

**问题**：方法名叫"拦截"但实际不拦截 API。DOM 刷新检测轮询 25 次太保守。

**替换整个方法**：

```python
async def 翻页并抓取(self) -> list[dict] | None:
    """翻到下一页，等待 DOM 刷新，再批量抓取。返回 None 表示没有下一页。"""
    if not await self._检查有下一页():
        return None

    # 记录翻页前首行订单号
    旧首行订单号 = await self.页面.evaluate(
        """
        () => {
            const row = document.querySelector('div[class*="after-sales-table_order_item"]');
            if (!row) return '';
            const sn = row.querySelector('[class*="table-item-header_sn"]');
            return sn ? sn.textContent.trim() : '';
        }
        """
    )

    翻页成功 = await self.翻页()
    if not 翻页成功:
        return None

    # 轮询等待 DOM 刷新：首行订单号变化 或 行数变化
    for i in range(40):  # 最多等 8 秒
        await asyncio.sleep(0.2)
        当前首行订单号 = await self.页面.evaluate(
            """
            () => {
                const row = document.querySelector('div[class*="after-sales-table_order_item"]');
                if (!row) return '';
                const sn = row.querySelector('[class*="table-item-header_sn"]');
                return sn ? sn.textContent.trim() : '';
            }
            """
        )
        if 当前首行订单号 and 当前首行订单号 != 旧首行订单号:
            print(f"[售后页] 翻页DOM已刷新: {旧首行订单号} → {当前首行订单号}")
            break
    else:
        print("[售后页] 翻页DOM刷新超时，尝试继续抓取")

    return await self.批量抓取当前页()
```

同时保留旧的 `翻页并拦截` 作为别名：

```python
# 向后兼容
翻页并拦截 = 翻页并抓取
```

---

#### **Step 6：`pages/售后页.py` — 重写 `导航并拦截售后列表()` → 重命名为 `导航并抓取售后列表()`**

**替换整个方法**：

```python
async def 导航并抓取售后列表(self) -> tuple[list[dict], int]:
    """
    导航到售后列表页 → 点击待商家处理 → 抓取第一页。
    返回 (第一页数据列表, 待处理总数)。
    """
    await self.导航到售后列表()

    # 先获取待处理总数
    待处理总数 = await self.获取待处理数量从卡片()

    # 确保在「待商家处理」Tab
    await self.确保待商家处理已选中(强制点击=True)

    # 等待列表加载
    await asyncio.sleep(1)

    # 抓取第一页
    第一页数据 = await self.批量抓取当前页()

    return 第一页数据, 待处理总数

# 向后兼容
async def 导航并拦截售后列表(self) -> list[dict]:
    数据, _ = await self.导航并抓取售后列表()
    return 数据
```

---

#### **Step 7：`backend/models/售后队列模型.py` — 新增 `(shop_id, 订单号)` 去重索引**

**文件**：`backend/models/售后队列模型.py`

**新增**：

```python
售后队列店铺订单去重索引SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_aftersale_queue_shop_order_unique
ON aftersale_queue (shop_id, 订单号);
"""
```

**修改 `初始化售后队列表()`**：在 `售后队列去重索引SQL` 执行之后，追加执行：

```python
await 连接.execute(售后队列店铺订单去重索引SQL)
```

> ⚠️ **注意**：如果已有数据中存在 `(shop_id, 订单号)` 重复行，创建唯一索引会失败。需要先清理：
> 

> 
> 

> `sql
> 

> DELETE FROM aftersale_queue
> 

> WHERE id NOT IN (
> 

> SELECT MIN(id) FROM aftersale_queue GROUP BY shop_id, 订单号
> 

> );
> 

> `
> 

---

#### **Step 8：`backend/services/售后队列服务.py` — 修复去重逻辑**

**修改 `_查询订单记录()`**：

```python
async def _查询订单记录(
    self,
    连接: aiosqlite.Connection,
    订单号: str,
    shop_id: str = "",
) -> aiosqlite.Row | None:
    """查询订单是否已存在（以 shop_id + 订单号 去重）。"""
    条件 = "WHERE 订单号 = ?"
    参数: list = [订单号]
    if shop_id:
        条件 += " AND shop_id = ?"
        参数.append(shop_id)

    async with 连接.execute(
        f"""
        SELECT id, batch_id, shop_id, 当前阶段
        FROM aftersale_queue
        {条件}
        ORDER BY id DESC
        LIMIT 1
        """,
        参数,
    ) as 游标:
        return await 游标.fetchone()
```

**修改 `批量写入队列()`** 中的调用：

```python
已有记录 = await self._查询订单记录(连接, 订单号, 数据["shop_id"])
```

**同样修改 `写入队列()`**：

```python
已有记录 = await self._查询订单记录(连接, 数据["订单号"], 数据["shop_id"])
```

---

#### **Step 9：`tasks/售后任务.py` — 重写 `执行()` 方法**

**替换 `执行()` 方法**：

```python
@自动回调("售后处理")
async def 执行(self, 页面, 店铺配置: dict) -> str:
    店铺ID = str(店铺配置.get("shop_id", "") or "").strip()
    店铺名称 = str(店铺配置.get("shop_name", "") or "").strip()
    self._售后页 = 售后页(页面)

    try:
        await 上报("[扫描] 开始扫描售后列表", 店铺ID)
        批次ID = await self._队列服务.创建批次(店铺ID)

        # Step 1: 导航 + 获取待处理总数 + 点击待商家处理 + 抓取第一页
        当前页数据, 待处理总数 = await self._售后页.导航并抓取售后列表()

        总页数 = max(1, -(-待处理总数 // 10))  # 向上取整
        await 上报(
            f"[扫描] 待处理 {待处理总数} 单，预计 {总页数} 页",
            店铺ID,
        )

        页码 = 1
        总扫描数 = 0
        总写入数 = 0
        已扫描订单号集合: set[str] = set()
        连续空页计数 = 0

        while True:
            # 构建队列记录
            队列记录列表 = self._构建当前页队列记录列表(
                当前页数据, 批次ID, 店铺ID, 店铺名称,
            )

            if not 队列记录列表:
                连续空页计数 += 1
                if 页码 == 1:
                    await 上报("[完成] 无待处理售后单", 店铺ID)
                    return "无待处理售后单"
                if 连续空页计数 >= 2:
                    await 上报(f"[扫描] 连续{连续空页计数}页为空，结束", 店铺ID)
                    break
                # 可能是翻页渲染延迟，继续尝试翻页
            else:
                连续空页计数 = 0

            # 检查是否全部已扫描
            当前页订单号集合 = {
                str(r.get("订单号", "") or "").strip()
                for r in 队列记录列表
                if str(r.get("订单号", "") or "").strip()
            }
            新订单数 = len(当前页订单号集合 - 已扫描订单号集合)
            已扫描订单号集合.update(当前页订单号集合)

            if 新订单数 == 0 and 队列记录列表:
                await 上报(f"[扫描] 第{页码}页全部已扫描，停止", 店铺ID)
                break

            # 写入数据库
            写入数 = await self._队列服务.批量写入队列(队列记录列表)
            总扫描数 += len(队列记录列表)
            总写入数 += 写入数
            await 上报(
                f"[扫描] 第{页码}/{总页数}页 "
                f"扫描{len(队列记录列表)}单(新{新订单数})，写入{写入数}单",
                店铺ID,
            )

            # 翻页
            下一页数据 = await self._售后页.翻页并抓取()
            if 下一页数据 is None:
                break
            当前页数据 = 下一页数据
            页码 += 1

        汇总 = f"扫描{总扫描数}单, 写入{总写入数}单, {页码}页"
        await 上报(f"[完成] {汇总}", 店铺ID)
        return 汇总
    except Exception as 异常:
        await 上报(f"[失败] 售后任务异常: {异常}", 店铺ID)
        return f"失败: {异常}"
```

---

### 5) 验收标准

| # | 验收项 | 方法 |
| --- | --- | --- |
| 1 | 导航到售后页后能正确读取待处理数量 | `获取待处理数量从卡片()` 返回 > 0 |
| 2 | 默认在「投诉预警」时能自动切换到「待商家处理」 | 日志打印 "已成功切换到「待商家处理」" |
| 3 | 第一页抓取到 ≤ 10 条数据 | `批量抓取当前页()` 返回列表 len ≤ 10 |
| 4 | 每条数据包含完整字段（订单号、售后类型、退款金额等） | 检查返回 dict 的 key 完整性 |
| 5 | 翻页后首行订单号变化 | 日志打印 "翻页DOM已刷新" |
| 6 | 同一 `(shop_id, 订单号)` 不重复写入 | 第二次运行写入数 = 0 |
| 7 | 全部页扫描完后返回正确汇总 | 返回字符串包含 "扫描N单, 写入M单" |

### 6) 风险与注意事项

| 风险 | 应对 |
| --- | --- |
| `(shop_id, 订单号)` 唯一索引创建失败（已有重复数据） | 先执行去重 DELETE SQL，再创建索引 |
| 拼多多前端改版，class 名变化 | 所有选择器使用 `contains` 模糊匹配，降低脆性 |
| 翻页后 DOM 刷新慢 | 轮询 40 次 × 0.2s = 最多等 8 秒，足够覆盖 |
| 批量抓取 JS 报错 | 加了 `最大重试=3`，每次重试间隔 1s |
| 向后兼容性 | `导航并拦截售后列表` 和 `翻页并拦截` 保留为别名 |

---

### ✅ 检查清单

- [ ]  **安全**：无敏感数据泄露，SQLite 参数化查询防注入
- [ ]  **边界**：空列表、0 条待处理、只有 1 页、翻页超时均有处理
- [ ]  **去重**：`(shop_id, 订单号)` 唯一索引 + 写入前查询双重保障
- [ ]  **测试**：可单独运行 `售后页.批量抓取当前页()` 验证 DOM 抓取
- [ ]  **日志**：每步关键操作均有 `print` 日志输出
- [ ]  **回滚**：所有改动都是新增/替换方法，不影响其他模块；唯一索引用 `IF NOT EXISTS`