需求复述
打包 exe 时自动脱敏，不携带数据库、日志、cookie 等运行时数据
新电脑首次运行自动初始化空数据库
所有配置项（包括原来放在 .env 的）全部通过前端"系统设置"页面管理，保存到数据库的 settings 表
不再需要 .env 文件
假设与约束
技术栈：Python/FastAPI/SQLite + Vue 3/Pinia/Tailwind/Headless UI + Electron
配置分两类：应用配置（端口、并发数等）和敏感配置（API Key、密码等），全存 SQLite
敏感配置在数据库中加密存储（AES），密钥由 exe 首次运行时自动生成，保存在 data/.secret_key
前端设置页面对敏感字段做 •••••••• 脱敏显示
Step 1：创建 settings 数据库表和 model
新建文件：backend/models/settings_model.py

表结构：
CREATE TABLE IF NOT EXISTS settings (
    key       TEXT PRIMARY KEY,
    value     TEXT,
    category  TEXT NOT NULL DEFAULT 'general',   -- 分类：general / celery / notification / security
    encrypted INTEGER NOT NULL DEFAULT 0,        -- 0=明文, 1=加密
    label     TEXT,                               -- 前端显示名称
    hint      TEXT,                               -- 前端提示文案
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

默认初始化数据（首次建表时 INSERT）：
| key                    | category     | encrypted | label          | default value    |
|------------------------|-------------|-----------|----------------|------------------|
| app_port               | general      | 0         | 应用端口        | 8000             |
| max_concurrency        | general      | 0         | 最大并发数      | 5                |
| browser_headless       | general      | 0         | 无头浏览器模式  | false            |
| celery_broker_url      | celery       | 0         | Celery Broker   | redis://localhost:6379/0 |
| celery_result_backend  | celery       | 0         | Celery Backend  | redis://localhost:6379/1 |
| feishu_webhook_url     | notification | 1         | 飞书 Webhook    |                  |
| feishu_secret          | notification | 1         | 飞书签名密钥    |                  |
| default_proxy          | general      | 0         | 默认代理地址    |                  |
| log_level              | general      | 0         | 日志级别        | INFO             |
| auto_restart_browser   | general      | 0         | 浏览器崩溃自动重启 | true          |

Model 类（中文风格，跟你现有 model 保持一致）：

@dataclass(slots=True)
class 设置模型:
    键名: str
    值: str | None = None
    分类: str = "general"
    加密: int = 0
    标签: str | None = None
    提示: str | None = None
    创建时间: datetime | None = None
    更新时间: datetime | None = None

    字段映射 = {
        "键名": "key",
        "值": "value",
        "分类": "category",
        "加密": "encrypted",
        "标签": "label",
        "提示": "hint",
        "创建时间": "created_at",
        "更新时间": "updated_at",
    }

验收：
  数据库初始化后 settings 表存在，有上述默认行
  python -c "from backend.models.settings_model import *" → 无报错
​
Step 2：创建加密工具模块
新建文件：backend/utils/crypto.py

功能：
  - 首次运行自动生成 256-bit AES 密钥，保存到 data/.secret_key
  - 提供 encrypt_value(plaintext) → ciphertext 和 decrypt_value(ciphertext) → plaintext
  - 使用 Fernet (cryptography 库) 对称加密

代码要点：

from cryptography.fernet import Fernet
from backend.config import APP_DATA_DIR

SECRET_KEY_PATH = APP_DATA_DIR / ".secret_key"

def _load_or_create_key() -> bytes:
    """加载或首次生成加密密钥。"""
    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_bytes()
    key = Fernet.generate_key()
    SECRET_KEY_PATH.write_bytes(key)
    return key

_fernet = Fernet(_load_or_create_key())

def encrypt_value(plaintext: str) -> str:
    """加密明文，返回 base64 密文。"""
    return _fernet.encrypt(plaintext.encode()).decode()

def decrypt_value(ciphertext: str) -> str:
    """解密密文，返回明文。"""
    return _fernet.decrypt(ciphertext.encode()).decode()

依赖添加：
  requirements.txt 中加入: cryptography>=42.0

.gitignore 中加入:
  data/.secret_key

验收：
  from backend.utils.crypto import encrypt_value, decrypt_value
  assert decrypt_value(encrypt_value("hello")) == "hello"
  data/.secret_key 文件自动生成
​
Step 3：创建 settings API（后端 CRUD）
新建文件：backend/api/settings_api.py

路由 = APIRouter(prefix="/api/settings", tags=["系统设置"])

# GET /api/settings
# 返回所有配置项，按 category 分组
# 加密字段返回 value=null（不泄露密文），但返回 has_value=true/false

@路由.get("", summary="获取所有配置")
async def 获取配置列表():
    rows = db.execute("SELECT * FROM settings ORDER BY category, key").fetchall()
    结果 = []
    for row in rows:
        item = dict(row)
        if item["encrypted"] and item["value"]:
            item["has_value"] = True
            item["value"] = None  # 不返回密文给前端
        else:
            item["has_value"] = bool(item["value"])
        结果.append(item)
    return 成功(data={"list": 结果})
​
PUT /api/settings/:key
更新单个配置项
@路由.put("/{key}", summary="更新配置")
async def 更新配置(key: str, body: dict):
value = body.get("value")
row = db.execute("SELECT encrypted FROM settings WHERE key = ?", [key]).fetchone()
if not row:
raise HTTPException(404, f"配置项 {key} 不存在")
if row["encrypted"] and value:
value = encrypt_value(value)
db.execute(
"UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
[value, key]
)
db.commit()
return 成功(message="配置已更新")
POST /api/settings/batch
批量更新（前端保存整个分类时用）
@路由.post("/batch", summary="批量更新配置")
async def 批量更新(body: dict):
items = body.get("items", [])  # [{"key": "xxx", "value": "yyy"}, ...]
for item in items:
key = item["key"]
value = item.get("value")
row = db.execute("SELECT encrypted FROM settings WHERE key = ?", [key]).fetchone()
if not row:
continue
如果是加密字段且 value 为 None 或空字符串，跳过（不覆盖已有值）
if row["encrypted"] and not value:
continue
if row["encrypted"] and value:
value = encrypt_value(value)
db.execute(
"UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
[value, key]
)
db.commit()
return 成功(message=f"已更新 {len(items)} 项配置")
注册路由：
在 backend/api/router.py 中添加:
from backend.api.settings_api import 路由 as 设置路由
app.include_router(设置路由)
验收：
GET /api/settings → 返回所有配置项，加密字段 value=null
PUT /api/settings/feishu_webhook_url body={"value":"https://xxx"} → 数据库中存密文
GET 后 feishu_webhook_url 的 has_value=true, value=null

---

### Step 4：创建 `get_setting()` 后端读取函数

​
新建文件：backend/utils/settings.py
这个函数替代所有 os.environ.get() 和 .env 读取：
from backend.utils.crypto import decrypt_value
def get_setting(key: str, default: str | None = None) -> str | None:
"""
从数据库读取配置值。加密字段自动解密。
替代 os.environ.get()，所有配置统一从这里读。
"""
row = db.execute(
"SELECT value, encrypted FROM settings WHERE key = ?", [key]
).fetchone()
if not row or not row["value"]:
return default
if row["encrypted"]:
try:
return decrypt_value(row["value"])
except Exception:
return default
return row["value"]
便捷函数
def get_setting_bool(key: str, default: bool = False) -> bool:
val = get_setting(key)
if val is None:
return default
return val.lower() in ("true", "1", "yes")
def get_setting_int(key: str, default: int = 0) -> int:
val = get_setting(key)
if val is None:
return default
try:
return int(val)
except ValueError:
return default
全局替换 — 搜索所有 os.environ.get / os.getenv / dotenv 调用：
grep -rn "os.environ|os.getenv|dotenv|load_dotenv" . --include="*.py"
逐一替换为 get_setting()：
旧: BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
新: BROKER_URL = get_setting("celery_broker_url", "redis://localhost:6379/0")
旧: FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK_URL")
新: FEISHU_WEBHOOK = get_setting("feishu_webhook_url")
删除 .env 相关：
删除 .env 文件（如果存在）
删除 load_dotenv() 调用
从 requirements.txt 删除 python-dotenv（如果有）
验收：
grep -rn "os.environ|os.getenv|load_dotenv|dotenv" . --include="*.py" → 零匹配
所有配置通过 get_setting() 读取

---

### Step 5：创建前端系统设置页面

​
新建文件：frontend/src/api/settings.ts
export function listSettings() {
return api.get<{ list: SettingItem[] }>('/api/settings')
}
export function updateSetting(key: string, value: string | null) {
return api.put(/api/settings/${key}, { value })
}
export function batchUpdateSettings(items: Array<{ key: string; value: string | null }>) {
return api.post('/api/settings/batch', { items })
}
新增类型（frontend/src/api/types.ts）：
export interface SettingItem {
key: string
value: string | null
category: string
encrypted: number
has_value: boolean
label: string | null
hint: string | null
}
新建文件：frontend/src/views/SystemSettings.vue
页面结构：
按 category 分成 Tab 或折叠面板：通用设置 / Celery 配置 / 通知配置 / 安全配置
每个配置项一行：左边 label + hint，右边 input
加密字段（encrypted=1）：
有值时显示 placeholder="••••••••（已设置，留空不修改）"
无值时显示 placeholder="请输入..."
type="password"
非加密字段：直接显示当前值
底部"保存"按钮，调用 batchUpdateSettings
<template> 骨架：
<div class="space-y-6">
<header class="space-y-1">
<h1 class="text-2xl font-semibold text-gray-900">系统设置</h1>
<p class="text-sm text-gray-500">应用运行参数配置，修改后点击保存立即生效。</p>
</header>
<!-- Tab 按分类切换 -->
<div class="flex gap-1 rounded-md bg-gray-100 p-0.5">
<button v-for="cat in categories" :key="cat.key"
:class="['flex-1 rounded-md px-3 py-2 text-sm transition',
activeCategory === cat.key ? 'bg-white font-medium text-gray-900 shadow-sm' : 'text-gray-500']"
@click="activeCategory = cat.key">
cat.label 
</button>
</div>
<!-- 配置项列表 -->
<section class="rounded-md border border-brand-200/50 bg-white p-5 shadow-sm">
<div v-for="item in filteredSettings" :key="item.key" class="grid gap-4 border-b border-gray-100 py-4 md:grid-cols-[1fr_1.5fr]">
<div>
<label class="text-sm font-medium text-gray-900"> item.label || item.key </label>
<p v-if="item.hint" class="text-xs text-gray-500"> item.hint </p>
</div>
<input
v-model="formData[item.key]"
:type="item.encrypted ? 'password' : 'text'"
:placeholder="item.encrypted && item.has_value ? '••••••••（已设置，留空不修改）' : '请输入...'"
class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
/>
</div>
</section>
<div class="flex justify-end">
<button @click="handleSave" :disabled="isSaving"
class="rounded-md bg-brand-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700">
isSaving ? '保存中...' : '保存设置' 
</button>
</div>
</div>
分类定义：
const categories = [
{ key: 'general',      label: '通用设置' },
{ key: 'celery',       label: '任务队列' },
{ key: 'notification', label: '通知配置' },
]
保存逻辑：
async function handleSave() {
const items = filteredSettings
.filter(item => {
const val = formData[item.key]
// 加密字段如果为空不提交（保留原值）
if (item.encrypted && !val) return false
return true
})
.map(item => ({ key: item.key, value: formData[item.key] || null }))
await batchUpdateSettings(items)
toast.success('设置已保存')
await loadSettings()  // 刷新
}
注册路由（frontend/src/router/index.ts）：
{ path: '/settings', name: 'SystemSettings', component: () => import('../views/SystemSettings.vue') }
侧边栏添加入口：在导航菜单最下方加"系统设置"。
验收：
前端 /settings 页面正常显示所有配置项
修改非加密项 → 保存 → 刷新后值已更新
修改加密项（如飞书 Webhook）→ 保存 → 刷新后显示"已设置"占位符
留空加密项 → 保存 → 不会覆盖已有值

---

### Step 6：数据目录规范化 + 路径配置

​
新建/修改文件：backend/config.py
import sys
from pathlib import Path
def get_app_data_dir() -> Path:
if getattr(sys, "frozen", False):
base = Path(sys.executable).parent
else:
base = Path(file).resolve().parent.parent
data_dir = base / "data"
data_dir.mkdir(exist_ok=True)
return data_dir
APP_DATA_DIR      = get_app_data_dir()
DB_PATH           = APP_DATA_DIR / "app.db"
LOG_DIR           = APP_DATA_DIR / "logs"
BROWSER_PROFILES  = APP_DATA_DIR / "browser_profiles"
COOKIE_DIR        = APP_DATA_DIR / "cookies"
确保子目录存在
for d in [LOG_DIR, BROWSER_PROFILES, COOKIE_DIR]:
d.mkdir(exist_ok=True)
全局替换所有硬编码路径：
grep -rn "app.db|pdd_pom.db|.dbb" . --include="*.py" | grep -v pycache
所有数据库路径 → DB_PATH
所有日志路径 → LOG_DIR
所有浏览器 profile 路径 → BROWSER_PROFILES
验收：
开发模式：data/ 在项目根目录
打包模式：data/ 在 exe 同级目录
首次运行自动创建 data/、data/logs/、data/browser_profiles/、data/cookies/

---

### Step 7：打包前清理脚本

​
新建文件：scripts/clean_for_dist.py
import shutil
from pathlib import Path
PROJECT_ROOT = Path(file).resolve().parent.parent
CLEAN_DIRS = [
PROJECT_ROOT / "data",
PROJECT_ROOT / "dist",
PROJECT_ROOT / "build",
]
CLEAN_PATTERNS = [
".db", ".db-journal", "*.db-wal",
".env", "*.log", ".secret_key",
]
def clean():
for d in CLEAN_DIRS:
if d.exists():
shutil.rmtree(d)
print(f"✅ 已删除目录: {d}")
for pattern in CLEAN_PATTERNS:
for f in PROJECT_ROOT.rglob(pattern):
if ".git" not in f.parts and "node_modules" not in f.parts:
f.unlink()
print(f"✅ 已删除文件: {f}")
print("n🎉 脱敏清理完成，可以打包了")
if name == "main":
clean()
打包流程（更新 README 或 AGENTS.md）：
python scripts/clean_for_dist.py     ← 自动脱敏
pyinstaller backend.spec             ← 打包
分发 dist/ 目录                       ← 干净的 exe
验收：
运行 clean_for_dist.py 后 data/ 目录不存在
打包后 dist/ 中不包含任何 .db / .env / .secret_key / .log

---

### Step 8：更新 PyInstaller .spec 排除数据

​
文件：backend.spec
datas 列表中确认：
只包含 frontend/dist 静态资源
不包含 data/、logs/、*.db、.env、.secret_key
如果有 hiddenimports 中的 platforms 相关（已在上个清理任务中删），确认已清理。
添加 cryptography 到 hiddenimports（如果需要）：
hiddenimports=['cryptography', 'cryptography.fernet', ...]
验收：
打包后的 exe 解压/检查不含敏感文件

---

### Step 9：更新 .gitignore

​
添加以下条目：
===== 运行时数据 =====
data/
*.db
*.db-journal
*.db-wal
.secret_key
.env
===== 日志 =====
logs/
*.log
===== 浏览器数据 =====
browser_profiles/
cookies/
===== 打包 =====
dist/
build/

---

### Step 10：删除 .env 及 dotenv 依赖

​
操作：
rm -f .env .env.example .env.local
从 requirements.txt 删除 python-dotenv（如果存在）
搜索并删除所有 load_dotenv() 调用：
grep -rn "load_dotenv|from dotenv|import dotenv" . --include="*.py"
→ 逐一删除
验收：
项目中不存在 .env 文件
grep "dotenv" . -r --include=".py" --include=".txt" → 零匹配

---

### 最终验收 Checklist

​
[ ] settings 表已创建，包含所有默认配置项
[ ] backend/utils/crypto.py 加解密工作正常
[ ] backend/api/settings_api.py CRUD 接口正常
[ ] backend/utils/settings.py get_setting() 替代所有 os.environ.get()
[ ] 前端 SystemSettings.vue 页面正常显示和保存
[ ] 加密字段（飞书 Webhook 等）保存后数据库存密文，前端不泄露
[ ] backend/config.py 统一数据目录路径
[ ] scripts/clean_for_dist.py 一键脱敏
[ ] .gitignore 覆盖所有敏感文件
[ ] 无 .env 文件、无 load_dotenv 调用
[ ] 全新电脑运行 exe → 自动创建 data/ + 空数据库 + 空 settings 默认值
[ ] 前端 /settings 修改配置 → 后端立即生效
[ ] 打包产物不含任何 .db / .env / .secret_key / .log

---

### 新建文件总览

| 文件 | 作用 |
|------|------|
| `backend/models/settings_model.py` | settings 表定义 + 模型 |
| `backend/utils/crypto.py` | AES 加解密（Fernet） |
| `backend/utils/settings.py` | `get_setting()` 统一配置读取 |
| `backend/api/settings_api.py` | 配置 CRUD API |
| `backend/config.py` | 数据目录路径统一管理 |
| `scripts/clean_for_dist.py` | 打包前脱敏清理 |
| `frontend/src/api/settings.ts` | 前端设置 API |
| `frontend/src/views/SystemSettings.vue` | 系统设置页面 |

### 修改文件总览

| 文件 | 改动 |
|------|------|
| `backend/api/router.py` | 注册 settings 路由 |
| `backend/database.py` | 初始化时建 settings 表 + 插入默认值 |
| `所有读 os.environ 的文件` | 替换为 `get_setting()` |
| `frontend/src/router/index.ts` | 添加 /settings 路由 |
| `frontend 侧边栏组件` | 添加"系统设置"菜单项 |
| `requirements.txt` | 添加 cryptography，删除 python-dotenv |
| `.gitignore` | 添加 data/ .secret_key 等 |
| `backend.spec` | 确认不打包数据目录 |