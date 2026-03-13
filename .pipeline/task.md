**二、涉及文件（新建）**

1. `selectors/推广页选择器.py` — 推广页所有页面元素定位
2. `pages/推广页.py` — 推广页页面操作（每个 def 只做一个页面操作）
3. `tasks/推广任务.py` — 推广任务编排，注册为 `"设置推广"`

**涉及文件（修改）**

1. `tasks/注册表.py` — 确认 `推广任务.py` 通过 `@register_task` 自动注册，无需手动改
2. `backend/services/任务服务.py` — 在 `任务参数任务集合` 中添加 `"设置推广"`

---

**三、流程**

**第1步：创建 `selectors/推广页选择器.py`**

参照老版本 `推广页选择器`，使用项目现有的 `选择器配置` dataclass。包含以下选择器：

```
from selectors.基础选择器 import 选择器配置

class 推广页选择器:

    # 广告弹窗关闭按钮
    广告弹窗关闭按钮 = 选择器配置(
        主选择器="div[class*='NormalModal'] span[class*='closeIcon']",
        备选选择器=[
            "div[data-testid^='amsModal'] span[class*='close']",
            "div[class*='anq-modal-wrap'] button[aria-label='Close']",
        ]
    )

    # Step 1: 添加推广商品按钮
    添加推广商品按钮 = 选择器配置(
        主选择器="button:has-text('添加推广商品')",
        备选选择器=[
            "button[data-testid*='add']",
            "a:has-text('添加推广商品')",
        ]
    )

    # Step 2: 全局优先起量开关
    全局优先起量开关 = 选择器配置(
        主选择器="button[role='switch'][aria-label*='优先起量']",
        备选选择器=[
            "button[role='switch'][class*='Switch']",
        ]
    )

    确认关闭优先起量按钮 = 选择器配置(
        主选择器="button:has-text('确认关闭')",
        备选选择器=[
            "button:has-text('确认')",
            "div[class*='Modal'] button[class*='primary']",
        ]
    )

    # Step 3: 商品ID输入框
    商品ID输入框 = 选择器配置(
        主选择器="input[placeholder*='商品ID']",
        备选选择器=[
            "input[placeholder*='输入商品']",
        ]
    )

    查询按钮 = 选择器配置(
        主选择器="button:has-text('查询')",
        备选选择器=[
            "button[data-testid*='search']",
        ]
    )

    商品列表数据行 = 选择器配置(
        主选择器="tr[data-testid*='table-body-tr']",
        备选选择器=[
            "tbody tr",
        ]
    )

    # Step 4: 全选复选框
    全选复选框 = 选择器配置(
        主选择器="th label[data-testid='beast-core-checkbox']",
        备选选择器=[
            "thead label[data-testid='beast-core-checkbox']",
            "th input[type='checkbox']",
        ]
    )

    # Step 5: 投产比相关（需要按商品ID动态生成的，用静态方法）
    投产输入框 = 选择器配置(
        主选择器="input[data-testid*='roi']",
        备选选择器=[
            "input[placeholder*='投产']",
            "div[class*='roi'] input",
        ]
    )

    投产比限制提示 = 选择器配置(
        主选择器="div[class*='error']:has-text('投产')",
        备选选择器=[
            "span[class*='error']",
        ]
    )

    二阶段投产输入框 = 选择器配置(
        主选择器="div[class*='Modal'] input[data-testid*='roi']",
        备选选择器=[
            "div[class*='Modal'] input[placeholder*='投产']",
        ]
    )

    二阶段确认按钮 = 选择器配置(
        主选择器="div[class*='Modal'] button:has-text('确定')",
        备选选择器=[
            "div[class*='Modal'] button[class*='primary']",
        ]
    )

    # Step 7: 开启推广按钮
    开启推广按钮 = 选择器配置(
        主选择器="button:has-text('开启推广')",
        备选选择器=[
            "button[class*='primary']:has-text('开启')",
        ]
    )

    # 推广成功弹窗
    推广成功弹窗 = 选择器配置(
        主选择器="div:has-text('推广成功')",
        备选选择器=[
            "div[class*='success']",
        ]
    )
```

另外新增**动态选择器方法**（按商品ID生成）：

```
@staticmethod
def 获取投产设置按钮(商品ID: str) -> 选择器配置:
    """根据商品ID生成投产设置按钮（铅笔图标）选择器"""
    return 选择器配置(
        主选择器=f"tr:has-text('{商品ID}') [data-testid*='edit']",
        备选选择器=[
            f"tr:has-text('{商品ID}') svg[class*='edit']",
            f"tr:has-text('{商品ID}') button[class*='edit']",
        ]
    )

@staticmethod
def 获取极速起量开关(商品ID: str) -> 选择器配置:
    return 选择器配置(
        主选择器=f"tr:has-text('{商品ID}') button[role='switch']",
        备选选择器=[]
    )

@staticmethod
def 获取确认按钮(商品ID: str) -> 选择器配置:
    return 选择器配置(
        主选择器="button:has-text('确定')",
        备选选择器=["button[class*='primary']:has-text('确定')"]
    )

@staticmethod
def 获取取消按钮(商品ID: str) -> 选择器配置:
    return 选择器配置(
        主选择器="button:has-text('取消')",
        备选选择器=["button:has-text('取消')"]
    )

@staticmethod
def 获取取消勾选框(商品ID: str) -> 选择器配置:
    return 选择器配置(
        主选择器=f"tr:has-text('{商品ID}') label[data-testid='beast-core-checkbox']",
        备选选择器=[]
    )
```

**第2步：创建 `pages/推广页.py`**

每个 def 只做一个页面操作。参照老版本拆分为以下原子方法：

```
class 推广页:
    全站推广URL = "https://yingxiao.pinduoduo.com/goods/promotion/list?msfrom=mms_sidenav"

    def __init__(self, 页面):
        self.页面 = 页面

    # --- 导航 ---
    async def 导航到全站推广页(self)
    async def 返回商品列表页(self)

    # --- 弹窗 ---
    async def 关闭广告弹窗(self) -> bool
        # 检测弹窗是否存在 → 不存在直接返回
        # 存在时：尝试选择器关闭 → JavaScript关闭 → ESC关闭
        # 循环最多3次（可能有多层弹窗）

    # --- Step 1 ---
    async def 点击添加推广商品(self) -> bool

    # --- Step 2 ---
    async def 获取全局优先起量状态(self) -> str
        # 返回 "true" / "false" / "not_found"
    async def 点击全局优先起量开关(self) -> bool
    async def 确认关闭优先起量(self) -> bool

    # --- Step 3 ---
    async def 输入商品ID(self, 商品ID字符串: str) -> bool
    async def 点击查询(self) -> bool
    async def 获取列表商品ID(self) -> list[str]
        # 正则提取12位数字商品ID

    # --- Step 4 ---
    async def 点击全选(self) -> bool

    # --- Step 5 ---
    async def 点击投产设置按钮(self, 商品ID: str) -> bool
    async def 获取极速起量状态(self, 商品ID: str) -> str
    async def 点击极速起量开关(self, 商品ID: str) -> bool
    async def 确认关闭极速起量(self) -> bool
    async def 填写一阶段投产比(self, 投产比: float) -> bool
    async def 检测投产比限制(self) -> bool
    async def 点击编辑二阶段(self, 商品ID: str) -> bool
    async def 填写二阶段投产比(self, 投产比: float) -> bool
    async def 确认二阶段(self) -> bool
    async def 确认投产设置(self, 商品ID: str) -> bool
    async def 取消投产设置(self, 商品ID: str) -> bool
    async def 取消勾选商品(self, 商品ID: str) -> bool

    # --- Step 7 ---
    async def 点击开启推广(self) -> bool
        # 先滚动到底部，再查找按钮
        # 选择器找不到时用JavaScript兜底
    async def 等待推广成功(self, 超时秒: int = 3) -> bool
```

注意：

- 每个方法内使用 `推广页选择器` 的选择器，遍历 `所有选择器()` 逐个尝试
- 每个方法内加 `随机延迟`（`asyncio.sleep(random.uniform(0.5, 1.5))`）
- 不写业务编排逻辑，只做单个页面操作

**第3步：创建 `tasks/推广任务.py`**

注册任务名 `"设置推广"`，编排完整流程：

```
@register_task("设置推广", "为商品设置全站推广（稳定成本）")
class 推广任务(基础任务):

    def __init__(self):
        self._执行结果 = {}

    @自动回调("设置推广")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        任务参数 = 店铺配置.get("task_param") or {}
        商品ID列表 = ...  # 从 任务参数 中读取，支持逗号分隔字符串或列表
        一阶段投产比 = float(任务参数.get("一阶段投产比") or 任务参数.get("phase1_roi") or 5.0)
        二阶段投产比 = float(任务参数.get("二阶段投产比") or 任务参数.get("phase2_roi") or 5.0)
        需要关闭极速起量 = True
```

执行流程：

1. `推广页.导航到全站推广页()`
2. `推广页.关闭广告弹窗()`（多次调用确保无遗漏）
3. `推广页.点击添加推广商品()`
4. 检查并关闭全局优先起量：`获取全局优先起量状态()` → 如果 "true" → `点击全局优先起量开关()` → `确认关闭优先起量()`
5. 批量搜索商品（带重试，最多5次）：`输入商品ID(逗号拼接)` → `点击查询()` → `获取列表商品ID()` → 对比验证
6. `点击全选()`
7. 逐个设置投产比（循环每个商品ID）：
    - `点击投产设置按钮(商品ID)`
    - 如果需要：`获取极速起量状态()` → `点击极速起量开关()` → `确认关闭极速起量()`
    - `填写一阶段投产比(值)` → `检测投产比限制()` → 如果受限：`取消投产设置()` → `取消勾选商品()` → 跳过
    - `点击编辑二阶段()` → `填写二阶段投产比(值)` → `确认二阶段()`
    - `确认投产设置(商品ID)`
8. `点击开启推广()`
9. `等待推广成功()`
10. `推广页.返回商品列表页()`

`_执行结果` 写入：

```python
self._执行结果 = {
    "推广商品数": len(成功列表),
    "成功列表": 成功列表,
    "失败列表": 失败列表,
    "一阶段投产比": 一阶段投产比,
    "二阶段投产比": 二阶段投产比,
}
```

**第4步：修改 `backend/services/任务服务.py`**

在 `任务参数任务集合` 中添加 `"设置推广"`：

```python
任务参数任务集合 = {"发布相似商品", "发布换图商品", "限时限量", "设置推广"}
```

---

**四、关键元素**

- 全站推广 URL：`https://yingxiao.pinduoduo.com/goods/promotion/list?msfrom=mms_sidenav`
- 任务注册名：`"设置推广"`
- 任务参数 key：`商品ID列表`（逗号分隔字符串或 JSON 数组）、`一阶段投产比`、`二阶段投产比`
- 商品ID 正则：`\b\d{12}\b`（12位纯数字）
- 投产设置按钮：按商品ID动态定位行内的铅笔图标
- 极速起量开关判断：`aria-checked` 属性，`"true"` 表示开启
- 广告弹窗检测选择器：`div[class*='NormalModal']`、`div[data-testid^='amsModal']`

---

**五、约束**

1. **POM层不写业务逻辑，Task层不写页面选择器**
2. **selectors/ 层只存页面元素定位，使用 `选择器配置` dataclass**
3. **Page层每个 def 只做一个页面操作**
4. **每个页面操作之间加随机延迟（0.5-1.5秒）**
5. **后端 Python 中文命名，前端英文命名**
6. **严格按流程步骤执行，不要自行添加步骤**
7. **不修改前端代码**
8. **不修改现有任务的逻辑**