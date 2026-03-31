<script setup lang="ts">
import PlatformSelector from './components/PlatformSelector.vue'
import Toast from './components/Toast.vue'
</script>

<template>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">自动化工作台</div>
        <PlatformSelector />
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
  background: var(--color-bg-card);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-border);
  flex-shrink: 0;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  border-bottom: 1px solid var(--color-border);
}

.logo {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
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
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: all 0.2s;
  gap: var(--spacing-md);
  position: relative;
}

.nav-item:hover {
  background: var(--color-border-light);
  color: var(--color-text);
}

.nav-item.router-link-active,
.nav-item.router-link-exact-active {
  background: var(--color-primary-light);
  color: var(--color-text);
  border-left: 3px solid var(--color-primary);
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
