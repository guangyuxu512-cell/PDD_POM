"""
系统配置迁移后补丁测试
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from backend.services import system_service as 系统服务模块
from backend.utils.settings import ensure_settings_schema, get_setting


class 测试_系统服务补丁:
    @pytest.mark.asyncio
    async def test_更新配置_规范化Redis地址并刷新Celery配置(self, tmp_path: Path):
        with patch("backend.utils.settings.DB_PATH", tmp_path / "ecom.db"), \
                patch("backend.services.system_service.刷新Celery配置") as 模拟刷新:
            ensure_settings_schema()
            服务 = 系统服务模块.系统服务()
            更新后配置 = await 服务.更新配置({"redis_url": " redis://192.168.0.43/:6380/0 "})

        assert 更新后配置["redis_url"] == "redis://192.168.0.43:6380/0"
        assert get_setting("celery_broker_url") == "redis://192.168.0.43:6380/0"
        模拟刷新.assert_called_once()
