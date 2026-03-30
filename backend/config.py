"""
配置模块

使用 pydantic-settings 从 .env 文件读取配置。
"""
import sys
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


def _解析env路径() -> Path:
    """根据运行模式解析 .env 文件路径。"""
    if getattr(sys, "frozen", False):
        # 打包后：exe 所在目录
        return Path(sys.executable).resolve().parent / ".env"
    # 开发环境：项目根目录（config.py 所在目录的上级）
    return Path(__file__).resolve().parent.parent / ".env"


_ENV_PATH = _解析env路径()


class 配置(BaseSettings):
    """应用配置类"""

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # Chrome 浏览器路径
    CHROME_PATH: Optional[str] = None

    # 浏览器实例配置
    MAX_BROWSER_INSTANCES: int = 5

    # 验证码服务配置
    CAPTCHA_PROVIDER: str = "capsolver"
    CAPTCHA_API_KEY: Optional[str] = None

    # 代理配置
    DEFAULT_PROXY: Optional[str] = None

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # 数据目录
    DATA_DIR: str = "./data"

    # 加密密钥
    ENCRYPTION_KEY: Optional[str] = None

    # 服务端口
    FRONTEND_PORT: int = 3000
    BACKEND_PORT: int = 8000
    API_BASE_URL: str = "http://localhost:8000"

    # Agent 回调地址
    AGENT_CALLBACK_URL: Optional[str] = None

    # Agent 心跳配置
    AGENT_MACHINE_ID: Optional[str] = None
    MACHINE_NAME: Optional[str] = None
    AGENT_HEARTBEAT_URL: Optional[str] = None
    X_RPA_KEY: Optional[str] = None

    # 飞书配置
    FEISHU_WEBHOOK_URL: Optional[str] = None
    FEISHU_APP_ID: Optional[str] = None
    FEISHU_APP_SECRET: Optional[str] = None
    FEISHU_BITABLE_APP_TOKEN: Optional[str] = None
    FEISHU_BITABLE_TABLE_ID: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# 全局配置实例
配置实例 = 配置()
