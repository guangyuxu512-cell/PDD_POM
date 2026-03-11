"""拼多多登录流程：优先 Cookie 登录 → 失败则手机号密码登录 → 处理短信验证码 → 保存 Cookie。"""
import asyncio
from pathlib import Path
from backend.配置 import 配置实例
from browser.反检测 import 真人模拟器
from browser.验证码识别 import 验证码识别器
from browser.滑块验证码 import 滑块处理器
from pages.登录页 import 登录页
from browser.任务回调 import 自动回调, 上报
from tasks.基础任务 import 基础任务
from tasks.注册表 import register_task


@register_task("登录", "打开浏览器并登录店铺后台")
class 登录任务(基础任务):
    """完整的登录流程：优先 Cookie 登录 → 失败则账号密码登录 → 处理短信验证码 → 保存 Cookie"""

    @自动回调("登录")
    async def 执行(self, 页面, 店铺配置: dict) -> str:
        """
        执行登录任务

        参数:
            页面: Playwright page 对象
            店铺配置: dict，必须包含 "username"、"password" 和 "shop_id"

        返回:
            "成功" — 登录成功
            "需要验证码" — 需要人工处理滑块验证码
            "失败" — 登录失败
            失败时抛出异常，装饰器自动回调 failed
        """
        登录 = 登录页(页面)
        店铺ID = 店铺配置.get("shop_id")
        兼容旧调用 = not 店铺ID

        if not 店铺ID:
            店铺ID = 店铺配置.get("username") or "临时店铺"

        # === 步骤 0：检测是否已登录 ===
        await 上报("检测当前登录状态", 店铺ID)

        # 先访问首页，检查是否已登录
        try:
            await 登录.访问首页()
            当前URL = 页面.url

            if isinstance(当前URL, str) and "mms.pinduoduo.com/home" in 当前URL:
                await 上报("[成功] 已登录状态，跳过登录流程", 店铺ID)
                return "成功"
            else:
                await 上报("未登录，开始登录流程", 店铺ID)
        except Exception as e:
            await 上报(f"登录状态检测失败: {str(e)}，继续登录流程", 店铺ID)

        # === 步骤 1：尝试 Cookie 登录 ===
        await 上报("检查本地 Cookie 文件", 店铺ID)
        Cookie文件路径 = Path(登录._获取Cookie文件路径(店铺ID))

        if Cookie文件路径.exists():
            await 上报("发现本地 Cookie 文件，尝试加载", 店铺ID)

            # 加载 Cookie
            加载成功 = await 登录.加载Cookie(店铺ID)
            if 加载成功:
                await 上报("Cookie 加载成功，验证有效性", 店铺ID)

                # 验证 Cookie 是否有效
                if await 登录.检测Cookie是否有效():
                    await 上报("[成功] Cookie 登录成功，跳过密码登录", 店铺ID)
                    return "成功"
                else:
                    await 上报("[失败] Cookie 无效，切换密码登录", 店铺ID)
            else:
                await 上报("[失败] Cookie 加载失败，切换密码登录", 店铺ID)
        else:
            await 上报("无本地 Cookie，开始密码登录", 店铺ID)

        # === 步骤 2：账号密码登录 ===
        await 上报("打开登录页", 店铺ID)
        await 登录.导航()

        await 上报("切换到账号登录", 店铺ID)
        await 登录.切换账号登录()

        手机号 = 店铺配置["username"]
        脱敏手机号 = 手机号[:3] + "****" + 手机号[-4:] if len(手机号) >= 7 else "***"
        await 上报(f"填写手机号: {脱敏手机号}", 店铺ID)
        await 登录.填写手机号(手机号)

        await 上报("填写密码", 店铺ID)
        await 登录.填写密码(店铺配置["password"])

        await 上报("点击登录按钮", 店铺ID)
        await 登录.点击登录()

        # === 步骤 3：处理验证码 ===
        await 上报("检测是否出现滑块验证码", 店铺ID)
        try:
            if await 登录.检测滑块验证码():
                if not 配置实例.CAPTCHA_API_KEY or 兼容旧调用:
                    await 上报("检测到滑块验证码，等待人工处理", 店铺ID)
                    try:
                        await 登录.截图登录状态()
                    except Exception:
                        pass
                    return "需要验证码"

                await 上报("检测到滑块验证码，开始处理", 店铺ID)
                识别器 = 验证码识别器(配置实例.CAPTCHA_PROVIDER, 配置实例.CAPTCHA_API_KEY)
                模拟器 = 真人模拟器(页面)
                滑块处理 = 滑块处理器(识别器, 模拟器)
                await 滑块处理.处理(页面)
                await 上报("滑块验证码处理完成", 店铺ID)
        except Exception as e:
            错误信息 = str(e).lower()
            if "context" in 错误信息 or "destroyed" in 错误信息:
                await 上报("页面已跳转，跳过验证码检测", 店铺ID)
            else:
                raise

        try:
            await 上报("检测是否需要短信验证码", 店铺ID)
            if await 登录.检测短信验证码():
                await 上报("需要短信验证码，等待人工输入（最多等待120秒）", 店铺ID)
                await 登录.截图登录状态()

                已成功 = False
                for _ in range(40):
                    await asyncio.sleep(3)
                    try:
                        当前URL = 页面.url
                        if "mms.pinduoduo.com/home" in 当前URL:
                            已成功 = True
                            break
                    except Exception:
                        continue

                if 已成功:
                    await 上报("[成功] 短信验证码验证通过，已跳转到首页", 店铺ID)
                    try:
                        await 登录.保存Cookie(店铺ID)
                        await 上报("[成功] Cookie 已保存到文件", 店铺ID)
                    except Exception as e:
                        await 上报(f"[警告] Cookie 保存失败: {str(e)}", 店铺ID)

                    try:
                        await 登录.截图登录状态()
                    except Exception:
                        pass

                    return "成功"

                await 上报("[失败] 等待短信验证码超时（120秒）", 店铺ID)
                try:
                    await 登录.截图登录状态()
                except Exception:
                    pass
                return "失败"
        except Exception as e:
            错误信息 = str(e).lower()
            if "context" in 错误信息 or "destroyed" in 错误信息:
                await 上报("页面已跳转，跳过短信验证码检测", 店铺ID)
            else:
                raise

        # === 步骤 4：检查登录结果 ===
        await 上报("检查登录结果", 店铺ID)
        try:
            是否成功 = await 登录.是否登录成功()

            if 是否成功:
                await 上报("[成功] 登录成功，保存 Cookie", 店铺ID)
                try:
                    await 登录.保存Cookie(店铺ID)
                    await 上报("[成功] Cookie 已保存到文件", 店铺ID)
                except Exception as e:
                    await 上报(f"[警告] Cookie 保存失败: {str(e)}", 店铺ID)

                try:
                    await 登录.截图登录状态()
                except Exception:
                    pass  # 截图失败不影响登录结果

                return "成功"
        except Exception as e:
            错误信息 = str(e).lower()
            if "context" in 错误信息 or "destroyed" in 错误信息:
                # Context destroyed 说明页面跳转了，检查是否跳转到首页
                await 上报("检测到页面跳转，验证登录状态", 店铺ID)
                try:
                    当前URL = 页面.url
                    if "mms.pinduoduo.com/home" in 当前URL:
                        await 上报("[成功] 登录成功（页面已跳转到首页），保存 Cookie", 店铺ID)
                        try:
                            await 登录.保存Cookie(店铺ID)
                            await 上报("[成功] Cookie 已保存到文件", 店铺ID)
                        except Exception as e2:
                            await 上报(f"[警告] Cookie 保存失败: {str(e2)}", 店铺ID)
                        return "成功"
                except Exception:
                    pass

        # 登录失败
        await 上报("[失败] 登录失败", 店铺ID)
        try:
            await 登录.截图登录状态()
        except Exception:
            pass  # 截图失败不影响结果

        if 兼容旧调用:
            raise Exception("登录结果未知")

        return "失败"
