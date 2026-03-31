"""
加密工具模块

统一管理 settings 与其他敏感数据使用的 Fernet 密钥。
"""
from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet

from backend.config import APP_DATA_DIR, 配置实例


SECRET_KEY_PATH = APP_DATA_DIR / ".secret_key"
_当前密钥路径: Path | None = None
_当前Fernet: Fernet | None = None


def 获取密钥文件路径() -> Path:
    """按当前运行配置解析密钥文件路径。"""
    数据目录 = Path(getattr(配置实例, "DATA_DIR", str(APP_DATA_DIR)))
    数据目录.mkdir(parents=True, exist_ok=True)
    return 数据目录 / ".secret_key"


def _load_or_create_key(密钥路径: Path | None = None) -> bytes:
    """加载或首次生成加密密钥。"""
    目标路径 = 密钥路径 or 获取密钥文件路径()
    目标路径.parent.mkdir(parents=True, exist_ok=True)
    if 目标路径.exists():
        return 目标路径.read_bytes()

    密钥 = Fernet.generate_key()
    目标路径.write_bytes(密钥)
    return 密钥


def get_fernet() -> Fernet:
    """返回与当前数据目录匹配的 Fernet 实例。"""
    global _当前密钥路径, _当前Fernet

    密钥路径 = 获取密钥文件路径()
    if _当前Fernet is None or _当前密钥路径 != 密钥路径:
        _当前密钥路径 = 密钥路径
        _当前Fernet = Fernet(_load_or_create_key(密钥路径))
    return _当前Fernet


def encrypt_value(plaintext: str) -> str:
    """加密明文，返回 base64 密文。"""
    return get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """解密密文，返回明文。"""
    return get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")


__all__ = [
    "SECRET_KEY_PATH",
    "获取密钥文件路径",
    "get_fernet",
    "encrypt_value",
    "decrypt_value",
]
