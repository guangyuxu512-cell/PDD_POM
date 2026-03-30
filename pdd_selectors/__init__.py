"""项目选择器包。

兼容 Python 标准库 ``selectors`` 模块，避免与本地同名目录冲突。
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sysconfig


_标准库选择器文件 = Path(sysconfig.get_path("stdlib")) / "selectors.py"
_标准库选择器规格 = spec_from_file_location("_标准库selectors", _标准库选择器文件)
if _标准库选择器规格 is None or _标准库选择器规格.loader is None:
    raise ImportError("无法加载标准库 selectors 模块")

_标准库选择器模块 = module_from_spec(_标准库选择器规格)
_标准库选择器规格.loader.exec_module(_标准库选择器模块)

__all__ = list(getattr(_标准库选择器模块, "__all__", []))

for _名称 in __all__:
    globals()[_名称] = getattr(_标准库选择器模块, _名称)

for _名称 in ("EVENT_READ", "EVENT_WRITE"):
    if _名称 not in globals() and hasattr(_标准库选择器模块, _名称):
        globals()[_名称] = getattr(_标准库选择器模块, _名称)
        __all__.append(_名称)


def __getattr__(名称: str):
    """将未声明属性继续透传给标准库 selectors 模块。"""
    return getattr(_标准库选择器模块, 名称)
