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
  <div class="flex h-screen bg-brand-100">
    <aside class="flex w-56 flex-shrink-0 flex-col bg-brand-950">
      <div class="px-4 py-5">
        <span class="text-base font-semibold tracking-tight text-white">
          自动化工作台
        </span>
      </div>

      <nav class="flex-1 space-y-0.5 px-3">
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
          <span class="text-base leading-none">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <main class="flex-1 overflow-auto bg-brand-100 p-6">
      <router-view />
    </main>

    <Toast />
  </div>
</template>
