"""
系统设置模型模块

定义 settings 表结构、中文字段映射和默认配置项。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from backend.models.table_schema import 字段定义, 数据表定义, 生成数据库记录


设置字段映射 = {
    "键名": "key",
    "值": "value",
    "分类": "category",
    "加密": "encrypted",
    "标签": "label",
    "提示": "hint",
    "创建时间": "created_at",
    "更新时间": "updated_at",
}


@dataclass(slots=True)
class 设置模型:
    """settings 表对应的数据模型。"""

    键名: str
    值: str | None = None
    分类: str = "general"
    加密: int = 0
    标签: str | None = None
    提示: str | None = None
    创建时间: datetime | None = None
    更新时间: datetime | None = None

    字段映射: ClassVar[dict[str, str]] = 设置字段映射

    def 转数据库记录(self) -> dict[str, object]:
        """转换为英文列名的数据库记录。"""
        return 生成数据库记录(self, self.字段映射)


def 创建设置表定义() -> 数据表定义:
    """创建 settings 表结构定义。"""
    return 数据表定义(
        表名="settings",
        字段列表=(
            字段定义("键名", "key", "TEXT", 主键=True),
            字段定义("值", "value", "TEXT"),
            字段定义("分类", "category", "TEXT", 非空=True, 默认值SQL="'general'"),
            字段定义("加密", "encrypted", "INTEGER", 非空=True, 默认值SQL="0"),
            字段定义("标签", "label", "TEXT"),
            字段定义("提示", "hint", "TEXT"),
            字段定义("创建时间", "created_at", "DATETIME", 默认值SQL="CURRENT_TIMESTAMP"),
            字段定义("更新时间", "updated_at", "DATETIME", 默认值SQL="CURRENT_TIMESTAMP"),
        ),
    )


设置表定义 = 创建设置表定义()


默认设置列表: tuple[设置模型, ...] = (
    设置模型("app_port", "8000", "general", 0, "应用端口", "桌面应用内置后端监听端口"),
    设置模型("api_base_url", "http://localhost:8000", "general", 0, "后端地址", "任务执行和本地 API 默认访问地址"),
    设置模型("max_concurrency", "5", "general", 0, "最大并发数", "浏览器池和批量执行默认并发上限"),
    设置模型("browser_headless", "false", "general", 0, "无头浏览器模式", "true 表示后台运行浏览器"),
    设置模型("chrome_path", "", "general", 0, "Chrome 路径", "留空时使用系统默认 Chrome"),
    设置模型("default_proxy", "", "general", 0, "默认代理地址", "未单独配置代理的店铺会回退到这里"),
    设置模型("log_level", "INFO", "general", 0, "日志级别", "支持 DEBUG / INFO / WARNING / ERROR"),
    设置模型("auto_restart_browser", "true", "general", 0, "浏览器崩溃自动重启", "浏览器异常关闭后是否自动尝试恢复"),
    设置模型("agent_machine_id", "", "general", 0, "机器码", "Worker 队列名和 Agent 注册使用的机器编号"),
    设置模型("machine_name", "", "general", 0, "机器名称", "Worker 注册时上报给 Agent 的展示名称"),
    设置模型("celery_broker_url", "redis://localhost:6379/0", "celery", 0, "Celery Broker", "Celery Broker 地址"),
    设置模型("celery_result_backend", "redis://localhost:6379/1", "celery", 0, "Celery Backend", "Celery Result Backend 地址"),
    设置模型("agent_callback_url", "", "celery", 0, "Agent 回调地址", "Worker/任务执行完成后回调 Agent 使用"),
    设置模型("agent_heartbeat_url", "", "celery", 0, "Agent 心跳地址", "Worker 心跳上报地址"),
    设置模型("feishu_webhook_url", "", "notification", 1, "飞书 Webhook", "群机器人 Webhook 地址"),
    设置模型("feishu_secret", "", "notification", 1, "飞书签名密钥", "群机器人签名密钥，可选"),
    设置模型("feishu_app_id", "", "notification", 0, "飞书 App ID", "飞书应用 App ID"),
    设置模型("feishu_app_secret", "", "notification", 1, "飞书 App Secret", "飞书应用密钥"),
    设置模型("feishu_bitable_app_token", "", "notification", 1, "多维表格 App Token", "飞书多维表格 App Token"),
    设置模型("feishu_bitable_table_id", "", "notification", 0, "多维表格 Table ID", "飞书多维表格 Table ID"),
    设置模型("captcha_provider", "yescaptcha", "security", 0, "验证码服务商", "如 yescaptcha / 2captcha / anticaptcha"),
    设置模型("captcha_api_key", "", "security", 1, "验证码 API Key", "验证码服务的访问密钥"),
    设置模型("x_rpa_key", "", "security", 1, "X-RPA-KEY", "Worker 与 Agent 通信使用的鉴权密钥"),
)


def 获取默认设置列表() -> tuple[设置模型, ...]:
    """返回默认设置项。"""
    return 默认设置列表


__all__ = [
    "设置模型",
    "设置字段映射",
    "设置表定义",
    "默认设置列表",
    "获取默认设置列表",
    "创建设置表定义",
]
