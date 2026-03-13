"""
配置模块

使用 pydantic-settings 从 .env 文件读取配置。
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# 全局配置实例
配置实例 = 配置()
