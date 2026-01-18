import { createRouter, createWebHistory } from 'vue-router'
import { useAdminStore } from '@/stores/admin'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'AdminLogin',
    component: () => import('@/views/AdminLogin.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'AdminDashboard',
    component: () => import('@/views/AdminDashboard.vue'),
    meta: { requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const adminStore = useAdminStore()
  
  // 需要管理员权限的页面
  if (to.meta.requiresAdmin) {
    if (!adminStore.isLoggedIn) {
      next('/login')
    } else {
      next()
    }
  }
  // 已登录管理员访问登录页，重定向到仪表盘
  else if (to.path === '/login' && adminStore.isLoggedIn) {
    next('/dashboard')
  }
  else {
    next()
  }
})

export default router
