"""
店铺模型模块

定义 shops 表的中文属性模型以及对应的数据表结构。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from backend.models.表结构 import 字段定义, 数据表定义, 生成数据库记录


店铺字段映射 = {
    "店铺ID": "id",
    "名称": "name",
    "账号": "username",
    "密码": "password",
    "代理": "proxy",
    "用户代理": "user_agent",
    "用户目录": "profile_dir",
    "Cookie路径": "cookie_path",
    "状态": "status",
    "最后登录时间": "last_login",
    "邮件服务器": "smtp_host",
    "邮件端口": "smtp_port",
    "邮件账号": "smtp_user",
    "邮件密码": "smtp_pass",
    "邮件协议": "smtp_protocol",
    "备注": "remark",
    "创建时间": "created_at",
    "更新时间": "updated_at",
}


@dataclass(slots=True)
class 店铺模型:
    """shops 表对应的店铺数据模型。"""

    店铺ID: str
    名称: str
    账号: str | None = None
    密码: str | None = None
    代理: str | None = None
    用户代理: str | None = None
    用户目录: str | None = None
    Cookie路径: str | None = None
    状态: str = "offline"
    最后登录时间: datetime | None = None
    邮件服务器: str | None = None
    邮件端口: int = 993
    邮件账号: str | None = None
    邮件密码: str | None = None
    邮件协议: str = "imap"
    备注: str | None = None
    创建时间: datetime | None = None
    更新时间: datetime | None = None

    字段映射: ClassVar[dict[str, str]] = 店铺字段映射

    def 转数据库记录(self) -> dict[str, object]:
        """转换为英文列名的数据库记录。"""
        return 生成数据库记录(self, self.字段映射)


def 创建店铺表定义() -> 数据表定义:
    """创建 shops 表结构定义。"""
    return 数据表定义(
        表名="shops",
        字段列表=(
            字段定义("店铺ID", "id", "TEXT", 主键=True),
            字段定义("名称", "name", "TEXT", 非空=True),
            字段定义("账号", "username", "TEXT"),
            字段定义("密码", "password", "TEXT"),
            字段定义("代理", "proxy", "TEXT"),
            字段定义("用户代理", "user_agent", "TEXT"),
            字段定义("用户目录", "profile_dir", "TEXT"),
            字段定义("Cookie路径", "cookie_path", "TEXT"),
            字段定义("状态", "status", "TEXT", 默认值SQL="'offline'"),
            字段定义("最后登录时间", "last_login", "DATETIME"),
            字段定义("邮件服务器", "smtp_host", "TEXT"),
            字段定义("邮件端口", "smtp_port", "INTEGER", 默认值SQL="993"),
            字段定义("邮件账号", "smtp_user", "TEXT"),
            字段定义("邮件密码", "smtp_pass", "TEXT"),
            字段定义("邮件协议", "smtp_protocol", "TEXT", 默认值SQL="'imap'"),
            字段定义("备注", "remark", "TEXT"),
            字段定义("创建时间", "created_at", "DATETIME", 默认值SQL="CURRENT_TIMESTAMP"),
            字段定义("更新时间", "updated_at", "DATETIME", 默认值SQL="CURRENT_TIMESTAMP"),
        ),
    )


店铺表定义 = 创建店铺表定义()


__all__ = [
    "店铺模型",
    "店铺字段映射",
    "店铺表定义",
    "创建店铺表定义",
]
