"""
用户目录工厂模块

管理浏览器用户数据目录（User Data Dir），每个店铺一个独立目录。
"""
from pathlib import Path
import shutil
from typing import List


class 用户目录工厂:
    """浏览器用户数据目录管理工厂"""

    def __init__(self, 基础目录: str = "data/profiles"):
        """
        初始化用户目录工厂

        Args:
            基础目录: 存储所有店铺 profile 的根目录
        """
        self.基础目录 = Path(基础目录)
        self.基础目录.mkdir(parents=True, exist_ok=True)

    def 获取或创建(self, 店铺ID: str) -> str:
        """
        获取或创建指定店铺的用户数据目录

        Args:
            店铺ID: 店铺的唯一标识

        Returns:
            str: 该店铺的用户数据目录绝对路径
        """
        店铺目录 = self.基础目录 / 店铺ID
        店铺目录.mkdir(parents=True, exist_ok=True)
        return str(店铺目录.absolute())

    def 删除(self, 店铺ID: str) -> bool:
        """
        删除指定店铺的用户数据目录

        Args:
            店铺ID: 店铺的唯一标识

        Returns:
            bool: 是否删除成功
        """
        店铺目录 = self.基础目录 / 店铺ID
        if not 店铺目录.exists():
            return False

        try:
            shutil.rmtree(店铺目录)
            return True
        except Exception as e:
            print(f"✗ 删除目录失败: {e}")
            return False

    def 列出全部(self) -> List[str]:
        """
        列出所有已有的店铺 ID

        Returns:
            List[str]: 所有店铺 ID 列表
        """
        if not self.基础目录.exists():
            return []

        return [
            目录.name
            for 目录 in self.基础目录.iterdir()
            if 目录.is_dir()
        ]
