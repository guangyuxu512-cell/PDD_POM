"""
系统服务模块

封装系统配置的读取、更新和健康检查。
"""
import re
import shutil
from typing import Dict, Any
from pathlib import Path

from backend.配置 import 配置实例
from backend.models.数据库 import 获取连接


class 系统服务:
    """系统配置管理服务"""

    # 允许更新的配置白名单
    _配置白名单 = {
        "redis_url": "REDIS_URL",
        "captcha_provider": "CAPTCHA_PROVIDER",
        "captcha_api_key": "CAPTCHA_API_KEY",
        "default_proxy": "DEFAULT_PROXY",
        "max_browser_instances": "MAX_BROWSER_INSTANCES",
        "chrome_path": "CHROME_PATH",
        "log_level": "LOG_LEVEL",
    }

    def __init__(self):
        """初始化系统服务"""
        self._env文件路径 = Path(".env")
        self._数据库路径 = Path(配置实例.DATA_DIR) / "ecom.db"

    def _脱敏redis_url(self, url: str) -> str:
        """
        脱敏 Redis URL 中的密码

        参数:
            url: Redis URL

        返回:
            str: 脱敏后的 URL
        """
        # 匹配 redis://:password@host 或 redis://user:password@host
        # 将密码部分替换为 ***
        pattern = r"(redis://[^:]*:)([^@]+)(@)"
        return re.sub(pattern, r"\1***\3", url)

    def _脱敏api_key(self, key: str) -> str:
        """
        脱敏 API Key，只显示前4位

        参数:
            key: API Key

        返回:
            str: 脱敏后的 Key
        """
        if not key or len(key) <= 4:
            return "***"
        return key[:4] + "***"

    async def 获取配置(self) -> Dict[str, Any]:
        """
        读取当前系统配置

        返回:
            Dict[str, Any]: 系统配置（脱敏后）
        """
        配置 = {
            "redis_url": self._脱敏redis_url(配置实例.REDIS_URL),
            "captcha_provider": 配置实例.CAPTCHA_PROVIDER,
            "captcha_api_key": self._脱敏api_key(配置实例.CAPTCHA_API_KEY) if 配置实例.CAPTCHA_API_KEY else None,
            "default_proxy": 配置实例.DEFAULT_PROXY,
            "max_browser_instances": 配置实例.MAX_BROWSER_INSTANCES,
            "chrome_path": 配置实例.CHROME_PATH,
            "log_level": 配置实例.LOG_LEVEL,
        }
        return 配置

    async def 更新配置(self, 新配置: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新系统配置

        参数:
            新配置: 新的配置项（前端字段名）

        返回:
            Dict[str, Any]: 更新后的配置

        异常:
            ValueError: 如果包含不允许更新的字段
        """
        # 转换为后端字段名，并检查白名单
        更新项 = {}
        for 前端字段, 值 in 新配置.items():
            if 前端字段 not in self._配置白名单:
                raise ValueError(f"不允许更新字段: {前端字段}")
            后端字段 = self._配置白名单[前端字段]
            更新项[后端字段] = 值

        # 读取 .env 文件
        if self._env文件路径.exists():
            行列表 = self._env文件路径.read_text(encoding="utf-8").splitlines()
        else:
            行列表 = []

        # 更新现有行
        已更新的键 = set()
        新行列表 = []
        for 行 in 行列表:
            行 = 行.rstrip()
            # 跳过注释和空行
            if not 行 or 行.startswith("#"):
                新行列表.append(行)
                continue

            # 匹配 KEY=VALUE
            匹配 = re.match(r"^([A-Z_]+)=(.*)$", 行)
            if 匹配:
                键 = 匹配.group(1)
                if 键 in 更新项:
                    # 更新这一行
                    新行列表.append(f"{键}={更新项[键]}")
                    已更新的键.add(键)
                else:
                    # 保留原样
                    新行列表.append(行)
            else:
                # 保留原样
                新行列表.append(行)

        # 追加新的键
        for 键, 值 in 更新项.items():
            if 键 not in 已更新的键:
                新行列表.append(f"{键}={值}")

        # 写回 .env 文件
        self._env文件路径.write_text("\n".join(新行列表) + "\n", encoding="utf-8")

        # 更新运行时配置
        for 键, 值 in 更新项.items():
            # 类型转换
            if 键 == "MAX_BROWSER_INSTANCES":
                值 = int(值)
            setattr(配置实例, 键, 值)

        # 返回更新后的配置
        return await self.获取配置()

    async def 健康检查(self) -> Dict[str, Any]:
        """
        健康检查

        返回:
            Dict[str, Any]: 系统健康状态
        """
        组件状态 = {}

        # 检查数据库
        try:
            async with 获取连接() as db:
                await db.execute("SELECT 1")
            组件状态["database"] = "ok"
        except Exception:
            组件状态["database"] = "error"

        # 检查浏览器实例
        try:
            from backend.services.浏览器服务 import 浏览器服务实例
            实例数 = len(浏览器服务实例._实例状态)
            组件状态["browser"] = {
                "count": 实例数,
                "status": "ok"
            }
        except Exception:
            组件状态["browser"] = {
                "count": 0,
                "status": "error"
            }

        # 检查磁盘空间
        try:
            数据目录 = Path(配置实例.DATA_DIR)
            if not 数据目录.exists():
                数据目录.mkdir(parents=True, exist_ok=True)
            磁盘使用 = shutil.disk_usage(数据目录)
            剩余空间_gb = 磁盘使用.free / (1024 ** 3)
            组件状态["disk"] = {
                "free_gb": round(剩余空间_gb, 2),
                "status": "ok" if 剩余空间_gb > 1 else "warning"
            }
        except Exception:
            组件状态["disk"] = {
                "free_gb": 0,
                "status": "error"
            }

        # 判断整体状态
        错误数 = sum(1 for v in 组件状态.values() if
                     (isinstance(v, str) and v == "error") or
                     (isinstance(v, dict) and v.get("status") == "error"))

        if 错误数 == 0:
            整体状态 = "healthy"
        elif 错误数 == len(组件状态):
            整体状态 = "unhealthy"
        else:
            整体状态 = "degraded"

        return {
            "status": 整体状态,
            "components": 组件状态
        }


# 创建单例
系统服务实例 = 系统服务()
