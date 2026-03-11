"""
店铺接口模块

提供店铺管理的 REST API 接口。
"""
from typing import Optional
from fastapi import APIRouter, Query

from backend.models.数据结构 import (
    统一响应,
    成功,
    失败,
    店铺创建请求,
    店铺更新请求,
    Cookie导入请求,
)
from backend.services.店铺服务 import 店铺服务实例
from backend.services.邮箱服务 import 邮箱服务实例
from backend.services import 浏览器服务


# 创建路由
路由 = APIRouter(prefix="/api/shops", tags=["店铺管理"])


@路由.get("", include_in_schema=False)
@路由.get("/", summary="获取店铺列表")
async def 获取店铺列表(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小")
) -> 统一响应:
    """
    获取店铺列表（分页）

    参数:
        page: 页码（从 1 开始）
        page_size: 每页大小（1-100）

    返回:
        统一响应: 包含分页数据的响应
    """
    try:
        结果 = await 店铺服务实例.获取全部(page=page, page_size=page_size)
        return 成功(data=结果)
    except Exception as e:
        return 失败(f"获取店铺列表失败: {str(e)}")


@路由.post("", include_in_schema=False)
@路由.post("/", summary="创建店铺")
async def 创建店铺(请求: 店铺创建请求) -> 统一响应:
    """
    创建新店铺

    参数:
        请求: 店铺创建请求

    返回:
        统一响应: 包含创建后的店铺数据
    """
    try:
        店铺数据 = 请求.model_dump(exclude_none=True)
        店铺 = await 店铺服务实例.创建(店铺数据)
        return 成功(data=店铺, message="创建成功")
    except Exception as e:
        return 失败(f"创建店铺失败: {str(e)}")


@路由.get("/{shop_id}", summary="获取店铺详情")
async def 获取店铺详情(shop_id: str) -> 统一响应:
    """
    获取店铺详情

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 包含店铺数据
    """
    try:
        店铺 = await 店铺服务实例.根据ID获取(shop_id)
        if not 店铺:
            return 失败("店铺不存在")
        return 成功(data=店铺)
    except Exception as e:
        return 失败(f"获取店铺详情失败: {str(e)}")


@路由.put("/{shop_id}", summary="更新店铺")
async def 更新店铺(shop_id: str, 请求: 店铺更新请求) -> 统一响应:
    """
    更新店铺信息

    参数:
        shop_id: 店铺 ID
        请求: 店铺更新请求

    返回:
        统一响应: 包含更新后的店铺数据
    """
    try:
        店铺数据 = 请求.model_dump(exclude_none=True)
        店铺 = await 店铺服务实例.更新(shop_id, 店铺数据)
        if not 店铺:
            return 失败("店铺不存在")
        return 成功(data=店铺, message="更新成功")
    except Exception as e:
        return 失败(f"更新店铺失败: {str(e)}")


@路由.delete("/{shop_id}", summary="删除店铺")
async def 删除店铺(shop_id: str) -> 统一响应:
    """
    删除店铺

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 删除结果
    """
    try:
        成功标志 = await 店铺服务实例.删除(shop_id)
        if not 成功标志:
            return 失败("店铺不存在")
        return 成功(message="删除成功")
    except Exception as e:
        return 失败(f"删除店铺失败: {str(e)}")


@路由.post("/{shop_id}/cookie", summary="导入 Cookie")
async def 导入Cookie(shop_id: str, 请求: Cookie导入请求) -> 统一响应:
    """
    导入店铺 Cookie

    参数:
        shop_id: 店铺 ID
        请求: Cookie 导入请求

    返回:
        统一响应: 导入结果
    """
    try:
        import json
        # 解析 cookie_data（JSON 字符串）
        cookies = json.loads(请求.cookie_data)
        成功标志 = await 店铺服务实例.导入Cookie(shop_id, cookies)
        if not 成功标志:
            return 失败("店铺不存在")
        return 成功(message="导入成功")
    except json.JSONDecodeError:
        return 失败("Cookie 数据格式错误")
    except Exception as e:
        return 失败(f"导入 Cookie 失败: {str(e)}")


@路由.get("/{shop_id}/cookie", summary="导出 Cookie")
async def 导出Cookie(shop_id: str) -> 统一响应:
    """
    导出店铺 Cookie

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 包含 Cookie 数据
    """
    try:
        cookies = await 店铺服务实例.导出Cookie(shop_id)
        if cookies is None:
            return 失败("Cookie 不存在")
        return 成功(data=cookies)
    except Exception as e:
        return 失败(f"导出 Cookie 失败: {str(e)}")


@路由.post("/{shop_id}/open-browser", summary="打开店铺浏览器")
async def 打开店铺浏览器(shop_id: str) -> 统一响应:
    """
    打开指定店铺的浏览器

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 包含浏览器实例信息
    """
    try:
        # 检查店铺是否存在
        店铺 = await 店铺服务实例.根据ID获取(shop_id)
        if not 店铺:
            return 失败("店铺不存在")

        # 打开浏览器
        实例信息 = await 浏览器服务.打开店铺浏览器(shop_id, 店铺)

        # 更新数据库中店铺状态为 online
        await 店铺服务实例.更新(shop_id, {"status": "online"})

        return 成功(data=实例信息, message="浏览器已打开")
    except Exception as e:
        return 失败(f"打开浏览器失败: {str(e)}")


@路由.post("/{shop_id}/close-browser", summary="关闭店铺浏览器")
async def 关闭店铺浏览器(shop_id: str) -> 统一响应:
    """
    关闭指定店铺的浏览器

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 关闭结果
    """
    try:
        # 关闭浏览器
        成功标志 = await 浏览器服务.关闭店铺浏览器(shop_id)
        if not 成功标志:
            return 失败("浏览器未打开或不存在")

        # 更新数据库中店铺状态为 offline
        await 店铺服务实例.更新(shop_id, {"status": "offline"})

        return 成功(message="浏览器已关闭")
    except Exception as e:
        return 失败(f"关闭浏览器失败: {str(e)}")


@路由.post("/{shop_id}/test-email", summary="测试店铺邮箱连接")
async def 测试店铺邮箱连接(shop_id: str) -> 统一响应:
    """
    测试店铺的邮箱连接

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 测试结果
    """
    try:
        结果 = await 邮箱服务实例.测试店铺邮箱连接(shop_id)
        if 结果["success"]:
            return 成功(message=结果["message"])
        else:
            return 失败(结果["message"])
    except Exception as e:
        return 失败(f"测试邮箱连接失败: {str(e)}")


@路由.post("/{shop_id}/read-captcha", summary="读取店铺邮箱验证码")
async def 读取店铺邮箱验证码(shop_id: str) -> 统一响应:
    """
    读取店铺邮箱的验证码

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 包含验证码或未找到提示
    """
    try:
        验证码 = await 邮箱服务实例.读取店铺验证码(shop_id)
        if 验证码:
            return 成功(data={"captcha": 验证码}, message="验证码读取成功")
        else:
            return 失败("未找到验证码")
    except Exception as e:
        return 失败(f"读取验证码失败: {str(e)}")


@路由.post("/{shop_id}/check-status", summary="检查店铺登录状态")
async def 检查店铺登录状态(shop_id: str) -> 统一响应:
    """
    静默检查店铺的登录状态（headless 模式）

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 检查结果
    """
    try:
        from backend.services import 浏览器服务
        from pages.登录页 import 登录页

        # 检查店铺是否存在
        店铺 = await 店铺服务实例.根据ID获取(shop_id)
        if not 店铺:
            return 失败("店铺不存在")

        print(f"检查店铺状态: {shop_id}")

        # 自动初始化并打开浏览器（headless 模式）
        浏览器实例 = await 浏览器服务.打开店铺浏览器(shop_id, 店铺, headless=True)
        页面 = 浏览器实例["page"]

        # 使用登录页的方法检查状态
        登录 = 登录页(页面)

        try:
            # 访问首页
            await 登录.访问首页()
            当前URL = 页面.url

            # 检查是否被重定向到登录页
            if "login" in 当前URL:
                # 被重定向，说明未登录
                await 店铺服务实例.更新(shop_id, {"status": "offline"})
                状态 = "offline"
                消息 = "未登录"
            else:
                # 没有重定向，说明已登录
                await 店铺服务实例.更新(shop_id, {"status": "online"})
                状态 = "online"
                消息 = "在线"
        finally:
            # 关闭 headless 浏览器（忽略 KeyError）
            try:
                await 浏览器服务.关闭店铺浏览器(shop_id)
            except Exception as e:
                print(f"⚠ 关闭浏览器时出错（已忽略）: {e}")

        return 成功(data={"status": 状态}, message=消息)
    except Exception as e:
        print(f"检查店铺状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 失败(f"检查状态失败: {str(e)}")


@路由.post("/{shop_id}/open", summary="打开店铺浏览器并自动登录")
async def 打开店铺浏览器并登录(shop_id: str) -> 统一响应:
    """
    打开店铺浏览器并自动登录到抖店首页

    逻辑：
    1. 自动初始化浏览器（非 headless）
    2. 触发登录任务
    3. 登录任务会自动加载 Cookie、访问首页、如果需要则登录
    4. 完成后浏览器窗口保持打开给用户操作

    参数:
        shop_id: 店铺 ID

    返回:
        统一响应: 操作结果
    """
    try:
        from backend.services.任务服务 import 任务服务实例

        # 检查店铺是否存在
        店铺 = await 店铺服务实例.根据ID获取(shop_id)
        if not 店铺:
            return 失败("店铺不存在")

        # 触发登录任务（任务服务会自动初始化浏览器）
        任务 = await 任务服务实例.触发任务(
            shop_id=shop_id,
            task_name="登录",
            params={}
        )

        return 成功(data=任务, message="登录任务已启动")
    except Exception as e:
        print(f"打开店铺浏览器失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 失败(f"打开浏览器失败: {str(e)}")
