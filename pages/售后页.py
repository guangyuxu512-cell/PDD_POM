"""拼多多后台售后管理页面对象。"""
from __future__ import annotations

import asyncio
import inspect
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from backend.配置 import 配置实例
from pages.基础页 import 基础页
from selectors.售后页选择器 import 售后页选择器

详情按钮查询选择器 = (
    'button:not(:disabled), '
    'a[data-testid="beast-core-button-link"], '
    'a[data-testid="beast-core-button"], '
    'a.ant-btn:not(.ant-btn-disabled), '
    'a[role="button"]:not([aria-disabled="true"])'
)


class 售后页(基础页):
    """售后管理页 POM。"""

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

    @staticmethod
    async def _点击目标页面元素(目标页面, 选择器: str, 超时: int = 10000) -> None:
        await 目标页面.wait_for_selector(选择器, timeout=超时)
        定位器 = 目标页面.locator(选择器).first
        点击结果 = 定位器.click(timeout=超时)
        if inspect.isawaitable(点击结果):
            await 点击结果

    @staticmethod
    async def _填写目标页面元素(目标页面, 选择器: str, 内容: str, 超时: int = 10000) -> None:
        await 目标页面.wait_for_selector(选择器, timeout=超时)
        定位器 = 目标页面.locator(选择器).first
        点击结果 = 定位器.click(timeout=超时)
        if inspect.isawaitable(点击结果):
            await 点击结果
        填写结果 = 定位器.fill(str(内容), timeout=超时)
        if inspect.isawaitable(填写结果):
            await 填写结果

    async def _等待并切换详情标签(self, 点击协程, 标识文本: str) -> None:
        上下文 = self.页面.context
        等待新标签任务 = asyncio.create_task(
            上下文.wait_for_event("page", timeout=10000)
        )
        try:
            await 点击协程
            新页面 = await 等待新标签任务
        except Exception:
            if not 等待新标签任务.done():
                等待新标签任务.cancel()
            raise
        await 新页面.wait_for_load_state("domcontentloaded")
        await self._等待详情页区域(新页面)
        self._详情页 = 新页面
        print(f"[售后页] 已切换到详情标签页: {标识文本}")

    async def _点击弹窗提交按钮(self, 页面, 按钮列表: list[str]) -> bool:
        for 按钮文本 in 按钮列表:
            if "确" in 按钮文本 or "提交" in 按钮文本:
                await self.随机延迟(0.3, 0.8)
                return await self._JS点击弹窗按钮(页面, 按钮文本)
        return False

    async def 导航到售后列表(self) -> None:
        await self.操作前延迟()
        await self.页面.goto(self.售后列表地址, wait_until="domcontentloaded")
        await self.页面加载延迟()
        print(f"[售后页] 售后列表页加载完成: {self.页面.url}")

    @staticmethod
    def _转换分转元(值: Any) -> float:
        try:
            return round(float(值 or 0) / 100, 2)
        except Exception:
            return 0.0

    @staticmethod
    def _转换整数(值: Any) -> int:
        try:
            return int(值 or 0)
        except Exception:
            return 0

    @staticmethod
    def _响应URL是否待商家处理(响应地址: str) -> bool:
        try:
            查询参数 = parse_qs(urlparse(str(响应地址 or "")).query)
        except Exception:
            return False

        if not 查询参数:
            return False

        状态值集合 = {
            "10",
            "pending",
            "todo",
            "seller_pending",
            "merchant_pending",
            "waitseller",
            "wait_seller",
        }
        for 键, 值列表 in 查询参数.items():
            键名 = str(键 or "").strip().lower()
            for 原始值 in 值列表:
                值 = unquote(str(原始值 or "")).strip().lower()
                if not 值:
                    continue
                if "待商家处理" in 值 or "待处理" in 值:
                    return True
                if any(片段 in 键名 for 片段 in ("status", "tab", "type")) and 值 in 状态值集合:
                    return True
        return False

    @staticmethod
    def _列表数据是否待商家处理(列表数据: list[dict[str, Any]]) -> bool:
        有效状态列表 = []
        for 项 in 列表数据:
            if not isinstance(项, dict):
                continue
            状态文本 = str(项.get("afterSalesTitle") or 项.get("售后状态") or "").strip()
            if 状态文本:
                有效状态列表.append(状态文本)
        return bool(有效状态列表) and all("待商家" in 状态 for 状态 in 有效状态列表)

    async def 拦截售后列表API(self, 超时秒: int = 15, 仅待商家处理: bool = False) -> list[dict]:
        """拦截售后列表接口响应并直接返回结构化摘要。"""
        结果容器: list[dict[str, Any]] = []
        捕获事件 = asyncio.Event()
        后台任务列表: list[asyncio.Task[Any]] = []

        async def _处理响应(response) -> None:
            try:
                响应地址 = str(getattr(response, "url", "") or "")
                if (
                    "/afterSales" not in 响应地址
                    and "/after-sales" not in 响应地址
                    and "/refund" not in 响应地址
                ):
                    return
                if int(getattr(response, "status", 0) or 0) != 200:
                    return
                try:
                    数据 = await response.json()
                except Exception:
                    return
                if not isinstance(数据, dict):
                    return
                result = 数据.get("result") or {}
                列表数据 = result.get("list") or result.get("pageItems") or []
                if not isinstance(列表数据, list) or not 列表数据:
                    return
                if 仅待商家处理:
                    if not self._响应URL是否待商家处理(响应地址) and not self._列表数据是否待商家处理(列表数据):
                        print(f"[售后页] 已忽略非待商家处理响应: {响应地址}")
                        return

                结果容器.clear()
                已捕获订单号集合: set[str] = set()
                for 项 in 列表数据:
                    if not isinstance(项, dict):
                        continue
                    订单号 = str(项.get("orderSn") or "").strip()
                    if not 订单号 or 订单号 in 已捕获订单号集合:
                        continue
                    已捕获订单号集合.add(订单号)
                    结果容器.append(
                        {
                            "订单号": 订单号,
                            "售后单ID": str(项.get("id") or ""),
                            "退款金额": self._转换分转元(项.get("refundAmount")),
                            "实收金额": self._转换分转元(项.get("receiveAmount")),
                            "售后类型": str(项.get("afterSalesTypeName") or ""),
                            "售后类型码": self._转换整数(项.get("afterSalesType")),
                            "售后状态": str(项.get("afterSalesTitle") or ""),
                            "售后状态码": self._转换整数(项.get("afterSalesStatus")),
                            "申请原因": str(项.get("afterSalesReasonDesc") or ""),
                            "商品名称": str(项.get("goodsName") or ""),
                            "发货状态": str(项.get("sellerAfterSalesShippingStatusDesc") or ""),
                            "操作码列表": list(项.get("actions") or []),
                            "剩余处理秒数": self._转换整数(项.get("expireRemainTime")),
                        }
                    )
                if 结果容器:
                    捕获事件.set()
            except Exception:
                return

        def _响应处理(response) -> None:
            try:
                后台任务列表.append(asyncio.create_task(_处理响应(response)))
            except Exception:
                return

        self.页面.on("response", _响应处理)
        try:
            await asyncio.wait_for(捕获事件.wait(), timeout=超时秒)
        except asyncio.TimeoutError:
            pass
        finally:
            self.页面.remove_listener("response", _响应处理)
            if 后台任务列表:
                await asyncio.gather(*后台任务列表, return_exceptions=True)

        print(f"[售后页] API拦截抓取到 {len(结果容器)} 条售后单")
        return 结果容器

    async def 导航并拦截售后列表(self) -> list[dict]:
        """先导航到列表页，再通过待商家处理卡片切换触发接口拦截。"""
        await self.导航到售后列表()
        await self.页面加载延迟()

        拦截任务 = asyncio.create_task(self.拦截售后列表API(超时秒=10, 仅待商家处理=True))
        await asyncio.sleep(0)
        await self.确保待商家处理已选中(强制点击=True)
        结果 = await 拦截任务

        if not 结果:
            print("[售后页] 首次 API 拦截为空，重试触发待商家处理请求")
            拦截任务 = asyncio.create_task(self.拦截售后列表API(超时秒=10, 仅待商家处理=True))
            await asyncio.sleep(0)
            await self.确保待商家处理已选中(强制点击=True)
            结果 = await 拦截任务

        if not 结果:
            print("[售后页] API拦截失败，fallback到JS抓取")

        return 结果

    async def 切换待处理(self) -> None:
        await self.确保待商家处理已选中()

    async def 确保待商家处理已选中(self, 强制点击: bool = False) -> None:
        await self.操作前延迟()
        类名片段 = 售后页选择器.待商家处理选中类名片段
        最后异常 = None
        for 选择器 in 售后页选择器.待商家处理卡片.所有选择器():
            try:
                已选中 = await self.页面.evaluate(
                    """
                    ({ 选择器, 类名片段 }) => {
                        const 查询 = (sel) => {
                            if (sel.startsWith('//') || sel.startsWith('(')) {
                                return document.evaluate(
                                    sel,
                                    document,
                                    null,
                                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                                    null,
                                ).singleNodeValue;
                            }
                            return document.querySelector(sel);
                        };
                        const 节点 = 查询(选择器);
                        return Boolean(节点) && String(节点.className || '').includes(类名片段);
                    }
                    """,
                    {"选择器": 选择器, "类名片段": 类名片段},
                )
                if 已选中:
                    if 强制点击:
                        await self.安全点击(选择器)
                        await self.页面加载延迟()
                        print("[售后页] 待商家处理卡片已选中，已强制再次点击")
                        return
                    print("[售后页] 待商家处理卡片已选中")
                    return
                await self.安全点击(选择器)
                await self.页面加载延迟()
                print("[售后页] 已点击待商家处理卡片")
                return
            except Exception as 异常:
                最后异常 = 异常
        raise RuntimeError(f"待商家处理卡片操作失败: {最后异常}")

    async def 搜索订单(self, 关键词: str) -> None:
        await self.操作前延迟()
        输入异常 = None
        for 选择器 in 售后页选择器.搜索输入框.所有选择器():
            try:
                await self.安全填写(选择器, 关键词)
                break
            except Exception as 异常:
                输入异常 = 异常
        else:
            raise RuntimeError(f"搜索框填写失败: {输入异常}")

        点击异常 = None
        for 选择器 in 售后页选择器.搜索按钮.所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                return
            except Exception as 异常:
                点击异常 = 异常
        raise RuntimeError(f"搜索按钮点击失败: {点击异常}")

    async def 获取售后单数量(self) -> int:
        await self.操作前延迟()
        数量 = await self.页面.evaluate(
            """
            () => document.querySelectorAll(
                'div[class*="after-sales-table_order_item"]'
            ).length
            """
        )
        await self.操作后延迟()
        return int(数量 or 0)

    async def 获取第N行信息(self, 行号: int) -> dict[str, str]:
        await self.操作前延迟()
        结果 = await self.页面.evaluate(
            """
            (行号) => {
                const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                const 所有行 = document.querySelectorAll(
                    'div[class*="after-sales-table_order_item"]'
                );
                if (行号 > 所有行.length) {
                    return null;
                }

                const 行 = 所有行[行号 - 1];
                const 订单号节点 = 行.querySelector('[class*="table-item-header_sn__"]');
                const 订单号 = 清洗(订单号节点 ? 订单号节点.textContent : '');

                const 申请时间节点 = 行.querySelector(
                    '[class*="table-item-header_apply_time"] span'
                );
                const 申请时间 = 清洗(申请时间节点 ? 申请时间节点.textContent : '');

                const 剩余时间节点 = 行.querySelector('[class*="table-item-header_time__"]');
                const 剩余处理时间 = 清洗(剩余时间节点 ? 剩余时间节点.textContent : '');

                const 所有列 = 行.querySelectorAll('[class*="after-sales-table_item_cell"]');
                const 读列 = (索引) => {
                    if (索引 >= 所有列.length) {
                        return '';
                    }
                    return 清洗(所有列[索引].textContent);
                };

                const 商品名节点 = 所有列[0]
                    ? 所有列[0].querySelector('[class*="order-info_main"]')
                    : null;
                const 规格节点 = 所有列[0]
                    ? 所有列[0].querySelector('[class*="order-info_sub"]')
                    : null;
                const 商品名称 = 清洗(商品名节点 ? 商品名节点.textContent : '');
                const 商品规格 = 清洗(规格节点 ? 规格节点.textContent : '');

                const 实收节点 = 所有列[1]
                    ? 所有列[1].querySelector('[class*="amount_dotted"]')
                    : null;
                const 退款节点 = 所有列[1]
                    ? 所有列[1].querySelector('[class*="amount_refund"]')
                    : null;
                const 实收金额 = 清洗(实收节点 ? 实收节点.textContent : '');
                const 退款金额 = 清洗(退款节点 ? 退款节点.textContent : '');

                const 售后状态节点 = 所有列[4] ? 所有列[4].querySelector('div') : null;
                const 售后状态 = 清洗(售后状态节点 ? 售后状态节点.textContent : '');

                const 操作按钮 = 所有列[7]
                    ? Array.from(所有列[7].querySelectorAll('a span, button span'))
                        .map((节点) => 清洗(节点.textContent))
                        .filter((文本) => 文本.length > 0)
                    : [];

                return {
                    订单号: 订单号,
                    申请时间: 申请时间,
                    剩余处理时间: 剩余处理时间,
                    商品名称: 商品名称,
                    商品规格: 商品规格,
                    实收金额: 实收金额,
                    退款金额: 退款金额,
                    发货状态: 清洗(读列(2)),
                    售后类型: 清洗(读列(3)),
                    售后状态: 售后状态,
                    售后协商: 清洗(读列(5)),
                    售后原因: 清洗(读列(6)),
                    操作按钮: 操作按钮,
                };
            }
            """,
            行号,
        )
        await self.操作后延迟()
        if 结果:
            print(
                f"[售后页] 第{行号}行: 订单={结果.get('订单号')}, "
                f"类型={结果.get('售后类型')}, 退款={结果.get('退款金额')}"
            )
        return dict(结果 or {})

    async def 点击订单详情(self, 订单号: str) -> None:
        await self.操作前延迟()
        最后异常 = None
        for 选择器 in 售后页选择器.获取订单详情链接(订单号).所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                return
            except Exception as 异常:
                最后异常 = 异常
        raise RuntimeError(f"订单 {订单号} 查看详情点击失败: {最后异常}")

    async def 点击订单详情并切换标签(self, 订单号: str) -> None:
        await self._等待并切换详情标签(self.点击订单详情(订单号), 订单号)

    async def 列表页添加备注(self, 订单号: str, 内容: str) -> bool:
        """在列表页按订单号添加备注。"""
        try:
            点击成功 = False
            for 选择器 in 售后页选择器.获取订单备注按钮(订单号).所有选择器():
                try:
                    await self.安全点击(选择器)
                    点击成功 = True
                    break
                except Exception:
                    continue
            if not 点击成功:
                print(f"[售后页] 未找到列表备注按钮: {订单号}")
                return False

            await self.随机延迟(0.5, 1)

            for 选择器 in 售后页选择器.列表备注输入框.所有选择器():
                try:
                    await self.安全填写(选择器, 内容)
                    break
                except Exception:
                    continue
            else:
                print(f"[售后页] 未找到列表备注输入框: {订单号}")
                return False

            await self.随机延迟(0.3, 0.8)

            for 选择器 in 售后页选择器.列表备注保存按钮.所有选择器():
                try:
                    await self.安全点击(选择器)
                    await self.操作后延迟()
                    print(f"[售后页] 列表备注已保存: {订单号} -> {内容[:30]}")
                    return True
                except Exception:
                    continue

            print(f"[售后页] 未找到列表备注保存按钮: {订单号}")
            return False
        except Exception as 异常:
            print(f"[售后页] 列表添加备注失败: {异常}")
            return False

    async def 详情页添加备注(self, 内容: str) -> bool:
        """在详情页添加备注。"""
        目标页面 = await self._获取目标页面()
        try:
            for 选择器 in 售后页选择器.详情备注按钮.所有选择器():
                try:
                    await self._点击目标页面元素(目标页面, 选择器)
                    break
                except Exception:
                    continue
            else:
                print("[售后页] 未找到详情备注按钮")
                return False

            await self.随机延迟(0.5, 1)

            for 选择器 in 售后页选择器.详情备注输入框.所有选择器():
                try:
                    await self._填写目标页面元素(目标页面, 选择器, 内容)
                    break
                except Exception:
                    continue
            else:
                print("[售后页] 未找到详情备注输入框")
                return False

            await self.随机延迟(0.3, 0.8)

            for 选择器 in 售后页选择器.详情备注保存按钮.所有选择器():
                try:
                    await self._点击目标页面元素(目标页面, 选择器)
                    await self.操作后延迟()
                    print(f"[售后页] 详情备注已保存: {内容[:30]}")
                    return True
                except Exception:
                    continue

            print("[售后页] 未找到详情备注保存按钮")
            return False
        except Exception as 异常:
            print(f"[售后页] 详情添加备注失败: {异常}")
            return False

    async def 抓取退货物流信息(self) -> dict:
        """切换退货物流 Tab 并抓取物流轨迹。"""
        目标页面 = await self._获取目标页面()

        退货Tab点击成功 = False
        for 选择器 in 售后页选择器.退货物流Tab.所有选择器():
            try:
                await self._点击目标页面元素(目标页面, 选择器)
                await self.随机延迟(0.5, 1)
                退货Tab点击成功 = True
                break
            except Exception:
                continue

        if not 退货Tab点击成功:
            print("[售后页] 未找到退货物流Tab，可能没有退货物流")
            return {"有退货物流": False}

        for 选择器 in 售后页选择器.查看全部按钮.所有选择器():
            try:
                await self._点击目标页面元素(目标页面, 选择器)
                await self.随机延迟(0.5, 1)
                break
            except Exception:
                continue

        try:
            结果 = await 目标页面.evaluate(
                """
                () => {
                    const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                    const body = document.body ? document.body.innerText : '';

                    const 公司匹配 = body.match(/快递公司[：:]\\s*([^\\n]+)/);
                    const 单号匹配 = body.match(/快递单号[：:]\\s*([A-Za-z0-9]+)/);
                    const 轨迹列表 = [];
                    const 轨迹正则 = /(\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}(?::\\d{2})?)\\s*\\n?\\s*(.+?)(?=\\d{4}-\\d{2}-\\d{2}|$)/gs;
                    let 匹配;
                    while ((匹配 = 轨迹正则.exec(body)) !== null) {
                        轨迹列表.push({
                            时间: 清洗(匹配[1]),
                            描述: 清洗(匹配[2]),
                        });
                    }

                    const 最新轨迹 = 轨迹列表.length > 0 ? 轨迹列表[0] : null;
                    const 派件人匹配 = body.match(/快递员[：:]\\s*([^\\s(（]+)/);
                    const 派件人备选 = body.match(/快递员[：:]\\s*\\S+?([\\u4e00-\\u9fa5]{2,4})\\s*[（(]/);
                    const 网点匹配 = body.match(/【([^】]+)】/);
                    const 起始位置 = body.indexOf('退货物流');
                    const 结束位置 = body.indexOf('备注');

                    return {
                        有退货物流: true,
                        退货快递公司: 公司匹配 ? 清洗(公司匹配[1]) : '',
                        退货快递单号: 单号匹配 ? 清洗(单号匹配[1]) : '',
                        轨迹全文: 清洗(body.substring(
                            起始位置 >= 0 ? 起始位置 : 0,
                            结束位置 >= 0 ? 结束位置 : body.length
                        )).substring(0, 2000),
                        轨迹列表: 轨迹列表.slice(0, 20),
                        最新轨迹,
                        退货物流状态: 最新轨迹 ? 清洗(最新轨迹.描述) : '',
                        派件人: 派件人匹配 ? 清洗(派件人匹配[1]) : (派件人备选 ? 清洗(派件人备选[1]) : ''),
                        网点: 网点匹配 ? 清洗(网点匹配[1]) : '',
                    };
                }
                """,
            )
        except Exception as 异常:
            print(f"[售后页] 抓取退货物流失败: {异常}")
            return {"有退货物流": False}

        结果字典 = dict(结果 or {"有退货物流": False})
        if 结果字典.get("有退货物流"):
            print(
                f"[售后页] 抓取退货物流成功: "
                f"{结果字典.get('退货快递公司', '')} {结果字典.get('退货快递单号', '')}"
            )
        return 结果字典

    async def 点击指定按钮(self, 按钮文本: str) -> bool:
        await self.操作前延迟()
        目标页面 = await self._获取目标页面()
        结果 = await 目标页面.evaluate(
            """
            ({ 按钮文本, 按钮选择器 }) => {
                const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                const 收集按钮 = (根节点) => Array.from(
                    根节点.querySelectorAll(按钮选择器)
                );
                const 其他操作区域 = Array.from(
                    document.querySelectorAll('div, section, footer, aside')
                ).filter((节点) => 清洗(节点.textContent).includes('其他操作'));
                const 按钮列表 = Array.from(
                    new Set([
                        ...收集按钮(document),
                        ...其他操作区域.flatMap((节点) => 收集按钮(节点)),
                    ])
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
            {"按钮文本": 按钮文本, "按钮选择器": 详情按钮查询选择器},
        )
        if 结果:
            await self.操作后延迟()
        return bool(结果)

    async def 读取当前所有按钮(self) -> list[str]:
        await self.操作前延迟()
        目标页面 = await self._获取目标页面()
        结果 = await 目标页面.evaluate(
            """
            (按钮选择器) => {
                const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                const 收集文本 = (根节点) => Array.from(根节点.querySelectorAll(按钮选择器))
                    .map((按钮) => 清洗(按钮.textContent))
                    .filter((文本) => 文本 && 文本.length < 30);
                const 其他操作区域 = Array.from(
                    document.querySelectorAll('div, section, footer, aside')
                ).filter((节点) => 清洗(节点.textContent).includes('其他操作'));
                return Array.from(new Set(
                    [
                        ...收集文本(document),
                        ...其他操作区域.flatMap((节点) => 收集文本(节点)),
                    ]
                ));
            }
            """,
            详情按钮查询选择器,
        )
        await self.操作后延迟()
        return list(结果 or [])

    async def 检查是否需要处理(self) -> bool:
        按钮列表 = await self.读取当前所有按钮()
        操作关键词 = ["同意退款", "同意退货", "拒绝", "拒收后退款", "快递拦截"]
        return any(关键词 in 按钮文本 for 按钮文本 in 按钮列表 for 关键词 in 操作关键词)

    async def _检查有下一页(self) -> bool:
        for 选择器 in 售后页选择器.下一页按钮.所有选择器():
            try:
                下一页按钮 = self.页面.locator(选择器).first
                aria_disabled = 下一页按钮.get_attribute("aria-disabled")
                if inspect.isawaitable(aria_disabled):
                    aria_disabled = await aria_disabled
                class_name = 下一页按钮.get_attribute("class")
                if inspect.isawaitable(class_name):
                    class_name = await class_name
                class_name_text = str(class_name or "").lower()
                if (
                    str(aria_disabled or "").lower() == "true"
                    or "disabled" in class_name_text
                    or "pgt_disabled" in class_name_text
                ):
                    return False
                return True
            except Exception:
                continue
        return False

    async def 翻页(self) -> bool:
        await self.操作前延迟()
        if not await self._检查有下一页():
            return False
        for 选择器 in 售后页选择器.下一页按钮.所有选择器():
            try:
                await self.安全点击(选择器)
                await self.操作后延迟()
                return True
            except Exception:
                continue
        return False

    async def 翻页并拦截(self) -> list[dict] | None:
        """翻到下一页并优先通过 API 拦截获取下一页数据。"""
        if not await self._检查有下一页():
            return None

        拦截任务 = asyncio.create_task(self.拦截售后列表API(超时秒=10, 仅待商家处理=True))
        await asyncio.sleep(0)
        翻页成功 = await self.翻页()
        if not 翻页成功:
            拦截任务.cancel()
            return None
        return await 拦截任务

    async def 扫描所有待处理(self) -> list[dict]:
        await self.确保待商家处理已选中()
        结果: list[dict] = []
        while True:
            数量 = await self.获取售后单数量()
            for 行号 in range(1, 数量 + 1):
                信息 = await self.获取第N行信息(行号)
                if 信息 and 信息.get("订单号"):
                    结果.append(信息)
            if not await self.翻页():
                break
        return 结果

    async def 关闭详情标签(self) -> None:
        详情页 = self._详情页
        if 详情页 and not await self._页面是否已关闭(详情页):
            await 详情页.close()
        self._详情页 = None

    async def 抓取详情页完整信息(self) -> dict:
        await self.操作前延迟()
        目标页面 = await self._获取目标页面()
        await self._等待详情页区域(目标页面)
        结果 = await 目标页面.evaluate(
            """
            (按钮选择器) => {
                const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                const 全文 = 清洗(document.body ? document.body.innerText : '');
                const 全元素 = Array.from(document.querySelectorAll('td, div, span, p, label, li, strong, a'));
                const 取文本 = (节点) => 清洗(节点 && 节点.textContent);

                const 提取字段 = (标签文本) => {
                    const 标签节点 = 全元素.find((元素) => {
                        const 文本 = 取文本(元素);
                        return 文本 === 标签文本 || 文本 === `${标签文本}：` || 文本 === `${标签文本}:` ||
                            文本.startsWith(`${标签文本}：`) || 文本.startsWith(`${标签文本}:`);
                    });
                    if (标签节点) {
                        const 文本 = 取文本(标签节点);
                        if (文本.startsWith(`${标签文本}：`) || 文本.startsWith(`${标签文本}:`)) {
                            return 清洗(文本.replace(标签文本, '').replace(/^[：:\\s]+/, ''));
                        }
                        const 邻居列表 = [
                            标签节点.nextElementSibling,
                            标签节点.parentElement && 标签节点.parentElement.nextElementSibling,
                            标签节点.parentElement && 标签节点.parentElement.querySelector('td:last-child, div:last-child, span:last-child'),
                        ].filter(Boolean);
                        for (const 节点 of 邻居列表) {
                            const 值 = 取文本(节点);
                            if (值 && 值 !== 标签文本) {
                                return 值;
                            }
                        }
                    }
                    const 匹配 = 全文.match(new RegExp(`${标签文本}[：: ]+([^\\n]+)`));
                    return 匹配 ? 清洗(匹配[1]) : '';
                };

                const 提取金额 = (文本) => {
                    const 匹配 = String(文本 || '').match(/[¥￥]\\s*(\\d+(?:\\.\\d+)?)/);
                    return 匹配 ? parseFloat(匹配[1]) : 0;
                };

                const 商品名称 = (() => {
                    const 文本列表 = Array.from(document.querySelectorAll('div, span, p'))
                        .map((元素) => 清洗(元素.textContent))
                        .filter((文本) => 文本.length > 10 && 文本.length < 100)
                        .filter((文本) => !['售后', '退款', '订单', '物流'].some((值) => 文本.includes(值)));
                    return 文本列表.find((文本) => /\\d+[件支个包套]/.test(文本)) || 文本列表[0] || '';
                })();

                const 协商最新 = (() => {
                    const 匹配 = 全文.match(/留言[：:]\\s*(.+?)(?=买家申请|$)/);
                    return 匹配 ? 匹配[1].trim() : '';
                })();

                const 售后状态描述 = (() => {
                    const 匹配 = 全文.match(/售后状态\\s+(.+?)(?=\\d+\\s*[天时分秒])/);
                    return 匹配 ? 匹配[1].trim() : (提取字段('售后状态') || '');
                })();

                const 物流文本 = (() => {
                    const 轨迹节点 = document.querySelectorAll('.logistics-item, .timeline-item, .ant-timeline-item, li');
                    for (const 节点 of 轨迹节点) {
                        const 文本 = 取文本(节点);
                        if (文本 && (文本.includes('物流') || /\\d{4}-\\d{2}-\\d{2}/.test(文本))) {
                            return 文本;
                        }
                    }
                    return 提取字段('物流轨迹') || 提取字段('物流信息') || '';
                })();

                const 读取按钮文本 = (根节点) => Array.from(根节点.querySelectorAll(按钮选择器))
                    .map((节点) => 取文本(节点))
                    .filter((文本) => 文本 && 文本.length < 30);
                const 其他操作区域 = Array.from(
                    document.querySelectorAll('div, section, footer, aside')
                ).filter((节点) => 清洗(节点.textContent).includes('其他操作'));
                const 按钮列表 = Array.from(new Set([
                    ...读取按钮文本(document),
                    ...其他操作区域.flatMap((节点) => 读取按钮文本(节点)),
                ]));
                const 售后编码 = 提取字段('售后编码') || 提取字段('售后编号');
                const 退款金额文本 = 提取字段('退款金额');
                const 实收金额文本 = 提取字段('实收');
                const 订单编号 = 提取字段('订单编号') || 提取字段('订单号');
                const 联系地址 = 提取字段('联系地址') || 提取字段('收货地址');

                return {
                    售后编码,
                    售后编号: 售后编码,
                    售后类型: 提取字段('售后类型'),
                    售后状态: 售后状态描述,
                    售后状态描述,
                    发货状态: 提取字段('发货状态'),
                    退款金额: 提取金额(退款金额文本),
                    退款金额文本,
                    实收金额: 提取金额(实收金额文本),
                    实收金额文本,
                    申请原因: 提取字段('申请原因'),
                    售后申请说明: 提取字段('售后申请说明') || 提取字段('申请说明'),
                    发货物流公司: 提取字段('发货物流公司') || 提取字段('物流公司'),
                    发货快递单号: 提取字段('发货快递单号') || 提取字段('快递单号'),
                    有售后图片: document.querySelectorAll('img[src*="upload"], img[src*="pic"], img[src*="pinduoduo"], .image-preview img').length > 0,
                    订单编号,
                    订单号: 订单编号,
                    商品名称,
                    联系地址,
                    收货地址: 联系地址,
                    收货人: 提取字段('收货人'),
                    退货包运费: 提取字段('退货包运费'),
                    成团时间: 提取字段('成团时间'),
                    物流最新状态: 物流文本,
                    物流最新时间: (物流文本.match(/\\d{4}-\\d{2}-\\d{2}[ T]\\d{2}:\\d{2}(?::\\d{2})?/) || [''])[0].replace('T', ' '),
                    剩余处理时间: (全文.match(/((?:\\d+天)?\\d+时\\d+分(?:\\d+秒)?)/) || [''])[0],
                    平台建议: 提取字段('平台建议') || '',
                    可用按钮列表: 按钮列表,
                    协商轮次: document.querySelectorAll('.negotiate-item, .apply-item, .chat-record-item, .ant-timeline-item').length || 0,
                    协商最新,
                    最新聊天内容: 协商最新,
                    商家已回复: Boolean(协商最新),
                };
            }
            """,
            详情按钮查询选择器,
        )
        await self.操作后延迟()
        return dict(结果 or {})

    async def 详情页截图(self, 名称: str) -> str | None:
        await self.操作前延迟()
        目标页面 = await self._获取目标页面()
        截图目录 = Path(配置实例.DATA_DIR) / "screenshots"
        截图目录.mkdir(parents=True, exist_ok=True)
        路径 = 截图目录 / f"{名称}.png"
        try:
            await 目标页面.screenshot(path=str(路径), full_page=True)
            await self.操作后延迟()
            return str(路径)
        except Exception:
            return None

    async def 弹窗扫描循环(self, 弹窗偏好: dict | None = None, 最大轮次: int = 8) -> str:
        目标页面 = await self._获取目标页面()
        偏好 = 弹窗偏好 or {}
        for 轮次 in range(最大轮次):
            await self.随机延迟(0.5, 1.5)
            弹窗信息 = await 目标页面.evaluate(
                """
                () => {
                    const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                    const 弹窗 = document.querySelector('.ant-modal-content, .ant-drawer-content, [role="dialog"]');
                    if (!弹窗) {
                        return null;
                    }
                    return {
                        文本: 清洗(弹窗.innerText),
                        按钮: Array.from(弹窗.querySelectorAll('button'))
                            .map((节点) => 清洗(节点.textContent))
                            .filter((文本) => 文本 && 文本.length < 20),
                        有选择框: 弹窗.querySelectorAll('select, .ant-select, [role="listbox"]').length > 0,
                        单选选项: Array.from(弹窗.querySelectorAll('.ant-radio-wrapper, .ant-checkbox-wrapper, [role="radio"], [role="checkbox"]'))
                            .map((节点) => 清洗(节点.textContent))
                            .filter(Boolean),
                        有输入框: 弹窗.querySelectorAll('input, textarea').length > 0,
                        有翻页: Boolean(弹窗.querySelector('.ant-pagination')),
                    };
                }
                """,
            )
            if not 弹窗信息:
                return "无弹窗" if 轮次 == 0 else "成功"
            处理结果 = await self._处理单个弹窗(目标页面, dict(弹窗信息), 偏好)
            if 处理结果 == "人工处理":
                await self.详情页截图(f"未识别弹窗_轮次{轮次 + 1}")
                return "人工处理"
        return "人工处理"

    async def _处理单个弹窗(self, 页面, 弹窗信息: dict, 偏好: dict) -> str:
        按钮 = list(弹窗信息.get("按钮") or [])
        单选选项 = list(弹窗信息.get("单选选项") or [])
        if not 弹窗信息.get("有选择框") and not 弹窗信息.get("有输入框") and not 单选选项:
            for 词 in ["确定", "确认", "知道了", "好的"]:
                for 按钮文本 in 按钮:
                    if 词 in 按钮文本:
                        return "继续" if await self._JS点击弹窗按钮(页面, 按钮文本) else "人工处理"
            return "人工处理"
        if 单选选项:
            偏好列表 = list(偏好.get("选项偏好") or [])
            for 偏好值 in 偏好列表:
                for 选项 in 单选选项:
                    if 偏好值 in 选项:
                        if not await self._JS点击包含文本(页面, 选项):
                            return "人工处理"
                        await self._点击弹窗提交按钮(页面, 按钮)
                        return "继续"
            if len(单选选项) == 1:
                if not await self._JS点击包含文本(页面, 单选选项[0]):
                    return "人工处理"
                await self._点击弹窗提交按钮(页面, 按钮)
                return "继续"
            return "人工处理"
        if 弹窗信息.get("有选择框"):
            偏好值 = str(偏好.get("下拉偏好") or "").strip()
            if not 偏好值 or not await self._JS选择下拉选项(页面, 偏好值):
                return "人工处理"
            await self._点击弹窗提交按钮(页面, 按钮)
            return "继续"
        if 弹窗信息.get("有输入框"):
            内容 = str(偏好.get("输入内容") or "").strip()
            if not 内容 or not await self._JS填写弹窗输入框(页面, 内容):
                return "人工处理"
            await self._点击弹窗提交按钮(页面, 按钮)
            return "继续"
        return "人工处理"

    async def _JS点击弹窗按钮(self, 页面, 按钮文本: str) -> bool:
        结果 = await 页面.evaluate(
            """
            (按钮文本) => {
                const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                const 弹窗 = document.querySelector('.ant-modal-content, .ant-drawer-content, [role="dialog"]');
                if (!弹窗) {
                    return false;
                }
                for (const 按钮 of 弹窗.querySelectorAll('button')) {
                    if (清洗(按钮.textContent).includes(按钮文本) && !按钮.disabled) {
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
        return bool(结果)

    async def _JS点击包含文本(self, 页面, 文本: str) -> bool:
        结果 = await 页面.evaluate(
            """
            (文本) => {
                const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                const 弹窗 = document.querySelector('.ant-modal-content, .ant-drawer-content, [role="dialog"]');
                if (!弹窗) {
                    return false;
                }
                for (const 元素 of 弹窗.querySelectorAll('.ant-radio-wrapper, .ant-checkbox-wrapper, [role="radio"], [role="checkbox"], .ant-select-item, label')) {
                    if (清洗(元素.textContent).includes(文本)) {
                        元素.click();
                        return true;
                    }
                }
                return false;
            }
            """,
            文本,
        )
        if 结果:
            await self.随机延迟(0.2, 0.5)
        return bool(结果)

    async def _JS选择下拉选项(self, 页面, 偏好值: str) -> bool:
        结果 = await 页面.evaluate(
            """
            (偏好值) => {
                const 清洗 = (值) => String(值 || '').replace(/\\s+/g, ' ').trim();
                const 弹窗 = document.querySelector('.ant-modal-content, .ant-drawer-content, [role="dialog"]');
                if (!弹窗) {
                    return false;
                }
                const 选择器 = 弹窗.querySelector('.ant-select, select, [role="combobox"]');
                if (!选择器) {
                    return false;
                }
                选择器.click();
                return new Promise((resolve) => {
                    setTimeout(() => {
                        const 选项列表 = document.querySelectorAll('.ant-select-item, .ant-select-dropdown .ant-select-item-option, option, [role="option"]');
                        for (const 选项 of 选项列表) {
                            if (清洗(选项.textContent).includes(偏好值)) {
                                选项.click();
                                resolve(true);
                                return;
                            }
                        }
                        resolve(false);
                    }, 500);
                });
            }
            """,
            偏好值,
        )
        if 结果:
            await self.随机延迟(0.2, 0.5)
        return bool(结果)

    async def _JS填写弹窗输入框(self, 页面, 内容: str) -> bool:
        结果 = await 页面.evaluate(
            """
            (内容) => {
                const 弹窗 = document.querySelector('.ant-modal-content, .ant-drawer-content, [role="dialog"]');
                if (!弹窗) {
                    return false;
                }
                const 输入框 = 弹窗.querySelector('textarea, input[type="text"], input:not([type])');
                if (!输入框) {
                    return false;
                }
                输入框.focus();
                输入框.value = 内容;
                输入框.dispatchEvent(new Event('input', { bubbles: true }));
                输入框.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }
            """,
            内容,
        )
        if 结果:
            await self.随机延迟(0.2, 0.5)
        return bool(结果)
