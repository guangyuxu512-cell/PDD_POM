"""
系统设置页与兼容服务测试
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from backend.services import system_service as 系统服务模块
from backend.utils.settings import ensure_settings_schema


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_系统设置页静态:
    """校验新系统设置页和配置代理已接入数据库设置。"""

    def test_系统设置页_包含分类切换与脱敏占位(self):
        页面文件 = 读取文件("frontend/src/views/SystemSettings.vue")

        for 关键字 in [
            "const categoryMap",
            "general: '通用设置'",
            "celery: '任务队列'",
            "notification: '通知配置'",
            "security: '安全配置'",
            "••••••••（已设置，留空不修改）",
            "batchUpdateSettings",
            "listSettings",
            "系统设置",
            "保存设置",
        ]:
            assert 关键字 in 页面文件

    def test_配置代理_包含_AGENT_MACHINE_ID_映射(self):
        配置文件 = 读取文件("backend/config.py")
        assert '"AGENT_MACHINE_ID": lambda: _读取可选字符串配置("agent_machine_id")' in 配置文件


class 测试_系统服务机器码:
    """验证旧 system/config 兼容层写入 settings 表。"""

    @pytest.mark.asyncio
    async def test_获取配置与更新配置_支持_agent_machine_id(self, tmp_path: Path):
        with patch("backend.utils.settings.DB_PATH", tmp_path / "ecom.db"):
            ensure_settings_schema()
            服务 = 系统服务模块.系统服务()

            当前配置 = await 服务.获取配置()
            assert 当前配置["agent_machine_id"] == ""

            await 服务.更新配置({"agent_machine_id": "office-pc-001"})
            更新后配置 = await 服务.获取配置()

        assert 更新后配置["agent_machine_id"] == "office-pc-001"

    @pytest.mark.asyncio
    async def test_更新配置_未知字段仍报错(self):
        服务 = 系统服务模块.系统服务()

        with pytest.raises(ValueError, match="不允许更新字段"):
            await 服务.更新配置({"unknown_field": "value"})
