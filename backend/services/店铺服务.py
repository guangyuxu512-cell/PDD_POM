"""
店铺服务模块

提供店铺 CRUD 和 Cookie 管理的业务逻辑。
"""
import json
import uuid
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from cryptography.fernet import Fernet
import base64

from backend.models.数据库 import 获取连接
from backend.配置 import 配置实例


class 店铺服务:
    """店铺业务服务类"""

    def __init__(self):
        """初始化店铺服务"""

    def _获取密钥文件路径(self) -> Path:
        """在未显式配置 ENCRYPTION_KEY 时，使用持久化密钥文件保证重启后可解密。"""
        return Path(配置实例.DATA_DIR) / ".encryption.key"

    def _标准化密钥(self, 原始密钥: str | bytes, *, 来源: str) -> bytes:
        """将环境变量或文件中的密钥标准化为 Fernet 可接受的格式。"""
        密钥 = 原始密钥.encode() if isinstance(原始密钥, str) else 原始密钥
        if not 密钥:
            raise ValueError(f"{来源} 不能为空")

        if len(密钥) != 44:
            密钥 = base64.urlsafe_b64encode(密钥[:32].ljust(32, b"0"))

        try:
            Fernet(密钥)
        except Exception as 异常:
            raise ValueError(f"{来源} 格式无效") from 异常

        return 密钥

    def _获取或创建密钥(self) -> bytes:
        """优先使用显式配置，否则回退到数据目录下的持久化密钥文件。"""
        if 配置实例.ENCRYPTION_KEY:
            return self._标准化密钥(配置实例.ENCRYPTION_KEY, 来源="ENCRYPTION_KEY")

        密钥文件 = self._获取密钥文件路径()
        密钥文件.parent.mkdir(parents=True, exist_ok=True)

        if 密钥文件.exists():
            return self._标准化密钥(
                密钥文件.read_text(encoding="utf-8").strip(),
                来源=f"密钥文件 {密钥文件}",
            )

        新密钥 = Fernet.generate_key()
        try:
            with 密钥文件.open("xb") as 文件:
                文件.write(新密钥)
        except FileExistsError:
            return self._标准化密钥(
                密钥文件.read_text(encoding="utf-8").strip(),
                来源=f"密钥文件 {密钥文件}",
            )
        return 新密钥

    def _获取加密器(self) -> Fernet:
        """按当前配置即时创建加密器，兼容测试时切换 DATA_DIR。"""
        return Fernet(self._获取或创建密钥())

    def _加密(self, 明文: str) -> str:
        """
        加密字符串

        参数:
            明文: 要加密的字符串

        返回:
            str: 加密后的字符串
        """
        if not 明文:
            return ""
        密文字节 = self._获取加密器().encrypt(明文.encode())
        return 密文字节.decode()

    def _解密(self, 密文: str) -> str:
        """
        解密字符串

        参数:
            密文: 要解密的字符串

        返回:
            str: 解密后的字符串
        """
        if not 密文:
            return ""
        加密器 = self._获取加密器()
        try:
            明文字节 = 加密器.decrypt(密文.encode())
            return 明文字节.decode()
        except Exception:
            return ""

    def _脱敏(self, 店铺数据: Dict[str, Any]) -> Dict[str, Any]:
        """
        脱敏店铺数据（移除敏感字段）

        参数:
            店铺数据: 店铺数据字典

        返回:
            Dict[str, Any]: 脱敏后的店铺数据
        """
        if 店铺数据:
            if 店铺数据.get("password"):
                店铺数据["password"] = "***"
            elif "password" in 店铺数据:
                店铺数据["password"] = None

            if 店铺数据.get("smtp_pass"):
                店铺数据["smtp_pass"] = "***"
            elif "smtp_pass" in 店铺数据:
                店铺数据["smtp_pass"] = None
        return 店铺数据

    async def 获取全部(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        分页获取所有店铺

        参数:
            page: 页码（从 1 开始）
            page_size: 每页大小

        返回:
            Dict[str, Any]: 包含 list, total, page, page_size 的字典
        """
        page = max(page, 1)
        page_size = max(page_size, 1)

        async with 获取连接() as 连接:
            # 查询总数
            async with 连接.execute("SELECT COUNT(*) FROM shops") as 游标:
                结果 = await 游标.fetchone()
                总数 = 结果[0] if 结果 else 0

            # 查询分页数据
            偏移量 = (page - 1) * page_size
            async with 连接.execute(
                "SELECT * FROM shops ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (page_size, 偏移量)
            ) as 游标:
                列名 = [描述[0] for 描述 in 游标.description]
                行列表 = await 游标.fetchall()
                店铺列表 = [dict(zip(列名, 行)) for 行 in 行列表]

            # 脱敏所有店铺数据
            店铺列表 = [self._脱敏(店铺) for 店铺 in 店铺列表]

            return {
                "list": 店铺列表,
                "total": 总数,
                "page": page,
                "page_size": page_size
            }

    async def 根据ID获取(self, 店铺ID: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取店铺

        参数:
            店铺ID: 店铺 ID

        返回:
            Optional[Dict[str, Any]]: 店铺数据，不存在返回 None
        """
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT * FROM shops WHERE id = ?",
                (店铺ID,)
            ) as 游标:
                行 = await 游标.fetchone()
                if not 行:
                    return None
                列名 = [描述[0] for 描述 in 游标.description]
                店铺数据 = dict(zip(列名, 行))
                return self._脱敏(店铺数据)

    async def 根据ID获取完整信息(self, 店铺ID: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取店铺完整信息（包括解密后的密码，供内部使用）

        参数:
            店铺ID: 店铺 ID

        返回:
            Optional[Dict[str, Any]]: 店铺完整数据（包含解密后的密码），不存在返回 None
        """
        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT * FROM shops WHERE id = ?",
                (店铺ID,)
            ) as 游标:
                行 = await 游标.fetchone()
                if not 行:
                    return None
                列名 = [描述[0] for 描述 in 游标.description]
                店铺数据 = dict(zip(列名, 行))

                # 解密密码字段
                if 店铺数据.get("password"):
                    店铺数据["password"] = self._解密(店铺数据["password"])
                if 店铺数据.get("smtp_pass"):
                    店铺数据["smtp_pass"] = self._解密(店铺数据["smtp_pass"])

                return 店铺数据

    async def 创建(self, 数据: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建店铺

        参数:
            数据: 店铺数据

        返回:
            Dict[str, Any]: 创建后的店铺数据
        """
        店铺名称 = str(数据.get("name", "")).strip()
        if not 店铺名称:
            raise ValueError("店铺名称不能为空")

        # 生成 UUID
        店铺ID = str(uuid.uuid4())

        # 创建用户数据目录
        用户目录 = Path(配置实例.DATA_DIR) / "profiles" / 店铺ID
        用户目录.mkdir(parents=True, exist_ok=True)

        # 加密密码字段
        密码 = 数据.get("password")
        if 密码:
            密码 = self._加密(密码)

        邮箱密码 = 数据.get("smtp_pass")
        if 邮箱密码:
            邮箱密码 = self._加密(邮箱密码)

        # 插入数据库
        async with 获取连接() as 连接:
            await 连接.execute(
                """
                INSERT INTO shops (
                    id, name, username, password, proxy, user_agent,
                    profile_dir, cookie_path, status, smtp_host, smtp_port,
                    smtp_user, smtp_pass, smtp_protocol, remark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    店铺ID,
                    店铺名称,
                    数据.get("username"),
                    密码,
                    数据.get("proxy"),
                    数据.get("user_agent"),
                    str(用户目录),
                    None,  # cookie_path 初始为空
                    "offline",  # 初始状态为 offline
                    数据.get("smtp_host"),
                    数据.get("smtp_port", 993),
                    数据.get("smtp_user"),
                    邮箱密码,
                    数据.get("smtp_protocol", "imap"),
                    数据.get("remark")
                )
            )
            await 连接.commit()

        # 返回创建后的店铺（脱敏）
        return await self.根据ID获取(店铺ID)

    async def 更新(self, 店铺ID: str, 数据: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新店铺

        参数:
            店铺ID: 店铺 ID
            数据: 要更新的数据

        返回:
            Optional[Dict[str, Any]]: 更新后的店铺数据，不存在返回 None
        """
        # 检查店铺是否存在
        店铺 = await self.根据ID获取(店铺ID)
        if not 店铺:
            return None

        # 构建更新语句
        更新字段 = []
        更新值 = []

        # 处理各个字段
        if "name" in 数据 and 数据["name"] is not None:
            if not str(数据["name"]).strip():
                raise ValueError("店铺名称不能为空")
            更新字段.append("name = ?")
            更新值.append(str(数据["name"]).strip())

        if "username" in 数据 and 数据["username"] is not None:
            更新字段.append("username = ?")
            更新值.append(数据["username"])

        if "password" in 数据 and 数据["password"] is not None and 数据["password"] != "":
            更新字段.append("password = ?")
            更新值.append(self._加密(数据["password"]))

        if "proxy" in 数据 and 数据["proxy"] is not None:
            更新字段.append("proxy = ?")
            更新值.append(数据["proxy"])

        if "user_agent" in 数据 and 数据["user_agent"] is not None:
            更新字段.append("user_agent = ?")
            更新值.append(数据["user_agent"])

        if "status" in 数据 and 数据["status"] is not None:
            更新字段.append("status = ?")
            更新值.append(数据["status"])

        if "smtp_host" in 数据 and 数据["smtp_host"] is not None:
            更新字段.append("smtp_host = ?")
            更新值.append(数据["smtp_host"])

        if "smtp_port" in 数据 and 数据["smtp_port"] is not None:
            更新字段.append("smtp_port = ?")
            更新值.append(数据["smtp_port"])

        if "smtp_user" in 数据 and 数据["smtp_user"] is not None:
            更新字段.append("smtp_user = ?")
            更新值.append(数据["smtp_user"])

        if "smtp_pass" in 数据 and 数据["smtp_pass"] is not None and 数据["smtp_pass"] != "":
            更新字段.append("smtp_pass = ?")
            更新值.append(self._加密(数据["smtp_pass"]))

        if "smtp_protocol" in 数据 and 数据["smtp_protocol"] is not None:
            更新字段.append("smtp_protocol = ?")
            更新值.append(数据["smtp_protocol"])

        if "remark" in 数据 and 数据["remark"] is not None:
            更新字段.append("remark = ?")
            更新值.append(数据["remark"])

        # 如果没有要更新的字段，直接返回
        if not 更新字段:
            return 店铺

        # 添加 updated_at
        更新字段.append("updated_at = CURRENT_TIMESTAMP")

        # 执行更新
        更新值.append(店铺ID)
        SQL = f"UPDATE shops SET {', '.join(更新字段)} WHERE id = ?"

        async with 获取连接() as 连接:
            await 连接.execute(SQL, 更新值)
            await 连接.commit()

        # 返回更新后的店铺
        return await self.根据ID获取(店铺ID)

    async def 删除(self, 店铺ID: str) -> bool:
        """
        删除店铺

        参数:
            店铺ID: 店铺 ID

        返回:
            bool: 是否删除成功
        """
        # 检查店铺是否存在
        店铺 = await self.根据ID获取(店铺ID)
        if not 店铺:
            return False

        from backend.services.定时执行服务 import 定时执行服务实例

        async with 获取连接() as 连接:
            async with 连接.execute(
                "SELECT id, shop_ids FROM execution_schedules"
            ) as 游标:
                关联计划列表 = await 游标.fetchall()

        for 计划 in 关联计划列表:
            try:
                店铺ID列表 = json.loads(计划["shop_ids"])
            except (TypeError, json.JSONDecodeError):
                continue

            if 店铺ID not in 店铺ID列表:
                continue

            剩余店铺ID列表 = [当前店铺ID for 当前店铺ID in 店铺ID列表 if 当前店铺ID != 店铺ID]
            if 剩余店铺ID列表:
                await 定时执行服务实例.更新(计划["id"], {"shop_ids": 剩余店铺ID列表})
            else:
                await 定时执行服务实例.删除(计划["id"])

        # 删除数据库记录
        async with 获取连接() as 连接:
            await 连接.execute("DELETE FROM shops WHERE id = ?", (店铺ID,))
            await 连接.commit()

        # 删除用户数据目录
        用户目录 = Path(配置实例.DATA_DIR) / "profiles" / 店铺ID
        if 用户目录.exists():
            shutil.rmtree(用户目录)

        # 删除 Cookie 文件
        Cookie文件 = Path(配置实例.DATA_DIR) / "cookies" / f"{店铺ID}.json"
        if Cookie文件.exists():
            Cookie文件.unlink()

        return True

    async def 导入Cookie(self, 店铺ID: str, cookies: List[Dict[str, Any]]) -> bool:
        """
        导入 Cookie

        参数:
            店铺ID: 店铺 ID
            cookies: Cookie 列表

        返回:
            bool: 是否导入成功
        """
        # 检查店铺是否存在
        店铺 = await self.根据ID获取(店铺ID)
        if not 店铺:
            return False

        # 确保 cookies 目录存在
        Cookie目录 = Path(配置实例.DATA_DIR) / "cookies"
        Cookie目录.mkdir(parents=True, exist_ok=True)

        # 写入 Cookie 文件
        Cookie文件 = Cookie目录 / f"{店铺ID}.json"
        with open(Cookie文件, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        # 更新数据库中的 cookie_path
        async with 获取连接() as 连接:
            await 连接.execute(
                "UPDATE shops SET cookie_path = ? WHERE id = ?",
                (str(Cookie文件), 店铺ID)
            )
            await 连接.commit()

        return True

    async def 导出Cookie(self, 店铺ID: str) -> Optional[List[Dict[str, Any]]]:
        """
        导出 Cookie

        参数:
            店铺ID: 店铺 ID

        返回:
            Optional[List[Dict[str, Any]]]: Cookie 列表，不存在返回 None
        """
        # 检查店铺是否存在
        店铺 = await self.根据ID获取(店铺ID)
        if not 店铺:
            return None

        # 读取 Cookie 文件
        Cookie文件 = Path(配置实例.DATA_DIR) / "cookies" / f"{店铺ID}.json"
        if not Cookie文件.exists():
            return None

        try:
            with open(Cookie文件, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            return cookies
        except Exception:
            return None


# 创建单例
店铺服务实例 = 店铺服务()
