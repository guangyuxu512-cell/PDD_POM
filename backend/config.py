"""
配置模块

统一管理运行时数据目录，并通过 settings 表提供兼容旧代码的配置代理。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable


def get_app_data_dir() -> Path:
    """根据运行模式解析应用数据目录。"""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent.parent

    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


APP_DATA_DIR = get_app_data_dir()
DB_PATH = APP_DATA_DIR / "ecom.db"
LOG_DIR = APP_DATA_DIR / "logs"
BROWSER_PROFILES = APP_DATA_DIR / "browser_profiles"
COOKIE_DIR = APP_DATA_DIR / "cookies"
SCREENSHOT_DIR = APP_DATA_DIR / "screenshots"

for 目录 in (LOG_DIR, BROWSER_PROFILES, COOKIE_DIR, SCREENSHOT_DIR):
    目录.mkdir(parents=True, exist_ok=True)


def _读取字符串配置(键名: str, 默认值: str | None = None) -> str | None:
    from backend.utils.settings import get_setting

    return get_setting(键名, 默认值)


def _读取整数配置(键名: str, 默认值: int) -> int:
    from backend.utils.settings import get_setting_int

    return get_setting_int(键名, 默认值)


def _读取布尔配置(键名: str, 默认值: bool) -> bool:
    from backend.utils.settings import get_setting_bool

    return get_setting_bool(键名, 默认值)


def _读取可选字符串配置(键名: str, 默认值: str | None = None) -> str | None:
    值 = _读取字符串配置(键名, 默认值)
    if 值 in (None, ""):
        return None
    return 值


class _配置代理:
    """兼容旧代码的运行时配置代理。"""

    def __init__(self) -> None:
        object.__setattr__(self, "_覆盖", {})
        object.__setattr__(
            self,
            "_读取器",
            {
                "DATA_DIR": lambda: str(APP_DATA_DIR),
                "ENCRYPTION_KEY": lambda: None,
                "FRONTEND_PORT": lambda: 3000,
                "BACKEND_PORT": lambda: _读取整数配置("app_port", 8000),
                "API_BASE_URL": lambda: _读取字符串配置(
                    "api_base_url",
                    f"http://localhost:{_读取整数配置('app_port', 8000)}",
                ),
                "REDIS_URL": lambda: _读取字符串配置(
                    "celery_broker_url",
                    "redis://localhost:6379/0",
                ),
                "CELERY_RESULT_BACKEND": lambda: _读取字符串配置(
                    "celery_result_backend",
                    "redis://localhost:6379/1",
                ),
                "CHROME_PATH": lambda: _读取可选字符串配置("chrome_path"),
                "MAX_BROWSER_INSTANCES": lambda: _读取整数配置("max_concurrency", 5),
                "BROWSER_HEADLESS": lambda: _读取布尔配置("browser_headless", False),
                "CAPTCHA_PROVIDER": lambda: _读取字符串配置("captcha_provider", "yescaptcha"),
                "CAPTCHA_API_KEY": lambda: _读取可选字符串配置("captcha_api_key"),
                "DEFAULT_PROXY": lambda: _读取可选字符串配置("default_proxy"),
                "LOG_LEVEL": lambda: _读取字符串配置("log_level", "INFO"),
                "AUTO_RESTART_BROWSER": lambda: _读取布尔配置("auto_restart_browser", True),
                "AGENT_CALLBACK_URL": lambda: _读取可选字符串配置("agent_callback_url"),
                "AGENT_MACHINE_ID": lambda: _读取可选字符串配置("agent_machine_id"),
                "MACHINE_NAME": lambda: _读取可选字符串配置("machine_name"),
                "AGENT_HEARTBEAT_URL": lambda: _读取可选字符串配置("agent_heartbeat_url"),
                "X_RPA_KEY": lambda: _读取可选字符串配置("x_rpa_key"),
                "FEISHU_WEBHOOK_URL": lambda: _读取可选字符串配置("feishu_webhook_url"),
                "FEISHU_SECRET": lambda: _读取可选字符串配置("feishu_secret"),
                "FEISHU_APP_ID": lambda: _读取可选字符串配置("feishu_app_id"),
                "FEISHU_APP_SECRET": lambda: _读取可选字符串配置("feishu_app_secret"),
                "FEISHU_BITABLE_APP_TOKEN": lambda: _读取可选字符串配置("feishu_bitable_app_token"),
                "FEISHU_BITABLE_TABLE_ID": lambda: _读取可选字符串配置("feishu_bitable_table_id"),
            },
        )

    def __getattr__(self, 名称: str) -> Any:
        覆盖 = object.__getattribute__(self, "_覆盖")
        if 名称 in 覆盖:
            return 覆盖[名称]

        读取器: dict[str, Callable[[], Any]] = object.__getattribute__(self, "_读取器")
        if 名称 not in 读取器:
            raise AttributeError(名称)
        return 读取器[名称]()

    def __setattr__(self, 名称: str, 值: Any) -> None:
        if 名称.startswith("_"):
            object.__setattr__(self, 名称, 值)
            return
        覆盖 = object.__getattribute__(self, "_覆盖")
        覆盖[名称] = 值

    def __delattr__(self, 名称: str) -> None:
        覆盖 = object.__getattribute__(self, "_覆盖")
        if 名称 in 覆盖:
            del 覆盖[名称]
            return
        raise AttributeError(名称)


配置实例 = _配置代理()


__all__ = [
    "APP_DATA_DIR",
    "DB_PATH",
    "LOG_DIR",
    "BROWSER_PROFILES",
    "COOKIE_DIR",
    "SCREENSHOT_DIR",
    "get_app_data_dir",
    "配置实例",
]
