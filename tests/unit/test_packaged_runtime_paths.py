"""
打包运行时路径解析回归测试
"""
from pathlib import Path

import backend.config as 配置模块
from backend.models import database as 数据库模块


class 测试_打包运行时路径:
    def test_解析env路径_冻结模式优先_exe_同级(self, monkeypatch, tmp_path: Path):
        exe目录 = tmp_path / "backend"
        exe目录.mkdir()
        env文件 = exe目录 / ".env"
        env文件.write_text("BACKEND_PORT=9000\n", encoding="utf-8")

        monkeypatch.setattr(配置模块.sys, "frozen", True, raising=False)
        monkeypatch.setattr(配置模块.sys, "executable", str(exe目录 / "backend.exe"), raising=False)
        monkeypatch.chdir(tmp_path)

        assert 配置模块._解析env路径() == env文件

    def test_解析env路径_冻结模式回退到_exe_上级(self, monkeypatch, tmp_path: Path):
        exe目录 = tmp_path / "backend"
        exe目录.mkdir()
        env文件 = tmp_path / ".env"
        env文件.write_text("BACKEND_PORT=9001\n", encoding="utf-8")
        其他目录 = tmp_path / "other"
        其他目录.mkdir()

        monkeypatch.setattr(配置模块.sys, "frozen", True, raising=False)
        monkeypatch.setattr(配置模块.sys, "executable", str(exe目录 / "backend.exe"), raising=False)
        monkeypatch.chdir(其他目录)

        assert 配置模块._解析env路径() == env文件

    def test_获取数据目录_冻结模式使用_exe_同级_data(self, monkeypatch, tmp_path: Path):
        exe目录 = tmp_path / "backend"
        exe目录.mkdir()

        monkeypatch.setattr(数据库模块.sys, "frozen", True, raising=False)
        monkeypatch.setattr(数据库模块.sys, "executable", str(exe目录 / "backend.exe"), raising=False)

        assert 数据库模块._获取数据目录() == exe目录 / "data"
