Task 44B：售后任务 + 状态机 + 规则匹配引擎
一、做什么
新建规则引擎（规则模型 + 规则服务 + 规则 API）— 通用的条件-动作匹配，不绑定具体业务
新建售后任务（状态机驱动）— 串联售后页 + 微信页 + 飞书服务
注册到任务注册表，支持流程编排系统调用
二、涉及文件
backend/models/规则模型.py — 新建，SQLite 规则表定义
backend/services/规则服务.py — 新建，规则 CRUD + 条件匹配引擎
backend/api/规则接口.py — 新建，规则 CRUD REST API
backend/api/路由注册.py — 注册规则路由蓝图
tasks/售后任务.py — 新建，状态机驱动的售后处理任务
tests/test_规则服务.py — 新建
tests/test_售后任务.py — 新建
三、规则模型
backend/models/规则模型.py：
数据库表 rules，用现有的 SQLite 连接（和 shops、flows、flow_params 同一个库）：
"""通用规则模型。"""

建表SQL = """
CREATE TABLE IF NOT EXISTS rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    platform    TEXT NOT NULL DEFAULT '*',
    business    TEXT NOT NULL,
    shop_id     TEXT NOT NULL DEFAULT '*',
    priority    INTEGER NOT NULL DEFAULT 0,
    conditions  TEXT NOT NULL DEFAULT '{}',
    actions     TEXT NOT NULL DEFAULT '[]',
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""
​
字段说明：
platform：平台标识，* 表示全部，pdd/taobao/jd 等
business：业务类型，售后/推广/限时限量 等
shop_id：店铺 ID，* 表示全部店铺
priority：优先级，数字越大越先匹配
conditions：JSON 字符串，条件组（支持嵌套 and/or）
actions：JSON 字符串，动作列表
enabled：是否启用
提供 初始化规则表() 方法，在应用启动时调用 CREATE TABLE IF NOT EXISTS。
四、规则服务
backend/services/规则服务.py：
4.1 CRUD 方法
class 规则服务:
    """通用规则引擎：CRUD + 条件匹配。"""

    async def 创建规则(self, 规则数据: dict) -> dict
    async def 更新规则(self, 规则ID: int, 规则数据: dict) -> dict
    async def 删除规则(self, 规则ID: int) -> bool
    async def 获取规则(self, 规则ID: int) -> dict
    async def 获取规则列表(self, platform: str = None, business: str = None, shop_id: str = None) -> list[dict]
    async def 切换启用(self, 规则ID: int, 启用: bool) -> bool
​
4.2 条件匹配引擎
async def 匹配规则(self, platform: str, business: str, shop_id: str, 数据: dict) -> list[dict]:
    """按优先级匹配第一条命中的规则，返回其 actions 列表。
    
    匹配顺序：
    1. 精确匹配 shop_id 的规则优先
    2. 同 shop_id 下按 priority 降序
    3. shop_id='*' 的通用规则兜底
    4. 都不命中则返回默认动作 [{"type": "默认", "action": "人工处理"}]
    """

def _评估条件(self, 条件组: dict, 数据: dict) -> bool:
    """递归评估条件组。
    
    条件组格式:
    {
        "operator": "and" | "or",
        "rules": [
            {"field": "售后类型", "op": "==", "value": "仅退款"},
            {"field": "退款金额", "op": "<=", "value": 10},
            { "operator": "or", "rules": [...] }  # 嵌套
        ]
    }
    """

def _评估单条(self, 规则: dict, 数据: dict) -> bool:
    """评估单条规则。
    
    支持操作符: ==, !=, >, <, >=, <=, in, not_in, contains
    
    类型转换: 
    - 数值比较时自动 float() 转换
    - 字符串比较不区分大小写
    """
​
4.3 默认规则种子数据
提供 初始化默认售后规则() 方法，预置几条基础售后规则（仅当 rules 表为空时插入）：
默认售后规则 = [
    {
        "name": "小额自动退款",
        "platform": "pdd",
        "business": "售后",
        "shop_id": "*",
        "priority": 100,
        "conditions": {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "仅退款"},
                {"field": "退款金额", "op": "<=", "value": 10}
            ]
        },
        "actions": [
            {"type": "页面操作", "action": "同意退款"}
        ]
    },
    {
        "name": "中额退款+微信通知",
        "platform": "pdd",
        "business": "售后",
        "shop_id": "*",
        "priority": 90,
        "conditions": {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "仅退款"},
                {"field": "退款金额", "op": "<=", "value": 50}
            ]
        },
        "actions": [
            {"type": "页面操作", "action": "同意退款"},
            {"type": "微信通知", "action": "发消息", "template": "亲，您的退款 {退款金额} 元已处理~"}
        ]
    },
    {
        "name": "大额人工审核",
        "platform": "pdd",
        "business": "售后",
        "shop_id": "*",
        "priority": 80,
        "conditions": {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "仅退款"},
                {"field": "退款金额", "op": ">", "value": 50}
            ]
        },
        "actions": [
            {"type": "飞书通知", "action": "发工单"},
            {"type": "标记", "action": "人工审核"}
        ]
    },
    {
        "name": "退货退款-已发货",
        "platform": "pdd",
        "business": "售后",
        "shop_id": "*",
        "priority": 70,
        "conditions": {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "退货退款"},
                {"field": "发货状态", "op": "==", "value": "已发货"}
            ]
        },
        "actions": [
            {"type": "页面操作", "action": "同意退货"},
            {"type": "微信通知", "action": "发消息", "template": "亲，退货已同意，请尽快寄回~"}
        ]
    },
    {
        "name": "退货退款-未发货",
        "platform": "pdd",
        "business": "售后",
        "shop_id": "*",
        "priority": 60,
        "conditions": {
            "operator": "and",
            "rules": [
                {"field": "售后类型", "op": "==", "value": "退货退款"},
                {"field": "发货状态", "op": "==", "value": "未发货"}
            ]
        },
        "actions": [
            {"type": "页面操作", "action": "同意退款"}
        ]
    },
]
​
五、规则接口
backend/api/规则接口.py：
GET    /api/rules                  → 规则列表（支持 ?platform=pdd&business=售后&shop_id=xxx 筛选）
GET    /api/rules/<id>             → 规则详情
POST   /api/rules                  → 创建规则
PUT    /api/rules/<id>             → 更新规则
DELETE /api/rules/<id>             → 删除规则
PUT    /api/rules/<id>/toggle      → 切换启用/禁用
POST   /api/rules/match            → 测试匹配（传入数据，返回命中的规则和动作）
​
POST /api/rules/match 用于前端调试，传入：
{
    "platform": "pdd",
    "business": "售后",
    "shop_id": "xxx",
    "data": {"售后类型": "仅退款", "退款金额": 8}
}
​
返回命中的规则名称 + 动作列表。
注册到 backend/api/路由注册.py。
六、售后任务（状态机驱动）
tasks/售后任务.py：
6.1 状态定义
from enum import Enum

class 售后状态(Enum):
    初始化 = "初始化"
    打开售后列表 = "打开售后列表"
    读取售后单 = "读取售后单"
    匹配规则 = "匹配规则"
    执行页面操作 = "执行页面操作"
    处理弹窗 = "处理弹窗"
    发送微信 = "发送微信"
    发送飞书 = "发送飞书"
    记录结果 = "记录结果"
    处理下一单 = "处理下一单"
    完成 = "完成"
    失败 = "失败"
​
6.2 状态转移表
状态转移表 = {
    售后状态.初始化: 售后状态.打开售后列表,
    售后状态.打开售后列表: 售后状态.读取售后单,
    售后状态.读取售后单: 售后状态.匹配规则,
    售后状态.匹配规则: 售后状态.执行页面操作,
    售后状态.执行页面操作: 售后状态.处理弹窗,
    售后状态.处理弹窗: 售后状态.发送微信,      # 有微信动作才执行，否则跳过
    售后状态.发送微信: 售后状态.发送飞书,       # 有飞书动作才执行，否则跳过
    售后状态.发送飞书: 售后状态.记录结果,
    售后状态.记录结果: 售后状态.处理下一单,
    售后状态.处理下一单: 售后状态.读取售后单,   # 循环：还有下一单 → 回到读取
}
​
6.3 任务类
@register_task("售后处理", "根据规则自动处理售后单（退款/退货/通知）")
class 售后任务(基础任务):

    def __init__(self):
        self._当前状态 = 售后状态.初始化
        self._售后页: 售后页 | None = None
        self._规则服务 = 规则服务()
        self._飞书服务 = 飞书服务()
        self._处理结果列表: list[dict] = []
        self._当前行号: int = 1
        self._当前订单数据: dict = {}
        self._当前动作列表: list[dict] = []

    async def _转移状态(self, 下一状态: 售后状态):
        """记录状态转移日志。"""
        print(f"[售后状态机] {self._当前状态.value} → {下一状态.value}")
        self._当前状态 = 下一状态

    async def _执行状态(self, 页面, 店铺配置: dict) -> 售后状态:
        """根据当前状态执行对应逻辑，返回下一状态。"""
        
        match self._当前状态:

            case 售后状态.初始化:
                self._售后页 = 售后页(页面)
                return 售后状态.打开售后列表

            case 售后状态.打开售后列表:
                await self._售后页.导航到售后列表()
                await self._售后页.切换待处理()
                return 售后状态.读取售后单

            case 售后状态.读取售后单:
                总数 = await self._售后页.获取售后单数量()
                if self._当前行号 > 总数:
                    return 售后状态.完成
                self._当前订单数据 = await self._售后页.获取第N行信息(self._当前行号)
                return 售后状态.匹配规则

            case 售后状态.匹配规则:
                shop_id = 店铺配置.get("shop_id", "*")
                self._当前动作列表 = await self._规则服务.匹配规则(
                    platform="pdd",
                    business="售后",
                    shop_id=shop_id,
                    数据=self._当前订单数据,
                )
                # 检查是否有"人工审核"标记
                for 动作 in self._当前动作列表:
                    if 动作.get("action") == "人工处理" or 动作.get("action") == "人工审核":
                        # 人工处理：不操作页面，直接去通知
                        return 售后状态.发送飞书
                return 售后状态.执行页面操作

            case 售后状态.执行页面操作:
                for 动作 in self._当前动作列表:
                    if 动作.get("type") != "页面操作":
                        continue
                    操作 = 动作.get("action", "")
                    if 操作 == "同意退款":
                        await self._售后页.点击第N行操作(self._当前行号, "同意退款")
                    elif 操作 == "同意退货":
                        await self._售后页.点击第N行操作(self._当前行号, "同意退货")
                    elif 操作 == "拒绝":
                        await self._售后页.点击第N行操作(self._当前行号, "拒绝")
                return 售后状态.处理弹窗

            case 售后状态.处理弹窗:
                await self._售后页.处理确认弹窗()
                return 售后状态.发送微信

            case 售后状态.发送微信:
                微信动作列表 = [a for a in self._当前动作列表 if a.get("type") == "微信通知"]
                if 微信动作列表:
                    任务参数 = 店铺配置.get("task_param", {})
                    联系人 = 任务参数.get("客户微信", "")
                    if 联系人:
                        模板 = 微信动作列表[0].get("template", "您的售后已处理")
                        消息 = self._渲染模板(模板, self._当前订单数据)
                        微信 = 微信页()
                        await asyncio.to_thread(微信.发送消息, 联系人, 消息)
                return 售后状态.发送飞书

            case 售后状态.发送飞书:
                飞书动作列表 = [a for a in self._当前动作列表 if a.get("type") == "飞书通知"]
                if 飞书动作列表:
                    await self._飞书服务.发送售后通知(
                        self._当前订单数据,
                        飞书动作列表[0].get("action", "通知"),
                    )
                return 售后状态.记录结果

            case 售后状态.记录结果:
                self._处理结果列表.append({
                    "订单号": self._当前订单数据.get("订单号", ""),
                    "售后类型": self._当前订单数据.get("售后类型", ""),
                    "处理方式": [a.get("action") for a in self._当前动作列表],
                    "状态": "已处理",
                })
                return 售后状态.处理下一单

            case 售后状态.处理下一单:
                self._当前行号 += 1
                return 售后状态.读取售后单

        return 售后状态.失败

    def _渲染模板(self, 模板: str, 数据: dict) -> str:
        """简单模板渲染，把 {字段名} 替换为数据值。"""
        结果 = 模板
        for 键, 值 in 数据.items():
            结果 = 结果.replace(f"{键}", str(值))
        return 结果

    @自动回调("售后处理")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        """状态机主循环。"""
        self._当前状态 = 售后状态.初始化
        self._当前行号 = 1
        self._处理结果列表 = []
        店铺ID = 店铺配置.get("shop_id", "")

        最大迭代 = 500  # 安全限制，防止死循环
        迭代次数 = 0

        while self._当前状态 not in (售后状态.完成, 售后状态.失败):
            迭代次数 += 1
            if 迭代次数 > 最大迭代:
                await 上报("[失败] 状态机迭代超限", 店铺ID)
                return "失败"

            try:
                下一状态 = await self._执行状态(页面, 店铺配置)
                await self._转移状态(下一状态)
                await 上报(f"[{下一状态.value}]", 店铺ID)
            except Exception as 异常:
                await 上报(f"[失败] 状态={self._当前状态.value} 异常={异常}", 店铺ID)
                # 截图保留现场
                if self._售后页:
                    try:
                        await self._售后页.截图(f"售后异常_{self._当前状态.value}")
                    except Exception:
                        pass
                return "失败"

        await 上报(f"[完成] 处理了 {len(self._处理结果列表)} 单", 店铺ID)
        return f"成功处理 {len(self._处理结果列表)} 单"
​
七、路由注册
在 backend/api/路由注册.py 中添加：
from backend.api.规则接口 import 规则蓝图
app.register_blueprint(规则蓝图)
​
同时确保应用启动时调用 初始化规则表() 和 初始化默认售后规则()。
八、测试
test_规则服务.py
测试 _评估单条：各操作符（==, !=, >, <, >=, <=, in, not_in, contains）
测试 _评估条件：and 组合、or 组合、嵌套
测试 匹配规则：精确 shop_id 优先于 *
测试 匹配规则：priority 降序匹配
测试 匹配规则：无命中返回默认动作
测试 CRUD：创建/读取/更新/删除/切换启用
测试默认种子数据插入
test_售后任务.py
mock 售后页 + 规则服务，测试状态机正常流转（初始化 → 打开列表 → 读取 → 匹配 → 操作 → 弹窗 → 记录 → 完成）
mock 售后页返回 0 条，测试直接完成
mock 规则服务返回"人工审核"，测试跳过页面操作直接到飞书通知
mock 微信页，测试微信通知分支
mock 飞书服务，测试飞书通知分支
测试 _渲染模板 方法
测试最大迭代安全限制
九、约束
规则引擎是通用的，不绑定售后——以后推广、限时限量的规则也可以用
售后任务通过 @register_task("售后处理", ...) 注册，流程编排系统可直接调用
微信操作用 asyncio.to_thread() 包装（微信页是同步的）
状态机加最大迭代限制（500），防止死循环
异常时截图保留现场
不修改现有任何任务文件
飞书/微信通知失败不中断售后处理流程（catch 异常，记录日志，继续下一单）
pytest 全量通过