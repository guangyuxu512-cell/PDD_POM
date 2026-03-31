"""
打包前清理脚本

删除运行时数据、日志和敏感文件，避免被打进分发产物。
"""
from __future__ import annotations

import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIRS = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "dist",
    PROJECT_ROOT / "build",
]
CLEAN_PATTERNS = [
    "*.db",
    "*.db-journal",
    "*.db-wal",
    ".env",
    "*.log",
    ".secret_key",
]


def clean() -> None:
    """执行打包前清理。"""
    for directory in CLEAN_DIRS:
        if directory.exists():
            shutil.rmtree(directory)
            print(f"已删除目录: {directory}")

    for pattern in CLEAN_PATTERNS:
        for file_path in PROJECT_ROOT.rglob(pattern):
            if ".git" in file_path.parts or "node_modules" in file_path.parts:
                continue
            if file_path.is_file():
                file_path.unlink()
                print(f"已删除文件: {file_path}")

    print("脱敏清理完成，可以开始打包。")


if __name__ == "__main__":
    clean()
