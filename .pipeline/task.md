步骤 1：修复 Celery 动态配置刷新（解决"等待中" + "需要重启"）
文件：tasks/celery_app.py
# 在 celery_app.conf.update(...) 之后添加函数：

def 刷新Celery配置():
    """从 settings 表重新读取 Redis URL，动态更新 Celery broker/backend。"""
    新broker = 配置实例.REDIS_URL
    新backend = 配置实例.CELERY_RESULT_BACKEND or 配置实例.REDIS_URL

    if celery_app.conf.broker_url != 新broker:
        celery_app.conf.broker_url = 新broker
        celery_app.conf.redbeat_redis_url = 新broker
        日志记录器.info(f"Celery broker 已更新: {新broker}")

    if celery_app.conf.result_backend != 新backend:
        celery_app.conf.result_backend = 新backend
        日志记录器.info(f"Celery backend 已更新: {新backend}")
​
文件：backend/services/system_service.py
在 更新配置 方法末尾，调用刷新：
async def 更新配置(self, 新配置: Dict[str, Any]) -> Dict[str, Any]:
    # ... existing code ...
    batch_update_settings(更新项)

    # ── 新增：动态刷新 Celery 配置 ──
    try:
        from tasks.celery_app import 刷新Celery配置
        刷新Celery配置()
    except Exception as e:
        import logging
        logging.getLogger().warning(f"刷新 Celery 配置失败（忽略）: {e}")

    return await self.获取配置()
​
文件：backend/services/execute_service.py
连接池已经有地址变化检测机制（_同步连接池地址 != 当前地址），这部分是对的，不需要改。
验收方式：
启动应用，在设置页面修改 Redis 地址
不重启，直接执行任务
验证任务能正常从"等待中"变为"运行中"
步骤 2：修复 Redis URL 解析错误
根因：你存的 Redis URL 可能是 redis://192.168.0.43/:6380/1（注意 : 前面多了 /），或者 celery_result_backend 存的值异常。
文件：backend/services/system_service.py
在 更新配置 中，对 redis_url 做校验和修正：
async def 更新配置(self, 新配置: Dict[str, Any]) -> Dict[str, Any]:
    # 在 batch_update_settings 之前，校验 Redis URL 格式
    redis_url_value = 新配置.get("redis_url")
    if redis_url_value and isinstance(redis_url_value, str):
        redis_url_value = redis_url_value.strip()
        # 修正常见格式错误：redis://host/:port → redis://host:port
        import re
        redis_url_value = re.sub(r'/:(\d+)', r':\1', redis_url_value)
        新配置["redis_url"] = redis_url_value

    # ... rest of existing code ...
​
验收方式：
设置 Redis 地址为 redis://192.168.0.43:6380/0（确认无多余 /）
点击"测试 Redis 连接"，应返回成功
执行任务，不应出现 invalid literal for int() 错误
步骤 3：添加 test-captcha 和 test-feishu-webhook 接口
文件：backend/models/data_structure.py
添加两个新模型：
class 验证码测试请求(BaseModel):
    """验证码服务测试请求"""
    captcha_provider: Optional[str] = Field(default=None, description="验证码服务商")
    captcha_api_key: Optional[str] = Field(default=None, description="验证码 API 密钥")
​
class 飞书Webhook测试请求(BaseModel):
"""飞书 Webhook 测试请求"""
webhook_url: Optional[str] = Field(default=None, description="飞书 Webhook 地址")
secret: Optional[str] = Field(default=None, description="飞书签名密钥")

**文件**：`backend/api/system_api.py`

在文件末尾（`健康检查` 路由之前）添加：

​
import hashlib
import hmac
import base64
import time
import httpx
from backend.models.data_structure import (
... existing imports ...
验证码测试请求,
飞书Webhook测试请求,
)
@路由.post("/test-captcha", summary="测试验证码服务连接")
async def 测试验证码服务(
请求: Optional[验证码测试请求] = Body(default=None, description="验证码服务信息")
) -> 统一响应:
"""
测试验证码第三方服务是否可用。
逻辑：向 YesCaptcha 的 /getBalance 接口请求余额，
能返回余额即表示 API Key 有效。
"""
服务商 = (请求.captcha_provider if 请求 else None) or 配置实例.CAPTCHA_PROVIDER or "yescaptcha"
密钥 = (请求.captcha_api_key if 请求 else None) or 配置实例.CAPTCHA_API_KEY or ""
密钥 = 密钥.strip() if 密钥 else ""
if not 密钥:
return 失败("验证码测试失败: API Key 不能为空")
if 服务商.lower() == "yescaptcha":
查询地址 = "https://api.yescaptcha.com/getBalance"
else:
return 失败(f"不支持的验证码服务商: {服务商}")
try:
async with httpx.AsyncClient(timeout=10) as 客户端:
响应 = await 客户端.post(查询地址, json={"clientKey": 密钥})
响应数据 = 响应.json()
if 响应数据.get("errorId", 1) == 0:
return 成功(
data={"balance": 响应数据.get("balance")},
message=f"验证码服务连接成功，余额: {响应数据.get('balance')}"
)
else:
return 失败(f"验证码测试失败: {响应数据.get('errorDescription', '未知错误')}")
except Exception as e:
return 失败(f"验证码测试失败: {str(e)}")
查看 system_api.py - 现有测试端点
查看 celery_app.py - Celery配置加载逻辑
查看任务执行相关代码 - 找出等待中的bug
添加 test-captcha 和 test-feishu 端点
修复设置更新后需要重启的问题
修复任务一直等待中的问题
输出完整 Codex 指令包
@路由.post("/test-feishu-webhook", summary="测试飞书 Webhook")
async def 测试飞书Webhook(
请求: Optional[飞书Webhook测试请求] = Body(default=None, description="飞书 Webhook 信息")
) -> 统一响应:
"""
向飞书 Webhook 发送一条测试消息。
"""
Webhook地址 = (请求.webhook_url if 请求 else None) or 配置实例.FEISHU_WEBHOOK_URL or ""
签名密钥 = (请求.secret if 请求 else None) or 配置实例.FEISHU_SECRET or ""
Webhook地址 = Webhook地址.strip() if Webhook地址 else ""
if not Webhook地址:
return 失败("飞书 Webhook 测试失败: Webhook 地址不能为空")
消息体: dict = {
"msg_type": "text",
"content": {"text": "RPA 系统连接测试 - 此消息表示 Webhook 配置正确 ✅"}
}
if 签名密钥:
时间戳 = str(int(time.time()))
签名字符串 = f"{时间戳}n{签名密钥}"
hmac摘要 = hmac.new(签名字符串.encode("utf-8"), digestmod=hashlib.sha256).digest()
签名 = base64.b64encode(hmac摘要).decode("utf-8")
消息体["timestamp"] = 时间戳
消息体["sign"] = 签名
try:
async with httpx.AsyncClient(timeout=10) as 客户端:
响应 = await 客户端.post(Webhook地址, json=消息体)
响应数据 = 响应.json()
if 响应数据.get("code") == 0 or 响应数据.get("StatusCode") == 0:
return 成功(message="飞书 Webhook 测试成功，消息已发送")
else:
return 失败(f"飞书 Webhook 测试失败: {响应数据.get('msg', '未知错误')}")
except Exception as e:
return 失败(f"飞书 Webhook 测试失败: {str(e)}")

**验收方式**：
1. `POST /api/system/test-captcha` — 传入 `captcha_api_key` 或留空用系统配置，返回余额
2. `POST /api/system/test-feishu-webhook` — 传入 `webhook_url` 或留空用系统配置，飞书群里收到测试消息

---

#### 步骤 4：确认 Celery Worker 侧也能动态感知新配置

**文件**：`tasks/execute_task.py`

在 `执行任务` 函数的开头，`初始化Worker环境()` 之后加一行：

​
@celery_app.task(name="执行任务", bind=True)
def 执行任务(self, *, batch_id, ...):
初始化Worker环境()
获取任务类(task_name)
── 新增：每次执行任务前刷新 Celery 配置 ──
from tasks.celery_app import 刷新Celery配置
刷新Celery配置()
... rest of code ...

> 注意：这只能解决 **backend 主进程的 Celery 客户端** 发任务时用的 broker 地址问题。Celery Worker 作为独立进程，如果 broker 地址变了，**Worker 仍然需要重启**——这是 Celery 架构的硬限制。但你的场景里 Redis 地址在部署后基本不变，所以这不是实际问题。

---

### 5) 验收标准

| 场景 | 预期结果 |
|---|---|
| `POST /api/system/test-redis` | 返回连接延迟 |
| `POST /api/system/test-captcha` | 返回 YesCaptcha 余额 |
| `POST /api/system/test-feishu-webhook` | 飞书群收到测试消息 |
| 修改 Redis 地址后不重启，执行任务 | 任务正常执行（不再卡等待中） |
| Redis URL 格式 `redis://192.168.0.43:6380/0` | 不再出现 `int()` 解析错误 |

### 6) 风险与注意事项

1. **Celery Worker 重启问题**：`刷新Celery配置()` 只对主进程 Celery 客户端生效。如果真的换了 Redis 服务器地址，Worker 进程必须重启。但 `execute_service.py` 里的 Redis 连接池在主进程里是动态的，不受影响。
2. **飞书签名**：`hmac.new` 的调用方式要确认飞书文档最新版本的签名算法（v2 用 SHA256）。
3. **YesCaptcha 接口**：如果用户换了其他验证码服务商（如 2captcha），需要补充对应的余额查询接口。
4. **你当前的 Redis URL**：请立即到设置页面确认 `celery_broker_url` 的值是 `redis://192.168.0.43:6380/0`（不是 `redis://192.168.0.43/:6380/0`），这很可能就是 `int()` 错误的直接原因。

---

### ✅ 检查清单

- [ ] Redis URL 格式校验与自动修正
- [ ] `test-captcha` 接口可用
- [ ] `test-feishu-webhook` 接口可用
- [ ] Celery 配置动态刷新（主进程侧）
- [ ] 改设置后无需重启即可执行任务
- [ ] 前端"系统设置"页面对应的测试按钮调用新接口（需前端配合）
- [ ] 单元测试覆盖三个测试接口