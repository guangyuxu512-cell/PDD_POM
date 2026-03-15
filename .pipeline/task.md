Task 42：桌面基础页 + 微信 POM + 桌面选择器配置
一、做什么
新建桌面自动化基础设施：
桌面选择器配置 数据类（类似现有 选择器配置，但面向 UIAutomation 控件属性）
桌面基础页（类似现有 基础页，但底层用 uiautomation 库而非 Playwright）
微信页 POM（搜索联系人、发消息、发图片）
微信选择器（微信桌面版控件定位）
依赖安装：uiautomation 库
二、涉及文件
selectors/桌面选择器配置.py — 新建
pages/桌面基础页.py — 新建
pages/微信页.py — 新建
selectors/微信选择器.py — 新建
requirements.txt — 新增 uiautomation 依赖
测试文件同步新建
三、桌面选择器配置
selectors/桌面选择器配置.py：
"""桌面应用选择器配置基类。"""
from dataclasses import dataclass, field
from typing import List, Optional
​
@dataclass
class 桌面选择器配置:
"""保存桌面控件定位属性。
UIAutomation 通过控件属性组合定位，不同于浏览器的 CSS/XPath。
"""
控件类型: str                          # ControlTypeName: ButtonControl, EditControl, ListItemControl...
名称: Optional[str] = None              # Name 属性
自动化ID: Optional[str] = None          # AutomationId
类名: Optional[str] = None              # ClassName
深度: int = 0                            # searchDepth, 0 表示不限制
备选: List['桌面选择器配置'] = field(default_factory=list)
def 所有配置(self) -> List['桌面选择器配置']:
"""按主选择器优先返回全部候选。"""
return [self] + self.备选

---

**四、桌面基础页**

`pages/桌面基础页.py`：

​
"""桌面应用页面对象模型基类。"""
import asyncio
import random
import time
from pathlib import Path
from typing import Optional, Any
import uiautomation as uia
from backend.配置 import 配置实例
from selectors.桌面选择器配置 import 桌面选择器配置
class 桌面基础页:
"""桌面应用 POM 基类，所有桌面页面类继承此类。"""
def init(self, 窗口控件: Optional[uia.WindowControl] = None):
self._窗口 = 窗口控件
def _查找控件(self, 配置: 桌面选择器配置, 父控件: Optional[Any] = None) -> Optional[Any]:
"""根据桌面选择器配置查找控件。"""
搜索范围 = 父控件 or self._窗口 or uia.GetRootControl()
搜索参数 = {"searchDepth": 配置.深度 or 0}
if 配置.名称:
搜索参数["Name"] = 配置.名称
if 配置.自动化ID:
搜索参数["AutomationId"] = 配置.自动化ID
if 配置.类名:
搜索参数["ClassName"] = 配置.类名
控件类型方法 = getattr(搜索范围, 配置.控件类型, None)
if not callable(控件类型方法):
return None
return 控件类型方法(搜索参数)
def 查找(self, 配置: 桌面选择器配置, 父控件: Optional[Any] = None) -> Optional[Any]:
"""按主选择器 + 备选依次查找控件。"""
for 单个配置 in 配置.所有配置():
try:
控件 = self._查找控件(单个配置, 父控件)
if 控件 and 控件.Exists(maxSearchSeconds=3):
return 控件
except Exception:
continue
return None
def 点击(self, 配置: 桌面选择器配置) -> bool:
"""查找并点击控件。"""
控件 = self.查找(配置)
if not 控件:
print(f"[桌面基础页] 未找到控件: {配置.名称 or 配置.控件类型}")
return False
控件.Click()
self._随机等待(0.3, 0.8)
return True
def 输入文本(self, 配置: 桌面选择器配置, 文本: str, 清空: bool = True) -> bool:
"""查找控件并输入文本。"""
控件 = self.查找(配置)
if not 控件:
print(f"[桌面基础页] 未找到输入控件: {配置.名称 or 配置.控件类型}")
return False
if 清空:
控件.GetValuePattern().SetValue("")
模拟逐字输入，降低被检测风险
for 字符 in 文本:
控件.SendKeys(字符)
time.sleep(random.uniform(0.05, 0.15))
self._随机等待(0.3, 0.5)
return True
def 获取文本(self, 配置: 桌面选择器配置) -> str:
"""获取控件文本。"""
控件 = self.查找(配置)
if not 控件:
return ""
return str(控件.Name or "")
def 元素是否存在(self, 配置: 桌面选择器配置, 超时秒: float = 3) -> bool:
"""检查控件是否存在。"""
控件 = self.查找(配置)
if not 控件:
return False
return 控件.Exists(maxSearchSeconds=超时秒)
def 截图(self, 名称: str) -> str:
"""对窗口截图。"""
截图目录 = Path(配置实例.DATA_DIR) / "screenshots"
截图目录.mkdir(parents=True, exist_ok=True)
文件名 = f"{名称}_{int(time.time())}.png"
文件路径 = 截图目录 / 文件名
if self._窗口:
self._窗口.CaptureToImage(str(文件路径))
return str(文件路径)
@staticmethod
def _随机等待(最小秒: float = 0.5, 最大秒: float = 2.0):
"""同步随机等待。"""
time.sleep(random.uniform(最小秒, 最大秒))
def 操作前延迟(self):
self._随机等待(0.3, 0.8)
def 操作后延迟(self):
self._随机等待(0.8, 2.0)

注意：桌面基础页的方法是**同步的**（不是 async），因为 `uiautomation` 是同步库。Task 层调用时用 `asyncio.to_thread()` 包装。

---

**五、微信选择器**

`selectors/微信选择器.py`：

​
"""微信桌面版选择器。"""
from selectors.桌面选择器配置 import 桌面选择器配置
class 微信选择器:
"""微信 PC 版控件选择器集合。"""
微信主窗口
主窗口 = 桌面选择器配置(
控件类型="WindowControl",
名称="微信",
类名="WeChatMainWndForPC",
)
搜索框（点击后出现的输入框）
搜索按钮 = 桌面选择器配置(
控件类型="ButtonControl",
名称="搜索",
)
搜索输入框 = 桌面选择器配置(
控件类型="EditControl",
名称="搜索",
)
聊天输入框
聊天输入框 = 桌面选择器配置(
控件类型="EditControl",
名称="输入",
)
发送按钮
发送按钮 = 桌面选择器配置(
控件类型="ButtonControl",
名称="sendBtn",
备选=[
桌面选择器配置(控件类型="ButtonControl", 名称="发送(S)"),
],
)
@staticmethod
def 获取联系人项(联系人名称: str) -> 桌面选择器配置:
"""根据联系人名称生成搜索结果列表项选择器。"""
return 桌面选择器配置(
控件类型="ListItemControl",
名称=联系人名称,
)

---

**六、微信页 POM**

`pages/微信页.py`：

​
"""微信桌面版页面对象。"""
import asyncio
import time
from typing import Optional
import uiautomation as uia
from pages.桌面基础页 import 桌面基础页
from selectors.微信选择器 import 微信选择器
class 微信页(桌面基础页):
"""微信 PC 版操作页面。"""
def init(self):
微信窗口 = uia.WindowControl(
Name="微信",
ClassName="WeChatMainWndForPC",
)
super().init(微信窗口)
def 激活窗口(self) -> bool:
"""将微信窗口置顶激活。"""
if not self._窗口 or not self._窗口.Exists(maxSearchSeconds=5):
print("[微信页] 微信窗口未找到，请确认微信已登录")
return False
self._窗口.SetActive()
self._窗口.SetTopmost(True)
self._随机等待(0.5, 1.0)
self._窗口.SetTopmost(False)
return True
def 搜索联系人(self, 联系人: str) -> bool:
"""通过搜索框搜索联系人并打开聊天。"""
点击搜索
if not self.点击(微信选择器.搜索按钮):
print("[微信页] 搜索按钮未找到")
return False
self._随机等待(0.5, 1.0)
输入联系人名称
if not self.输入文本(微信选择器.搜索输入框, 联系人):
print(f"[微信页] 搜索输入框未找到")
return False
self._随机等待(1.0, 2.0)  # 等待搜索结果
点击搜索结果
联系人选择器 = 微信选择器.获取联系人项(联系人)
if not self.点击(联系人选择器):
print(f"[微信页] 联系人未找到: {联系人}")
return False
self._随机等待(0.5, 1.0)
return True
def 发送消息(self, 联系人: str, 消息: str) -> bool:
"""搜索联系人并发送文本消息。"""
if not self.激活窗口():
return False
if not self.搜索联系人(联系人):
return False
输入消息
if not self.输入文本(微信选择器.聊天输入框, 消息, 清空=True):
print("[微信页] 聊天输入框未找到")
return False
self._随机等待(0.3, 0.8)
点击发送
if not self.点击(微信选择器.发送按钮):
备用：按 Enter 发送
聊天框 = self.查找(微信选择器.聊天输入框)
if 聊天框:
聊天框.SendKeys("{Enter}")
else:
print("[微信页] 发送按钮和Enter都失败")
return False
self._随机等待(1.0, 2.0)
print(f"[微信页] 已发送消息给 {联系人}")
return True
def 发送消息到当前聊天(self, 消息: str) -> bool:
"""在当前已打开的聊天窗口直接发送消息（不搜索联系人）。"""
if not self.激活窗口():
return False
if not self.输入文本(微信选择器.聊天输入框, 消息, 清空=True):
return False
self._随机等待(0.3, 0.8)
if not self.点击(微信选择器.发送按钮):
聊天框 = self.查找(微信选择器.聊天输入框)
if 聊天框:
聊天框.SendKeys("{Enter}")
else:
return False
self._随机等待(1.0, 2.0)
return True

---

**七、Task 层调用示例（不用实现，仅供参考）**

​
tasks/售后任务.py 未来的调用方式：
async def 执行(self, 页面, 店铺配置):
浏览器操作（async）
售后页实例 = 售后页(页面)
await 售后页实例.处理退款(订单号)
桌面操作（sync → 用 to_thread 包装成 async）
微信页实例 = 微信页()
await asyncio.to_thread(微信页实例.发送消息, "客户微信号", "退款已处理~")

---

**八、约束**

1. 桌面基础页方法全部是**同步的**（uiautomation 是同步库），Task 层用 `asyncio.to_thread()` 调用
2. 微信选择器的 Name/ClassName 基于微信 PC 版 3.9.x，后续版本可能需要更新
3. 不修改现有 `基础页.py`、`选择器配置.py` 任何代码
4. `uiautomation` 添加到 `requirements.txt`
5. 新建测试文件 `tests/test_桌面基础页.py`、`tests/test_微信页.py`，测试基础方法（mock uiautomation）
6. 确保 pytest 通过