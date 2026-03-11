<script setup lang="ts">
import Toast from './components/Toast.vue'
</script>

<template>
  <div class="app">
    <aside class="sidebar">
      <div class="logo">自动化工作台</div>
      <nav class="nav">
        <router-link to="/" class="nav-item" exact>
          <span class="icon">📊</span>
          <span>仪表盘</span>
        </router-link>
        <router-link to="/shops" class="nav-item">
          <span class="icon">🏪</span>
          <span>店铺管理</span>
        </router-link>
        <router-link to="/flows" class="nav-item">
          <span class="icon">🧩</span>
          <span>流程模板</span>
        </router-link>
        <router-link to="/execute" class="nav-item">
          <span class="icon">⚡</span>
          <span>批量执行</span>
        </router-link>
        <router-link to="/schedules" class="nav-item">
          <span class="icon">⏰</span>
          <span>定时任务</span>
        </router-link>
        <router-link to="/browser" class="nav-item">
          <span class="icon">🌐</span>
          <span>浏览器</span>
        </router-link>
        <router-link to="/tasks" class="nav-item">
          <span class="icon">📋</span>
          <span>任务监控</span>
        </router-link>
        <router-link to="/task-params" class="nav-item">
          <span class="icon">🗂️</span>
          <span>任务参数</span>
        </router-link>
        <router-link to="/logs" class="nav-item">
          <span class="icon">📝</span>
          <span>日志</span>
        </router-link>
        <router-link to="/settings" class="nav-item">
          <span class="icon">⚙️</span>
          <span>设置</span>
        </router-link>
      </nav>
    </aside>
    <main class="content">
      <router-view />
    </main>
    <Toast />
  </div>
</template>

<style scoped>
.app {
  display: flex;
  height: 100vh;
  background: #f5f5f5;
  color: #1a1a2e;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  min-width: 240px;
  background: white;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.logo {
  padding: 24px 20px;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
  color: #1a1a2e;
}

.nav {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: #6b7280;
  text-decoration: none;
  transition: all 0.2s;
  gap: 12px;
  position: relative;
}

.nav-item:hover {
  background: #f3f4f6;
  color: #1a1a2e;
}

.nav-item.router-link-active,
.nav-item.router-link-exact-active {
  background: #eff6ff;
  color: #1a1a2e;
  border-left: 3px solid #3b82f6;
  padding-left: 17px;
}

.icon {
  font-size: 20px;
  line-height: 1;
}

.content {
  flex: 1;
  overflow: auto;
  padding: 24px;
  min-width: 0;
  background: #f5f5f5;
  color: #1a1a2e;
}

@media (max-width: 1200px) {
  .content {
    padding: 20px;
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: 200px;
    min-width: 200px;
  }

  .content {
    padding: 16px;
  }

  .logo {
    font-size: 16px;
    padding: 20px 16px;
  }

  .nav-item {
    padding: 10px 16px;
  }
}
</style>
