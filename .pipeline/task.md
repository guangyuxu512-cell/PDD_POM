Codex 任务 1（续）：数据库 migration — 添加 platform 字段
同样给 flow_model.py（如果有）和 task_logs 相关的 model 添加 platform 字段，逻辑与 shop_model 相同。
验收方式：
启动应用，SQLite 数据库自动执行 migration
执行 SELECT platform FROM shops LIMIT 1; 返回 pdd
现有数据不受影响，所有店铺的 platform 都是 pdd
Codex 任务 2：后端 API 支持 platform 参数
任务目标： 后端 API 增加 platform 过滤和创建店铺时绑定平台。
需要修改的文件：
backend/api/shop_api.py
backend/services/shop_service.py
backend/api/flow_api.py（如有）
backend/services/flow_service.py（如有）
具体实现要点：
创建店铺时支持 platform 参数：
# shop_api.py — 创建店铺接口
# 请求体新增 platform 字段，默认 "pdd"
class 创建店铺请求(BaseModel):
    name: str
    platform: str = "pdd"     # ← 新增
    username: str | None = None
    password: str | None = None
    ...

# shop_service.py — 创建店铺时写入 platform
async def 创建(self, data: dict) -> dict:
    ...
    # INSERT 语句中加入 platform 列
​
列表接口支持 platform 查询参数过滤：
# shop_api.py — 店铺列表接口
@router.get("/shops")
async def 获取店铺列表(platform: str | None = None):
    return await 店铺服务实例.获取列表(platform=platform)

# shop_service.py
async def 获取列表(self, platform: str | None = None):
    where = ""
    params = []
    if platform:
        where = "WHERE platform = ?"
        params.append(platform)
    ...
​
流程列表同理： GET /flows?platform=pdd
新增平台列表接口（简单版）：
# 新文件 backend/api/platform_api.py
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["平台"])

# 暂时硬编码，后续迁移到 platforms/ 注册制
SUPPORTED_PLATFORMS = [
    {"id": "pdd", "name": "拼多多", "icon": "🟠"},
    # {"id": "douyin", "name": "抖音", "icon": "🎵"},  # 以后开启
]

@router.get("/platforms")
async def 获取平台列表():
    return {"list": SUPPORTED_PLATFORMS}
​
在 main.py 中注册这个 router。
验收方式：
POST /api/shops body 里传 {"name": "测试", "platform": "pdd"} → 创建成功，数据库 platform = pdd
GET /api/shops?platform=pdd → 只返回 pdd 的店铺
GET /api/platforms → 返回平台列表
不传 platform 参数时，行为与之前完全一致（默认 pdd）
Codex 任务 3：前端全局平台切换器 + 店铺表单绑定平台
任务目标： 添加全局平台选择器，店铺管理页面按平台过滤，新建店铺时绑定平台。
需要修改/新增的文件：
frontend/src/stores/platform.ts（新增）
frontend/src/components/PlatformSelector.vue（新增）
frontend/src/api/platforms.ts（新增）
frontend/src/api/types.ts（修改）
frontend/src/views/ShopManage.vue（修改）
frontend/src/App.vue 或侧边栏布局组件（修改）
具体实现要点：
新建 Pinia store 管理当前选中平台：
// frontend/src/stores/platform.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Platform {
  id: string
  name: string
  icon: string
}

export const usePlatformStore = defineStore('platform', () => {
  const platforms = ref<Platform[]>([])
  const currentPlatform = ref<string>(
    localStorage.getItem('selectedPlatform') || 'pdd'
  )

  async function loadPlatforms() {
    const res = await fetch('/api/platforms')
    const data = await res.json()
    platforms.value = data.list
  }

  function setPlatform(id: string) {
    currentPlatform.value = id
    localStorage.setItem('selectedPlatform', id)
  }

  return { platforms, currentPlatform, loadPlatforms, setPlatform }
})
​
新建平台选择器组件：
<!-- frontend/src/components/PlatformSelector.vue -->
<template>
  <div class="platform-selector">
    <select :value="store.currentPlatform" @change="onChange">
      <option
        v-for="p in store.platforms"
        :key="p.id"
        :value="p.id"
      >
         p.icon   p.name 
      </option>
    </select>
  </div>
</template>
​
样式匹配你现在的深色主题（background: #0f3460, color: #e0e0e0）。
放到侧边栏或顶栏： 在 App.vue 或你的 layout 组件的 header 区域插入 <PlatformSelector />。
修改 ShopManage.vue：
import { usePlatformStore } from '../stores/platform'
import { watch } from 'vue'

const platformStore = usePlatformStore()

async function loadShops() {
  const result = await listShops(platformStore.currentPlatform)
  shops.value = result.list
}

// 平台切换时自动刷新
watch(() => platformStore.currentPlatform, () => {
  void loadShops()
})
​
修改 api/shops.ts：
export async function listShops(platform?: string) {
  const params = platform ? `?platform=${platform}` : ''
  const res = await fetch(`/api/shops${params}`)
  ...
}
​
新建店铺表单： 不需要让用户手动选平台，自动使用当前选中的平台：
// ShopManage.vue — handleSave() 中
const payload = buildPayload()
if (!editingShop.value) {
  payload.platform = platformStore.currentPlatform  // ← 自动绑定
}
​
修改 api/types.ts：
export interface Shop {
  id: string
  name: string
  platform: string    // ← 新增
  username?: string
  ...
}

export interface ShopPayload {
  name: string
  platform?: string   // ← 新增
  ...
}
​
验收方式：
页面顶部/侧边栏出现平台下拉框，默认选中"🟠 拼多多"
切换平台时，店铺列表自动刷新
新建店铺时，不需要手动选平台，自动使用当前选中平台
刷新页面后，选中的平台保持不变（localStorage 持久化）
现有数据全部正常显示
Codex 任务 4：平台基类接口（为多平台做准备）
任务目标： 创建 platforms/ 目录和基类定义，PDD 平台注册。这一步不迁移现有代码，只建立接口框架。
需要新增的文件：
platforms/__init__.py
platforms/base/__init__.py
platforms/base/base_platform.py
platforms/pdd/__init__.py
platforms/pdd/platform.py
具体实现要点：
platforms/base/base_platform.py：
from abc import ABC, abstractmethod
from typing import Dict, List

# 平台注册表（全局）
_平台注册表: Dict[str, "BasePlatform"] = {}


def register_platform(platform_id: str):
    """装饰器：注册一个平台到全局注册表"""
    def decorator(cls):
        _平台注册表[platform_id] = cls()
        return cls
    return decorator


def get_platform(platform_id: str) -> "BasePlatform":
    """根据 ID 获取平台实例"""
    if platform_id not in _平台注册表:
        raise ValueError(f"未注册的平台: {platform_id}")
    return _平台注册表[platform_id]


def list_platforms() -> List[Dict[str, str]]:
    """列出所有已注册平台"""
    return [
        {
            "id": pid,
            "name": p.display_name,
            "icon": p.icon,
        }
        for pid, p in _平台注册表.items()
    ]


class BasePlatform(ABC):
    """平台基类 — 每个新平台必须实现这些方法"""
    
    @property
    @abstractmethod
    def platform_id(self) -> str:
        """平台唯一标识，如 'pdd', 'douyin'"""
        ...
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """平台显示名称，如 '拼多多'"""
        ...
    
    @property
    def icon(self) -> str:
        """平台图标 emoji"""
        return "🏪"
    
    @property
    @abstractmethod
    def login_url(self) -> str:
        """平台登录页 URL"""
        ...
    
    @abstractmethod
    def get_available_tasks(self) -> List[str]:
        """返回该平台支持的任务名称列表"""
        ...
​
platforms/pdd/platform.py：
from platforms.base.base_platform import BasePlatform, register_platform


@register_platform("pdd")
class PddPlatform(BasePlatform):
    
    @property
    def platform_id(self) -> str:
        return "pdd"
    
    @property
    def display_name(self) -> str:
        return "拼多多"
    
    @property
    def icon(self) -> str:
        return "🟠"
    
    @property
    def login_url(self) -> str:
        return "https://mms.pinduoduo.com/login"
    
    def get_available_tasks(self) -> list[str]:
        # 暂时硬编码，后续从 tasks/ 注册表按 platform 过滤
        return [
            "登录",
            "售后处理",
            "发布相似商品",
            "发布换图商品",
            "限时限量",
            "设置推广",
        ]
​
platforms/__init__.py：
# 导入所有平台，触发 @register_platform 注册
import platforms.pdd  # noqa: F401
​
改造 platform_api.py（任务 2 中创建的）使用注册表：
from platforms.base.base_platform import list_platforms

@router.get("/platforms")
async def 获取平台列表():
    return {"list": list_platforms()}
​
验收方式：
from platforms.base.base_platform import get_platform, list_platforms
get_platform("pdd").display_name → "拼多多"
get_platform("pdd").login_url → "https://mms.pinduoduo.com/login"
list_platforms() → [{"id": "pdd", "name": "拼多多", "icon": "🟠"}]
get_platform("douyin") → ValueError: 未注册的平台: douyin
现有功能不受任何影响
检查清单
项目
说明
✅ 数据兼容
DEFAULT 'pdd' 保证现有数据无损
✅ API 兼容
不传 platform 参数时行为不变
✅ 前端兼容
localStorage 默认 pdd，首次加载无影响
✅ Migration 安全
ALTER TABLE 用 try/except 包装，重复执行不报错
✅ 无现有代码迁移
这 4 个任务都是增量添加，不移动/重命名现有文件
⚠️ 后续做
把 pages/、pdd_selectors/、tasks/ 按平台迁移（等第二个平台再做）