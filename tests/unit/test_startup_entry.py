"""
启动入口相关回归测试
"""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class 测试_启动入口:
    """测试 FastAPI lifespan 资源管理"""

    @pytest.mark.asyncio
    async def test_生命周期_启动并关闭心跳服务(self):
        """lifespan 启动时拉起心跳，关闭时正确清理资源"""
        from backend import main as 启动入口模块

        with patch("tasks.task_registry.初始化任务注册表") as 模拟初始化任务注册表, \
                patch("browser.task_callback.设置回调地址") as 模拟设置回调地址, \
                patch("backend.main.初始化数据库", new=AsyncMock()) as 模拟初始化数据库, \
                patch("backend.main.关闭数据库", new=AsyncMock()) as 模拟关闭数据库, \
                patch("backend.services.heartbeat_service.心跳服务实例.启动", new=AsyncMock()) as 模拟启动心跳, \
                patch("backend.services.heartbeat_service.心跳服务实例.停止", new=AsyncMock()) as 模拟停止心跳, \
                patch.object(启动入口模块.配置实例, "AGENT_CALLBACK_URL", "http://agent/callback"):
            async with 启动入口模块.生命周期(MagicMock()):
                pass

        模拟初始化数据库.assert_awaited_once()
        模拟关闭数据库.assert_awaited_once()
        模拟初始化任务注册表.assert_called_once()
        模拟设置回调地址.assert_called_once_with("http://agent/callback")
        模拟启动心跳.assert_awaited_once()
        模拟停止心跳.assert_awaited_once()

    def test_挂载前端静态资源_可返回静态文件与SPA首页(self, tmp_path: Path):
        """存在构建产物时，非 API 路径应回退到 index.html。"""
        from backend import main as 启动入口模块

        前端目录 = tmp_path / "frontend" / "dist"
        资源目录 = 前端目录 / "assets"
        资源目录.mkdir(parents=True)
        (前端目录 / "index.html").write_text("<html>spa</html>", encoding="utf-8")
        (资源目录 / "app.js").write_text("console.log('ok')", encoding="utf-8")

        应用 = FastAPI()
        启动入口模块.挂载前端静态资源(应用, 前端目录)

        with TestClient(应用) as 客户端:
            首页响应 = 客户端.get("/shops")
            资源响应 = 客户端.get("/assets/app.js")

        assert 首页响应.status_code == 200
        assert "<html>spa</html>" in 首页响应.text
        assert 资源响应.status_code == 200
        assert "console.log('ok')" in 资源响应.text

    def test_挂载前端静态资源_保留后端路径返回404(self, tmp_path: Path):
        """API 等后端保留路径不存在时，不应错误回退到前端首页。"""
        from backend import main as 启动入口模块

        前端目录 = tmp_path / "frontend" / "dist"
        前端目录.mkdir(parents=True)
        (前端目录 / "index.html").write_text("<html>spa</html>", encoding="utf-8")

        应用 = FastAPI()
        启动入口模块.挂载前端静态资源(应用, 前端目录)

        with TestClient(应用) as 客户端:
            响应 = 客户端.get("/api/not-found")

        assert 响应.status_code == 404
