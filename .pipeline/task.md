## ask 24：前端任务列表优化（参数展示 + 执行结果 Tab）

### 目标

优化前端任务列表页面，增加执行结果展示能力，让用户能看到完整参数和新商品ID等执行结果。

### 涉及文件

- 改动：前端任务列表页组件（显示 task_params 的那个页面）
- 改动：后端 API（如需增加字段返回）

### 功能 1：参数列显示优化

- 参数列默认显示关键字段摘要：`父商品ID: xxx / 折扣: x`
- 摘要从 params JSON 中提取以下字段（有则显示，无则跳过）：`父商品ID`、`新标题`、`折扣`、`投产比`、`发布次数`
- 鼠标 hover 参数列时，用 tooltip 显示完整 JSON（格式化缩进）
- 如果参数列宽度不够，用省略号截断，不要换行撑开表格

### 功能 2：新增"执行结果"列

- 在表格中新增一列"执行结果"，放在"结果"列后面
- 从 `task_params.result` JSON 中提取关键字段显示：
    - `新商品ID`（或 `new_product_id`）
    - `父商品ID`（或 `parent_product_id`）
- 显示格式：`新ID: 917634708961`
- 如果 result 为空或无 `新商品ID`，显示 `-`
- hover 显示完整 result JSON

### 功能 3：新增"执行结果"Tab 页

- 在任务列表页面顶部新增一个 Tab：`任务列表 | 执行结果`
- "执行结果" Tab 显示一个专门的表格，列如下：
    - ID
    - 店铺
    - 任务类型
    - 父商品ID（从 params 读取）
    - 新商品ID（从 result 读取）
    - 折扣（从 params 读取）
    - 投产比（从 params 读取）
    - 状态
    - 错误信息
    - 执行时间（updated_at）
- 只显示 `status` 为 `success` 或 `failed` 的记录（已执行过的）
- 默认按 `updated_at` 倒序排列
- 支持按 `batch_id` 筛选（顶部加一个下拉框，列出所有 batch_id）
- 支持按日期范围筛选

### 功能 4：batch_id 筛选

- 后端 API 需支持 `batch_id` 查询参数
- 前端两个 Tab 都支持按 batch_id 筛选
- batch_id 下拉框显示格式：`批次 xxx (2026-03-12, 5条)`

### 约束

- 不要改 task_params 表结构
- 前端英文命名，后端 Python 中文命名
- 不要改 selectors/、pages/、tasks/、browser/ 目录
- 兼容 result 字段为空或 JSON 格式不正确的情况（显示 `-`，不要报错）

---

## Task 25：限时限量批量设置任务

### 目标

新增限时限量批量设置任务，自动查询同批次已成功发布的新商品ID，批量创建限时折扣活动。

### 涉及文件

- 新建：`selectors/限时限量页选择器.py`
- 新建：`pages/限时限量页.py`
- 新建：`tasks/限时限量任务.py`
- 改动：`tasks/注册表.py`（注册新任务）
- 改动：`backend/services/任务参数服务.py`（增加按批次查询成功记录的方法）

### 新增服务方法（backend/services/[任务参数服务.py](http://任务参数服务.py)）

```
async def 查询批次成功记录(self, shop_id: str, batch_id: str, task_name: str) -> list:
    """查询同批次中指定任务名称且执行成功的记录，返回 result JSON 列表"""
    SQL: SELECT result FROM task_params 
         WHERE shop_id = ? AND batch_id = ? AND task_name = ? AND status = 'success'
```

### 流程步骤（Task 层编排，Page 层原子方法）

1. Task 启动，从自身 params 读取 `batch_id` 和 `折扣` 值
2. 调用 `任务参数服务.查询批次成功记录(shop_id, batch_id, "发布相似商品")` 获取新商品ID列表
3. 如果列表为空，返回"跳过：无成功发布的商品"
4. 导航到限时限量创建页 `https://mms.pinduoduo.com/tool/promotion/create?tool_full_channel=10921_77271`
5. 点击"展开更多设置"
6. 勾选"自动创建活动"（自动续期）
7. 点击"选择商品"按钮，打开选品弹窗
8. 循环每个新商品ID：
    - 在弹窗搜索框输入商品ID
    - 点击查询
    - 等待结果
    - 勾选第一行商品
9. 点击"确认选择"，关闭弹窗
10. 填写折扣值（统一折扣）
11. 点击"确认设置"
12. 点击"创建"
13. 等待创建成功提示
14. 返回商品列表页

### Page 层原子方法（pages/[限时限量页.py](http://限时限量页.py)）

每个方法只做一件事：

```
async def 导航到创建页(self) -> None
async def 点击展开更多设置(self) -> None
async def 勾选自动创建(self) -> None
async def 点击选择商品(self) -> None（打开弹窗）
async def 弹窗输入商品ID(self, 商品ID: str) -> None
async def 弹窗点击查询(self) -> None
async def 弹窗等待结果(self) -> None
async def 弹窗勾选第一行(self) -> None
async def 弹窗点击确认选择(self) -> None
async def 填写折扣(self, 折扣值: float) -> None
async def 点击确认设置(self) -> None
async def 点击创建(self) -> None
async def 等待创建成功(self) -> bool
```

### 选择器（selectors/[限时限量页选择器.py](http://限时限量页选择器.py)）

从老版本代码 `营销页选择器` 中提取，用选择器配置模式：

- 更多设置展开按钮 = 选择器配置(主选择器="待补充", 备选选择器=["待补充"])
- 自动创建活动选项 = 选择器配置(主选择器="待补充")
- 选择商品按钮 = 选择器配置(主选择器="待补充")
- 选择商品弹窗_搜索输入框 = 选择器配置(主选择器="待补充")
- 选择商品弹窗_查询按钮 = 选择器配置(主选择器="待补充")
- 选择商品弹窗_第一行勾选框 = 选择器配置(主选择器="label[data-testid='beast-core-checkbox']", 备选选择器=["td[class*='TB_checkCell'] label[data-testid='beast-core-checkbox']"])
- 选择商品弹窗_确认选择按钮 = 选择器配置(主选择器="待补充")
- 折扣输入框 = 选择器配置(主选择器="待补充")
- 确认设置按钮 = 选择器配置(主选择器="待补充")
- 创建按钮 = 选择器配置(主选择器="待补充")
- 创建成功提示 = 选择器配置(主选择器="待补充")

注意：选择器值标"待补充"的，Codex 用 TODO 占位。用户后续手动用 F12 获取后填入。

### 任务注册

在 `tasks/注册表.py` 中注册：`@register_task("限时限量", "批量创建限时折扣活动")`

### 如何触发

CSV 导入时，折扣值已写入每条发布任务的 params。限时限量任务单独创建一条记录：

```json
{
  "task_name": "限时限量",
  "params": {"batch_id": "xxx", "折扣": 6},
  "shop_id": "xxx"
}
```

可以在前端加一个按钮"创建限时限量任务"，自动填入当前批次的 batch_id 和折扣值。也可以 CSV 多加一行。

### ⚠️ 约束

- Page 层每个 def 只做一个页面操作
- 不要把多个操作合成一个大方法
- 不要自行添加流程步骤（比如搜索类型下拉）
- 每个原子方法内部用 `for sel in 选择器.所有选择器()` 遍历 fallback
- 每个原子方法前后加随机延迟（继承基础页的延迟方法）
- 不要改 browser/ 目录
- 不要改已有的 selectors/ 文件
- 不要在选择器层添加 Task 描述中没提到的选择器
- 所有测试必须通过