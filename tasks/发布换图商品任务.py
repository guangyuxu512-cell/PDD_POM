"""发布换图商品任务模块"""
from backend.配置 import 配置实例
from backend.services.任务参数服务 import 任务参数服务实例
from browser.反检测 import 真人模拟器
from browser.任务回调 import 自动回调, 上报
from browser.验证码识别 import 验证码识别器
from browser.滑块验证码 import 滑块处理器
from pages.发布商品页 import 发布商品页
from pages.商品列表页 import 商品列表页
from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task


@register_task(
    "发布换图商品",
    "搜索商品并发布相似品（换图+调整主图位置）",
    requires_input=True,
    required_fields=["parent_product_id"],
    supports_empty_context=False,
)
class 发布换图商品任务(基础任务):
    """发布换图商品任务（换图版）"""

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
        except Exception as e:
            print(f"[发布换图商品任务] 回填任务参数失败: {e}")

    async def _安全截图并关闭(self, 发布页对象: 发布商品页 | None) -> None:
        """安全截图并关闭发布页。"""
        if 发布页对象 is None:
            return

        try:
            await 发布页对象.截图当前状态()
        except Exception:
            pass

        try:
            await 发布页对象.关闭页面()
        except Exception:
            pass

    @自动回调("发布换图商品")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        """执行发布换图商品流程。"""
        self._执行结果 = {}

        任务参数 = 店铺配置.get("task_param") or {}
        父商品ID = str(任务参数.get("parent_product_id") or "").strip()
        新标题 = str(任务参数.get("new_title") or "").strip()
        图片路径 = str(任务参数.get("image_path") or "").strip()
        任务参数ID = 任务参数.get("task_param_id")
        店铺ID = 店铺配置.get("shop_id") or 店铺配置.get("username") or "临时店铺"

        if not 父商品ID:
            raise ValueError("parent_product_id 不能为空")

        await self._回填任务参数(任务参数ID, "running", {"parent_product_id": 父商品ID})

        商品列表对象 = 商品列表页(页面)
        发布页对象: 发布商品页 | None = None
        初始新商品ID = ""

        try:
            await 上报("打开商品列表页", 店铺ID)
            await 商品列表对象.导航到商品列表()

            await 上报(f"搜索商品: {父商品ID}", 店铺ID)
            await 商品列表对象.输入商品ID(父商品ID)
            await 商品列表对象.点击查询()
            await 商品列表对象.等待搜索结果()

            await 上报("点击发布相似品", 店铺ID)
            async with 页面.expect_popup() as 弹窗信息:
                await 商品列表对象.点击发布相似()
                await 商品列表对象.确认发布相似弹窗()
            新页面 = await 弹窗信息.value

            await 上报("初始化发布页", 店铺ID)
            发布页对象 = 发布商品页(新页面)
            await 发布页对象.初始化页面()

            初始新商品ID = 发布页对象.从URL提取新商品ID()
            await 上报(f"新商品ID: {初始新商品ID or '未获取到'}", 店铺ID)

            if 图片路径:
                await 上报("上传新主图", 店铺ID)
                try:
                    await 发布页对象.上传主图(图片路径)
                except FileNotFoundError as e:
                    await 上报(f"[警告] 上传主图失败，跳过上传: {str(e)}", 店铺ID)
                except Exception as e:
                    await 上报(f"[警告] 上传主图异常，继续执行: {str(e)}", 店铺ID)
            else:
                await 上报("跳过上传", 店铺ID)

            await 上报("调整主图位置", 店铺ID)
            调整结果 = await 发布页对象.随机调整主图到第一位()
            await 上报(f"调整结果: {调整结果}", 店铺ID)

            if 新标题:
                await 上报("修改标题", 店铺ID)
                await 发布页对象.修改标题(新标题)
            else:
                await 上报("不修改标题", 店铺ID)

            await 上报("点击提交并上架", 店铺ID)
            await 发布页对象.点击提交并上架()

            await 上报("检测是否出现滑块验证码", 店铺ID)
            try:
                if await 发布页对象.检测滑块验证码():
                    if not 配置实例.CAPTCHA_API_KEY:
                        await 上报("检测到滑块验证码，等待人工处理", 店铺ID)
                        try:
                            await 发布页对象.截图当前状态()
                        except Exception:
                            pass
                        await self._回填任务参数(
                            任务参数ID,
                            "failed",
                            {"parent_product_id": 父商品ID},
                            "需要验证码",
                        )
                        return "需要验证码"

                    await 上报("检测到滑块验证码，开始处理", 店铺ID)
                    识别器 = 验证码识别器(配置实例.CAPTCHA_PROVIDER, 配置实例.CAPTCHA_API_KEY)
                    模拟器 = 真人模拟器(新页面)
                    滑块处理 = 滑块处理器(识别器, 模拟器)
                    await 滑块处理.处理(新页面)
                    await 上报("滑块验证码处理完成", 店铺ID)
            except Exception as e:
                错误信息 = str(e).lower()
                if "context" in 错误信息 or "destroyed" in 错误信息:
                    await 上报("页面已跳转，跳过验证码检测", 店铺ID)
                else:
                    raise

            await 上报("检查发布结果", 店铺ID)
            if await 发布页对象.是否发布成功():
                成功商品ID = 发布页对象.从成功页提取商品ID() or 初始新商品ID
                self._执行结果 = {
                    "new_product_id": 成功商品ID,
                    "parent_product_id": 父商品ID,
                }
                await 上报(f"[成功] 发布成功，新商品ID: {成功商品ID or '未获取到'}", 店铺ID)
                await self._回填任务参数(任务参数ID, "success", self._执行结果)
                await self._安全截图并关闭(发布页对象)
                return "成功"

            await 上报("[失败] 发布失败", 店铺ID)
            await self._回填任务参数(
                任务参数ID,
                "failed",
                {"parent_product_id": 父商品ID},
                "发布失败",
            )
            await self._安全截图并关闭(发布页对象)
            return "失败"

        except Exception as e:
            await 上报(f"[失败] 发布换图商品异常: {str(e)}", 店铺ID)
            await self._回填任务参数(
                任务参数ID,
                "failed",
                {"parent_product_id": 父商品ID},
                str(e),
            )
            await self._安全截图并关闭(发布页对象)
            return "失败"
