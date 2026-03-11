import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue')
    },
    {
      path: '/shops',
      name: 'ShopManage',
      component: () => import('../views/ShopManage.vue')
    },
    {
      path: '/flows',
      name: 'FlowManage',
      component: () => import('../views/FlowManage.vue')
    },
    {
      path: '/execute',
      name: 'BatchExecute',
      component: () => import('../views/BatchExecute.vue')
    },
    {
      path: '/schedules',
      name: 'ScheduleManage',
      component: () => import('../views/ScheduleManage.vue')
    },
    {
      path: '/browser',
      name: 'BrowserManager',
      component: () => import('../views/BrowserManager.vue')
    },
    {
      path: '/tasks',
      name: 'TaskMonitor',
      component: () => import('../views/TaskMonitor.vue')
    },
    {
      path: '/task-params',
      name: 'TaskParamsManage',
      component: () => import('../views/TaskParamsManage.vue')
    },
    {
      path: '/logs',
      name: 'LogViewer',
      component: () => import('../views/LogViewer.vue')
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue')
    }
  ]
})

export default router
