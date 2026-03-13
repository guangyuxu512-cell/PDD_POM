"""
任务服务模块

封装任务日志的 CRUD 和任务触发逻辑。
"""
import json
import uuid
import asyncio
import aiosqlite
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from backend.配置 import 配置实例
from backend.models.数据库 import 获取连接
from backend.services.任务参数服务 import 任务参数服务实例

浏览器初始化超时秒 = 60
打开浏览器超时秒 = 120
任务执行超时秒 = 1800
任务参数任务集合 = {"发布相似商品", "发布换图商品", "限时限量"}


class 任务服务:
    """任务业务服务类"""

    def __init__(self):
        """初始化任务服务"""
        self._数据库路径 = Path(配置实例.DATA_DIR) / "ecom.db"

    @staticmethod
    def _页面已关闭(页面: Any) -> bool:
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

    async def _确保页面可用(self, 管理器实例: Any, shop_id: str):
        """确保任务执行前拿到一个可用页面。"""
        页面 = None
        try:
            页面 = 管理器实例.获取页面(shop_id)
        except RuntimeError as 异常:
            if "所有页面已关闭" not in str(异常):
                raise

        if 页面 is not None and not self._页面已关闭(页面):
            return 页面

        if shop_id not in 管理器实例.实例集:
            raise RuntimeError(f"店铺 {shop_id} 未启动，请先调用 打开店铺() 方法")

        实例 = 管理器实例.实例集[shop_id]
        浏览器上下文 = 实例["浏览器"]
        现有页面 = [
            当前页面
            for 当前页面 in getattr(浏览器上下文, "pages", [])
            if not self._页面已关闭(当前页面)
        ]

        if 现有页面:
            页面 = 现有页面[0]
        else:
            页面 = await 浏览器上下文.new_page()

        实例["页面"] = 页面
        实例["page"] = 页面
        print(f"[任务服务] 页面已刷新: {页面}")
        return 页面

    async def _获取待执行任务参数记录(
        self,
        shop_id: str,
        task_name: str,
    ) -> Optional[Dict[str, Any]]:
        """为依赖 task_params 的任务取一条待执行记录。"""
        if task_name not in 任务参数任务集合:
            return None

        待执行列表 = await 任务参数服务实例.获取待执行列表(shop_id, task_name)
        if not 待执行列表:
            return None
        return 待执行列表[0]

    async def _准备任务参数(
        self,
        shop_id: str,
        task_name: str,
        店铺配置: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """读取 task_params 并注入到店铺配置。"""
        if task_name not in 任务参数任务集合:
            return None

        任务参数记录 = await self._获取待执行任务参数记录(shop_id, task_name)
        if not 任务参数记录:
            from browser.任务回调 import 上报

            await 上报("没有待执行的任务参数", shop_id)
            return None

        任务参数 = dict(任务参数记录.get("params") or {})
        任务参数["task_param_id"] = 任务参数记录["id"]
        店铺配置["task_param"] = 任务参数

        await 任务参数服务实例.更新执行结果(
            任务参数记录["id"],
            "running",
            结果=任务参数记录.get("result") or {},
            错误信息=None,
        )
        return 任务参数记录

    async def _回填任务参数执行结果(
        self,
        任务参数记录: Optional[Dict[str, Any]],
        状态: str,
        结果: Optional[Dict[str, Any]] = None,
        错误信息: Optional[str] = None,
    ) -> None:
        """按执行结果回填 task_params 记录。"""
        if not 任务参数记录:
            return

        await 任务参数服务实例.更新执行结果(
            任务参数记录["id"],
            状态,
            结果=结果 or {},
            错误信息=错误信息,
        )

    async def 获取任务列表(
        self,
        shop_id: Optional[str] = None,
        status: Optional[str] = None,
        task_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取任务列表（分页 + 筛选）

        参数:
            shop_id: 店铺 ID（可选）
            status: 任务状态（可选）
            task_name: 任务名称（可选）
            page: 页码（从 1 开始）
            page_size: 每页大小

        返回:
            Dict[str, Any]: 分页数据 { "list": [...], "total": N, "page": P, "page_size": S }
        """
        # 构建 WHERE 子句
        where_条件 = []
        where_参数 = []

        if shop_id:
            where_条件.append("shop_id = ?")
            where_参数.append(shop_id)

        if status:
            where_条件.append("status = ?")
            where_参数.append(status)

        if task_name:
            where_条件.append("task_name = ?")
            where_参数.append(task_name)

        where_子句 = " WHERE " + " AND ".join(where_条件) if where_条件 else ""

        # 查询总数
        async with 获取连接() as db:
            db.row_factory = aiosqlite.Row

            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM task_logs{where_子句}"
            async with db.execute(count_sql, where_参数) as cursor:
                row = await cursor.fetchone()
                总数 = row["total"]

            # 查询分页数据
            offset = (page - 1) * page_size
            list_sql = f"""
                SELECT * FROM task_logs{where_子句}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            async with db.execute(list_sql, where_参数 + [page_size, offset]) as cursor:
                rows = await cursor.fetchall()
                任务列表 = [dict(row) for row in rows]

        return {
            "list": 任务列表,
            "total": 总数,
            "page": page,
            "page_size": page_size
        }

    async def 获取任务详情(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务详情

        参数:
            task_id: 任务 ID

        返回:
            Optional[Dict[str, Any]]: 任务详情，不存在返回 None
        """
        async with 获取连接() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM task_logs WHERE task_id = ?",
                (task_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def 创建任务记录(
        self,
        shop_id: str,
        task_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建任务记录

        参数:
            shop_id: 店铺 ID
            task_name: 任务名称
            params: 任务参数（可选）

        返回:
            Dict[str, Any]: 新建任务记录
        """
        task_id = uuid.uuid4().hex
        当前时间 = datetime.now().isoformat()
        params_json = json.dumps(params, ensure_ascii=False) if params else None

        async with 获取连接() as db:
            await db.execute(
                """
                INSERT INTO task_logs (
                    task_id, shop_id, task_name, status, params,
                    started_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, shop_id, task_name, "pending", params_json, 当前时间, 当前时间)
            )
            await db.commit()

        return {
            "task_id": task_id,
            "shop_id": shop_id,
            "task_name": task_name,
            "status": "pending",
            "params": params_json,
            "started_at": 当前时间,
            "created_at": 当前时间
        }

    async def 触发任务(
        self,
        shop_id: str,
        task_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        触发任务

        参数:
            shop_id: 店铺 ID
            task_name: 任务名称
            params: 任务参数（可选）

        返回:
            Dict[str, Any]: 任务信息
        """
        任务记录 = await self.创建任务记录(shop_id=shop_id, task_name=task_name, params=params)

        # 后台异步执行任务（不阻塞 API 返回）
        asyncio.create_task(
            self.统一执行任务(
                task_id=任务记录["task_id"],
                shop_id=shop_id,
                task_name=task_name,
                params=params,
                来源="http"
            )
        )

        return 任务记录

    async def _后台执行任务(
        self,
        task_id: str,
        shop_id: str,
        task_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        后台执行任务

        参数:
            task_id: 任务 ID
            shop_id: 店铺 ID
            task_name: 任务名称
            params: 任务参数（可选）
        """
        await self.统一执行任务(
            task_id=task_id,
            shop_id=shop_id,
            task_name=task_name,
            params=params,
            来源="http"
        )

    async def 统一执行任务(
        self,
        task_id: str,
        shop_id: str,
        task_name: str,
        params: Optional[Dict[str, Any]] = None,
        来源: str = "http"
    ) -> Dict[str, Any]:
        """
        统一执行任务链路

        参数:
            task_id: 任务 ID
            shop_id: 店铺 ID
            task_name: 任务名称
            params: 任务参数（可选）
            来源: 触发来源，仅用于日志记录

        返回:
            Dict[str, Any]: 执行结果
        """
        展示店铺名 = shop_id
        if isinstance(params, dict):
            展示店铺名 = str(params.get("shop_name") or shop_id)

        try:
            print(
                f"[任务服务] 开始执行任务: 来源={来源}, task_id={task_id}, "
                f"shop_name={展示店铺名}, shop_id={shop_id}, task_name={task_name}"
            )

            # 如果是登录任务，更新店铺状态为 logging_in
            if task_name == "登录":
                from backend.services.店铺服务 import 店铺服务实例
                await 店铺服务实例.更新(shop_id, {"status": "logging_in"})
                print(f"[任务服务] 店铺状态已更新为 logging_in")

            # 更新状态为 running
            await self.更新任务状态(task_id, "running")
            print(f"[任务服务] 任务状态已更新为 running")

            # 获取浏览器页面
            from backend.services import 浏览器服务 as 浏览器服务模块

            # 中文注释：浏览器初始化依赖 Playwright，必须加超时和异常包装，避免任务一直卡在启动阶段。
            try:
                await asyncio.wait_for(
                    浏览器服务模块.确保已初始化(),
                    timeout=浏览器初始化超时秒
                )
            except asyncio.TimeoutError as e:
                raise TimeoutError(f"浏览器初始化超时（{浏览器初始化超时秒}秒）") from e
            except Exception as e:
                raise RuntimeError(f"浏览器初始化失败: {e}") from e

            管理器实例 = 浏览器服务模块.获取当前管理器实例()
            if 管理器实例 is None:
                raise RuntimeError("浏览器初始化失败: 管理器实例为空")

            print(f"[任务服务] 浏览器管理器实例: {管理器实例}")

            # 检查店铺浏览器是否已打开
            if shop_id not in 管理器实例.实例集:
                print(f"[任务服务] 店铺浏览器未打开，开始自动初始化...")
                # 自动初始化浏览器
                from backend.services.店铺服务 import 店铺服务实例
                店铺 = await 店铺服务实例.根据ID获取(shop_id)
                if not 店铺:
                    raise Exception(f"店铺不存在: {shop_id}")

                # 打开浏览器
                from backend.services.浏览器服务 import 打开店铺浏览器
                店铺配置 = {
                    "name": 店铺.get("name"),
                    "proxy": 店铺.get("proxy")
                }
                # 中文注释：打开浏览器属于外部 IO，这里单独加超时兜底，避免任务长时间挂起。
                try:
                    await asyncio.wait_for(
                        打开店铺浏览器(shop_id, 店铺配置),
                        timeout=打开浏览器超时秒
                    )
                except asyncio.TimeoutError as e:
                    raise TimeoutError(f"打开店铺浏览器超时（{打开浏览器超时秒}秒）") from e
                except Exception as e:
                    raise RuntimeError(f"打开店铺浏览器失败: {e}") from e

                管理器实例 = 浏览器服务模块.获取当前管理器实例()
                if 管理器实例 is None:
                    raise RuntimeError("浏览器打开失败: 管理器实例为空")
                print(f"[任务服务] 浏览器已自动打开")
            else:
                print(f"[任务服务] 店铺浏览器已打开，复用现有实例")

            # 获取页面
            页面 = await self._确保页面可用(管理器实例, shop_id)
            if 页面 is None:
                raise RuntimeError("浏览器页面获取失败: 页面对象为空")
            print(f"[任务服务] 获取到页面对象: {页面}")

            # 获取店铺配置（包含解密后的密码）
            from backend.services.店铺服务 import 店铺服务实例

            店铺完整信息 = await 店铺服务实例.根据ID获取完整信息(shop_id)
            if not 店铺完整信息:
                raise Exception(f"店铺不存在: {shop_id}")
            展示店铺名 = str(店铺完整信息.get("name") or 展示店铺名)

            print(f"[任务服务] 获取到店铺完整信息，用户名: {店铺完整信息.get('username')}")

            # 构建店铺配置
            店铺配置 = {
                "shop_id": shop_id,  # 添加 shop_id 用于 Cookie 文件命名
                "username": 店铺完整信息.get("username"),
                "password": 店铺完整信息.get("password")
            }

            # 边界检查：密码不能为空
            if not 店铺配置.get("username"):
                raise Exception("店铺用户名为空，请先在店铺管理中设置用户名")

            if not 店铺配置.get("password"):
                raise Exception("店铺密码为空，请先在店铺管理中设置密码")

            print(f"[任务服务] 店铺配置验证通过，密码长度: {len(店铺配置.get('password', ''))}")

            # 添加邮箱配置（用于邮箱验证码功能）
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

            print(f"[任务服务] 开始执行任务...")
            # 中文注释：任务执行过程可能包含页面交互和网络等待，设置超时可避免任务永久占用 Worker。
            try:
                执行结果 = await asyncio.wait_for(
                    self.执行任务(
                        shop_id=shop_id,
                        task_name=task_name,
                        页面=页面,
                        店铺配置=店铺配置
                    ),
                    timeout=任务执行超时秒
                )
            except asyncio.TimeoutError as e:
                raise TimeoutError(f"任务执行超时（{任务执行超时秒}秒）") from e

            结果 = 执行结果["result"]
            print(f"[任务服务] 任务执行完成，结果: {结果}")

            # 更新任务状态为 completed
            await self.更新任务状态(task_id, "completed", result=str(结果))
            print(f"[任务服务] 任务状态已更新为 completed")

            # 如果是登录任务，根据结果更新店铺状态
            if task_name == "登录":
                from backend.services.店铺服务 import 店铺服务实例
                if 结果 == "成功":
                    await 店铺服务实例.更新(shop_id, {"status": "online"})
                    print(f"[任务服务] 登录成功，店铺状态已更新为 online")
                else:
                    await 店铺服务实例.更新(shop_id, {"status": "offline"})
                    print(f"[任务服务] 登录失败，店铺状态已更新为 offline")

            return {
                "task_id": task_id,
                "shop_id": shop_id,
                "shop_name": 展示店铺名,
                "task_name": task_name,
                "status": "completed",
                "result": str(结果),
                "error": None
            }

        except Exception as e:
            print(f"[任务服务] 任务执行失败: shop_name={展示店铺名}, shop_id={shop_id}, error={e}")
            import traceback
            traceback.print_exc()

            # 更新任务状态为 failed
            await self.更新任务状态(task_id, "failed", error=str(e))

            # 如果是登录任务，更新店铺状态为 offline
            if task_name == "登录":
                from backend.services.店铺服务 import 店铺服务实例
                await 店铺服务实例.更新(shop_id, {"status": "offline"})
                print(f"[任务服务] 登录异常，店铺状态已更新为 offline")

            return {
                "task_id": task_id,
                "shop_id": shop_id,
                "shop_name": 展示店铺名,
                "task_name": task_name,
                "status": "failed",
                "result": None,
                "error": str(e)
            }

    async def 取消任务(self, task_id: str) -> bool:
        """
        取消任务（仅限 pending 状态）

        参数:
            task_id: 任务 ID

        返回:
            bool: 是否取消成功
        """
        # 查询任务状态
        任务 = await self.获取任务详情(task_id)
        if not 任务:
            return False

        # 只能取消 pending 状态的任务
        if 任务["status"] != "pending":
            return False

        # TODO: 集成 Celery revoke 逻辑（Phase 7）
        # 示例代码：
        # from tasks.celery应用 import celery应用
        # celery应用.control.revoke(task_id, terminate=True)

        # 更新状态为 cancelled
        async with 获取连接() as db:
            await db.execute(
                """
                UPDATE task_logs
                SET status = ?, finished_at = ?
                WHERE task_id = ?
                """,
                ("cancelled", datetime.now().isoformat(), task_id)
            )
            await db.commit()

        return True

    async def 删除任务(self, task_id: str) -> bool:
        """
        删除任务记录

        参数:
            task_id: 任务 ID

        返回:
            bool: 是否删除成功
        """
        # 查询任务是否存在
        任务 = await self.获取任务详情(task_id)
        if not 任务:
            return False

        # 删除任务记录
        async with 获取连接() as db:
            await db.execute(
                "DELETE FROM task_logs WHERE task_id = ?",
                (task_id,)
            )
            await db.commit()

        return True

    async def 清空历史记录(self) -> int:
        """
        删除所有已完成和已失败的任务记录

        返回:
            int: 删除的记录数量
        """
        async with 获取连接() as db:
            # 查询要删除的记录数量
            async with db.execute(
                "SELECT COUNT(*) FROM task_logs WHERE status IN ('completed', 'failed', 'cancelled')"
            ) as cursor:
                result = await cursor.fetchone()
                删除数量 = result[0] if result else 0

            # 删除记录
            await db.execute(
                "DELETE FROM task_logs WHERE status IN ('completed', 'failed', 'cancelled')"
            )
            await db.commit()

        return 删除数量

    async def 更新任务状态(
        self,
        task_id: str,
        status: str,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        更新任务状态（供回调装饰器内部调用）

        参数:
            task_id: 任务 ID
            status: 任务状态
            result: 执行结果（可选）
            error: 错误信息（可选）

        返回:
            bool: 是否更新成功
        """
        # 构建更新字段
        更新字段 = ["status = ?"]
        更新参数 = [status]

        if result is not None:
            更新字段.append("result = ?")
            更新参数.append(result)

        if error is not None:
            更新字段.append("error = ?")
            更新参数.append(error)

        # 如果是完成或失败状态，更新 finished_at
        if status in ("completed", "failed", "cancelled"):
            更新字段.append("finished_at = ?")
            更新参数.append(datetime.now().isoformat())

        # 执行更新
        async with 获取连接() as db:
            cursor = await db.execute(
                f"""
                UPDATE task_logs
                SET {", ".join(更新字段)}
                WHERE task_id = ?
                """,
                更新参数 + [task_id]
            )
            await db.commit()
            return cursor.rowcount > 0

    async def 执行任务(
        self,
        shop_id: str,
        task_name: str,
        页面,
        店铺配置: dict
    ) -> Dict[str, Any]:
        """
        执行已注册任务

        参数:
            shop_id: 店铺 ID
            task_name: 任务名称
            页面: Playwright page 对象
            店铺配置: 店铺配置字典

        返回:
            Dict[str, Any]: 执行结果
        """
        from tasks.任务注册表 import 获取任务

        任务参数记录 = await self._准备任务参数(shop_id, task_name, 店铺配置)
        if task_name in 任务参数任务集合 and not 任务参数记录:
            return {
                "task_name": task_name,
                "shop_id": shop_id,
                "result": "跳过",
            }

        # 获取任务实例
        任务实例 = 获取任务(task_name)

        try:
            # 执行任务
            结果 = await 任务实例.执行(页面, 店铺配置)
        except Exception as e:
            await self._回填任务参数执行结果(
                任务参数记录,
                "failed",
                结果=getattr(任务实例, "_执行结果", {}) or {},
                错误信息=str(e),
            )
            raise

        执行结果数据 = getattr(任务实例, "_执行结果", {}) or {}
        if 任务参数记录:
            if 结果 == "成功":
                await self._回填任务参数执行结果(
                    任务参数记录,
                    "success",
                    结果=执行结果数据,
                )
                if task_name == "发布相似商品":
                    批次ID = str(任务参数记录.get("batch_id") or "").strip()
                    if 批次ID:
                        try:
                            await 任务参数服务实例.批次完成后创建后续任务(批次ID)
                        except Exception as e:
                            print(f"[任务服务] 自动创建后续任务失败（忽略）: {e}")
            elif 结果 != "跳过":
                await self._回填任务参数执行结果(
                    任务参数记录,
                    "failed",
                    结果=执行结果数据,
                    错误信息=str(结果 or "任务执行失败"),
                )

        return {
            "task_name": task_name,
            "shop_id": shop_id,
            "result": 结果
        }


# 创建单例
任务服务实例 = 任务服务()
