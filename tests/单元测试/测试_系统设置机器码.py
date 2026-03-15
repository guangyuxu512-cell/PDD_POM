"""
系统设置机器码静态与服务测试
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from backend.services import 系统服务 as 系统服务模块


仓库根目录 = Path(__file__).resolve().parents[2]


def 读取文件(相对路径: str) -> str:
    return (仓库根目录 / 相对路径).read_text(encoding="utf-8")


class 测试_系统设置机器码静态:
    """校验系统设置页和系统服务已接入机器码与飞书配置。"""

    def test_设置页_包含机器码输入与提示(self):
        页面文件 = 读取文件("frontend/src/views/Settings.vue")

        for 关键字 in [
            "agent_machine_id?: string",
            "agent_machine_id: ''",
            "agent_machine_id: data.agent_machine_id || ''",
            "机器码",
            'v-model="config.agent_machine_id"',
            "office-pc-001",
            "修改后需重启 Worker 生效",
        ]:
            assert 关键字 in 页面文件

    def test_设置页_包含飞书配置区块与测试按钮(self):
        页面文件 = 读取文件("frontend/src/views/Settings.vue")

        for 关键字 in [
            "feishu_webhook_url?: string",
            "feishu_app_id?: string",
            "feishu_app_secret?: string",
            "feishu_bitable_app_token?: string",
            "feishu_bitable_table_id?: string",
            "feishu_webhook_url: ''",
            "feishu_app_id: ''",
            "feishu_app_secret: ''",
            "feishu_bitable_app_token: ''",
            "feishu_bitable_table_id: ''",
            "feishu_webhook_url: data.feishu_webhook_url || ''",
            "feishu_app_id: data.feishu_app_id || ''",
            "feishu_app_secret: data.feishu_app_secret || ''",
            "feishu_bitable_app_token: data.feishu_bitable_app_token || ''",
            "feishu_bitable_table_id: data.feishu_bitable_table_id || ''",
            "const testingFeishu = ref(false)",
            "const testFeishuWebhook = async () => {",
            "/api/feishu/test-webhook",
            "飞书配置",
            "Webhook 地址",
            "测试 Webhook",
            "App ID",
            "App Secret",
            "多维表格 App Token",
            "多维表格 Table ID",
            "飞书群机器人的 Webhook 地址，用于发送通知",
        ]:
            assert 关键字 in 页面文件

    def test_配置模型_包含_AGENT_MACHINE_ID(self):
        配置文件 = 读取文件("backend/配置.py")
        assert "AGENT_MACHINE_ID: Optional[str] = None" in 配置文件


class 测试_系统服务机器码:
    """验证系统服务能读写机器码配置。"""

    @pytest.mark.asyncio
    async def test_获取配置与更新配置_支持_agent_machine_id(self, tmp_path: Path):
        服务 = 系统服务模块.系统服务()
        服务._env文件路径 = tmp_path / ".env"
        服务._env文件路径.write_text("REDIS_URL=redis://localhost:6379/0\n", encoding="utf-8")

        with patch.object(系统服务模块.配置实例, "REDIS_URL", "redis://localhost:6379/0"), \
                patch.object(系统服务模块.配置实例, "AGENT_MACHINE_ID", "machine-old"), \
                patch.object(系统服务模块.配置实例, "CAPTCHA_PROVIDER", "yescaptcha"), \
                patch.object(系统服务模块.配置实例, "CAPTCHA_API_KEY", None), \
                patch.object(系统服务模块.配置实例, "DEFAULT_PROXY", None), \
                patch.object(系统服务模块.配置实例, "MAX_BROWSER_INSTANCES", 5), \
                patch.object(系统服务模块.配置实例, "CHROME_PATH", None), \
                patch.object(系统服务模块.配置实例, "LOG_LEVEL", "INFO"):
            当前配置 = await 服务.获取配置()
            assert 当前配置["agent_machine_id"] == "machine-old"

            更新后配置 = await 服务.更新配置({"agent_machine_id": "office-pc-001"})

        assert 更新后配置["agent_machine_id"] == "office-pc-001"
        assert "AGENT_MACHINE_ID=office-pc-001" in 服务._env文件路径.read_text(encoding="utf-8")

    @pytest.mark.asyncio
    async def test_更新配置_未知字段仍报错(self):
        服务 = 系统服务模块.系统服务()

        with pytest.raises(ValueError, match="不允许更新字段"):
            await 服务.更新配置({"unknown_field": "value"})
