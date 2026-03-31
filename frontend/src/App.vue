<script setup lang="ts">
import { useRoute } from 'vue-router'
import Toast from './components/Toast.vue'

const route = useRoute()

const navItems = [
  { path: '/shops', icon: '🏪', label: '店铺管理' },
  { path: '/business', icon: '📋', label: '业务管理' },
  { path: '/aftersale-config', icon: '🛡️', label: '售后配置' },
  { path: '/data', icon: '📁', label: '数据管理' },
  { path: '/monitor', icon: '📊', label: '运行监控' },
  { path: '/settings', icon: '⚙️', label: '设置' },
]
</script>

<template>
  <div class="flex h-screen bg-brand-50">
    <aside class="flex w-56 flex-shrink-0 flex-col bg-brand-950">
      <div class="px-4 py-5">
        <h1 class="text-base font-semibold text-white tracking-wide">PDD 自动化</h1>
      </div>

      <nav class="flex-1 space-y-0.5 px-2">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors"
          :class="
            route.path.startsWith(item.path)
              ? 'bg-brand-900 font-medium text-white'
              : 'text-brand-200/80 hover:bg-brand-900 hover:text-white'
          "
        >
          <span class="text-base leading-none">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <main class="flex-1 overflow-y-auto bg-brand-50 p-6">
      <router-view />
    </main>

    <Toast />
  </div>
</template>
