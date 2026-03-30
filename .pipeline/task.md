指令 1：登录态失效检测与告警（问题 5）
任务目标：为浏览器管理器添加登录态失效检测，在 Cookie 过期或被踢出时自动告警并暂停相关任务。

需要修改/新增的文件：
- 新增 browser/session_monitor.py
- 修改 browser/manager.py
- 修改 pages/base_page.py

具体实现要点：

1. 新建 browser/session_monitor.py：
   - 定义 class 登录态监控器
   - 方法 async def 检查登录态(页面, 店铺ID) -> bool：
     - 检查当前 URL 是否被重定向到登录页（包含 /login、/passport、mms.pinduoduo.com/login 等特征）
     - 检查页面中是否存在"登录已过期"、"请重新登录"等关键文本
     - 检查关键 Cookie（如 PASS_ID、JSESSIONID）是否存在且未过期
     - 返回 True 表示已登录，False 表示已失效
   - 方法 async def 触发失效告警(店铺ID, 店铺名称, 原因)：
     - 写入 operation_logs 表，level='ERROR', source='session_monitor'
     - 如果配置了飞书 Webhook（配置实例.FEISHU_WEBHOOK_URL），发送飞书告警消息
     - 通过 Redis Pub/Sub 发布告警事件到 channel "session:expired"
   - 导出单例 登录态监控实例

2. 修改 pages/base_page.py：
   - 在 基础页 类中新增方法 async def 检查并处理登录态(self) -> bool
   - 调用 登录态监控实例.检查登录态(self.页面, self.店铺ID)
   - 如果检测到失效，调用触发失效告警，并 raise RuntimeError("登录态已失效")
   - 在关键操作（导航、点击、填写）前自动调用此检查

3. 修改 browser/manager.py 的 获取页面 方法：
   - 获取页面后，如果页面 URL 包含 login 特征，自动标记该店铺为"需要重新登录"
   - 在 _清理实例 中发布 Redis 事件通知

验收方式：
- 单元测试：mock 一个 URL 为登录页的页面，验证 检查登录态 返回 False
- 单元测试：验证触发失效告警后 operation_logs 中有对应记录
- 集成测试：模拟 Cookie 被清除后执行任务，验证任务被中断并有告警日志
​
指令 2：结构化日志体系（问题 6）
任务目标：将全项目的 print() 替换为 loguru 结构化日志，支持文件轮转、JSON 格式、trace_id 追踪。

需要修改/新增的文件：
- 新增 backend/logging_config.py
- 修改 requirements.txt（添加 loguru）
- 修改所有包含 print() 的文件（批量替换）

具体实现要点：

1. 在 requirements.txt 中添加 loguru>=0.7.0

2. 新建 backend/logging_config.py：
​
import sys
from pathlib import Path
from loguru import logger
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
移除 loguru 默认 handler
logger.remove()
控制台输出（人类可读）
logger.add(
sys.stderr,
format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[trace_id]}</cyan> | {message}",
level="INFO",
filter=lambda record: record["extra"].setdefault("trace_id", "—"),
)
文件输出（JSON 格式，自动轮转）
logger.add(
LOG_DIR / "app_{time:YYYY-MM-DD}.log",
format="{time:YYYY-MM-DDTHH:mm:ss.SSS} | {level} | {extra[trace_id]} | {name}:{function}:{line} | {message}",
rotation="50 MB",
retention="30 days",
compression="gz",
level="DEBUG",
encoding="utf-8",
)
错误专用日志
logger.add(
LOG_DIR / "error_{time:YYYY-MM-DD}.log",
rotation="20 MB",
retention="60 days",
level="ERROR",
encoding="utf-8",
)
def get_logger(trace_id: str = "—"):
return logger.bind(trace_id=trace_id)

3. 批量替换 print() 为 logger 调用：
   - 在项目根目录执行以下替换策略：
   - 所有 print(f"[xxx]...) 替换为 logger.info(...)，保留方括号内容作为 logger 的 name
   - 所有 print(f"✓ ...") 替换为 logger.success(...)
   - 所有 print(f"✗ ...") 或 print(f"⚠ ...") 替换为 logger.warning(...) 或 logger.error(...)
   - 关键文件优先替换：
     - backend/main.py
     - tasks/celery_app.py
     - tasks/execute_task.py
     - browser/manager.py
     - backend/models/database.py
     - backend/services/execute_service.py
   
4. 在 backend/main.py 的 startup 中导入 backend.logging_config 触发初始化

5. 为 Celery Worker 在 tasks/celery_app.py 的 初始化Worker环境() 中也导入日志配置

6. 在 execute_task.py 中为每个批次执行绑定 trace_id = batch_id[:8]，实现链路追踪

验收方式：
- 启动后端，检查 data/logs/ 目录下生成 app_*.log 和 error_*.log
- 执行一个任务，验证日志中包含 trace_id
- 检查全项目无残留 print()（grep -rn "print(" --include="*.py" 结果应为 0）
- 验证日志文件超过 50MB 后自动轮转
​
指令 3：依赖版本锁定（问题 7）
任务目标：为 requirements.txt 中的所有依赖添加精确版本锁定，并生成 requirements-lock.txt。

需要修改的文件：
- requirements.txt

具体实现要点：

1. 将 requirements.txt 更新为以下内容（版本号基于当前最新稳定版，请在执行时用 pip show 确认实际安装版本）：

​
fastapi>=0.115.0,<1.0
uvicorn[standard]>=0.32.0,<1.0
playwright>=1.49.0,<2.0
celery>=5.4.0,<6.0
celery-redbeat>=2.2.0,<3.0
redis>=5.2.0,<6.0
httpx>=0.28.0,<1.0
python-dotenv>=1.0.0,<2.0
pydantic>=2.10.0,<3.0
pydantic-settings>=2.7.0,<3.0
aiosqlite>=0.20.0,<1.0
cryptography>=44.0.0,<45.0
nest_asyncio>=1.6.0,<2.0
openpyxl>=3.1.0,<4.0
uiautomation>=2.0.0,<3.0
loguru>=0.7.0,<1.0

2. 将测试依赖拆分到 requirements-dev.txt：
​
pytest>=8.0.0,<9.0
pytest-asyncio>=0.24.0,<1.0

3. 在项目根目录生成完整锁定文件：
​
pip freeze > requirements-lock.txt

4. 在 README 或 docs/ 中说明：
   - 开发安装：pip install -r requirements.txt -r requirements-dev.txt
   - 生产安装：pip install -r requirements-lock.txt

验收方式：
- pip install -r requirements.txt 无冲突
- pip install -r requirements-dev.txt 无冲突
- requirements-lock.txt 中所有包都有精确版本号（==）
​
指令 4：健康检查与监控端点（问题 9）
任务目标：为后端添加完整的健康检查端点和基础监控指标，支持外部监控系统接入。

需要修改/新增的文件：
- 修改 backend/api/system_api.py
- 新增 backend/services/metrics_service.py
- 修改 backend/main.py（添加中间件）

具体实现要点：

1. 修改 backend/api/system_api.py，扩展现有 /api/system/health 端点：
   返回结构化健康信息：
​
{
"status": "healthy | degraded | unhealthy",
"version": "从 pyproject.toml 或 version 读取",
"uptime_seconds": 12345,
"checks": {
"redis": {"status": "ok", "latency_ms": 2.5},
"sqlite": {"status": "ok", "latency_ms": 1.2},
"browser_pool": {"status": "ok", "active": 2, "max": 5},
"celery_workers": {"status": "ok", "count": 1}
},
"timestamp": "2026-03-31T06:00:00+08:00"
}
   - Redis 检查：ping 并记录延迟
   - SQLite 检查：执行 SELECT 1 并记录延迟
   - 浏览器池：从浏览器管理器读取 len(实例集) / MAX_BROWSER_INSTANCES
   - Celery Workers：通过 celery_app.control.ping(timeout=2) 检查活跃 Worker 数

2. 新增 /api/system/metrics 端点（Prometheus 格式可选，先做 JSON）：
​
{
"tasks_total": 1234,
"tasks_success": 1100,
"tasks_failed": 134,
"tasks_running": 3,
"avg_task_duration_ms": 4500,
"browser_instances_active": 2,
"browser_instances_max": 5,
"redis_memory_used_mb": 45.2,
"uptime_seconds": 12345
}

3. 新建 backend/services/metrics_service.py：
   - class 指标服务
   - 使用内存计数器追踪任务执行数量（进程内统计）
   - 启动时间记录用于计算 uptime
   - 提供 记录任务开始() / 记录任务完成(成功: bool, 耗时毫秒: float) 方法
   - 导出单例 指标服务实例

4. 修改 backend/main.py：
   - 添加一个简单的 ASGIMiddleware 记录请求数和响应时间（可选）
   - 在 startup 事件中初始化 指标服务实例
   - 注册 /health 到根路径（无前缀），方便负载均衡探针：
     @app.get("/health")
     async def root_health(): return {"status": "ok"}

验收方式：
- curl http://localhost:8000/health 返回 {"status": "ok"}
- curl http://localhost:8000/api/system/health 返回完整健康信息
- curl http://localhost:8000/api/system/metrics 返回指标数据
- Redis 断开后，health 返回 degraded 状态
​
指令 5：浏览器崩溃自动恢复（问题 10）
任务目标：当浏览器实例意外崩溃或页面全部关闭时，自动重建浏览器上下文并恢复任务执行。

需要修改的文件：
- browser/manager.py
- tasks/execute_task.py
- 新增 browser/recovery.py

具体实现要点：

1. 新建 browser/recovery.py：
​
class 浏览器恢复器:
MAX_RECOVERY_ATTEMPTS = 3
RECOVERY_COOLDOWN_SECONDS = 5
def init(self):
self._恢复计数: dict[str, int] = {}  # 店铺ID -> 连续恢复次数
self._上次恢复时间: dict[str, float] = {}
async def 尝试恢复(self, 管理器, 店铺ID, 店铺配置) -> bool:
"""尝试恢复崩溃的浏览器实例，返回是否恢复成功"""
连续恢复次数 = self._恢复计数.get(店铺ID, 0)
if 连续恢复次数 >= self.MAX_RECOVERY_ATTEMPTS:
logger.error(f"店铺 {店铺ID} 连续恢复 {连续恢复次数} 次均失败，放弃恢复")
return False
await asyncio.sleep(self.RECOVERY_COOLDOWN_SECONDS)
try:
先清理旧实例
if 店铺ID in 管理器.实例集:
try:
await 管理器.关闭店铺(店铺ID)
except Exception:
管理器.实例集.pop(店铺ID, None)
重新打开
await 管理器.打开店铺(店铺ID, 店铺配置)
self._恢复计数[店铺ID] = 0
logger.success(f"店铺 {店铺ID} 浏览器恢复成功")
return True
except Exception as e:
self._恢复计数[店铺ID] = 连续恢复次数 + 1
logger.error(f"店铺 {店铺ID} 浏览器恢复失败: {e}")
return False
def 重置恢复计数(self, 店铺ID):
self._恢复计数.pop(店铺ID, None)
浏览器恢复实例 = 浏览器恢复器()

2. 修改 browser/manager.py：
   - 在 _清理实例 方法中：
     - 记录崩溃事件到 operation_logs（通过 Redis Pub/Sub 异步通知，避免在同步回调中写数据库）
     - 发布 Redis 事件 "browser:crashed" + 店铺ID
   - 新增方法 async def 安全获取页面(self, 店铺ID, 店铺配置=None) -> Page：
     - 先尝试 获取页面(店铺ID)
     - 如果 RuntimeError（页面全部关闭），调用 浏览器恢复实例.尝试恢复()
     - 恢复成功后重新获取页面
     - 恢复失败则 raise

3. 修改 tasks/execute_task.py：
   - 在主进程执行任务的 httpx 调用外层包一层重试：
     - 如果任务失败原因包含"页面已关闭"、"浏览器已断开"、"Target closed"等关键词
     - 且 on_fail 不是 abort
     - 则触发浏览器恢复 + 重试当前步骤（最多 1 次自动恢复重试）

4. 在 base_page.py 的 安全点击/安全填写 等方法中：
   - catch Playwright 的 TargetClosedError
   - 向上抛出带有明确标识的 RuntimeError("浏览器上下文已关闭，需要恢复")

验收方式：
- 单元测试：mock 浏览器崩溃（关闭 BrowserContext），验证恢复器自动重建
- 单元测试：验证连续崩溃 3 次后放弃恢复
- 集成测试：在任务执行中手动关闭浏览器窗口，验证任务自动恢复并继续
- 验证 operation_logs 中有崩溃和恢复记录
​
📋 通用检查清单（适用于以上所有修复）
修复完成后的统一验收清单：

□ 安全：新增的端点（/health, /metrics）不泄露敏感信息
□ 边界：所有新增方法有 try/except 兜底，不因监控/日志代码导致主流程崩溃
□ 测试：每项修复至少 2 个单元测试，总测试数 ≥ 470 passed
□ 文档：AGENTS.md 或 docs/ 中补充新增配置项说明
□ 配置：.env.example 中补充新增环境变量（LOG_LEVEL 已有）
□ 打包：如果新增了 Python 模块，同步更新 backend.spec 的 hiddenimports
□ 向后兼容：所有新功能默认关闭或 graceful degradation，不影响现有流程