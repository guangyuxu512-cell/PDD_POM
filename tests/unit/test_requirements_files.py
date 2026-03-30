"""
依赖清单文件静态校验
"""
from pathlib import Path


def test_requirements_拆分生产与开发依赖且包含日志库():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    requirements_dev = Path("requirements-dev.txt").read_text(encoding="utf-8")

    assert "loguru" in requirements
    assert "pytest" not in requirements
    assert "pytest" in requirements_dev
    assert "pytest-asyncio" in requirements_dev


def test_requirements_lock_使用精确版本号():
    行列表 = [
        行.strip()
        for 行 in Path("requirements-lock.txt").read_text(encoding="utf-8").splitlines()
        if 行.strip() and not 行.startswith("#")
    ]
    assert 行列表
    assert any("==" in 行 for 行 in 行列表)

