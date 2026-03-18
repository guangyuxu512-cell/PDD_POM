import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/shops'
    },
    {
      path: '/shops',
      name: 'ShopManage',
      component: () => import('../views/ShopManage.vue')
    },
    {
      path: '/business',
      name: 'BusinessManage',
      component: () => import('../views/BusinessManage.vue')
    },
    {
      path: '/data',
      name: 'DataManage',
      component: () => import('../views/DataManage.vue')
    },
    {
      path: '/aftersale-config',
      name: 'AftersaleConfig',
      component: () => import('../views/AftersaleConfig.vue')
    },
    {
      path: '/monitor',
      name: 'MonitorManage',
      component: () => import('../views/MonitorManage.vue')
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue')
    },
    {
      path: '/flows',
      redirect: '/business?tab=flow'
    },
    {
      path: '/execute',
      redirect: '/business?tab=execute'
    },
    {
      path: '/schedules',
      redirect: '/business?tab=schedule'
    },
    {
      path: '/task-params',
      redirect: '/data?tab=params'
    },
    {
      path: '/logs',
      redirect: '/monitor?tab=logs'
    },
    {
      path: '/tasks',
      redirect: '/monitor?tab=monitor'
    },
    {
      path: '/browser',
      name: 'BrowserManager',
      component: () => import('../views/BrowserManager.vue')
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue')
    }
  ]
})

export default router
