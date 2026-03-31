任务目标：
把平台切换器从左侧边栏移到店铺管理页面的 header 区域（和"店铺管理"标题、"新增店铺"按钮在同一行）
修复配色，去掉蓝色调，统一为深灰色系
需要修改的文件：
frontend/src/views/ShopManage.vue
frontend/src/App.vue（移除侧边栏中的 PlatformSelector）
frontend/src/components/PlatformSelector.vue（配色重做）
1. App.vue — 移除侧边栏的平台选择器
删掉侧边栏里的 <PlatformSelector /> 组件和对应的 import。侧边栏不再显示平台切换器。
2. ShopManage.vue — header 区域嵌入平台切换器
把 header 改成三栏布局：标题 + 平台切换 + 新增按钮：
<div class="header">
  <h1>店铺管理</h1>
  <div class="header-actions">
    <!-- 平台切换：改为简洁的按钮组样式，不是下拉框 -->
    <div class="platform-tabs">
      <button
        v-for="p in platformStore.platforms"
        :key="p.id"
        class="platform-tab"
        :class="{ active: platformStore.currentPlatform === p.id }"
        @click="platformStore.setPlatform(p.id)"
      >
         p.icon   p.name 
      </button>
    </div>
    <button class="btn btn-primary" @click="openAddModal">新增店铺</button>
  </div>
</div>
​
对应样式（深灰色系，不要蓝色）：
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.platform-tabs {
  display: flex;
  gap: 4px;
  background: #2a2a3a;
  border-radius: 8px;
  padding: 3px;
}

.platform-tab {
  padding: 6px 16px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #999;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.platform-tab:hover {
  color: #ddd;
  background: #333345;
}

.platform-tab.active {
  background: #4f46e5;  /* 紫色高亮，不是蓝色 */
  color: #fff;
  font-weight: 500;
}
​
这样效果是一排胶囊按钮：[🟠 拼多多] [🎵 抖音] [🟧 淘宝]，选中的高亮，比下拉框更直观。
3. PlatformSelector.vue — 可以删除或保留为备用
如果侧边栏不再需要它，直接删除 PlatformSelector.vue 文件。如果想保留备用就不删，但从 App.vue 里去掉引用。
4. App.vue 侧边栏配色修复
侧边栏里原来放平台选择器的区域样式（如果有 .sidebar 或类似样式里的蓝色），也一并改为灰色系：
/* 所有 #0f3460 → #2a2a3a */
/* 所有 #1a4d7a → #3a3a4a */
/* 所有 #16213e → #1e1e2e */
​
5. ShopManage.vue 里也 import platformStore
已经有了，确保 onMounted 和 watch 都正常触发 loadShops。
验收方式：
左侧边栏不再有平台选择器
店铺管理页面的标题行右侧显示 [🟠 拼多多] [🎵 抖音] [🟧 淘宝] 按钮组，后面跟"新增店铺"按钮
点击不同平台按钮，选中态切换，店铺列表自动刷新
整体配色为深灰色系（#1e1e2e / #2a2a3a），没有蓝色调
选中平台用紫色高亮（#4f46e5），视觉上干净清爽