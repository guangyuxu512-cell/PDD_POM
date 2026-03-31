<script setup lang="ts">
import Toast from './components/Toast.vue'
</script>

<template>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">自动化工作台</div>
      </div>
      <nav class="nav">
        <router-link to="/shops" class="nav-item">
          <span class="icon">🏪</span>
          <span>店铺管理</span>
        </router-link>
        <router-link to="/business" class="nav-item">
          <span class="icon">📋</span>
          <span>业务管理</span>
        </router-link>
        <router-link to="/aftersale-config" class="nav-item">
          <span class="icon">🛡️</span>
          <span>售后配置</span>
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
  background: var(--color-bg);
  color: var(--color-text);
  overflow: hidden;
}

.sidebar {
  width: 200px;
  min-width: 200px;
  background: #1e1e2e;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #2e2e3e;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-bottom: 1px solid #2e2e3e;
}

.logo {
  font-size: 18px;
  font-weight: 600;
  color: #f4f4f5;
}

.nav {
  flex: 1;
  padding: var(--spacing-md) 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  color: #a1a1aa;
  text-decoration: none;
  transition: all 0.2s;
  gap: var(--spacing-md);
  position: relative;
}

.nav-item:hover {
  background: #2a2a3a;
  color: #f4f4f5;
}

.nav-item.router-link-active,
.nav-item.router-link-exact-active {
  background: #312e81;
  color: #ffffff;
  border-left: 3px solid #4f46e5;
  padding-left: 13px;
}

.icon {
  font-size: 20px;
  line-height: 1;
}

.content {
  flex: 1;
  overflow: auto;
  padding: var(--spacing-lg);
  min-width: 0;
  background: var(--color-bg);
  color: var(--color-text);
}

@media (max-width: 1200px) {
  .content {
    padding: var(--spacing-lg);
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: 200px;
    min-width: 200px;
  }

  .content {
    padding: var(--spacing-lg);
  }

  .logo {
    font-size: 16px;
  }

  .nav-item {
    padding: 10px 16px;
  }
}
</style>
