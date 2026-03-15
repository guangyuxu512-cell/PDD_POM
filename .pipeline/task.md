Task 41：前端菜单重构 — 10 合 5
一、做什么
将前端侧边栏从 10 个菜单项精简为 5 个，使用 Tab 切换合并同类页面。
目标菜单结构：
自动化工作台
├── 🏪 店铺管理         /shops
├── 📋 业务管理         /business    Tab: 流程管理 | 批量执行 | 定时任务
├── 📁 数据管理         /data        Tab: CSV导入 | 执行结果 | 规则配置
├── 📊 运行监控         /monitor     Tab: 运行日志 | 任务监控
└── ⚙️ 设置            /settings
​
二、涉及文件
frontend/src/App.vue — 侧边栏菜单精简为 5 项
frontend/src/router/index.ts — 路由重组
frontend/src/views/BusinessManage.vue — 新建，业务管理页（Tab容器）
frontend/src/views/DataManage.vue — 新建，数据管理页（Tab容器）
frontend/src/views/MonitorManage.vue — 新建，运行监控页（Tab容器）
现有 Vue 文件不删除，作为 Tab 内容组件复用
三、App.vue 侧边栏修改
将 <nav> 里的 10 个 <router-link> 替换为 5 个：
<nav class="nav">
  <router-link to="/shops" class="nav-item">
    <span class="icon">🏪</span>
    <span>店铺管理</span>
  </router-link>
  <router-link to="/business" class="nav-item">
    <span class="icon">📋</span>
    <span>业务管理</span>
  </router-link>
  <router-link to="/data" class="nav-item">
    <span class="icon">📁</span>
    <span>数据管理</span>
  </router-link>
  <router-link to="/monitor" class="nav-item">
    <span class="icon">📊</span>
    <span>运行监控</span>
  </router-link>
  <router-link to="/settings" class="nav-item">
    <span class="icon">⚙️</span>
    <span>设置</span>
  </router-link>
</nav>
​
四、路由修改
frontend/src/router/index.ts 修改为：
routes: [
  // 默认首页重定向到店铺管理
  { path: '/', redirect: '/shops' },

  // 5 个主菜单
  { path: '/shops', name: 'ShopManage', component: () => import('../views/ShopManage.vue') },
  { path: '/business', name: 'BusinessManage', component: () => import('../views/BusinessManage.vue') },
  { path: '/data', name: 'DataManage', component: () => import('../views/DataManage.vue') },
  { path: '/monitor', name: 'MonitorManage', component: () => import('../views/MonitorManage.vue') },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue') },

  // 隐藏路由（不显示在菜单，但保留可访问）
  { path: '/browser', name: 'BrowserManager', component: () => import('../views/BrowserManager.vue') },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
]
​
五、三个新 Tab 容器页面
5.1 BusinessManage.vue（业务管理）
<template>
  <div class="manage-page">
    <h1>业务管理</h1>
    <div class="tab-bar">
      <button v-for="tab in tabs" :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key">
         tab.label 
      </button>
    </div>
    <div class="tab-content">
      <FlowManage v-if="activeTab === 'flow'" />
      <BatchExecute v-if="activeTab === 'execute'" />
      <ScheduleManage v-if="activeTab === 'schedule'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FlowManage from './FlowManage.vue'
import BatchExecute from './BatchExecute.vue'
import ScheduleManage from './ScheduleManage.vue'

const tabs = [
  { key: 'flow', label: '流程管理' },
  { key: 'execute', label: '批量执行' },
  { key: 'schedule', label: '定时任务' },
]
const activeTab = ref('flow')
</script>
​
5.2 DataManage.vue（数据管理）
<template>
  <div class="manage-page">
    <h1>数据管理</h1>
    <div class="tab-bar">
      <button v-for="tab in tabs" :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key">
         tab.label 
      </button>
    </div>
    <div class="tab-content">
      <TaskParamsManage v-if="activeTab === 'params'" />
      <!-- 规则配置 Tab 暂时显示占位，后续实现 -->
      <div v-if="activeTab === 'rules'" class="placeholder">
        <p>📋 规则配置功能开发中...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import TaskParamsManage from './TaskParamsManage.vue'

const tabs = [
  { key: 'params', label: 'CSV导入 / 执行结果' },
  { key: 'rules', label: '规则配置' },
]
const activeTab = ref('params')
</script>
​
注意：TaskParamsManage.vue 内部已有"任务列表 / 执行结果 / 流程参数"三个 Tab，作为子级 Tab 保留不变。
5.3 MonitorManage.vue（运行监控）
<template>
  <div class="manage-page">
    <h1>运行监控</h1>
    <div class="tab-bar">
      <button v-for="tab in tabs" :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key">
         tab.label 
      </button>
    </div>
    <div class="tab-content">
      <LogViewer v-if="activeTab === 'logs'" />
      <TaskMonitor v-if="activeTab === 'monitor'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import LogViewer from './LogViewer.vue'
import TaskMonitor from './TaskMonitor.vue'

const tabs = [
  { key: 'logs', label: '运行日志' },
  { key: 'monitor', label: '任务监控' },
]
const activeTab = ref('logs')
</script>
​
六、Tab 样式（三个容器页共用）
在每个容器页的 <style scoped> 中添加（或抽成共用 CSS class）：
.manage-page h1 {
  font-size: 28px;
  margin-bottom: 20px;
  color: #1a1a2e;
}

.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #e5e7eb;
  margin-bottom: 24px;
}

.tab-btn {
  padding: 10px 24px;
  border: none;
  background: none;
  font-size: 15px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #1a1a2e;
}

.tab-btn.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.tab-content {
  min-height: 0;
}

.placeholder {
  padding: 60px;
  text-align: center;
  color: #9ca3af;
  font-size: 16px;
}
​
七、子组件适配
现有的 FlowManage.vue、BatchExecute.vue、ScheduleManage.vue、TaskParamsManage.vue、LogViewer.vue、TaskMonitor.vue 被嵌入 Tab 容器后，需要做一个小调整：
去掉每个子组件内部的 <h1> 标题（因为容器页已经有了）
或者改为：检测是否有父容器，有则隐藏自身标题
推荐做法：每个子组件的 <h1> 改为可选显示，加一个 prop：
const props = withDefaults(defineProps<{ showTitle?: boolean }>(), {
  showTitle: true
})
​
模板中：<h1 v-if="showTitle">流程模板</h1>
容器页引用时传入：<FlowManage :showTitle="false" />
八、约束
不删除任何现有 Vue 文件，只是把它们嵌入 Tab 容器
隐藏路由（/browser、/dashboard）保留可访问，只是不出现在侧边栏
App.vue 侧边栏 router-link-active 样式确保匹配 /business、/data、/monitor 路径
Tab 样式保持与现有项目风格一致（白底、蓝色高亮、圆角卡片）
规则配置 Tab 暂时显示占位文字，不需要实现功能
测试确保所有页面功能正常