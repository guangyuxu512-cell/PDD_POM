任务目标
修复店铺管理（及所有表格页面）字段与表头错位
集成冷灰蓝配色方案
修复侧栏字体偏小
平台选择器改为下拉框
重写未迁移的 task-params 子组件
删除所有旧 CSS 文件
需要修改的文件
frontend/src/style.css — 注册 brand 色板
frontend/src/App.vue — 侧栏深色 + 字体加大
frontend/src/views/ShopManage.vue — 表格对齐 + 下拉框
frontend/src/components/ShopCard.vue — 对齐修复
frontend/src/components/Modal.vue — 配色
frontend/src/components/StatusBadge.vue — 配色
frontend/src/views/task-params/FlowParamsTab.vue — 全量 Tailwind 重写
frontend/src/views/task-params/TaskListTab.vue — 全量 Tailwind 重写
frontend/src/views/task-params/TaskResultTab.vue — 全量 Tailwind 重写
frontend/src/views/task-params/JsonTooltip.vue — Tailwind 重写
所有已重写页面（FlowManage / ScheduleManage / Settings / TaskMonitor / LogViewer / BatchExecute / BrowserManager / TaskParamsManage）— 全局换色
需要删除的文件
frontend/src/views/task-params/FlowParamsTab.css
frontend/src/views/task-params/TaskListTab.css
frontend/src/views/task-params/TaskResultTab.css
frontend/src/views/task-params/TaskParamsManage.css
Step 1：style.css — 注册色板（Tailwind v4 用 @theme）
@import "tailwindcss";

@theme {
  --color-brand-950: #06141B;
  --color-brand-900: #11212D;
  --color-brand-700: #253745;
  --color-brand-500: #4A5C6A;
  --color-brand-300: #9BA8AB;
  --color-brand-100: #CCD0CF;
}

@layer base {
  body {
    font-family:
      'Inter',
      -apple-system,
      BlinkMacSystemFont,
      'Segoe UI',
      'PingFang SC',
      'Hiragino Sans GB',
      'Microsoft YaHei',
      sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}
​
验收： brand-950、brand-900 等 class 可用。
Step 2：App.vue — 深色侧栏 + 字体加大 + 页面底色
<template>
  <div class="flex h-screen bg-brand-100">
    <!-- ↑ 页面底色 #CCD0CF -->

    <aside class="flex w-56 flex-shrink-0 flex-col bg-brand-950">
      <!-- ↑ 侧栏底色 #06141B，宽度 w-52→w-56 -->

      <div class="px-4 py-5">
        <span class="text-base font-semibold tracking-tight text-white">
          自动化工作台
        </span>
        <!-- ↑ text-sm→text-base，text-gray-900→text-white -->
      </div>

      <nav class="flex-1 space-y-0.5 px-3">
        <!-- ↑ px-2→px-3 给更多呼吸感 -->
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors"
          :class="
            route.path.startsWith(item.path)
              ? 'bg-brand-900 font-medium text-white'
              : 'text-brand-300 hover:bg-brand-900/50 hover:text-white'
          "
        >
          <!-- ↑ py-1.5→py-2 增加行高
               选中态：bg-gray-100→bg-brand-900 text-gray-900→text-white
               未选中：text-gray-500→text-brand-300 -->
          <span class="text-base leading-none"> item.icon </span>
          <span> item.label </span>
        </router-link>
      </nav>
    </aside>

    <main class="flex-1 overflow-auto bg-brand-100 p-6">
      <!-- ↑ bg-gray-50→bg-brand-100，增加 p-6 内边距 -->
      <router-view />
    </main>

    <Toast />
  </div>
</template>
​
验收： 侧栏深色 #06141B，菜单 text-sm（14px）+ py-2 不再偏小，选中态 #11212D。页面底色 #CCD0CF。
Step 3：ShopManage.vue — 用 <table> 替换 grid 彻底修复对齐 + 平台下拉框
错位根因： 表头用 <div class="grid-cols-[...]">，行用 ShopCard 组件的另一个 grid。两者虽然定义相同，但 minmax + 复杂内容会导致宽度计算不一致。
解决方案：把整个店铺列表改成真正的 <table>，表头和行自然对齐。
<!-- 平台选择器：改为下拉框 -->
<div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
  <div class="space-y-1">
    <h1 class="text-2xl font-semibold text-gray-900">店铺管理</h1>
    <p class="text-sm text-brand-500">按平台管理店铺账号、代理与邮箱连接配置。</p>
  </div>

  <div class="flex items-center gap-3">
    <!-- 平台下拉框（替代 pill buttons） -->
    <Listbox :model-value="platformStore.currentPlatform"
             @update:model-value="platformStore.setPlatform($event)">
      <div class="relative w-40">
        <ListboxButton class="flex w-full items-center justify-between rounded-md
          border border-brand-300 bg-white px-3 py-2 text-sm text-gray-900
          shadow-sm transition hover:border-brand-500">
          <span class="truncate">
             currentPlatformLabel 
          </span>
          <svg class="h-4 w-4 text-brand-500" fill="none" viewBox="0 0 24 24"
               stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </ListboxButton>
        <transition
          enter-active-class="transition duration-100 ease-out"
          enter-from-class="scale-95 opacity-0"
          enter-to-class="scale-100 opacity-100"
          leave-active-class="transition duration-75 ease-in"
          leave-from-class="scale-100 opacity-100"
          leave-to-class="scale-95 opacity-0"
        >
          <ListboxOptions class="absolute z-20 mt-2 w-full rounded-md border
            border-brand-300 bg-white py-1 shadow-lg">
            <ListboxOption v-for="p in platformStore.platforms" :key="p.id"
              :value="p.id" v-slot="{ active, selected }">
              <li :class="[
                'cursor-pointer px-3 py-2 text-sm',
                active ? 'bg-brand-100 text-brand-900' : 'text-gray-700',
                selected ? 'font-medium' : ''
              ]">
                 p.icon   p.label 
              </li>
            </ListboxOption>
          </ListboxOptions>
        </transition>
      </div>
    </Listbox>

    <button type="button"
      class="rounded-md bg-brand-900 px-3 py-2 text-sm font-medium text-white
             transition hover:bg-brand-700"
      @click="openAddModal">
      新增店铺
    </button>
  </div>
</div>

<!-- 添加 computed -->
<!-- script 中增加：
const currentPlatformLabel = computed(() => {
  const p = platformStore.platforms.find(pl => pl.id === platformStore.currentPlatform)
  return p ? `${p.icon} ${p.label}` : '选择平台'
})
-->
​
店铺列表改用 <table>（不再嵌套 ShopCard 组件）：
<div v-if="shops.length === 0" class="rounded-md border border-brand-300/50 bg-white px-6 py-14 text-center shadow-sm">
  <p class="text-sm text-brand-500">当前平台下暂无店铺数据。</p>
</div>

<div v-else class="overflow-x-auto rounded-md border border-brand-300/50 bg-white shadow-sm">
  <table class="w-full min-w-[900px] table-fixed divide-y divide-brand-300/30">
    <thead class="bg-brand-700/10">
      <tr class="text-xs font-medium uppercase tracking-wider text-brand-700">
        <th class="w-16 px-4 py-3 text-center">状态</th>
        <th class="w-44 px-4 py-3 text-center">店铺名称</th>
        <th class="w-28 px-4 py-3 text-center">账号</th>
        <th class="w-36 px-4 py-3 text-center">邮箱</th>
        <th class="w-24 px-4 py-3 text-center">协议</th>
        <th class="w-36 px-4 py-3 text-center">代理</th>
        <th class="w-36 px-4 py-3 text-center">最近登录</th>
        <th class="w-36 px-4 py-3 text-center">操作</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-brand-300/20 text-sm text-gray-900">
      <tr v-for="shop in shops" :key="shop.id"
          class="transition hover:bg-brand-100/50">
        <td class="px-4 py-3 text-center">
          <StatusBadge :status="shop.status" type="shop" />
        </td>
        <td class="px-4 py-3 text-center">
          <p class="truncate text-sm font-medium text-gray-900"> shop.name </p>
          <p class="truncate font-mono text-[11px] text-brand-500"> shop.id </p>
        </td>
        <td class="truncate px-4 py-3 text-center font-mono text-xs text-brand-500">
           shop.username || '-' 
        </td>
        <td class="truncate px-4 py-3 text-center text-xs">
           shop.smtp_user || '未配置' 
        </td>
        <td class="px-4 py-3 text-center font-mono text-xs uppercase text-brand-500">
           shop.smtp_protocol || '-' 
        </td>
        <td class="truncate px-4 py-3 text-center text-xs text-brand-500">
           shop.proxy || '无代理' 
        </td>
        <td class="px-4 py-3 text-center font-mono text-xs text-brand-500">
           shop.last_login ? new Date(shop.last_login).toLocaleString('zh-CN') : '暂无记录' 
        </td>
        <td class="whitespace-nowrap px-4 py-3 text-center">
          <div class="inline-flex gap-3">
            <button type="button"
              class="text-xs font-medium text-brand-500 transition hover:text-brand-900"
              @click="handleOpenBrowser(shop.id)">打开</button>
            <button type="button"
              class="text-xs font-medium text-brand-500 transition hover:text-brand-900"
              @click="openEditModal(shop)">编辑</button>
            <button type="button"
              class="text-xs font-medium text-brand-500 transition hover:text-brand-900"
              @click="handleCheckStatus(shop.id)">检查</button>
            <button type="button"
              class="text-xs font-medium text-rose-500 transition hover:text-rose-700"
              @click="openDeleteConfirm(shop.id)">删除</button>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</div>
​
ShopCard 组件不再需要了。 店铺数据直接在 ShopManage 里用 <table> 渲染。如果其他页面没有引用 ShopCard.vue，可以删除。
Step 4：全站换色（批量 find & replace 所有已重写的 .vue）
旧 class
新 class
说明
bg-gray-900（主按钮）
bg-brand-900
主操作按钮 #11212D
hover:bg-gray-800
hover:bg-brand-700
主按钮 hover #253745
bg-gray-50/60（表头）
bg-brand-700/10
表头背景（半透明深色底）
text-gray-500（表头/次文字）
text-brand-500
次要文字 #4A5C6A
bg-gray-100（Tab 容器 / badge 底）
bg-brand-100
Tab/标签底 #CCD0CF
border-gray-200
border-brand-300/50
卡片边框
border-gray-100
border-brand-300/30
分割线
divide-gray-200
divide-brand-300/30
表格分割线
divide-gray-100
divide-brand-300/20
行内分割线
peer-checked:bg-gray-900
peer-checked:bg-brand-500
Toggle on 态 #4A5C6A
focus:ring-gray-400
focus:ring-brand-500
input focus
focus:border-gray-400
focus:border-brand-500
input focus
hover:bg-gray-50（次按钮 hover）
hover:bg-brand-100/50
次按钮 hover
bg-gray-50（页面底色 / 空状态）
bg-brand-100
页面底色 #CCD0CF
不要替换的：
bg-white — 卡片内底色保持白
text-gray-900 — 正文黑字保持
text-rose-600 / text-rose-500 — 删除/危险按钮保持红色
bg-gray-200 — Toggle off 态保持灰（和 on 态 brand-500 形成对比）
disabled:bg-gray-400 — disabled 态保持灰
placeholder:text-gray-400 — placeholder 保持淡灰
Step 5：重写 FlowParamsTab / TaskListTab / TaskResultTab / JsonTooltip
规则和上一条消息完全相同，但颜色全部使用 brand-* 体系：
表头 → bg-brand-700/10 text-brand-700
开关 on → peer-checked:bg-brand-500
重置按钮 → text-brand-500 hover:text-brand-900
删除按钮 → text-rose-500 hover:text-rose-700
分割线 → divide-brand-300/20
行 hover → hover:bg-brand-100/50
批量按钮 → border-brand-300 hover:bg-brand-100/50
删除所有旧 CSS 引用和 .css 文件。
Step 6：Modal 弹窗
- border border-gray-200 bg-white
+ border border-brand-300/50 bg-white

- border-b border-gray-100   (header)
+ border-b border-brand-300/30

- border-t border-gray-100   (footer)
+ border-t border-brand-300/30

- hover:bg-gray-100   (close button)
+ hover:bg-brand-100
​
验收标准
字段对齐 — 店铺列表用 <table> + table-fixed + 每列 w-XX，表头和行完美对齐，全部 text-center
侧栏 — 深色 #06141B，选中 #11212D，字体 text-sm + py-2（不再偏小）
页面底色 — #CCD0CF（浅灰蓝），不是纯白
卡片/表格 — bg-white 在 #CCD0CF 底上清晰可见
平台选择器 — 下拉框，不是 pill 按钮
开关 — off 灰 / on #4A5C6A，对比明显
操作按钮 — 所有表格行的 重置/删除/编辑 按钮可见可点
没有旧 CSS 残留
没有蓝色（#253745 偏向深灰绿，不是蓝色）
全站风格统一：深灰侧栏 + 浅灰页面底 + 白色卡片 + 灰蓝点缀