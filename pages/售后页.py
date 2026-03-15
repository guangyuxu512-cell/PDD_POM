"""拼多多后台售后管理页面对象。"""
import inspect

from pages.基础页 import 基础页
from selectors.售后页选择器 import 售后页选择器


class 售后页(基础页):
    """拼多多后台售后管理页面对象。"""

    def __init__(self, 页面):
        super().__init__(页面)
        self.售后列表地址 = 售后页选择器.售后列表页URL

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
        for 选择器 in 售后页选择器.待处理Tab.所有选择器():
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
