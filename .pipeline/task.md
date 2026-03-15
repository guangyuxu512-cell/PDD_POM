Task 44A：售后页 POM + 售后选择器
一、做什么
新建拼多多后台售后管理页面的 POM 层，覆盖售后单列表浏览、订单详情读取、退款操作、弹窗处理等原子操作。每个 def 只做一个页面操作。
二、涉及文件
selectors/售后页选择器.py — 新建
pages/售后页.py — 新建
tests/test_售后页.py — 新建
三、售后页选择器
selectors/售后页选择器.py：
拼多多后台售后单页面 URL：https://mms.pinduoduo.com/aftersales/list
"""拼多多后台售后管理页选择器。"""
from selectors.选择器配置 import 选择器配置
​
class 售后页选择器:
"""售后管理页面元素定位。"""
========== 售后列表页 ==========
售后单列表容器
列表容器 = 选择器配置(
主选择器="//div[contains(@class, 'after-sales-list')]",
备选选择器=["//div[contains(@class, 'refund-list')]"],
)
售后单行（每一条售后单）
售后单行 = 选择器配置(
主选择器="//tr[contains(@class, 'ant-table-row')]",
备选选择器=["//div[contains(@class, 'refund-item')]"],
)
售后状态筛选 Tab
待处理Tab = 选择器配置(
主选择器="//div[contains(@class, 'ant-tabs-tab') and contains(., '待处理')]",
)
已处理Tab = 选择器配置(
主选择器="//div[contains(@class, 'ant-tabs-tab') and contains(., '已处理')]",
)
搜索框（订单号/商品名）
搜索输入框 = 选择器配置(
主选择器="//input[contains(@placeholder, '订单号') or contains(@placeholder, '售后单号')]",
备选选择器=["//input[contains(@placeholder, '搜索')]"],
)
搜索按钮 = 选择器配置(
主选择器="//button[.//span[text()='查询'] or .//span[text()='搜索']]",
)
========== 售后单详情 ==========
售后类型标签（仅退款/退货退款/换货）
售后类型标签 = 选择器配置(
主选择器="//span[contains(@class, 'refund-type') or contains(@class, 'after-sale-type')]",
)
退款金额
退款金额 = 选择器配置(
主选择器="//span[contains(@class, 'refund-amount') or contains(@class, 'refund-money')]",
备选选择器=["//td[contains(., '退款金额')]/following-sibling::td[1]"],
)
订单号
订单号 = 选择器配置(
主选择器="//span[contains(@class, 'order-sn')]",
备选选择器=["//td[contains(., '订单号')]/following-sibling::td[1]"],
)
商品名称
商品名称 = 选择器配置(
主选择器="//span[contains(@class, 'goods-name')]",
备选选择器=["//td[contains(., '商品')]/following-sibling::td[1]"],
)
买家备注/退款原因
退款原因 = 选择器配置(
主选择器="//span[contains(@class, 'refund-reason')]",
备选选择器=["//td[contains(., '退款原因')]/following-sibling::td[1]"],
)
发货状态
发货状态 = 选择器配置(
主选择器="//span[contains(@class, 'shipping-status')]",
备选选择器=["//td[contains(., '物流状态')]/following-sibling::td[1]"],
)
========== 操作按钮 ==========
同意退款按钮 = 选择器配置(
主选择器="//button[.//span[text()='同意退款']]",
备选选择器=[
"//button[contains(., '同意')]",
"//a[contains(., '同意退款')]",
],
)
同意退货按钮 = 选择器配置(
主选择器="//button[.//span[text()='同意退货']]",
备选选择器=["//button[contains(., '同意退货')]"],
)
拒绝按钮 = 选择器配置(
主选择器="//button[.//span[text()='拒绝']]",
备选选择器=["//button[contains(., '拒绝退款')]"],
)
查看详情按钮（列表页每行）
查看详情按钮 = 选择器配置(
主选择器="//a[contains(., '查看详情')]",
备选选择器=["//button[contains(., '详情')]"],
)
========== 确认弹窗 ==========
确认弹窗 = 选择器配置(
主选择器="//div[contains(@class, 'ant-modal-content')]",
)
确认弹窗确定按钮 = 选择器配置(
主选择器="//div[contains(@class, 'ant-modal-content')]//button[.//span[text()='确定']]",
备选选择器=[
"//div[contains(@class, 'ant-modal')]//button[contains(@class, 'ant-btn-primary')]",
],
)
确认弹窗取消按钮 = 选择器配置(
主选择器="//div[contains(@class, 'ant-modal-content')]//button[.//span[text()='取消']]",
)
========== 物流信息（退货退款场景） ==========
物流单号输入框 = 选择器配置(
主选择器="//input[contains(@placeholder, '物流单号') or contains(@placeholder, '快递单号')]",
)
物流公司选择框 = 选择器配置(
主选择器="//div[contains(@class, 'logistics-select')]//input",
备选选择器=["//input[contains(@placeholder, '物流公司') or contains(@placeholder, '快递公司')]"],
)
========== 翻页 ==========
下一页按钮 = 选择器配置(
主选择器="//li[contains(@class, 'ant-pagination-next')]",
)
@staticmethod
def 获取第N行操作按钮(行号: int, 操作文本: str) -> 选择器配置:
"""获取列表第N行的指定操作按钮。"""
return 选择器配置(
主选择器=f"(//tr[contains(@class, 'ant-table-row')])[{行号}]//button[contains(., '{操作文本}')]",
备选选择器=[
f"(//tr[contains(@class, 'ant-table-row')])[{行号}]//a[contains(., '{操作文本}')]",
],
)
@staticmethod
def 获取第N行详情链接(行号: int) -> 选择器配置:
"""获取列表第N行的查看详情链接。"""
return 选择器配置(
主选择器=f"(//tr[contains(@class, 'ant-table-row')])[{行号}]//a[contains(., '查看详情')]",
备选选择器=[
f"(//div[contains(@class, 'refund-item')])[{行号}]//a[contains(., '详情')]",
],
)

---

**四、售后页 POM**

`pages/售后页.py`：

继承 `基础页`，每个 def 只做一个原子操作。

​
"""拼多多后台售后管理页面对象。"""
class 售后页(基础页):
—— 导航 ——
async def 导航到售后列表(self)
"""导航到售后管理列表页。URL: https://mms.pinduoduo.com/aftersales/list"""
async def 切换待处理(self)
"""点击"待处理"Tab筛选。"""
async def 切换已处理(self)
"""点击"已处理"Tab筛选。"""
—— 搜索 ——
async def 搜索订单(self, 关键词: str)
"""在搜索框输入关键词并点击查询。"""
—— 列表读取 ——
async def 获取售后单数量(self) -> int
"""返回当前列表页的售后单行数。"""
async def 获取第N行信息(self, 行号: int) -> dict
"""读取列表第N行的售后单摘要信息。
返回: {"订单号": str, "售后类型": str, "退款金额": str, "商品名称": str}
通过 evaluate 获取该行各列的 textContent。"""
async def 点击第N行详情(self, 行号: int)
"""点击列表第N行的"查看详情"链接。"""
async def 点击第N行操作(self, 行号: int, 操作文本: str)
"""点击列表第N行的指定操作按钮（如"同意退款"）。"""
async def 翻页(self) -> bool
"""点击下一页，如果有的话。返回是否成功翻页。"""
—— 详情页读取 ——
async def 读取售后详情(self) -> dict
"""从售后单详情页读取完整信息。
返回: {"订单号", "售后类型", "退款金额", "退款原因", "商品名称", "发货状态"}"""
—— 操作 ——
async def 点击同意退款(self)
"""点击"同意退款"按钮。"""
async def 点击同意退货(self)
"""点击"同意退货"按钮。"""
async def 点击拒绝(self)
"""点击"拒绝"按钮。"""
—— 弹窗处理 ——
async def 等待确认弹窗(self, 超时: int = 5000) -> bool
"""等待确认弹窗出现，返回是否出现。"""
async def 点击弹窗确定(self)
"""点击确认弹窗的"确定"按钮。"""
async def 点击弹窗取消(self)
"""点击确认弹窗的"取消"按钮。"""
async def 处理确认弹窗(self) -> bool
"""等待确认弹窗 → 点击确定。返回是否成功。"""
—— 物流信息（退货场景） ——
async def 填写物流单号(self, 单号: str)
"""在物流单号输入框填写单号。"""
async def 选择物流公司(self, 公司名: str)
"""选择物流公司（下拉框选择）。"""

**实现要求：**

1. 每个方法内部使用 `售后页选择器` 的选择器，通过 `self.安全点击()` / `self.安全填写()` 等基础页方法操作
2. `获取第N行信息` 和 `读取售后详情` 使用 `page.evaluate()` 读取 DOM 文本，返回 dict
3. 所有操作前后加 `self.操作前延迟()` / `self.操作后延迟()`
4. `翻页` 方法先检查下一页按钮是否 disabled，是则返回 False
5. `处理确认弹窗` 是一个组合方法（等待弹窗 + 点击确定），用于简化 Task 层调用

---

**五、测试**

`tests/test_售后页.py`：

1. mock Playwright，测试 `导航到售后列表` 调用正确 URL
2. mock Playwright，测试 `搜索订单` 正确填写搜索框并点击查询
3. mock Playwright，测试 `获取第N行信息` 返回正确的 dict 结构
4. mock Playwright，测试 `点击同意退款` 调用正确选择器
5. mock Playwright，测试 `处理确认弹窗` 等待弹窗 → 点击确定
6. mock Playwright，测试 `翻页` 检查 disabled 逻辑

---

**六、约束**

1. POM 层不写任何业务逻辑（不判断"金额>50就拒绝"之类的），只做原子操作
2. 每个 def 只做一个页面操作（与现有 推广页.py、限时限量页.py 风格一致）
3. 选择器都放在 `售后页选择器.py`，页面类不硬编码任何 XPath/CSS
4. 不修改现有任何文件
5. 选择器基于拼多多后台 Ant Design 组件库（`ant-table-row`、`ant-modal`、`ant-tabs-tab` 等 class）
6. 注意：拼多多后台页面可能会改版，选择器设计备选方案以提高容错
7. pytest 全量通过
