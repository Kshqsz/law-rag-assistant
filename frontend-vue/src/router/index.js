import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAdminStore } from '@/stores/admin'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    redirect: '/chat',
    children: [
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/Chat.vue')
      },
      {
        path: 'favorites',
        name: 'Favorites',
        component: () => import('@/views/Favorites.vue')
      }
    ]
  },
  // 管理员路由
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/AdminLogin.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/admin/dashboard',
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
  const userStore = useUserStore()
  const adminStore = useAdminStore()
  
  // 管理员页面
  if (to.meta.requiresAdmin) {
    if (!adminStore.isLoggedIn) {
      next('/admin/login')
    } else {
      next()
    }
  }
  // 普通用户页面
  else if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } 
  // 已登录用户访问登录页
  else if (to.path === '/login' && userStore.isLoggedIn) {
    next('/')
  }
  // 已登录管理员访问管理登录页
  else if (to.path === '/admin/login' && adminStore.isLoggedIn) {
    next('/admin/dashboard')
  }
  else {
    next()
  }
})

export default router
