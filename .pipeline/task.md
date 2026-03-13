## Task 30：任务链自动串联重构

### 做什么

把"批次完成后创建后续任务"改为"逐条成功后立即创建下一步任务"

### 涉及文件

- 改动：`backend/services/任务服务.py`
- 改动：`backend/services/任务参数服务.py`
- 改动：`tasks/限时限量任务.py`
- 不改：`pages/`、`selectors/`

### 流程

#### 步骤 1：[任务服务.py](http://任务服务.py) — 定义任务链 + 逐条创建

在 `任务服务.py` 顶部定义任务链映射：

```python
任务链映射 = {
    "发布相似商品": "限时限量",
    # 未来: "限时限量": "推广",
}
```

修改 `执行任务()` 方法，当任务成功后：

**删掉**原来的：

```python
if task_name == "发布相似商品":
    批次ID = str(任务参数记录.get("batch_id") or "").strip()
    if 批次ID:
        try:
            await 任务参数服务实例.批次完成后创建后续任务(批次ID)
        except Exception as e:
            print(f"[任务服务] 自动创建后续任务失败（忽略）: {e}")
```

**替换为**通用逻辑：

```python
下一步任务名 = 任务链映射.get(task_name)
if 下一步任务名 and 任务参数记录:
    try:
        await 任务参数服务实例.创建后续任务(
            源记录=任务参数记录,
            执行结果=执行结果数据,
            下一步任务名=下一步任务名,
        )
    except Exception as e:
        print(f"[任务服务] 自动创建后续任务失败（忽略）: {e}")
```

#### 步骤 2：[任务参数服务.py](http://任务参数服务.py) — 新增 `创建后续任务` 方法

**删掉** `批次完成后创建后续任务` 方法。

**新增** `创建后续任务` 方法：

```python
async def 创建后续任务(
    self,
    源记录: Dict[str, Any],
    执行结果: Dict[str, Any],
    下一步任务名: str,
) -> Optional[Dict[str, Any]]:
```

逻辑：

1. 从源记录读 `shop_id`
2. 从源记录的 `params` 读所有参数（折扣、投产比等），作为基础参数传递
3. 把执行结果中的关键字段（如 `新商品ID`、`父商品ID`、`标题`）合并进新 params
4. 添加 `source_task_param_id` = 源记录 id，用于溯源
5. 如果源记录有 `batch_id`，继承 batch_id
6. 调用 `self.创建()` 插入一条新记录，task_name = 下一步任务名，status = pending
7. 打印日志：`[任务参数服务] 已创建后续任务: {下一步任务名}, source_id={源记录id}`
8. 返回新记录

幂等检查：如果已存在 `source_task_param_id` 相同且 `task_name` 相同的记录，跳过不重复创建。

#### 步骤 3：[限时限量任务.py](http://限时限量任务.py) — 改为从自身 params 读参数

当前逻辑：从 batch_id 查询同批次所有成功记录 → 提取新商品ID列表 → 批量创建活动。

改为：

1. 从自身 `task_param` 的 params 直接读 `新商品ID`（由创建后续任务写入）
2. 从自身 `task_param` 的 params 直接读 `折扣`
3. 不再调用 `查询批次成功记录`
4. 只处理单个商品（一条限时限量记录对应一个商品）

修改 `执行` 方法：

- 删掉 `成功结果列表 = await 任务参数服务实例.查询批次成功记录(...)`
- 删掉 `新商品ID列表 = self._提取新商品ID列表(...)`
- 改为直接读：`新商品ID = self._读取字符串参数(任务参数, "新商品ID", "new_product_id")`
- 如果 `新商品ID` 为空，返回 `"跳过：无新商品ID"`
- 后续流程只操作这一个商品（选择商品弹窗只搜索一次）

### 关键元素

- `任务链映射`：dict，key = 当前任务名，value = 下一步任务名
- `source_task_param_id`：int，写入新记录 params JSON，溯源用
- `创建后续任务`：新方法，替代 `批次完成后创建后续任务`

### ⚠️ 约束

- 不要改 `pages/` 目录
- 不要改 `selectors/` 目录
- 后端 Python 中文命名
- 幂等：同一个 source_task_param_id + task_name 不重复创建
- 删掉 `批次完成后创建后续任务` 方法及其测试
- `查询批次成功记录` 方法保留不删（可能其他地方用到）
- pytest 必须通过