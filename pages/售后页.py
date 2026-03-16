"""拼多多后台售后管理页面对象。"""
import asyncio
import inspect
from pathlib import Path

from backend.配置 import 配置实例
from pages.基础页 import 基础页
from selectors.售后页选择器 import 售后页选择器


class 售后页(基础页):
    """拼多多后台售后管理页面对象。"""

    def __init__(self, 页面):
        super().__init__(页面)
        self.售后列表地址 = 售后页选择器.售后列表页URL
        self._详情页 = None

    @staticmethod
    async def _页面是否已关闭(页面) -> bool:
        if 页面 is None:
            return True
        检查方法 = getattr(页面, "is_closed", None)
        if not callable(检查方法):
            return False
        try:
            结果 = 检查方法()
            if inspect.isawaitable(结果):
                结果 = await 结果
        except Exception:
            return False
        return 结果 if isinstance(结果, bool) else False

    async def _获取目标页面(self):
        if self._详情页 and not await self._页面是否已关闭(self._详情页):
            return self._详情页
        self._详情页 = None
        return self.页面

    async def _等待详情页区域(self, 目标页面, 超时: int = 5000) -> bool:
        for 选择器 in 售后页选择器.详情页区域.所有选择器():
            try:
                await 目标页面.wait_for_selector(选择器, timeout=超时)
                return True
            except Exception:
                continue
        return False

    async def 导航到售后列表(self) -> None:
        """导航到售后管理列表页。URL: https://mms.pinduoduo.com/aftersales/list"""
        await self.操作前延迟()
        await self.页面.goto(self.售后列表地址, wait_until="domcontentloaded")
        await self.页面加载延迟()
        print(f"[售后页] 售后列表页加载完成: {self.页面.url}")

    async def 切换待处理(self) -> None:
        """点击“待处理”Tab筛选。"""
        await self.操作前延迟()
        最后异常 = None
        选择器列表 = list(
            dict.fromkeys(
                [
                    *售后页选择器.待商家处理Tab.所有选择器(),
                    *售后页选择器.待处理Tab.所有选择器(),
                ]
            )
        )
        for 选择器 in 选择器列表:
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 已切换到待处理: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 待处理Tab点击失败({选择器}): {异常}")
        raise RuntimeError(f"待处理Tab点击失败: {最后异常}")

    async def 切换已处理(self) -> None:
        """点击“已处理”Tab筛选。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.已处理Tab.所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 已切换到已处理: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 已处理Tab点击失败({选择器}): {异常}")
        raise RuntimeError(f"已处理Tab点击失败: {最后异常}")

    async def 搜索订单(self, 关键词: str) -> None:
        """在搜索框输入关键词并点击查询。"""
        await self.操作前延迟()
        输入异常 = None
        for 选择器 in 售后页选择器.搜索输入框.所有选择器():
            try:
                await self.安全填写(选择器, 关键词)
                print(f"[售后页] 搜索关键词填写完成: {关键词}")
                break
            except Exception as 异常:
                输入异常 = 异常
                print(f"[售后页] 搜索框填写失败({选择器}): {异常}")
        else:
            raise RuntimeError(f"搜索框填写失败: {输入异常}")

        点击异常 = None
        for 选择器 in 售后页选择器.搜索按钮.所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 搜索按钮点击完成: {选择器}")
                return
            except Exception as 异常:
                点击异常 = 异常
                print(f"[售后页] 搜索按钮点击失败({选择器}): {异常}")
        raise RuntimeError(f"搜索按钮点击失败: {点击异常}")

    async def 获取售后单数量(self) -> int:
        """返回当前列表页的售后单行数。"""
        await self.操作前延迟()
        for 选择器 in 售后页选择器.售后单行.所有选择器():
            try:
                行列表 = await self.页面.query_selector_all(选择器)
                if 行列表:
                    await self.操作后延迟()
                    print(f"[售后页] 售后单数量读取完成: {len(行列表)}")
                    return len(行列表)
            except Exception as 异常:
                print(f"[售后页] 售后单数量读取失败({选择器}): {异常}")
        print("[售后页] 售后单数量读取完成: 0")
        return 0

    async def 获取第N行信息(self, 行号: int) -> dict[str, str]:
        """读取列表第 N 行的售后单摘要信息。"""
        await self.操作前延迟()
        结果 = await self.页面.evaluate(
            """
            ({ 行选择器列表, 行号 }) => {
                const 清洗文本 = (值) => String(值 || "").replace(/\\s+/g, " ").trim();
                const 查询全部 = (选择器) => {
                    if (!选择器) {
                        return [];
                    }
                    if (选择器.startsWith("//") || 选择器.startsWith("(")) {
                        const 快照 = document.evaluate(
                            选择器,
                            document,
                            null,
                            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                            null,
                        );
                        const 节点列表 = [];
                        for (let 索引 = 0; 索引 < 快照.snapshotLength; 索引 += 1) {
                            const 节点 = 快照.snapshotItem(索引);
                            if (节点) {
                                节点列表.push(节点);
                            }
                        }
                        return 节点列表;
                    }
                    return Array.from(document.querySelectorAll(选择器));
                };

                let 行节点 = null;
                for (const 选择器 of 行选择器列表) {
                    const 节点列表 = 查询全部(选择器);
                    if (节点列表.length >= 行号) {
                        行节点 = 节点列表[行号 - 1];
                        break;
                    }
                }

                if (!行节点) {
                    return {
                        订单号: "",
                        售后类型: "",
                        退款金额: "",
                        商品名称: "",
                    };
                }

                const 原始文本列表 = Array.from(
                    行节点.querySelectorAll("td, .ant-table-cell, [role='cell'], span, div"),
                )
                    .map((节点) => 清洗文本(节点.textContent))
                    .filter(Boolean);
                const 文本列表 = [...new Set(原始文本列表)];
                const 行文本 = 清洗文本(行节点.textContent);
                const 订单号匹配 = 行文本.match(/\\d{6,}/);
                const 商品候选 = 文本列表
                    .filter((文本) => !["查看详情", "同意退款", "同意退货", "拒绝"].some((值) => 文本.includes(值)))
                    .filter((文本) => !["仅退款", "退货退款", "换货"].some((值) => 文本.includes(值)))
                    .filter((文本) => !/[¥￥]\\s*\\d+(\\.\\d{1,2})?/.test(文本))
                    .sort((左侧, 右侧) => 右侧.length - 左侧.length);

                return {
                    订单号: 清洗文本(文本列表.find((文本) => /\\d{6,}/.test(文本)) || (订单号匹配 ? 订单号匹配[0] : "")),
                    售后类型: 清洗文本(
                        文本列表.find((文本) => ["仅退款", "退货退款", "换货"].some((值) => 文本.includes(值))) || "",
                    ),
                    退款金额: 清洗文本(
                        文本列表.find((文本) => /[¥￥]\\s*\\d+(\\.\\d{1,2})?/.test(文本)) || "",
                    ),
                    商品名称: 清洗文本(商品候选[0] || ""),
                };
            }
            """,
            {
                "行选择器列表": 售后页选择器.售后单行.所有选择器(),
                "行号": 行号,
            },
        )
        await self.操作后延迟()
        print(f"[售后页] 已读取第{行号}行售后信息")
        return dict(结果 or {})

    async def 点击第N行详情(self, 行号: int) -> None:
        """点击列表第 N 行的“查看详情”链接。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.获取第N行详情链接(行号).所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 已点击第{行号}行详情: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 第{行号}行详情点击失败({选择器}): {异常}")
        raise RuntimeError(f"第{行号}行详情点击失败: {最后异常}")

    async def 点击第N行操作(self, 行号: int, 操作文本: str) -> None:
        """点击列表第 N 行的指定操作按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.获取第N行操作按钮(行号, 操作文本).所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 已点击第{行号}行操作: {操作文本}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 第{行号}行操作点击失败({选择器}): {异常}")
        raise RuntimeError(f"第{行号}行操作点击失败: {最后异常}")

    async def 翻页(self) -> bool:
        """点击下一页，如果有的话。返回是否成功翻页。"""
        await self.操作前延迟()
        for 选择器 in 售后页选择器.下一页按钮.所有选择器():
            try:
                下一页按钮 = self.页面.locator(选择器).first
                aria_disabled = 下一页按钮.get_attribute("aria-disabled")
                if inspect.isawaitable(aria_disabled):
                    aria_disabled = await aria_disabled
                class_name = 下一页按钮.get_attribute("class")
                if inspect.isawaitable(class_name):
                    class_name = await class_name

                if str(aria_disabled or "").lower() == "true" or "disabled" in str(class_name or "").lower():
                    print(f"[售后页] 下一页按钮不可用: {选择器}")
                    return False

                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 翻页成功: {选择器}")
                return True
            except Exception as 异常:
                print(f"[售后页] 翻页失败({选择器}): {异常}")
        return False

    async def 扫描所有待处理(self) -> list[dict]:
        """扫描所有"待商家处理"的售后单（含翻页），返回摘要列表。"""
        await self.切换待处理()
        所有记录: list[dict] = []
        while True:
            数量 = await self.获取售后单数量()
            for 行号 in range(1, 数量 + 1):
                信息 = await self.获取第N行信息(行号)
                if 信息.get("订单号"):
                    所有记录.append(信息)
            if not await self.翻页():
                break
        print(f"[售后页] 待处理列表扫描完成，共 {len(所有记录)} 条")
        return 所有记录

    async def 点击详情并切换标签(self, 行号: int) -> None:
        """点击查看详情，等待新标签页打开，切换到新标签页。"""
        上下文 = self.页面.context
        原始页面数 = len(getattr(上下文, "pages", []))
        等待新标签任务 = asyncio.create_task(
            上下文.wait_for_event("page", timeout=10000)
        )
        await self.点击第N行详情(行号)
        新页面 = await 等待新标签任务
        await 新页面.wait_for_load_state("domcontentloaded")
        await self._等待详情页区域(新页面)
        self._详情页 = 新页面
        print(
            f"[售后页] 已切换到详情标签页: {新页面.url} "
            f"(原始页数={原始页面数}, 当前页数={len(getattr(上下文, 'pages', []))})"
        )

    async def 关闭详情标签(self) -> None:
        """关闭详情标签页，焦点回到列表页。"""
        详情页 = self._详情页
        if 详情页 and not await self._页面是否已关闭(详情页):
            await 详情页.close()
        self._详情页 = None
        print("[售后页] 详情标签已关闭")

    async def 抓取详情页完整信息(self) -> dict:
        """从售后详情新标签页用 JS 一次性抓取所有关键信息。"""
        await self.操作前延迟()
        目标页面 = await self._获取目标页面()
        await self._等待详情页区域(目标页面)
        结果 = await 目标页面.evaluate(
            """
            () => {
                const 清洗 = (s) => String(s || '').replace(/\\s+/g, ' ').trim();
                const 全文 = 清洗(document.body && document.body.innerText);
                const 全元素 = Array.from(document.querySelectorAll('td, div, span, p, label, li, strong, a'));

                const 取文本 = (节点) => 清洗(节点 && 节点.textContent);
                const 去重 = (列表) => Array.from(new Set(列表.filter(Boolean)));
                const 查找标签元素 = (标签文本) => {
                    const 标签集合 = [标签文本, `${标签文本}：`, `${标签文本}:`];
                    return 全元素.find((元素) => {
                        const 文本 = 取文本(元素);
                        return 标签集合.includes(文本) || 文本.startsWith(`${标签文本}：`) || 文本.startsWith(`${标签文本}:`);
                    }) || null;
                };

                const 提取字段 = (标签文本) => {
                    const 命中元素 = 查找标签元素(标签文本);
                    if (命中元素) {
                        const 文本 = 取文本(命中元素);
                        if (文本.startsWith(`${标签文本}：`) || 文本.startsWith(`${标签文本}:`)) {
                            return 清洗(文本.replace(标签文本, '').replace(/^[：:\\s]+/, ''));
                        }
                        const 相邻列表 = [
                            命中元素.nextElementSibling,
                            命中元素.parentElement && 命中元素.parentElement.nextElementSibling,
                            命中元素.parentElement && 命中元素.parentElement.querySelector('td:last-child, div:last-child, span:last-child'),
                        ].filter(Boolean);
                        for (const 相邻元素 of 相邻列表) {
                            const 值 = 取文本(相邻元素);
                            if (值 && 值 !== 标签文本) {
                                return 值;
                            }
                        }
                    }

                    const 正则 = new RegExp(`${标签文本}[：: ]+([^\\n]+)`);
                    const 匹配 = 全文.match(正则);
                    return 匹配 ? 清洗(匹配[1]) : '';
                };

                const 提取金额 = (文本) => {
                    const 匹配 = String(文本 || '').match(/[¥￥]\\s*(\\d+(?:\\.\\d+)?)/);
                    return 匹配 ? parseFloat(匹配[1]) : 0;
                };

                const 读取按钮 = () => {
                    const 按钮 = document.querySelectorAll(
                        'button:not(:disabled), a.ant-btn:not(.ant-btn-disabled), a[role="button"]:not([aria-disabled="true"])'
                    );
                    return 去重(
                        Array.from(按钮)
                            .map((按钮元素) => 取文本(按钮元素))
                            .filter((文本) => 文本 && 文本.length < 30)
                    );
                };

                const 读取物流 = () => {
                    const 轨迹项 = document.querySelectorAll(
                        '.logistics-item, .timeline-item, .ant-timeline-item, li'
                    );
                    for (const 项 of 轨迹项) {
                        const 文本 = 取文本(项);
                        if (文本 && (文本.includes('物流') || /\\d{4}-\\d{2}-\\d{2}/.test(文本))) {
                            return 文本;
                        }
                    }
                    const 物流文本 = 提取字段('物流轨迹') || 提取字段('物流信息');
                    return 物流文本 || '';
                };

                const 提取物流时间 = (物流文本) => {
                    const 匹配 = String(物流文本 || '').match(/\\d{4}-\\d{2}-\\d{2}[ T]\\d{2}:\\d{2}(?::\\d{2})?/);
                    return 匹配 ? 匹配[0].replace('T', ' ') : '';
                };

                const 有图片 = () => {
                    const 图片 = document.querySelectorAll(
                        'img[src*="upload"], img[src*="pic"], img[src*="pinduoduo"], .image-preview img'
                    );
                    for (const 图片元素 of 图片) {
                        const 宽度 = 图片元素.naturalWidth || 图片元素.width || 0;
                        if (宽度 > 50) {
                            return true;
                        }
                    }
                    return false;
                };

                const 读取聊天 = () => {
                    const 聊天项 = document.querySelectorAll('.chat-item, .message-item, .chat-record-item, .ant-comment');
                    if (!聊天项.length) {
                        return { 内容: '', 商家已回复: false };
                    }
                    const 文本列表 = Array.from(聊天项).map((项) => 取文本(项)).filter(Boolean);
                    const 最新内容 = 文本列表[文本列表.length - 1] || '';
                    const 商家已回复 = 文本列表.some((文本) => 文本.includes('商家') || 文本.includes('售后'));
                    return { 内容: 最新内容, 商家已回复 };
                };

                const 提取剩余时间 = () => {
                    const 匹配 = 全文.match(/((?:\\d+天)?\\d+时\\d+分(?:\\d+秒)?)/);
                    return 匹配 ? 匹配[1] : '';
                };

                const 提取城市 = (地址) => {
                    const 文本 = String(地址 || '');
                    const 市匹配 = 文本.match(/省(.+?)[市州]/);
                    if (市匹配) {
                        return 清洗(市匹配[1]);
                    }
                    const 直辖市匹配 = 文本.match(/(北京|上海|天津|重庆)市/);
                    return 直辖市匹配 ? 直辖市匹配[1] : '';
                };

                const 计算协商轮次 = () => {
                    const 轮次节点 = document.querySelectorAll('.negotiate-item, .apply-item, .chat-record-item, .ant-timeline-item');
                    return 轮次节点.length || 0;
                };

                const 订单编号 = 提取字段('订单编号') || 提取字段('订单号');
                const 售后编号 = 提取字段('售后编号');
                const 售后类型原文 = 提取字段('售后类型');
                const 售后状态字段 = 提取字段('售后状态');
                const 退款金额文本 = 提取字段('退款金额');
                const 发货状态 = 提取字段('发货状态');
                const 申请原因 = 提取字段('申请原因');
                const 售后申请说明 = 提取字段('售后申请说明') || 提取字段('申请说明');
                const 发货物流公司 = 提取字段('发货物流公司') || 提取字段('物流公司');
                const 发货快递单号 = 提取字段('发货快递单号') || 提取字段('快递单号');
                const 商品名称 = 提取字段('商品名称') || 提取字段('商品');
                const 收货地址 = 提取字段('联系地址') || 提取字段('收货地址');
                const 物流信息 = 读取物流();
                const 聊天信息 = 读取聊天();
                const 按钮列表 = 读取按钮();
                const 售后类型 = 清洗((售后类型原文 || '').split(/[，,]/)[0]);
                const 售后状态 = 清洗(
                    售后状态字段 ||
                    (售后类型原文.includes('待') ? 售后类型原文.slice(售后类型原文.indexOf('待')) : '')
                );

                return {
                    售后编号,
                    售后类型,
                    售后状态,
                    发货状态,
                    退款金额: 提取金额(退款金额文本),
                    退款金额文本,
                    实收金额: 提取金额(提取字段('实收金额') || 提取字段('实收')),
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
                    物流最新时间: 提取物流时间(物流信息),
                    剩余处理时间: 提取剩余时间(),
                    平台建议: 提取字段('平台建议') || '',
                    可用按钮列表: 按钮列表,
                    协商轮次: 计算协商轮次(),
                    最新聊天内容: 聊天信息.内容,
                    商家已回复: 聊天信息.商家已回复,
                    有同意退款按钮: 按钮列表.some((文本) => 文本.includes('同意退款')),
                    有同意拒收后退款按钮: 按钮列表.some((文本) => 文本.includes('拒收后退款')),
                    有同意退货按钮: 按钮列表.some((文本) => 文本.includes('同意退货')),
                    有拒绝按钮: 按钮列表.some((文本) => 文本.includes('拒绝')),
                    有免费退如快递拦截按钮: 按钮列表.some((文本) => 文本.includes('快递拦截')),
                    有添加留言按钮: 按钮列表.some((文本) => 文本.includes('留言') || 文本.includes('凭证')),
                };
            }
            """
        )
        await self.操作后延迟()
        结果字典 = dict(结果 or {})
        print(
            f"[售后页] 详情抓取完成: 订单={结果字典.get('订单编号')}, "
            f"类型={结果字典.get('售后类型')}, 按钮={结果字典.get('可用按钮列表')}"
        )
        return 结果字典

    async def 点击指定按钮(self, 按钮文本: str) -> bool:
        """在详情页通过 JS 查找并点击包含指定文本的按钮。"""
        await self.操作前延迟()
        目标页面 = await self._获取目标页面()
        结果 = await 目标页面.evaluate(
            """
            (按钮文本) => {
                const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                const 按钮列表 = document.querySelectorAll(
                    'button:not(:disabled), a.ant-btn:not(.ant-btn-disabled), a[role="button"]:not([aria-disabled="true"])'
                );
                for (const 按钮 of 按钮列表) {
                    if (清洗(按钮.textContent).includes(按钮文本)) {
                        按钮.click();
                        return true;
                    }
                }
                return false;
            }
            """,
            按钮文本,
        )
        if 结果:
            await self.操作后延迟()
            print(f"[售后页] 已点击按钮: {按钮文本}")
        else:
            print(f"[售后页] 未找到按钮: {按钮文本}")
        return bool(结果)

    async def 读取当前所有按钮(self) -> list[str]:
        """用 JS 读取当前页面（列表页或详情页）所有可点击按钮的文本。"""
        await self.操作前延迟()
        目标页面 = await self._获取目标页面()
        结果 = await 目标页面.evaluate(
            """
            () => {
                const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                const 按钮列表 = document.querySelectorAll(
                    'button:not(:disabled), a.ant-btn:not(.ant-btn-disabled), a[role="button"]:not([aria-disabled="true"])'
                );
                return Array.from(new Set(
                    Array.from(按钮列表)
                        .map((按钮) => 清洗(按钮.textContent))
                        .filter((文本) => 文本 && 文本.length < 30)
                ));
            }
            """
        )
        await self.操作后延迟()
        return list(结果 or [])

    async def 检查订单是否待处理(self) -> bool:
        """在详情页检查售后状态是否仍为"待商家处理"。"""
        await self.操作前延迟()
        目标页面 = await self._获取目标页面()
        全文 = await 目标页面.evaluate("() => document.body && document.body.innerText")
        await self.操作后延迟()
        文本 = str(全文 or "")
        return "待商家处理" in 文本 or "待卖家处理" in 文本

    async def 详情页截图(self, 名称: str) -> str | None:
        """对详情标签页截图。"""
        await self.操作前延迟()
        目标页面 = await self._获取目标页面()
        截图目录 = Path(配置实例.DATA_DIR) / "screenshots"
        截图目录.mkdir(parents=True, exist_ok=True)
        路径 = 截图目录 / f"{名称}.png"
        try:
            await 目标页面.screenshot(path=str(路径), full_page=True)
            await self.操作后延迟()
            print(f"[售后页] 截图保存: {路径}")
            return str(路径)
        except Exception as 异常:
            print(f"[售后页] 截图失败: {异常}")
            return None

    async def 读取售后详情(self) -> dict[str, str]:
        """从售后单详情页读取完整信息。"""
        await self.操作前延迟()
        结果 = await self.页面.evaluate(
            """
            ({ 字段选择器 }) => {
                const 清洗文本 = (值) => String(值 || "").replace(/\\s+/g, " ").trim();
                const 查询单个 = (选择器) => {
                    if (!选择器) {
                        return null;
                    }
                    if (选择器.startsWith("//") || 选择器.startsWith("(")) {
                        return document.evaluate(
                            选择器,
                            document,
                            null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE,
                            null,
                        ).singleNodeValue;
                    }
                    return document.querySelector(选择器);
                };
                const 读取字段 = (选择器列表) => {
                    for (const 选择器 of 选择器列表) {
                        const 节点 = 查询单个(选择器);
                        const 文本 = 清洗文本(节点 && 节点.textContent);
                        if (文本) {
                            return 文本;
                        }
                    }
                    return "";
                };

                return {
                    订单号: 读取字段(字段选择器.订单号),
                    售后类型: 读取字段(字段选择器.售后类型),
                    退款金额: 读取字段(字段选择器.退款金额),
                    退款原因: 读取字段(字段选择器.退款原因),
                    商品名称: 读取字段(字段选择器.商品名称),
                    发货状态: 读取字段(字段选择器.发货状态),
                };
            }
            """,
            {
                "字段选择器": {
                    "订单号": 售后页选择器.订单号.所有选择器(),
                    "售后类型": 售后页选择器.售后类型标签.所有选择器(),
                    "退款金额": 售后页选择器.退款金额.所有选择器(),
                    "退款原因": 售后页选择器.退款原因.所有选择器(),
                    "商品名称": 售后页选择器.商品名称.所有选择器(),
                    "发货状态": 售后页选择器.发货状态.所有选择器(),
                },
            },
        )
        await self.操作后延迟()
        print("[售后页] 售后详情读取完成")
        return dict(结果 or {})

    async def 点击同意退款(self) -> None:
        """点击“同意退款”按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.同意退款按钮.所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 已点击同意退款: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 同意退款点击失败({选择器}): {异常}")
        raise RuntimeError(f"同意退款点击失败: {最后异常}")

    async def 点击同意退货(self) -> None:
        """点击“同意退货”按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.同意退货按钮.所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 已点击同意退货: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 同意退货点击失败({选择器}): {异常}")
        raise RuntimeError(f"同意退货点击失败: {最后异常}")

    async def 点击拒绝(self) -> None:
        """点击“拒绝”按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.拒绝按钮.所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 已点击拒绝: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 拒绝按钮点击失败({选择器}): {异常}")
        raise RuntimeError(f"拒绝按钮点击失败: {最后异常}")

    async def 等待确认弹窗(self, 超时: int = 5000) -> bool:
        """等待确认弹窗出现，返回是否出现。"""
        await self.操作前延迟()
        for 选择器 in 售后页选择器.确认弹窗.所有选择器():
            try:
                await self.页面.wait_for_selector(选择器, timeout=超时)
                await self.操作后延迟()
                print(f"[售后页] 确认弹窗已出现: {选择器}")
                return True
            except Exception as 异常:
                print(f"[售后页] 等待确认弹窗失败({选择器}): {异常}")
        return False

    async def 点击弹窗确定(self) -> None:
        """点击确认弹窗的“确定”按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.确认弹窗确定按钮.所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 已点击弹窗确定: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 弹窗确定点击失败({选择器}): {异常}")
        raise RuntimeError(f"弹窗确定点击失败: {最后异常}")

    async def 点击弹窗取消(self) -> None:
        """点击确认弹窗的“取消”按钮。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.确认弹窗取消按钮.所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                print(f"[售后页] 已点击弹窗取消: {选择器}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 弹窗取消点击失败({选择器}): {异常}")
        raise RuntimeError(f"弹窗取消点击失败: {最后异常}")

    async def 处理确认弹窗(self) -> bool:
        """等待确认弹窗后点击确定。"""
        if not await self.等待确认弹窗():
            return False
        await self.点击弹窗确定()
        return True

    async def 填写物流单号(self, 单号: str) -> None:
        """在物流单号输入框填写单号。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.物流单号输入框.所有选择器():
            try:
                await self.安全填写(选择器, 单号)
                await self.操作后延迟()
                print(f"[售后页] 物流单号填写完成: {单号}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 物流单号填写失败({选择器}): {异常}")
        raise RuntimeError(f"物流单号填写失败: {最后异常}")

    async def 选择物流公司(self, 公司名: str) -> None:
        """选择物流公司（下拉框选择）。"""
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.物流公司选择框.所有选择器():
            try:
                await self.安全填写(选择器, 公司名)
                await self.安全点击_文本(公司名)
                await self.操作后延迟()
                print(f"[售后页] 物流公司选择完成: {公司名}")
                return
            except Exception as 异常:
                最后异常 = 异常
                print(f"[售后页] 物流公司选择失败({选择器}): {异常}")
        raise RuntimeError(f"物流公司选择失败: {最后异常}")
