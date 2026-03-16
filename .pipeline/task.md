Task 46A：售后队列表 + 详情页完整抓取 + 列表翻页扫描 + JS 动态读取
一、做什么
新建 aftersale_queue 表（售后工作队列）
重构售后页 POM：新增详情页完整信息抓取（全用 JS evaluate，不依赖固定选择器） + 列表翻页扫描 + 新标签页管理 + 动态按钮读取
新增售后队列服务（队列 CRUD + 批次管理）
不改售后任务.py（46B 再改），本轮只做数据抓取层。
二、涉及文件
backend/models/售后队列模型.py — 新建
backend/services/售后队列服务.py — 新建
backend/models/数据库.py — 修改（加入售后队列建表）
pages/售后页.py — 修改（新增详情页抓取 + 翻页扫描 + 标签页管理 + 动态按钮）
selectors/售后页选择器.py — 修改（新增详情页区域选择器）
tests/test_售后队列服务.py — 新建
tests/test_售后页.py — 修改（补充新方法测试）
三、售后队列表
backend/models/售后队列模型.py：
CREATE TABLE IF NOT EXISTS aftersale_queue (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id            TEXT NOT NULL,
    shop_id             TEXT NOT NULL,

    -- 列表页抓取的摘要信息
    订单号               TEXT NOT NULL,
    售后类型             TEXT,           -- 退款/退货退款/补寄/换货/维修
    售后状态             TEXT,           -- 待商家处理/退款中/已完成/...
    退款金额             REAL DEFAULT 0,
    商品名称             TEXT,

    -- 详情页抓取的完整信息（JSON，一次性存整个 dict）
    详情数据             TEXT DEFAULT '{}',

    -- 详情页抓取的关键字段（从详情数据提取，方便 SQL 查询）
    申请原因             TEXT,
    售后申请说明         TEXT,
    发货物流公司         TEXT,
    发货快递单号         TEXT,
    有售后图片           INTEGER DEFAULT 0,
    物流最新状态         TEXT,
    物流最新时间         TEXT,
    收货城市             TEXT,
    剩余处理时间         TEXT,
    平台建议             TEXT,

    -- 详情页读取的当前可用按钮（JSON 数组）
    可用按钮列表         TEXT DEFAULT '[]',

    -- 协商信息
    协商轮次             INTEGER DEFAULT 0,
    商家已回复           INTEGER DEFAULT 0,

    -- 生命周期管理
    当前阶段             TEXT DEFAULT '待处理',
    -- 待处理/处理中/已完成/失败/跳过/人工审核/等待退回/等待验货/待退款
    处理次数             INTEGER DEFAULT 0,
    最大处理次数         INTEGER DEFAULT 5,
    下次处理时间         TEXT,
    拒绝次数             INTEGER DEFAULT 0,
    上次拒绝时间         TEXT,

    -- 决策与结果
    匹配规则名           TEXT,
    决策动作             TEXT,           -- JSON
    处理结果             TEXT,
    错误信息             TEXT,

    -- 时间戳
    created_at          TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at          TEXT DEFAULT (datetime('now', 'localtime'))
);
​
同时提供 初始化售后队列表(连接) 方法。
四、售后队列服务
backend/services/售后队列服务.py：
class 售后队列服务:
    """售后工作队列 CRUD + 批次管理。"""

    async def 创建批次(self, shop_id: str) -> str:
        """生成新的 batch_id（格式: AS-{shop_id}-{时间戳}）。"""

    async def 写入队列(self, 记录: dict) -> int:
        """写入一条售后单到队列（从列表页扫描阶段调用）。"""

    async def 批量写入队列(self, 记录列表: list[dict]) -> int:
        """批量写入。返回实际写入条数（去重：同 batch_id + 同订单号不重复写）。"""

    async def 更新详情(self, id: int, 详情数据: dict) -> bool:
        """从详情页抓取后更新完整信息。"""

    async def 更新阶段(self, id: int, 阶段: str, 
                      下次处理时间: str = None,
                      拒绝次数: int = None,
                      处理结果: str = None,
                      错误信息: str = None) -> bool:
        """更新售后单的处理阶段和相关字段。"""

    async def 获取待处理列表(self, batch_id: str = None, 
                           shop_id: str = None) -> list[dict]:
        """获取当前阶段为'待处理'的记录。"""

    async def 获取到期记录(self) -> list[dict]:
        """获取 下次处理时间 <= now 且 当前阶段 in ('待处理','等待退回','等待验货','待退款') 的记录。"""

    async def 查询拒绝次数(self, 订单号: str) -> int:
        """查询某订单的累计拒绝次数。"""

    async def 标记已完成(self, id: int, 处理结果: str = "成功") -> bool

    async def 标记已被处理(self, id: int) -> bool:
        """人工已处理，跳过。"""

    async def 标记人工(self, id: int, 原因: str = "") -> bool

    async def 获取批次统计(self, batch_id: str) -> dict:
        """返回批次统计：总数/已完成/失败/人工/待处理。"""
​
五、售后页 POM 新增方法
在 pages/售后页.py 中新增以下方法（不删除现有方法）：
5.1 列表翻页扫描
async def 扫描所有待处理(self) -> list[dict]:
    """扫描所有"待商家处理"的售后单（含翻页），返回摘要列表。
    
    流程：
    1. 切换到"待商家处理"Tab
    2. 读取当前页所有行的摘要
    3. 翻页 → 继续读取
    4. 直到无法翻页
    
    返回: [{"订单号", "售后类型", "退款金额", "商品名称", "售后状态"}, ...]
    """
    所有记录 = []
    while True:
        数量 = await self.获取售后单数量()
        for 行号 in range(1, 数量 + 1):
            信息 = await self.获取第N行信息(行号)
            if 信息.get("订单号"):
                所有记录.append(信息)
        if not await self.翻页():
            break
    return 所有记录
​
5.2 新标签页管理
async def 点击详情并切换标签(self, 行号: int) -> None:
    """点击查看详情，等待新标签页打开，切换到新标签页。
    
    拼多多点"查看详情"会打开新标签页。
    """
    上下文 = self.页面.context
    原始页面数 = len(上下文.pages)
    await self.点击第N行详情(行号)
    
    # 等待新标签页
    新页面 = await 上下文.wait_for_event("page", timeout=10000)
    await 新页面.wait_for_load_state("domcontentloaded")
    self._详情页 = 新页面
    print(f"[售后页] 已切换到详情标签页: {新页面.url}")

async def 关闭详情标签(self) -> None:
    """关闭详情标签页，焦点回到列表页。"""
    if self._详情页 and not self._详情页.is_closed():
        await self._详情页.close()
        self._详情页 = None
    print("[售后页] 详情标签已关闭")
​
5.3 详情页完整信息抓取（核心 — 全用 JS）
async def 抓取详情页完整信息(self) -> dict:
    """从售后详情新标签页用 JS 一次性抓取所有关键信息。
    
    不依赖固定选择器，而是通过 JS 扫描页面文本和 DOM 结构。
    """
    目标页面 = self._详情页 or self.页面
    
    结果 = await 目标页面.evaluate("""
        () => {
            const 清洗 = (s) => String(s || '').replace(/\\s+/g, ' ').trim();
            const 全文 = 清洗(document.body.innerText);
            
            // ---- 辅助函数 ----
            const 提取字段 = (标签文本) => {
                // 找到包含标签文本的元素，取其后面的文本
                const 所有元素 = document.querySelectorAll('td, div, span, p, label');
                for (const 元素 of 所有元素) {
                    const 文本 = 清洗(元素.textContent);
                    if (文本.startsWith(标签文本)) {
                        // "退款金额：¥6.08" → "¥6.08"
                        const 值 = 文本.replace(标签文本, '').replace(/^[：:：\\s]+/, '');
                        if (值) return 值;
                    }
                }
                // 备选：找 label + 相邻元素
                for (const 元素 of 所有元素) {
                    if (清洗(元素.textContent) === 标签文本) {
                        const 下一个 = 元素.nextElementSibling;
                        if (下一个) return 清洗(下一个.textContent);
                    }
                }
                return '';
            };
            
            // ---- 读取所有可用按钮 ----
            const 读取按钮 = () => {
                const 按钮 = document.querySelectorAll(
                    'button:not(:disabled), a.ant-btn:not(.ant-btn-disabled)'
                );
                return Array.from(按钮)
                    .map(b => 清洗(b.textContent))
                    .filter(t => t.length > 0 && t.length < 30);
            };
            
            // ---- 读取物流轨迹最新一条 ----
            const 读取物流 = () => {
                // 物流轨迹通常是时间线列表
                const 轨迹项 = document.querySelectorAll(
                    '.logistics-item, .timeline-item, .ant-timeline-item'
                );
                if (轨迹项.length > 0) {
                    return 清洗(轨迹项[0].textContent);
                }
                // 备选：找"物流轨迹"附近的文本
                return '';
            };
            
            // ---- 判断是否有图片 ----
            const 有图片 = () => {
                // 售后图片通常在申请单区域
                const 图片 = document.querySelectorAll(
                    'img[src*="upload"], img[src*="pic"], .image-preview img'
                );
                // 排除logo等小图
                for (const img of 图片) {
                    const w = img.naturalWidth || img.width || 0;
                    if (w > 50) return true;
                }
                return false;
            };
            
            // ---- 读取聊天记录 ----
            const 读取聊天 = () => {
                const 聊天项 = document.querySelectorAll(
                    '.chat-item, .message-item, .chat-record-item'
                );
                if (聊天项.length === 0) return { 发送方: '', 内容: '', 商家已回复: false };
                const 最新 = 聊天项[聊天项.length - 1];
                const 文本 = 清洗(最新.textContent);
                const 商家已回复 = Array.from(聊天项).some(
                    项 => 清洗(项.textContent).includes('售后') || 
                          清洗(项.textContent).includes('商家')
                );
                return { 发送方: '', 内容: 文本, 商家已回复 };
            };
            
            // ---- 提取退款金额数值 ----
            const 提取金额 = (文本) => {
                const 匹配 = String(文本).match(/[¥￥]\\s*(\\d+\\.?\\d*)/);
                return 匹配 ? parseFloat(匹配[1]) : 0;
            };
            
            // ---- 提取剩余时间 ----
            const 提取剩余时间 = () => {
                const 匹配 = 全文.match(/(\\d+时\\d+分\\d+秒)/);
                return 匹配 ? 匹配[1] : '';
            };
            
            // ---- 从地址提取城市 ----
            const 提取城市 = (地址) => {
                // "安徽省合肥市肥西县 ****" → "合肥"
                const 匹配 = String(地址).match(/省(.+?)[市州]/);
                return 匹配 ? 匹配[1] : '';
            };
            
            // ---- 协商轮次 ----
            const 计算协商轮次 = () => {
                const 申请项 = document.querySelectorAll(
                    '.negotiate-item, .apply-item, .协商记录'
                );
                return 申请项.length || 0;
            };

            // ---- 组装结果 ----
            const 售后编号 = 提取字段('售后编号');
            const 售后类型 = 提取字段('售后类型');
            const 发货状态 = 提取字段('发货状态');
            const 退款金额文本 = 提取字段('退款金额');
            const 申请原因 = 提取字段('申请原因');
            const 售后申请说明 = 提取字段('售后申请说明');
            const 发货物流公司 = 提取字段('发货物流公司');
            const 发货快递单号 = 提取字段('发货快递单号');
            const 订单编号 = 提取字段('订单编号');
            const 商品名称 = 提取字段('商品名称') || 提取字段('商品');
            const 收货地址 = 提取字段('联系地址') || 提取字段('收货地址');
            const 物流信息 = 读取物流();
            const 聊天信息 = 读取聊天();
            const 按钮列表 = 读取按钮();
            
            return {
                售后编号,
                售后类型: 清洗(售后类型.split(/[，,]/)[0]),
                售后状态: 清洗(售后类型.includes('待') ? 
                    售后类型.substring(售后类型.indexOf('待')) : ''),
                发货状态,
                退款金额: 提取金额(退款金额文本),
                退款金额文本,
                实收金额: 提取金额(提取字段('实收')),
                申请原因,
                售后申请说明,
                发货物流公司,
                发货快递单号,
                有售后图片: 有图片(),
                订单编号,
                商品名称,
                收货地址,
                收货城市: 提取城市(收货地址),
                物流最新状态: 物流信息,
                剩余处理时间: 提取剩余时间(),
                平台建议: 提取字段('平台建议') || '',
                可用按钮列表: 按钮列表,
                协商轮次: 计算协商轮次(),
                最新聊天内容: 聊天信息.内容,
                商家已回复: 聊天信息.商家已回复,
                
                // 便于判断的布尔值
                有同意退款按钮: 按钮列表.some(b => b.includes('同意退款')),
                有同意拒收后退款按钮: 按钮列表.some(b => b.includes('拒收后退款')),
                有同意退货按钮: 按钮列表.some(b => b.includes('同意退货')),
                有拒绝按钮: 按钮列表.some(b => b.includes('拒绝')),
                有免费退如快递拦截按钮: 按钮列表.some(b => b.includes('快递拦截')),
                有添加留言按钮: 按钮列表.some(b => b.includes('留言') || b.includes('凭证')),
            };
        }
    """)
    
    print(f"[售后页] 详情抓取完成: 订单={结果.get('订单编号')}, 类型={结果.get('售后类型')}, "
          f"按钮={结果.get('可用按钮列表')}")
    return dict(结果 or {})
​
5.4 动态按钮操作（JS 直接点击）
async def 点击指定按钮(self, 按钮文本: str) -> bool:
    """在详情页通过 JS 查找并点击包含指定文本的按钮。
    
    不依赖选择器，直接遍历所有 button/a 元素匹配文本。
    """
    目标页面 = self._详情页 or self.页面
    结果 = await 目标页面.evaluate("""
        (按钮文本) => {
            const buttons = document.querySelectorAll(
                'button:not(:disabled), a.ant-btn:not(.ant-btn-disabled)'
            );
            for (const btn of buttons) {
                if (btn.textContent.trim().includes(按钮文本)) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }
    """, 按钮文本)
    if 结果:
        await self.操作后延迟()
        print(f"[售后页] 已点击按钮: {按钮文本}")
    else:
        print(f"[售后页] 未找到按钮: {按钮文本}")
    return 结果

async def 读取当前所有按钮(self) -> list[str]:
    """用 JS 读取当前页面（列表页或详情页）所有可点击按钮的文本。"""
    目标页面 = self._详情页 or self.页面
    return await 目标页面.evaluate("""
        () => {
            const buttons = document.querySelectorAll(
                'button:not(:disabled), a.ant-btn:not(.ant-btn-disabled)'
            );
            return Array.from(buttons)
                .map(b => b.textContent.trim())
                .filter(t => t.length > 0 && t.length < 30);
        }
    """)
​
5.5 检查订单是否还在
async def 检查订单是否待处理(self) -> bool:
    """在详情页检查售后状态是否仍为"待商家处理"。"""
    目标页面 = self._详情页 or self.页面
    全文 = await 目标页面.evaluate("() => document.body.innerText")
    return "待商家处理" in str(全文) or "待卖家处理" in str(全文)
​
5.6 截图（详情页）
async def 详情页截图(self, 名称: str) -> str | None:
    """对详情标签页截图。"""
    目标页面 = self._详情页 or self.页面
    路径 = f"data/screenshots/{名称}.png"
    try:
        await 目标页面.screenshot(path=路径, full_page=True)
        print(f"[售后页] 截图保存: {路径}")
        return 路径
    except Exception as 异常:
        print(f"[售后页] 截图失败: {异常}")
        return None
​
六、售后页选择器修改
在 selectors/售后页选择器.py 中新增：
# 列表页"待商家处理"Tab（更精确的选择器）
待商家处理Tab = 选择器配置(
    主选择器="//div[contains(@class, 'ant-tabs-tab') and contains(., '待商家处理')]",
    备选选择器=[
        "//div[contains(@class, 'ant-tabs-tab') and contains(., '待处理')]",
    ],
)
​
并将 售后页.切换待处理() 改为优先使用 待商家处理Tab。
七、数据库.py 修改
在 获取建表语句列表() 中加入：
from backend.models.售后队列模型 import 售后队列建表SQL
# 加入列表
售后队列建表SQL,
​
在 初始化数据库() 中调用 初始化售后队列表(连接)。
八、测试
test_售后队列服务.py（新建）
测试 创建批次：格式正确
测试 写入队列 + 获取待处理列表
测试 批量写入队列 去重（同 batch_id + 同订单号）
测试 更新详情：详情数据 JSON 写入和关键字段提取
测试 更新阶段：阶段、拒绝次数、下次处理时间正确更新
测试 获取到期记录：只返回到期且未完成的
测试 查询拒绝次数
测试 获取批次统计
test_售后页.py（修改，补充）
mock Playwright，测试 扫描所有待处理（含翻页循环）
mock context.wait_for_event，测试 点击详情并切换标签
mock evaluate，测试 抓取详情页完整信息 返回完整 dict
mock evaluate，测试 点击指定按钮 JS 执行
mock evaluate，测试 读取当前所有按钮
测试 检查订单是否待处理
测试 关闭详情标签
九、约束
详情页抓取全用 JS evaluate，不依赖固定 XPath 选择器（拼多多改版时只需改 JS 里的标签文本匹配逻辑）
抓取详情页完整信息 是一个大 JS，一次性执行，减少网络往返
列表页的 获取第N行信息 保留现有实现（列表页结构相对稳定）
售后队列表去重：同一个 batch_id 内同一个订单号不重复写入
_详情页 属性在 __init__ 中初始化为 None
不修改 tasks/售后任务.py（46B 再改）
不修改 backend/api/ 目录（队列 API 在 46C 再加）
pytest 全量通过