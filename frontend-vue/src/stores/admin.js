import { defineStore } from 'pinia'
import api, { setJustLoggedIn } from '@/api'

export const useAdminStore = defineStore('admin', {
  state: () => ({
    token: localStorage.getItem('admin_token') || '',
    user: JSON.parse(localStorage.getItem('admin_user') || 'null'),
    stats: null
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token,
    username: (state) => state.user?.username || '管理员'
  },
  
  actions: {
    async login(username, password) {
      try {
        const res = await api.login(username, password)
        
        // 先保存 token，这样 getCurrentUser 请求才能带上 token
        this.token = res.access_token
        localStorage.setItem('admin_token', res.access_token)
        
        // 标记刚登录成功，防止后续请求触发401处理
        setJustLoggedIn()
        
        // 获取用户信息并验证是否是管理员
        try {
          const userInfo = await api.getCurrentUser()
          
          if (!userInfo.is_admin) {
            // 不是管理员，清除 token
            this.token = ''
            localStorage.removeItem('admin_token')
            return { success: false, message: '该账号不是管理员' }
          }
          
          this.user = userInfo
          localStorage.setItem('admin_user', JSON.stringify(userInfo))
          return { success: true }
        } catch (userError) {
          // 获取用户信息失败，清除 token
          this.token = ''
          localStorage.removeItem('admin_token')
          return { success: false, message: '获取用户信息失败，请重新登录' }
        }
      } catch (error) {
        // 登录失败，清除可能存在的 token
        this.token = ''
        localStorage.removeItem('admin_token')
        const errorMsg = error.message || '登录失败，请检查用户名和密码'
        return { success: false, message: errorMsg }
      }
    },
    
    async fetchStats() {
      try {
        const res = await api.getAdminStats()
        this.stats = res
        return { success: true, data: res }
      } catch (error) {
        return { success: false, error: error.message }
      }
    },
    
    logout() {
      this.token = ''
      this.user = null
      this.stats = null
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
    }
  }
})
