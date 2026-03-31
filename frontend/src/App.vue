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
  <div class="flex h-screen bg-gray-50">
    <aside class="flex w-52 flex-shrink-0 flex-col border-r border-gray-200 bg-white">
      <div class="px-4 py-5">
        <span class="text-sm font-semibold tracking-tight text-gray-900">
          自动化工作台
        </span>
      </div>

      <nav class="flex-1 space-y-0.5 px-2">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-colors"
          :class="
            route.path.startsWith(item.path)
              ? 'bg-gray-100 font-medium text-gray-900'
              : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
          "
        >
          <span class="text-base leading-none">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <main class="flex-1 overflow-auto bg-gray-50">
      <router-view />
    </main>

    <Toast />
  </div>
</template>
