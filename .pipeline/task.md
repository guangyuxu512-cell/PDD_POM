Task 25：限时限量批量设置任务
目标
新增限时限量批量设置任务，自动查询同批次已成功发布的新商品ID，批量创建限时折扣活动。
涉及文件
新建：selectors/限时限量页选择器.py
新建：pages/限时限量页.py
新建：tasks/限时限量任务.py
改动：backend/services/任务参数服务.py（增加按批次查询成功记录的方法）
新增服务方法（backend/services/任务参数服务.py）
新增方法 查询批次成功记录：
参数：shop_id: str, batch_id: str, task_name: str
SQL：SELECT result FROM task_params WHERE shop_id = ? AND batch_id = ? AND task_name = ? AND status = 'success'
返回：result JSON 列表
流程步骤（Task 层编排，Page 层原子方法）
Task 启动，从自身 params 读取 batch_id 和 折扣 值
调用 任务参数服务.查询批次成功记录(shop_id, batch_id, "发布相似商品") 获取新商品ID列表
如果列表为空，返回"跳过：无成功发布的商品"
导航到限时限量创建页 https://mms.pinduoduo.com/tool/promotion/create?tool_full_channel=10921_77271
点击"展开更多设置"
勾选"自动创建活动"（自动续期）
点击"选择商品"按钮，打开选品弹窗
循环每个新商品ID：在弹窗搜索框输入商品ID → 点击查询 → 等待结果 → 勾选第一行商品
点击"确认选择"，关闭弹窗
填写折扣值（统一折扣）
点击"确认设置"
点击"创建"
等待创建成功提示
返回
Page 层原子方法（pages/限时限量页.py）
每个方法只做一件事：
async def 导航到创建页(self) -> None
async def 点击展开更多设置(self) -> None
async def 勾选自动创建(self) -> None
async def 点击选择商品(self) -> None
async def 弹窗输入商品ID(self, 商品ID: str) -> None
async def 弹窗点击查询(self) -> None
async def 弹窗等待结果(self) -> None
async def 弹窗勾选第一行(self) -> None
async def 弹窗点击确认选择(self) -> None
async def 填写折扣(self, 折扣值: float) -> None
async def 点击确认设置(self) -> None
async def 点击创建(self) -> None
async def 等待创建成功(self) -> bool
选择器（selectors/限时限量页选择器.py）
使用选择器配置 dataclass 模式。所有选择器值标"TODO_待手动获取"，Codex 用占位符，用户后续用 F12 手动填入。
任务注册
在 tasks/限时限量任务.py 顶部：@register_task("限时限量", "批量创建限时折扣活动")
注册表.py 的 排除模块 列表不需要改动，因为"限时限量任务"不在排除列表中，会被自动发现。
约束
Page 层每个 def 只做一个页面操作
不要把多个操作合成一个大方法
严格按流程步骤执行，不要自行添加步骤
每个原子方法内部用 for sel in 选择器.所有选择器() 遍历 fallback
每个原子方法前后加随机延迟（继承基础页的延迟方法）
不要改 browser/ 目录
不要改已有的 selectors/ 文件（登录页选择器、商品列表页选择器、发布商品页选择器、基础页选择器）
不要在选择器层添加 Task 描述中没提到的选择器
后端 Python 中文命名，前端英文命名
所有测试必须通过
