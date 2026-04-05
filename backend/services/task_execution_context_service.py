"""
任务执行上下文服务模块

负责浏览器初始化、页面获取与店铺执行配置构建。
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional

from backend.logging_config import get_logger


logger = get_logger()


class 任务执行上下文服务:
    """为任务执行准备浏览器页面与店铺配置。"""

    def __init__(
        self,
        *,
        浏览器初始化超时秒: int,
        打开浏览器超时秒: int,
        标准化流程参数ID列表: Callable[[Any], List[int]],
    ) -> None:
        self._浏览器初始化超时秒 = 浏览器初始化超时秒
        self._打开浏览器超时秒 = 打开浏览器超时秒
        self._标准化流程参数ID列表 = 标准化流程参数ID列表

    @staticmethod
    def 页面已关闭(页面: Any) -> bool:
        """兼容真实 Page 与测试替身，判断页面是否关闭。"""
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

    async def 确保页面可用(self, 管理器实例: Any, shop_id: str):
        """确保任务执行前拿到一个可用页面。"""
        页面 = None
        try:
            if hasattr(管理器实例, "安全获取页面"):
                页面 = await 管理器实例.安全获取页面(shop_id)
            else:
                页面 = 管理器实例.获取页面(shop_id)
        except RuntimeError as 异常:
            if "所有页面已关闭" not in str(异常) and "需要恢复" not in str(异常):
                raise

        if 页面 is not None and not self.页面已关闭(页面):
            return 页面

        if shop_id not in 管理器实例.实例集:
            raise RuntimeError(f"店铺 {shop_id} 未启动，请先调用 打开店铺() 方法")

        实例 = 管理器实例.实例集[shop_id]
        浏览器上下文 = 实例["浏览器"]
        现有页面 = [
            当前页面
            for 当前页面 in getattr(浏览器上下文, "pages", [])
            if not self.页面已关闭(当前页面)
        ]

        if 现有页面:
            页面 = 现有页面[0]
        else:
            页面 = await 浏览器上下文.new_page()

        实例["页面"] = 页面
        实例["page"] = 页面
        logger.info(f"[任务服务] 页面已刷新: {页面}")
        return 页面

    async def 准备执行上下文(
        self,
        *,
        shop_id: str,
        params: Optional[Dict[str, Any]],
        展示店铺名: str,
        确保页面可用: Callable[[Any, str], Awaitable[Any]],
    ) -> Dict[str, Any]:
        """准备浏览器、页面与店铺执行配置。"""
        from backend.services import browser_service as 浏览器服务模块

        try:
            await asyncio.wait_for(
                浏览器服务模块.确保已初始化(),
                timeout=self._浏览器初始化超时秒,
            )
        except asyncio.TimeoutError as e:
            raise TimeoutError(f"浏览器初始化超时（{self._浏览器初始化超时秒}秒）") from e
        except Exception as e:
            raise RuntimeError(f"浏览器初始化失败: {e}") from e

        管理器实例 = 浏览器服务模块.获取当前管理器实例()
        if 管理器实例 is None:
            raise RuntimeError("浏览器初始化失败: 管理器实例为空")

        logger.info(f"[任务服务] 浏览器管理器实例: {管理器实例}")

        if shop_id not in 管理器实例.实例集:
            logger.info("[任务服务] 店铺浏览器未打开，开始自动初始化...")
            from backend.services.shop_service import 店铺服务实例
            from backend.services.browser_service import 打开店铺浏览器

            店铺 = await 店铺服务实例.根据ID获取(shop_id)
            if not 店铺:
                raise Exception(f"店铺不存在: {shop_id}")

            店铺配置 = {
                "name": 店铺.get("name"),
                "proxy": 店铺.get("proxy"),
            }
            try:
                await asyncio.wait_for(
                    打开店铺浏览器(shop_id, 店铺配置),
                    timeout=self._打开浏览器超时秒,
                )
            except asyncio.TimeoutError as e:
                raise TimeoutError(f"打开店铺浏览器超时（{self._打开浏览器超时秒}秒）") from e
            except Exception as e:
                raise RuntimeError(f"打开店铺浏览器失败: {e}") from e

            管理器实例 = 浏览器服务模块.获取当前管理器实例()
            if 管理器实例 is None:
                raise RuntimeError("浏览器打开失败: 管理器实例为空")
            logger.info("[任务服务] 浏览器已自动打开")
        else:
            logger.info("[任务服务] 店铺浏览器已打开，复用现有实例")

        页面 = await 确保页面可用(管理器实例, shop_id)
        if 页面 is None:
            raise RuntimeError("浏览器页面获取失败: 页面对象为空")
        logger.info(f"[任务服务] 获取到页面对象: {页面}")

        from backend.services.shop_service import 店铺服务实例

        店铺完整信息 = await 店铺服务实例.根据ID获取完整信息(shop_id)
        if not 店铺完整信息:
            raise Exception(f"店铺不存在: {shop_id}")

        展示店铺名 = str(店铺完整信息.get("name") or 展示店铺名)
        logger.info(f"[任务服务] 获取到店铺完整信息，用户名: {店铺完整信息.get('username')}")

        店铺配置 = {
            "shop_id": shop_id,
            "username": 店铺完整信息.get("username"),
            "password": 店铺完整信息.get("password"),
        }

        if not 店铺配置.get("username"):
            raise Exception("店铺用户名为空，请先在店铺管理中设置用户名")
        if not 店铺配置.get("password"):
            raise Exception("店铺密码为空，请先在店铺管理中设置密码")

        logger.info(f"[任务服务] 店铺配置验证通过，密码长度: {len(店铺配置.get('password', ''))}")

        if 店铺完整信息.get("smtp_host"):
            店铺配置["smtp_host"] = 店铺完整信息.get("smtp_host")
        if 店铺完整信息.get("smtp_port"):
            店铺配置["smtp_port"] = 店铺完整信息.get("smtp_port")
        if 店铺完整信息.get("smtp_user"):
            店铺配置["smtp_user"] = 店铺完整信息.get("smtp_user")
        if 店铺完整信息.get("smtp_pass"):
            店铺配置["smtp_pass"] = 店铺完整信息.get("smtp_pass")
        if 店铺完整信息.get("smtp_protocol"):
            店铺配置["smtp_protocol"] = 店铺完整信息.get("smtp_protocol")

        if isinstance(params, dict):
            if params.get("batch_id") is not None:
                店铺配置["batch_id"] = params.get("batch_id")
            if params.get("step_index") is not None:
                店铺配置["step_index"] = params.get("step_index")
            if params.get("total_steps") is not None:
                店铺配置["total_steps"] = params.get("total_steps")
            if params.get("on_fail") is not None:
                店铺配置["on_fail"] = params.get("on_fail")
            if params.get("flow_param_ids") is not None:
                店铺配置["flow_param_ids"] = self._标准化流程参数ID列表(params.get("flow_param_ids"))
            if params.get("merge") is not None:
                店铺配置["merge"] = bool(params.get("merge"))
            if isinstance(params.get("flow_context"), dict):
                店铺配置["flow_context"] = dict(params.get("flow_context") or {})

        return {
            "页面": 页面,
            "店铺配置": 店铺配置,
            "展示店铺名": 展示店铺名,
        }
