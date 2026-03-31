"""
打包运行时路径解析回归测试
"""
from pathlib import Path

import backend.config as 配置模块
from backend.models import database as 数据库模块


class 测试_打包运行时路径:
    def test_应用数据目录_冻结模式使用_exe_同级_data(self, monkeypatch, tmp_path: Path):
        exe目录 = tmp_path / "backend"
        exe目录.mkdir()

        monkeypatch.setattr(配置模块.sys, "frozen", True, raising=False)
        monkeypatch.setattr(配置模块.sys, "executable", str(exe目录 / "backend.exe"), raising=False)

        assert 配置模块.get_app_data_dir() == exe目录 / "data"

    def test_应用数据目录_开发模式使用项目根_data(self, monkeypatch):
        monkeypatch.delattr(配置模块.sys, "frozen", raising=False)
        期望路径 = Path(配置模块.__file__).resolve().parent.parent / "data"

        assert 配置模块.get_app_data_dir() == 期望路径

    def test_数据库路径_统一取自_config_DB_PATH(self):
        assert 数据库模块.数据库路径 == 配置模块.DB_PATH
