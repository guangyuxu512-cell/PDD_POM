## Task 27：浏览器最大化修复 + 浏览器复用修复 + 批次完成自动创建限时限量记录

### 涉及文件

- 改动：`browser/管理器.py`
- 改动：`backend/services/任务服务.py`
- 改动：`backend/services/任务参数服务.py`
- 改动：`tasks/发布相似商品任务.py`

### 功能 1：浏览器最大化修复

文件：`browser/管理器.py`

当前 `打开店铺` 方法的 `launch_persistent_context` 调用已有 `viewport: None` 和 `--start-maximized`，但浏览器窗口仍然不是最大化。

修改：在 `launch_persistent_context` 调用时增加 `no_viewport=True` 参数。

```python
浏览器上下文 = await self.playwright实例.chromium.launch_persistent_context(
    用户目录,
    no_viewport=True,
    **启动参数
)
```

同时确保 `启动参数` 中的 `viewport` 值为 `None`（已有），`args` 列表中包含 `--start-maximized`（已有）。

### 功能 2：浏览器复用修复

问题：任务执行后调用 `关闭当前标签页()`，如果浏览器只有一个标签页，关掉后 context 的 pages 为空。下一个任务通过 `获取页面(shop_id)` 拿到的是旧的已关闭页面对象，导致 `Target page, context or browser has been closed` 错误。

文件：`browser/管理器.py`

修改 `获取页面` 方法：获取页面时检查页面是否已关闭，如果已关闭则自动创建新页面。

```python
def 获取页面(self, 店铺ID: str) -> Page:
    if 店铺ID not in self.实例集:
        raise RuntimeError(f"店铺 {店铺ID} 未启动")

    实例 = self.实例集[店铺ID]
    页面 = 实例["页面"]
    浏览器 = 实例["浏览器"]

    # 检查页面是否仍然有效
    if 页面.is_closed():
        # 尝试从现有页面列表获取
        现有页面 = 浏览器.pages
        if 现有页面:
            页面 = 现有页面[0]
        else:
            # 所有页面都关了，创建新页面（这是异步的，需要特殊处理）
            raise RuntimeError(f"店铺 {店铺ID} 所有页面已关闭，需要重新打开")
        实例["页面"] = 页面
        实例["page"] = 页面
        print(f"✓ 店铺 {店铺ID} 页面已刷新")

    return 页面
```

但因为 `获取页面` 是同步方法，无法调用 `await new_page()`。所以还需要改 `任务服务.py`。

文件：`backend/services/任务服务.py`

在 `统一执行任务` 方法中，获取页面后增加有效性检查：

在 `页面 = 管理器实例.获取页面(shop_id)` 之后，加：

```python
# 检查页面是否有效，无效则从 context 获取或创建新页面
if 页面.is_closed():
    浏览器上下文 = 管理器实例.实例集[shop_id]["浏览器"]
    现有页面 = 浏览器上下文.pages
    if 现有页面:
        页面 = 现有页面[0]
    else:
        页面 = await 浏览器上下文.new_page()
    管理器实例.实例集[shop_id]["页面"] = 页面
    管理器实例.实例集[shop_id]["page"] = 页面
    print(f"[任务服务] 页面已刷新: {页面}")
```

文件：`tasks/发布相似商品任务.py`

在 `_安全截图并关闭` 方法中，`关闭当前标签页` 改为只关闭**新弹出的标签页**（发布页），不关闭主页面。当前代码已经是这样做的（只关发布页对象），但要确保 `商品列表对象.切回前台()` 能正确切换回主页面。如果主页面也被关闭了，需要创建新页面并导航到商品列表。

### 功能 3：批次完成后自动创建限时限量记录

文件：`backend/services/任务参数服务.py`

新增方法：

```python
async def 批次完成后创建后续任务(self, batch_id: str) -> int:
    """当一个批次的发布相似商品全部执行完毕后，自动创建限时限量记录。
    
    条件：
    - 同批次中存在 task_name='发布相似商品' 且 status='success' 的记录
    - 同批次中不存在 task_name='限时限量' 的记录（避免重复创建）
    
    创建规则：
    - 从同批次任意一条成功的发布相似商品记录的 params 中读取 '折扣' 值
    - 如果 '折扣' 值不存在或为空，跳过创建
    - shop_id 取同批次记录的 shop_id
    - params 设置为 {"batch_id": "发布相似商品的batch_id", "折扣": 折扣值}
    - 只创建一条限时限量记录（不是每个商品一条）
    """
```

文件：`backend/services/任务服务.py`

在 `执行任务` 方法的末尾，当任务执行结果为"成功"且 task_name 为"发布相似商品"时，调用：

```python
if 结果 == "成功" and task_name == "发布相似商品" and 任务参数记录:
    batch_id = 任务参数记录.get("batch_id")
    if batch_id:
        try:
            await 任务参数服务实例.批次完成后创建后续任务(batch_id)
        except Exception as e:
            print(f"[任务服务] 自动创建后续任务失败（忽略）: {e}")
```

### ⚠️ 约束

- Page 层每个 def 只做一个页面操作
- 不要改 selectors/ 目录
- 不要改 pages/ 目录（除非修复 切回前台 逻辑）
- 不要自行添加流程步骤
- 后端 Python 中文命名
- 所有测试必须通过
- `批次完成后创建后续任务` 必须是幂等的——多次调用不会重复创建限时限量记录