"""选择器配置基类。"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class 选择器配置:
    """保存主选择器和备选选择器。"""

    主选择器: str
    备选选择器: Optional[List[str]] = None

    def 所有选择器(self) -> List[str]:
        """按主选择器优先返回全部候选选择器。"""
        结果 = [self.主选择器]
        if self.备选选择器:
            结果.extend(self.备选选择器)
        return 结果
