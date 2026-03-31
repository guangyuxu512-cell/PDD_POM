需求复述
当前代码中存在一整套"多平台"抽象层（platforms/ 目录、平台注册表、平台选择器、platform API、前端 platform store 等），但实际只有 PDD 一个平台在用，douyin 和 taobao 都是空壳。用户决定 一个框架对应一个平台，复用时整体复制项目换掉 PDD 技能。因此需要彻底删除多平台抽象，让项目回归简洁的单平台模式。
假设与约束
技术栈：Python/FastAPI + Vue 3/Pinia/Tailwind/Headless UI
数据库 shops 表和 flows 表中的 platform 列保留（值固定为 "pdd"），不做 DB 迁移
前端去掉平台选择器，所有页面默认就是 PDD
不改动 pages/、pdd_selectors/、tasks/、browser/ 的内部文件
Step 1：删除整个 platforms/ 目录
操作：
  rm -rf platforms/

删除的文件清单：
  platforms/__init__.py
  platforms/base/__init__.py
  platforms/base/base_platform.py      ← 平台基类 + 注册表
  platforms/pdd/__init__.py
  platforms/pdd/platform.py            ← PDD 平台注册
  platforms/douyin/__init__.py
  platforms/douyin/platform.py         ← 抖音空壳
  platforms/taobao/__init__.py
  platforms/taobao/platform.py         ← 淘宝空壳

验收：
  项目根目录不再有 platforms/ 文件夹
  grep -rn "from platforms" . --include="*.py" → 列出所有待修复引用（Step 2 处理）
​
Step 2：删除后端 platform_api.py，清理路由注册
文件删除：
  rm backend/api/platform_api.py

文件修改：backend/api/router.py
  找到 platform_api 的 import 和 include_router 行，删除。
  示例：
    旧: from backend.api.platform_api import 路由 as 平台路由
    旧: app.include_router(平台路由)
    → 整行删除

  同时删除 router.py 中任何 `import platforms` 的行。

验收：
  python -c "from backend.api.router import *"  → 不报错
  curl http://localhost:8000/api/platforms       → 404（接口不存在了）
​
Step 3：清理后端所有 import platforms 引用
搜索命令：
  grep -rn "import platforms\|from platforms" . --include="*.py"

预期只有以下位置引用了 platforms：
  1. backend/api/platform_api.py        ← 已在 Step 2 删除
  2. platforms/ 内部文件                 ← 已在 Step 1 删除

如果还有其他文件引用了 platforms，逐一删除对应的 import 行。
如果有代码调用了 get_platform() 或 list_platforms()，替换为硬编码的 PDD 信息：
  例如：
    旧: from platforms.base.base_platform import get_platform
         platform = get_platform(shop.platform)
         login_url = platform.login_url
    新: login_url = "https://mms.pinduoduo.com/login"

验收：
  grep -rn "from platforms\|import platforms" . --include="*.py" → 零匹配
​
Step 4：清理后端 model 中 platform 字段的动态逻辑（保留列，固定值）
文件：backend/models/shop_model.py
  不删 platform 字段和数据库列，但确认默认值固定为 "pdd"。
  当前已经是 平台: str = "pdd"，无需改动。✅

文件：backend/models/flow_model.py
  同上，平台: str = "pdd" 已固定。✅

文件：backend/api/shop_api.py
  检查创建店铺接口，看是否从请求体读取 platform 参数。
  如果有动态赋值，改为固定：
    旧: platform = body.get("platform", "pdd")
    新: platform = "pdd"  # 单平台模式，固定值

验收：
  创建一个店铺 → platform 字段为 "pdd"
​
Step 5：删除前端 platform store 和 platform API
文件删除：
  rm frontend/src/stores/platform.ts
  rm frontend/src/api/platforms.ts

文件修改：frontend/src/api/types.ts
  删除 Platform interface：
    旧:
    export interface Platform {
      id: string
      name: string
      icon: string
    }
    → 整块删除

验收：
  这两个文件不存在了
  types.ts 中不再有 Platform 接口
​
Step 6：清理 ShopManage.vue — 去掉平台选择器
文件：frontend/src/views/ShopManage.vue

<script> 部分删除：
  1. 删除 import { usePlatformStore } from '../stores/platform'
  2. 删除 import { Listbox, ListboxButton, ListboxOption, ListboxOptions } from '@headlessui/vue'
     （注意：如果弹窗里"所属平台"的 Listbox 也要删，那 Headless UI import 可能还被其他组件用。
       但如果此文件唯一使用，可以删。检查后决定。）
  3. 删除 const platformStore = usePlatformStore()
  4. 删除 const formPlatform = ref(...)
  5. 删除 const selectedFormPlatform = computed(...)
  6. 删除 const currentPlatformLabel = computed(...)
  7. 修改 loadShops()：
     旧: const result = await listShops(platformStore.currentPlatform)
     新: const result = await listShops()
  8. 修改 openAddModal()：
     删除: formPlatform.value = platformStore.currentPlatform
  9. 修改 openEditModal()：
     删除: formPlatform.value = shop.platform || 'pdd'
  10. 修改 handleSave()：
      删除: payload.platform = formPlatform.value
      （创建店铺时后端已固定 platform="pdd"）
  11. 删除 onMounted 中的 platformStore.loadPlatforms()：
      旧: void platformStore.loadPlatforms().then(loadShops)
      新: void loadShops()
  12. 删除 watch(() => platformStore.currentPlatform, ...)

<template> 部分删除：
  1. 删除标题区右侧的平台选择 Listbox 整块（从 <Listbox :model-value="platformStore.currentPlatform" ...> 到对应的 </Listbox>）
  2. 删除副标题文案中"按平台管理"：
     旧: 按平台管理店铺账号、代理与邮箱连接配置。
     新: 管理店铺账号、代理与邮箱连接配置。
  3. 弹窗中"所属平台"字段 — 整个 <div class="space-y-2"> + <label>所属平台</label> + 内部的 Listbox 全部删除
  4. "基本信息"网格从 md:grid-cols-2 改为 md:grid-cols-1（因为去掉了平台下拉，只剩"店铺名称"）
     或者把"店铺名称"改成独占一行即可

验收：
  - 店铺管理页无平台下拉选择器
  - 新增/编辑弹窗无"所属平台"字段
  - 加载店铺不传 platform 参数
  - 页面正常渲染
​
Step 7：清理 shops.ts API — 去掉 platform 参数
文件：frontend/src/api/shops.ts

修改 listShops：
  旧:
  export function listShops(platform?: string) {
    const params = new URLSearchParams()
    if (platform?.trim()) {
      params.set('platform', platform.trim())
    }
    const query = params.toString()
    return api.get<PaginatedList<Shop>>(`/api/shops${query ? `?${query}` : ''}`)
  }

  新:
  export function listShops() {
    return api.get<PaginatedList<Shop>>('/api/shops')
  }

修改 ShopPayload（在 types.ts 中）：
  删除 platform? 可选字段：
  旧: platform?: string
  → 删除该行

修改 Shop 接口（在 types.ts 中）：
  platform 字段保留（后端还会返回），但不需要用户填写。
  不改。✅

验收：
  listShops() 不带任何查询参数
  创建店铺时不传 platform
​
Step 8：清理 BatchExecute.vue — 去掉 platform 相关逻辑
文件：frontend/src/views/BatchExecute.vue

检查 loadReferenceData()：
  当前代码：const [flowResponse, shopResponse, availableTasks] = await Promise.all([
    listFlows(),
    listShops(),          ← 已经不传 platform 了（Step 7 修了签名后自动生效）
    listAvailableTasks(),
  ])

  确认 listShops() 调用无参数即可。✅

如果有其他平台筛选逻辑，搜索 "platform" 关键字全部清理。
当前 BatchExecute.vue 中没有直接的 platform 过滤逻辑。✅

验收：
  批量执行页正常加载所有店铺，无 platform 过滤
​
Step 9：全局搜索清理残留引用
前端搜索：
  grep -rn "platformStore\|usePlatformStore\|listPlatforms\|platform\.ts\|Platform" frontend/src/ --include="*.ts" --include="*.vue"

  逐一检查结果：
  - 如果是 import → 删除
  - 如果是 platformStore.xxx 调用 → 删除或替换
  - 如果是 Platform 类型引用 → 删除

后端搜索：
  grep -rn "platform_api\|from platforms\|import platforms\|get_platform\|list_platforms\|BasePlatform\|register_platform" . --include="*.py"

  逐一检查，全部清理。

验收：
  前端：grep "platformStore\|usePlatformStore\|listPlatforms" → 零匹配
  后端：grep "from platforms\|import platforms\|platform_api" → 零匹配
  全面编译/启动无报错
​
Step 10：清理 pyproject.toml / requirements.txt / 打包配置
检查打包配置（如 backend.spec 或 build script）：
  如果有 hiddenimports 包含 platforms.xxx，删除：
    旧: hiddenimports=['platforms', 'platforms.pdd', 'platforms.douyin', ...]
    新: 删除所有 platforms 相关 hiddenimport

检查 AGENTS.md：
  如果提到 platforms 目录结构或多平台架构，更新描述为单平台模式。

验收：
  打包配置中无 platforms 相关引用
​
最终验收 Checklist
[ ] platforms/ 目录已完全删除
[ ] backend/api/platform_api.py 已删除
[ ] router.py 中无 platform 路由注册
[ ] 后端无 `from platforms` 或 `import platforms` 引用
[ ] 前端 stores/platform.ts 已删除
[ ] 前端 api/platforms.ts 已删除
[ ] types.ts 中 Platform 接口已删除
[ ] ShopManage.vue 无平台选择器、无 platformStore 引用
[ ] shops.ts listShops() 无 platform 参数
[ ] BatchExecute.vue 无 platform 过滤
[ ] 全局搜索 "platformStore|usePlatformStore|listPlatforms|from platforms" → 零匹配
[ ] python main.py 启动无报错
[ ] npm run dev 启动无报错
[ ] 创建店铺 → platform="pdd" ✅
[ ] 打包配置无 platforms 引用