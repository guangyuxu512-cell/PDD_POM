Task 46B：决策引擎 + 弹窗扫描器 + 售后任务重写 + 选择器校准
一、做什么
校准售后页选择器和 URL（基于真实页面）
售后页 POM 新增：确保待商家处理选中、按订单号点详情、弹窗扫描器、检查是否需要处理
新建决策引擎（基于可用按钮 + 规则 + 拒绝次数做判断）
重写售后任务：扫描写入队列 → 逐条打开详情 → 实时读取 → 决策 → 执行 → 弹窗处理
二、涉及文件
selectors/售后页选择器.py — 修改（URL + 卡片选择器 + 行结构 + 详情链接）
pages/售后页.py — 修改（新增方法 + 校准 JS 字段匹配）
backend/services/售后决策引擎.py — 新建
tasks/售后任务.py — 重写
tests/test_售后决策引擎.py — 新建
tests/test_售后任务.py — 重写
tests/test_售后页.py — 修改（补充新方法测试）
三、选择器校准
selectors/售后页选择器.py 修改：
class 售后页选择器:

    # URL 校准
    售后列表页URL = "https://mms.pinduoduo.com/aftersales/aftersale_list?msfrom=mms_sidenav"

    # ========== 工作台卡片 ==========

    待商家处理卡片 = 选择器配置(
        主选择器='//span[text()="待商家处理"]/ancestor::div[@data-testid="beast-core-card"]',
    )

    # 选中状态 class 包含 CAD_beastCardChecked
    待商家处理选中类名片段 = "CAD_beastCardChecked"

    # ========== 售后单行（order_item 而非 ant-table-row） ==========

    售后单行 = 选择器配置(
        主选择器='//div[contains(@class, "order_item")]',
        备选选择器=[
            "//tr[contains(@class, 'ant-table-row')]",  # 兼容旧版
        ],
    )

    # ========== 按订单号定位查看详情 ==========

    @staticmethod
    def 获取订单详情链接(订单号: str) -> 选择器配置:
        """按订单号定位该行的"查看详情"链接。"""
        return 选择器配置(
            主选择器=f'//span[text()="{订单号}"]/ancestor::div[contains(@class, "order_item")]//a[span[text()="查看详情"]]',
            备选选择器=[
                f'//span[text()="{订单号}"]/ancestor::div[contains(@class, "order_item")]//a[contains(., "详情")]',
            ],
        )

    @staticmethod
    def 获取订单操作按钮(订单号: str, 操作文本: str) -> 选择器配置:
        """按订单号定位该行的指定操作按钮。"""
        return 选择器配置(
            主选择器=f'//span[text()="{订单号}"]/ancestor::div[contains(@class, "order_item")]//a[span[text()="{操作文本}"]] | //span[text()="{订单号}"]/ancestor::div[contains(@class, "order_item")]//button[span[text()="{操作文本}"]]',
        )

    # 保留现有的行号版本（兼容），但新逻辑优先用订单号版本
​
四、售后页 POM 新增方法
4.1 确保待商家处理已选中
async def 确保待商家处理已选中(self) -> None:
    """检查"待商家处理"卡片是否选中，未选中则点击。"""
    卡片选择器 = 售后页选择器.待商家处理卡片.主选择器
    类名片段 = 售后页选择器.待商家处理选中类名片段
    
    已选中 = await self.页面.evaluate("""
        ({ 选择器, 类名片段 }) => {
            const 查询 = (sel) => {
                if (sel.startsWith('//')) {
                    return document.evaluate(sel, document, null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                }
                return document.querySelector(sel);
            };
            const 节点 = 查询(选择器);
            if (!节点) return false;
            return 节点.className.includes(类名片段);
        }
    """, {"选择器": 卡片选择器, "类名片段": 类名片段})
    
    if not 已选中:
        await self.安全点击(卡片选择器)
        await self.页面加载延迟()
        print("[售后页] 已点击待商家处理卡片")
    else:
        print("[售后页] 待商家处理卡片已选中")
​
4.2 按订单号点击查看详情
async def 点击订单详情(self, 订单号: str) -> None:
    """按订单号定位并点击"查看详情"链接。"""
    选择器配置 = 售后页选择器.获取订单详情链接(订单号)
    最后异常 = None
    for 选择器 in 选择器配置.所有选择器():
        try:
            await self.安全点击(选择器)
            await self.操作后延迟()
            print(f"[售后页] 已点击订单详情: {订单号}")
            return
        except Exception as 异常:
            最后异常 = 异常
    raise RuntimeError(f"订单 {订单号} 查看详情点击失败: {最后异常}")

async def 点击订单详情并切换标签(self, 订单号: str) -> None:
    """按订单号点击查看详情，等待新标签页打开并切换。"""
    上下文 = self.页面.context
    await self.点击订单详情(订单号)
    新页面 = await 上下文.wait_for_event("page", timeout=10000)
    await 新页面.wait_for_load_state("domcontentloaded")
    self._详情页 = 新页面
    print(f"[售后页] 已切换到详情标签页: {订单号}")
​
4.3 检查是否还需要处理
async def 检查是否需要处理(self) -> bool:
    """详情页有操作按钮 = 需要处理，没有 = 已被处理。"""
    按钮列表 = await self.读取当前所有按钮()
    操作关键词 = ["同意退款", "同意退货", "拒绝", "拒收后退款", "快递拦截"]
    for 按钮文本 in 按钮列表:
        for 关键词 in 操作关键词:
            if 关键词 in 按钮文本:
                return True
    return False
​
4.4 JS 字段匹配校准
修改 抓取详情页完整信息 中的 JS，基于真实页面校准：
// 校准后的字段提取
const 售后编码 = 提取字段('售后编码');     // 不是"售后编号"
const 售后类型 = 提取字段('售后类型');
const 发货状态 = 提取字段('发货状态');     // 值: "未收到货"/"已收到货" 等
const 退款金额文本 = 提取字段('退款金额');
const 申请原因 = 提取字段('申请原因');
const 售后申请说明 = 提取字段('售后申请说明');
const 发货物流公司 = 提取字段('发货物流公司');
const 发货快递单号 = 提取字段('发货快递单号');
const 订单编号 = 提取字段('订单编号');     // 不是"订单号"
const 联系地址 = 提取字段('联系地址');     // 不是"收货地址"
const 收货人 = 提取字段('收货人');
const 退货包运费 = 提取字段('退货包运费');
const 成团时间 = 提取字段('成团时间');
const 实收金额文本 = 提取字段('实收');

// 商品名称：没有标签，从商品描述区域提取
// 在 order_item 或商品图片附近找长文本
const 商品名称 = (() => {
    const 所有文本 = Array.from(document.querySelectorAll('div, span, p'))
        .map(e => 清洗(e.textContent))
        .filter(t => t.length > 10 && t.length < 100)
        .filter(t => !t.includes('售后') && !t.includes('退款') && 
                     !t.includes('订单') && !t.includes('物流'));
    // 找包含商品特征词的（件/支/个/包/套）
    return 商品名称候选 = 所有文本.find(t => /\d+[件支个包套]/.test(t)) || '';
})();

// 协商详情区域的最新内容
const 协商最新 = (() => {
    const 全文 = 清洗(document.body.innerText);
    // 找"处理账号"附近的留言
    const 匹配 = 全文.match(/留言[：:]\s*(.+?)(?=买家申请|$)/);
    return 匹配 ? 匹配[1].trim() : '';
})();

// 售后状态区的描述文本（不是简单枚举）
const 售后状态描述 = (() => {
    // 找"售后状态"标题后面的第一段描述
    const 全文 = 清洗(document.body.innerText);
    const 匹配 = 全文.match(/售后状态\s+(.+?)(?=\d+\s*[天时分秒])/);
    return 匹配 ? 匹配[1].trim() : '';
})();
​
4.5 弹窗扫描器
async def 弹窗扫描循环(self, 弹窗偏好: dict = None, 最大轮次: int = 8) -> str:
    """点击操作按钮后，循环检测并处理弹窗。
    
    返回: "成功" / "人工处理" / "无弹窗"
    """
    目标页面 = self._详情页 or self.页面
    偏好 = 弹窗偏好 or {}
    
    for 轮次 in range(最大轮次):
        await self.随机延迟(0.5, 1.5)
        
        弹窗信息 = await 目标页面.evaluate("""
            () => {
                const 清洗 = (s) => String(s || '').replace(/\\s+/g, ' ').trim();
                
                // 检测弹窗（ant-modal / dialog / 弹层）
                const 弹窗 = document.querySelector(
                    '.ant-modal-content, .ant-drawer-content, [role="dialog"]'
                );
                if (!弹窗) return null;
                
                const 文本 = 清洗(弹窗.innerText);
                
                // 读取弹窗内按钮
                const 按钮 = Array.from(弹窗.querySelectorAll('button'))
                    .map(b => 清洗(b.textContent))
                    .filter(t => t.length > 0 && t.length < 20);
                
                // 有无下拉选择框
                const 选择框 = 弹窗.querySelectorAll(
                    'select, .ant-select, [role="listbox"]'
                );
                
                // 有无单选/多选
                const 单选 = 弹窗.querySelectorAll(
                    '.ant-radio-wrapper, .ant-checkbox-wrapper, [role="radio"], [role="checkbox"]'
                );
                const 单选文本 = Array.from(单选).map(r => 清洗(r.textContent));
                
                // 有无输入框
                const 输入框 = 弹窗.querySelectorAll('input, textarea');
                
                // 有无翻页
                const 翻页 = 弹窗.querySelector('.ant-pagination');
                
                return {
                    文本: 文本,
                    按钮: 按钮,
                    有选择框: 选择框.length > 0,
                    单选选项: 单选文本,
                    有输入框: 输入框.length > 0,
                    有翻页: 翻页 !== null,
                };
            }
        """)
        
        if not 弹窗信息:
            print(f"[弹窗扫描] 第{轮次+1}轮: 无弹窗")
            return "无弹窗" if 轮次 == 0 else "成功"
        
        print(f"[弹窗扫描] 第{轮次+1}轮: 按钮={弹窗信息['按钮']}, 单选={弹窗信息['单选选项']}")
        
        # ---- 处理逻辑 ----
        处理结果 = await self._处理单个弹窗(目标页面, 弹窗信息, 偏好)
        
        if 处理结果 == "人工处理":
            await self.详情页截图(f"未识别弹窗_轮次{轮次+1}")
            return "人工处理"
    
    return "人工处理"  # 超过最大轮次

async def _处理单个弹窗(self, 页面, 弹窗信息: dict, 偏好: dict) -> str:
    """处理单个弹窗，返回 "继续" / "人工处理"。"""
    
    文本 = 弹窗信息["文本"]
    按钮 = 弹窗信息["按钮"]
    单选选项 = 弹窗信息["单选选项"]
    
    # ---- 类型A: 纯确认框（只有确定/取消，没有选择和输入） ----
    if (not 弹窗信息["有选择框"] and 
        not 弹窗信息["有输入框"] and 
        len(单选选项) == 0):
        
        确认词 = ["确定", "确认", "知道了", "好的"]
        for 词 in 确认词:
            for 按钮文本 in 按钮:
                if 词 in 按钮文本:
                    await self._JS点击弹窗按钮(页面, 按钮文本)
                    return "继续"
        # 有按钮但不认识
        return "人工处理"
    
    # ---- 类型B: 有单选选项（拒绝理由、退款原因等） ----
    if len(单选选项) > 0:
        # 按偏好列表匹配
        偏好列表 = 偏好.get("选项偏好", [])
        
        for 偏好值 in 偏好列表:
            for 选项 in 单选选项:
                if 偏好值 in 选项:
                    await self._JS点击包含文本(页面, 选项)
                    # 选完后点确定
                    for 按钮文本 in 按钮:
                        if "确" in 按钮文本 or "提交" in 按钮文本:
                            await self.随机延迟(0.3, 0.8)
                            await self._JS点击弹窗按钮(页面, 按钮文本)
                            break
                    return "继续"
        
        # 没有偏好或没匹配到：如果只有一个选项就直接选
        if len(单选选项) == 1:
            await self._JS点击包含文本(页面, 单选选项[0])
            for 按钮文本 in 按钮:
                if "确" in 按钮文本 or "提交" in 按钮文本:
                    await self.随机延迟(0.3, 0.8)
                    await self._JS点击弹窗按钮(页面, 按钮文本)
                    break
            return "继续"
        
        return "人工处理"
    
    # ---- 类型C: 有下拉选择框 ----
    if 弹窗信息["有选择框"]:
        偏好值 = 偏好.get("下拉偏好", "")
        if 偏好值:
            await self._JS选择下拉选项(页面, 偏好值)
            for 按钮文本 in 按钮:
                if "确" in 按钮文本 or "提交" in 按钮文本:
                    await self.随机延迟(0.3, 0.8)
                    await self._JS点击弹窗按钮(页面, 按钮文本)
                    break
            return "继续"
        return "人工处理"
    
    # ---- 类型D: 有输入框（备注、留言） ----
    if 弹窗信息["有输入框"]:
        填写内容 = 偏好.get("输入内容", "")
        if 填写内容:
            await self._JS填写弹窗输入框(页面, 填写内容)
            for 按钮文本 in 按钮:
                if "确" in 按钮文本 or "提交" in 按钮文本:
                    await self.随机延迟(0.3, 0.8)
                    await self._JS点击弹窗按钮(页面, 按钮文本)
                    break
            return "继续"
        return "人工处理"
    
    return "人工处理"

# ---- JS 辅助方法 ----

async def _JS点击弹窗按钮(self, 页面, 按钮文本: str) -> bool:
    """在弹窗内点击指定文本的按钮。"""
    结果 = await 页面.evaluate("""
        (文本) => {
            const 弹窗 = document.querySelector(
                '.ant-modal-content, .ant-drawer-content, [role="dialog"]'
            );
            if (!弹窗) return false;
            const 按钮列表 = 弹窗.querySelectorAll('button');
            for (const btn of 按钮列表) {
                if (btn.textContent.trim().includes(文本) && !btn.disabled) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }
    """, 按钮文本)
    if 结果:
        await self.操作后延迟()
        print(f"[弹窗扫描] 已点击弹窗按钮: {按钮文本}")
    return 结果

async def _JS点击包含文本(self, 页面, 文本: str) -> bool:
    """在弹窗内点击包含指定文本的单选/多选/选项。"""
    结果 = await 页面.evaluate("""
        (文本) => {
            const 弹窗 = document.querySelector(
                '.ant-modal-content, .ant-drawer-content, [role="dialog"]'
            );
            if (!弹窗) return false;
            const 候选 = 弹窗.querySelectorAll(
                '.ant-radio-wrapper, .ant-checkbox-wrapper, [role="radio"], [role="checkbox"], .ant-select-item, label'
            );
            for (const 元素 of 候选) {
                if (元素.textContent.trim().includes(文本)) {
                    元素.click();
                    return true;
                }
            }
            return false;
        }
    """, 文本)
    if 结果:
        await self.随机延迟(0.2, 0.5)
        print(f"[弹窗扫描] 已选择选项: {文本}")
    return 结果

async def _JS选择下拉选项(self, 页面, 偏好值: str) -> bool:
    """点击下拉框并选择包含偏好值的选项。"""
    结果 = await 页面.evaluate("""
        (偏好值) => {
            const 弹窗 = document.querySelector(
                '.ant-modal-content, .ant-drawer-content, [role="dialog"]'
            );
            if (!弹窗) return false;
            // 先点击 select 打开下拉
            const 选择器 = 弹窗.querySelector('.ant-select, select');
            if (选择器) 选择器.click();
            // 等下拉展开后选择（通过 setTimeout 异步）
            return new Promise(resolve => {
                setTimeout(() => {
                    const 选项列表 = document.querySelectorAll(
                        '.ant-select-item, .ant-select-dropdown .ant-select-item-option, option'
                    );
                    for (const 选项 of 选项列表) {
                        if (选项.textContent.trim().includes(偏好值)) {
                            选项.click();
                            resolve(true);
                            return;
                        }
                    }
                    resolve(false);
                }, 500);
            });
        }
    """, 偏好值)
    if 结果:
        await self.随机延迟(0.2, 0.5)
        print(f"[弹窗扫描] 已选择下拉: {偏好值}")
    return 结果

async def _JS填写弹窗输入框(self, 页面, 内容: str) -> bool:
    """在弹窗内的输入框/文本域填写内容。"""
    return await 页面.evaluate("""
        (内容) => {
            const 弹窗 = document.querySelector(
                '.ant-modal-content, .ant-drawer-content, [role="dialog"]'
            );
            if (!弹窗) return false;
            const 输入框 = 弹窗.querySelector('textarea, input[type="text"], input:not([type])');
            if (!输入框) return false;
            输入框.focus();
            输入框.value = 内容;
            输入框.dispatchEvent(new Event('input', { bubbles: true }));
            输入框.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
        }
    """, 内容)
​
五、决策引擎
backend/services/售后决策引擎.py：
"""售后决策引擎 — 基于详情页抓取信息 + 可用按钮 + 规则配置做决策。"""
from __future__ import annotations

from backend.services.规则服务 import 规则服务
from backend.services.售后队列服务 import 售后队列服务
​
class 售后决策引擎:
def init(self):
self._规则服务 = 规则服务()
self._队列服务 = 售后队列服务()
async def 决策(self, 详情: dict, 规则配置: dict, 队列记录: dict) -> dict:
"""根据详情页信息做出处理决策。
Args:
详情: 抓取详情页完整信息() 的返回值
规则配置: 规则匹配结果（含弹窗偏好等）
队列记录: SQLite aftersale_queue 中的记录（含拒绝次数等）
Returns:
{
"操作": "同意退款" / "同意退货" / "拒绝" / "人工处理" / "跳过",
"目标按钮": "同意退款",       # 要点击的按钮文本
"备选按钮": ["同意拒收后退款"], # 主按钮找不到时的备选
"弹窗偏好": {...},             # 传给弹窗扫描器
"需要备注": False,
"备注内容": "",
"需要飞书通知": False,
"飞书通知内容": "",
"人工原因": "",               # 如果是人工处理，说明原因
}
"""
售后类型 = str(详情.get("售后类型", "")).strip()
金额 = float(详情.get("退款金额", 0))
可用按钮 = 详情.get("可用按钮列表", [])
发货状态 = str(详情.get("发货状态", "")).strip()
有售后图片 = 详情.get("有售后图片", False)
拒绝次数 = int(队列记录.get("拒绝次数", 0))
兜底模板
结果 = {
"操作": "人工处理",
"目标按钮": "",
"备选按钮": [],
"弹窗偏好": {},
"需要备注": False,
"备注内容": "",
"需要飞书通知": True,
"飞书通知内容": "",
"人工原因": "",
}
没有可操作按钮 → 已被处理
if not self._有操作按钮(可用按钮):
结果["操作"] = "跳过"
结果["人工原因"] = "详情页无操作按钮，可能已被人工处理"
结果["需要飞书通知"] = False
return 结果
========== 退货退款 ==========
if "退货退款" in 售后类型:
return await self._决策_退货退款(详情, 可用按钮, 规则配置, 结果)
========== 退款 ==========
if "退款" in 售后类型 and "退货" not in 售后类型:
return await self._决策_退款(详情, 可用按钮, 规则配置, 队列记录, 结果)
========== 补寄/换货/维修 ==========
结果["人工原因"] = f"{售后类型}暂不支持自动处理"
return 结果
async def _决策_退货退款(self, 详情, 可用按钮, 规则配置, 结果) -> dict:
"""退货退款决策。"""
有"同意退货"按钮 → 买家还没寄回
if any("同意退货" in b for b in 可用按钮):
结果["操作"] = "同意退货"
结果["目标按钮"] = "同意退货"
结果["需要飞书通知"] = False
return 结果
有"同意退款"按钮 → 买家已退货且确认收到
if any("同意退款" in b for b in 可用按钮):
结果["操作"] = "同意退款"
结果["目标按钮"] = "同意退款"
结果["需要飞书通知"] = False
return 结果
结果["人工原因"] = f"退货退款但无可用操作按钮: {可用按钮}"
return 结果
async def _决策_退款(self, 详情, 可用按钮, 规则配置, 队列记录, 结果) -> dict:
"""退款决策（最复杂）。"""
金额 = float(详情.get("退款金额", 0))
有售后图片 = 详情.get("有售后图片", False)
发货状态 = str(详情.get("发货状态", ""))
物流状态 = str(详情.get("物流最新状态", ""))
拒绝次数 = int(队列记录.get("拒绝次数", 0))
自动同意上限 = float(规则配置.get("自动同意金额上限", 10))
需要拒绝 = bool(规则配置.get("需要拒绝", False))
---- 小额直接同意 ----
if 金额 <= 自动同意上限:
目标 = self._找按钮(可用按钮, ["同意退款", "同意拒收后退款"])
if 目标:
结果["操作"] = "同意退款"
结果["目标按钮"] = 目标
结果["需要备注"] = True
结果["备注内容"] = "小额自动退款"
结果["需要飞书通知"] = False
return 结果
---- 有售后图片 → 人工 ----
if 有售后图片:
结果["人工原因"] = "有售后图片需人工查看"
结果["飞书通知内容"] = f"订单{详情.get('订单编号')}有售后图片，请人工审核"
return 结果
---- 物流拒收 → 同意拒收后退款 ----
if "拒收" in 物流状态 or "退回" in 物流状态:
目标 = self._找按钮(可用按钮, ["同意拒收后退款", "同意退款"])
if 目标:
结果["操作"] = "同意拒收退款"
结果["目标按钮"] = 目标
结果["需要飞书通知"] = False
return 结果
---- 需要拒绝且还没拒绝满3次 ----
if 需要拒绝 and 拒绝次数 < 3:
目标 = self._找按钮(可用按钮, ["拒绝"])
if 目标:
结果["操作"] = "拒绝"
结果["目标按钮"] = 目标
结果["弹窗偏好"] = 规则配置.get("弹窗偏好", {})
结果["需要备注"] = True
结果["备注内容"] = f"系统拒绝第{拒绝次数 + 1}次"
结果["需要飞书通知"] = False
return 结果
---- 已拒绝3次 ----
if 需要拒绝 and 拒绝次数 >= 3:
结果["操作"] = "跳过"
结果["人工原因"] = "已拒绝3次，不再自动处理"
结果["需要飞书通知"] = True
结果["飞书通知内容"] = f"订单{详情.get('订单编号')}已拒绝3次，请人工跟进"
return 结果
---- 兜底 ----
结果["人工原因"] = f"退款场景未匹配到规则，金额={金额}"
结果["飞书通知内容"] = f"订单{详情.get('订单编号')}需人工处理，金额{金额}"
return 结果
def _有操作按钮(self, 可用按钮: list) -> bool:
操作词 = ["同意退款", "同意退货", "拒绝", "拒收后退款", "快递拦截"]
return any(词 in b for b in 可用按钮 for 词 in 操作词)
def _找按钮(self, 可用按钮: list, 优先级列表: list) -> str:
"""按优先级在可用按钮中找第一个匹配的。"""
for 关键词 in 优先级列表:
for 按钮 in 可用按钮:
if 关键词 in 按钮:
return 按钮
return ""

---

**六、售后任务重写**

`tasks/售后任务.py` 完全重写：

​
"""售后任务模块 — 基于工作队列 + 决策引擎。"""
from future import annotations
import json
from datetime import datetime, timedelta
from typing import Any
from browser.任务回调 import 自动回调, 上报
from backend.services.售后队列服务 import 售后队列服务
from backend.services.售后决策引擎 import 售后决策引擎
from backend.services.规则服务 import 规则服务
from backend.services.飞书服务 import 飞书服务
from pages.售后页 import 售后页
from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task
@register_task("售后处理", "扫描待商家处理售后单，根据规则自动处理")
class 售后任务(基础任务):
def init(self):
self._售后页: 售后页 | None = None
self._队列服务 = 售后队列服务()
self._决策引擎 = 售后决策引擎()
self._规则服务 = 规则服务()
self._飞书服务 = 飞书服务()
self._执行结果: dict[str, Any] = {}
@自动回调("售后处理")
async def 执行(self, 页面, 店铺配置: dict) -> str:
"""主入口。"""
店铺ID = str(店铺配置.get("shop_id", ""))
店铺名称 = str(店铺配置.get("shop_name", ""))
self._售后页 = 售后页(页面)
try:
========== 阶段一：扫描 ==========
await 上报("[扫描] 开始扫描售后列表", 店铺ID)
batch_id = await self._队列服务.创建批次(店铺ID)
await self._售后页.导航到售后列表()
await self._售后页.确保待商家处理已选中()
摘要列表 = await self._售后页.扫描所有待处理()
if not 摘要列表:
await 上报("[完成] 无待处理售后单", 店铺ID)
return "无待处理售后单"
写入队列
记录列表 = [
{
"batch_id": batch_id,
"shop_id": 店铺ID,
"shop_name": 店铺名称,
"订单号": 摘要.get("订单号", ""),
"售后类型": 摘要.get("售后类型", ""),
"退款金额": self._提取金额(摘要.get("退款金额", "")),
"商品名称": 摘要.get("商品名称", ""),
}
for 摘要 in 摘要列表
if 摘要.get("订单号")
]
写入数 = await self._队列服务.批量写入队列(记录列表)
await 上报(f"[扫描] 扫描到 {len(摘要列表)} 单，写入 {写入数} 单", 店铺ID)
========== 阶段二：逐条处理 ==========
待处理列表 = await self._队列服务.获取待处理列表(batch_id=batch_id)
已处理数 = 0
人工数 = 0
跳过数 = 0
for 记录 in 待处理列表:
try:
结果 = await self._处理单条(记录, 店铺配置)
if 结果 == "已处理":
已处理数 += 1
elif 结果 == "人工":
人工数 += 1
else:
跳过数 += 1
except Exception as 异常:
await 上报(f"[失败] 订单{记录.get('订单号')} 异常: {异常}", 店铺ID)
await self._队列服务.更新阶段(
记录["id"], "失败", 错误信息=str(异常)
)
if self._售后页._详情页:
await self.售后页.详情页截图(f"异常{记录.get('订单号')}")
await self._售后页.关闭详情标签()
========== 统计 ==========
汇总 = f"处理{已处理数}单, 人工{人工数}单, 跳过{跳过数}单"
await 上报(f"[完成] {汇总}", 店铺ID)
self._执行结果 = await self._队列服务.获取批次统计(batch_id)
return 汇总
except Exception as 异常:
await 上报(f"[失败] 售后任务异常: {异常}", 店铺ID)
return f"失败: {异常}"
async def _处理单条(self, 记录: dict, 店铺配置: dict) -> str:
"""处理单条售后单。返回 "已处理" / "人工" / "跳过"。"""
店铺ID = str(店铺配置.get("shop_id", ""))
订单号 = str(记录.get("订单号", ""))
await 上报(f"[处理] 订单 {订单号}", 店铺ID)
await self._队列服务.更新阶段(记录["id"], "处理中")
1. 搜索并打开详情
await self._售后页.搜索订单(订单号)
await self._售后页.随机延迟(1, 2)
2. 尝试点击详情
try:
await self._售后页.点击订单详情并切换标签(订单号)
except Exception:
可能已被处理，搜不到了
await self._队列服务.标记已被处理(记录["id"])
return "跳过"
try:
3. 抓取详情页完整信息
详情 = await self._售后页.抓取详情页完整信息()
await self._队列服务.更新详情(记录["id"], 详情)
4. 检查是否还需要处理
if not await self._售后页.检查是否需要处理():
await self._队列服务.标记已被处理(记录["id"])
await self._售后页.关闭详情标签()
return "跳过"
5. 匹配规则
规则结果 = await self._规则服务.匹配规则(
platform="pdd", business="售后",
shop_id=店铺ID, 数据=详情,
)
规则配置 = self._组装规则配置(规则结果)
6. 决策
决策 = await self._决策引擎.决策(详情, 规则配置, 记录)
await 上报(f"[决策] {订单号}: {决策['操作']}", 店铺ID)
7. 执行
if 决策["操作"] == "跳过":
await self._队列服务.标记已被处理(记录["id"])
await self._售后页.关闭详情标签()
return "跳过"
if 决策["操作"] == "人工处理":
await self.售后页.详情页截图(f"人工{订单号}")
await self._队列服务.标记人工(记录["id"], 决策["人工原因"])
if 决策["需要飞书通知"]:
try:
await self._飞书服务.发送售后通知(
详情, 决策.get("飞书通知内容", "需人工处理")
)
except Exception:
pass
await self._售后页.关闭详情标签()
return "人工"
有操作要执行
目标按钮 = 决策["目标按钮"]
点击成功 = await self._售后页.点击指定按钮(目标按钮)
if not 点击成功:
尝试备选按钮
for 备选 in 决策.get("备选按钮", []):
点击成功 = await self._售后页.点击指定按钮(备选)
if 点击成功:
break
if not 点击成功:
await self.售后页.详情页截图(f"按钮未找到{订单号}")
await self._队列服务.标记人工(记录["id"], f"按钮未找到: {目标按钮}")
await self._售后页.关闭详情标签()
return "人工"
8. 弹窗扫描
弹窗结果 = await self._售后页.弹窗扫描循环(决策.get("弹窗偏好", {}))
if 弹窗结果 == "人工处理":
await self._队列服务.标记人工(记录["id"], "弹窗无法自动处理")
await self._售后页.关闭详情标签()
return "人工"
9. 根据操作类型更新队列
if 决策["操作"] == "拒绝":
新拒绝次数 = int(记录.get("拒绝次数", 0)) + 1
下次时间 = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
await self._队列服务.更新阶段(
记录["id"], "待处理",
拒绝次数=新拒绝次数,
下次处理时间=下次时间,
处理结果=f"拒绝第{新拒绝次数}次",
)
else:
await self._队列服务.标记已完成(记录["id"], f"{决策['操作']}成功")
10. 备注
if 决策.get("需要备注") and 决策.get("备注内容"):
try:
备注成功 = await self._售后页.点击指定按钮("添加备注")
if 备注成功:
await self._售后页.弹窗扫描循环({"输入内容": 决策["备注内容"]})
except Exception:
pass
await self._售后页.关闭详情标签()
return "已处理"
except Exception as 异常:
if self._售后页._详情页:
await self._售后页.关闭详情标签()
raise
def _提取金额(self, 文本: str) -> float:
import re
匹配 = re.search(r'[¥￥]s(d+.?d)', str(文本))
return float(匹配.group(1)) if 匹配 else 0.0
def _组装规则配置(self, 规则结果: list) -> dict:
"""把规则服务匹配结果转为决策引擎需要的配置格式。"""
配置 = {
"自动同意金额上限": 10,
"需要拒绝": False,
"弹窗偏好": {},
}
for 动作 in 规则结果:
if 动作.get("action") == "同意退款":
pass  # 默认行为
elif 动作.get("action") == "拒绝":
配置["需要拒绝"] = True
if 动作.get("弹窗偏好"):
配置["弹窗偏好"] = 动作["弹窗偏好"]
return 配置

---

**七、测试**

### test_售后决策引擎.py（新建）

1. 退货退款 + 有"同意退货"按钮 → 决策=同意退货
2. 退货退款 + 有"同意退款"按钮 → 决策=同意退款
3. 退款 + 小额 + 有"同意退款"按钮 → 同意退款
4. 退款 + 有售后图片 → 人工处理
5. 退款 + 物流拒收 + 有"同意拒收后退款" → 同意拒收退款
6. 退款 + 需要拒绝 + 拒绝次数<3 → 拒绝
7. 退款 + 拒绝次数>=3 → 跳过
8. 无操作按钮 → 跳过（已被处理）
9. 补寄/换货 → 人工处理
10. `_找按钮` 优先级测试

### test_售后任务.py（重写）

11. mock 完整流程：扫描 → 写队列 → 打开详情 → 决策 → 执行 → 关标签
12. mock 详情页无按钮 → 跳过
13. mock 弹窗扫描返回"人工处理" → 标记人工
14. mock 拒绝场景 → 拒绝次数+1 + 下次处理时间
15. mock 按钮点击失败 → 备选按钮
16. mock 搜不到订单 → 跳过

### test_售后页.py（修改补充）

17. 测试 `确保待商家处理已选中`：已选中不点、未选中点
18. 测试 `点击订单详情并切换标签`
19. 测试 `检查是否需要处理`：有操作按钮/无操作按钮
20. 测试 `弹窗扫描循环`：纯确认框/有单选/有下拉/看不懂
21. 测试 `_JS点击弹窗按钮`
22. 测试 `点击指定按钮`

---

**八、约束**

1. 售后任务完全重写，不保留旧的状态机 Enum 和状态转移表
2. 阶段持久化在 SQLite `aftersale_queue.当前阶段`，不在内存
3. 每条订单处理前重新读取详情页实时状态，防止人工已处理
4. 弹窗扫描器不预设弹窗类型，扫描 DOM 后按元素类型动态处理
5. 拒绝场景写入 `下次处理时间=now+30min`，由 46C 的定时任务扫描处理
6. JS evaluate 中的字段标签文本基于真实页面校准（售后编码、订单编号、联系地址等）
7. 所有 JS 按钮操作在弹窗内限定作用域（`弹窗.querySelectorAll`），避免误点页面其他按钮
8. 异常时截图保留现场 + 关闭详情标签页 + 不影响下一条处理
9. pytest 全量通过