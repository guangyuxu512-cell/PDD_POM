"""发布相似商品任务模块"""
import asyncio
import random

from backend.services.任务参数服务 import 任务参数服务实例
from browser.任务回调 import 自动回调, 上报
from pages.发布商品页 import 发布商品页
from pages.商品列表页 import 商品列表页
from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task


@register_task("发布相似商品", "搜索商品并发布相似品（不换图）")
class 发布相似商品任务(基础任务):
    """发布相似商品任务（不换图版）"""

    def __init__(self):
        self._执行结果 = {}

    async def _回填任务参数(
        self,
        task_param_id,
        状态: str,
        结果=None,
        错误信息: str | None = None,
    ) -> None:
        """按 task_param_id 回填执行结果。"""
        if not task_param_id:
            return
        try:
            await 任务参数服务实例.更新执行结果(
                int(task_param_id),
                状态,
                结果=结果 or {},
                错误信息=错误信息,
            )
        except Exception as 异常:
            print(f"[发布相似商品任务] 回填任务参数失败: {异常}")

    @staticmethod
    def _页面已关闭(页面) -> bool:
        """兼容真实 Page 与测试替身判断页面关闭状态。"""
        if 页面 is None:
            return True

        检查方法 = getattr(页面, "is_closed", None)
        if not callable(检查方法):
            return False

        try:
            检查结果 = 检查方法()
        except Exception:
            return False

        return 检查结果 if isinstance(检查结果, bool) else False

    @staticmethod
    def _获取页面上下文(页面):
        """获取页面所属 context。"""
        if 页面 is None:
            return None
        return getattr(页面, "context", None)

    async def _安全截图并关闭(
        self,
        发布页对象: 发布商品页 | None,
        商品列表对象: 商品列表页 | None = None,
    ) -> None:
        """安全截图并关闭发布页。"""
        if 发布页对象 is None:
            return

        浏览器上下文 = self._获取页面上下文(getattr(发布页对象, "页面", None))

        try:
            await 发布页对象.截图当前状态()
        except Exception:
            pass

        try:
            await 发布页对象.关闭当前标签页()
        except Exception:
            pass

        if 商品列表对象 is not None:
            try:
                主页面 = getattr(商品列表对象, "页面", None)
                if self._页面已关闭(主页面) and 浏览器上下文 is not None:
                    新主页面 = await 浏览器上下文.new_page()
                    商品列表对象 = 商品列表页(新主页面)
                    await 商品列表对象.导航到商品列表()
                await 商品列表对象.切回前台()
            except Exception:
                pass

    @staticmethod
    def _读取参数(任务参数: dict, 中文键名: str, 英文键名: str) -> str:
        """兼容中文任务单与当前 task_params 注入结构。"""
        return str(任务参数.get(中文键名) or 任务参数.get(英文键名) or "").strip()

    async def _步骤间延迟(self) -> None:
        """在任务步骤之间加入思考停顿。"""
        await asyncio.sleep(random.uniform(1.0, 3.0))

    @自动回调("发布相似商品")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        """严格执行单次发布相似商品流程。"""
        self._执行结果 = {}

        任务参数 = 店铺配置.get("task_param") or {}
        父商品ID = self._读取参数(任务参数, "父商品ID", "parent_product_id")
        新标题 = self._读取参数(任务参数, "新标题", "new_title")
        任务参数ID = 任务参数.get("task_param_id")
        店铺ID = 店铺配置.get("shop_id") or 店铺配置.get("username") or "临时店铺"

        if not 父商品ID:
            raise ValueError("父商品ID不能为空")

        await self._回填任务参数(任务参数ID, "running", {"父商品ID": 父商品ID})

        商品列表对象 = 商品列表页(页面)
        发布页对象: 发布商品页 | None = None
        初始新商品ID = ""
        实际标题 = ""

        try:
            await 上报("打开商品列表页", 店铺ID)
            await 商品列表对象.导航到商品列表()
            await self._步骤间延迟()

            await 上报(f"搜索商品: {父商品ID}", 店铺ID)
            await 商品列表对象.输入商品ID(父商品ID)
            await 商品列表对象.点击查询()
            await 商品列表对象.等待搜索结果()
            await self._步骤间延迟()

            await 上报("点击发布相似品", 店铺ID)
            async with 页面.expect_popup() as 弹窗信息:
                await 商品列表对象.点击发布相似()
                await 商品列表对象.确认发布相似弹窗()
            新页面 = await 弹窗信息.value
            await self._步骤间延迟()

            await 上报("等待发布页加载", 店铺ID)
            await 新页面.wait_for_load_state("domcontentloaded")
            发布页对象 = 发布商品页(新页面)
            await 发布页对象.关闭所有弹窗()
            await self._步骤间延迟()

            初始新商品ID = await 发布页对象.提取商品ID()
            await 上报(f"新商品ID: {初始新商品ID or '未获取到'}", 店铺ID)

            await 上报("调整主图顺序", 店铺ID)
            主图列表 = await 发布页对象.获取主图列表()
            if len(主图列表) > 1:
                最大索引 = min(4, len(主图列表) - 1)
                源索引 = random.randint(1, 最大索引)
                await 发布页对象.拖拽主图(源索引, 0)
                await 上报(f"已将第{源索引 + 1}张图拖到第1位", 店铺ID)
            else:
                await 上报("只有1张主图，跳过拖拽", 店铺ID)
            await self._步骤间延迟()

            if 新标题:
                await 上报("修改标题", 店铺ID)
                await 发布页对象.输入商品标题(新标题)
                实际标题 = 新标题
            else:
                await 上报("不修改标题", 店铺ID)
                实际标题 = await 发布页对象.获取商品标题()
            await self._步骤间延迟()

            await 上报("点击提交并上架", 店铺ID)
            await 发布页对象.点击提交并上架()
            await self._步骤间延迟()

            await 上报("检查发布结果", 店铺ID)
            if await 发布页对象.等待发布成功():
                成功商品ID = await 发布页对象.提取商品ID() or 初始新商品ID
                self._执行结果 = {
                    "新商品ID": 成功商品ID,
                    "父商品ID": 父商品ID,
                    "标题": 实际标题,
                }
                await 上报(f"[成功] 发布成功，新商品ID: {成功商品ID or '未获取到'}", 店铺ID)
                await self._回填任务参数(任务参数ID, "success", self._执行结果)
                await self._安全截图并关闭(发布页对象, 商品列表对象)
                return "成功"

            self._执行结果 = {
                "父商品ID": 父商品ID,
                "标题": 实际标题,
            }
            await 上报("[失败] 发布失败", 店铺ID)
            await self._回填任务参数(
                任务参数ID,
                "failed",
                self._执行结果,
                "发布失败",
            )
            await self._安全截图并关闭(发布页对象, 商品列表对象)
            return "失败"

        except Exception as 异常:
            if not self._执行结果:
                self._执行结果 = {
                    "父商品ID": 父商品ID,
                    "标题": 实际标题,
                }
            await 上报(f"[失败] 发布相似商品异常: {异常}", 店铺ID)
            await self._回填任务参数(
                任务参数ID,
                "failed",
                self._执行结果,
                str(异常),
            )
            await self._安全截图并关闭(发布页对象, 商品列表对象)
            return "失败"
