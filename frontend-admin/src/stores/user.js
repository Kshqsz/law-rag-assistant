import { defineStore } from 'pinia'
import api, { setJustLoggedIn } from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token,
    username: (state) => state.user?.username || '用户'
  },
  
  actions: {
    async login(username, password) {
      try {
        const res = await api.login(username, password)
        
        // 先保存 token，这样 getCurrentUser 请求才能带上 token
        this.token = res.access_token
        localStorage.setItem('token', res.access_token)
        
        // 标记刚登录成功，防止后续请求触发401处理
        setJustLoggedIn()
        
        // 获取用户信息
        try {
          const userInfo = await api.getCurrentUser()
          this.user = userInfo
          localStorage.setItem('user', JSON.stringify(userInfo))
          return { success: true }
        } catch (userError) {
          // 如果获取用户信息失败，清除 token
          this.token = ''
          localStorage.removeItem('token')
          return { success: false, message: '获取用户信息失败，请重新登录' }
        }
      } catch (error) {
        // 清除可能存在的 token
        this.token = ''
        localStorage.removeItem('token')
        // 获取后端返回的错误信息
        const errorMsg = error.message || '登录失败，请检查用户名和密码'
        return { success: false, message: errorMsg }
      }
    },
    
    async register(username, password) {
      try {
        await api.register(username, password)
        return { success: true }
      } catch (error) {
        const errorMsg = error.message || '注册失败'
        return { success: false, error: errorMsg }
      }
    },
    
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
