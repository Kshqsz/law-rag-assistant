import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const instance = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 用于标记刚刚登录成功的状态，在此期间不处理401错误
let justLoggedIn = false
let loginTimer = null

// 设置刚登录状态（登录成功后调用）
export const setJustLoggedIn = () => {
  justLoggedIn = true
  if (loginTimer) clearTimeout(loginTimer)
  loginTimer = setTimeout(() => {
    justLoggedIn = false
  }, 10000) // 10秒内不处理401，给页面加载和初始请求足够时间
}

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    // 优先使用管理员 token，否则使用用户 token
    const adminToken = localStorage.getItem('admin_token')
    const userToken = localStorage.getItem('token')
    const token = adminToken || userToken
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    
    if (error.response?.status === 401) {
      // 检查是否跳过认证错误处理（用于登录流程中的请求）
      const skipAuthError = error.config?.skipAuthError
      
      // 如果刚登录成功，或者特别标记跳过认证错误，则不处理401
      if (!skipAuthError && !justLoggedIn) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('admin_token')
        localStorage.removeItem('admin_user')
        
        // 避免重复跳转和在登录页显示错误
        const currentPath = router.currentRoute.value.path
        if (currentPath !== '/login' && currentPath !== '/admin/login') {
          ElMessage.error('登录已过期，请重新登录')
          
          // 根据当前路径判断跳转到哪个登录页
          if (currentPath.startsWith('/admin')) {
            router.push('/admin/login')
          } else {
            router.push('/login')
          }
        }
      }
      // 如果是登录流程中的错误，不显示消息，让调用方处理
    } else if (!error.config?.skipErrorMessage) {
      // 其他错误显示消息（除非特别标记跳过）
      ElMessage.error(message)
    }
    
    return Promise.reject(new Error(message))
  }
)

export default {
  // 认证 - 使用 form-data 格式
  login: (username, password) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    return instance.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      skipAuthError: true, // 登录请求跳过认证错误处理
      skipErrorMessage: true // 登录错误由调用方处理
    })
  },
  
  register: (username, password) => 
    instance.post('/auth/register', { username, password }, {
      skipErrorMessage: true // 注册错误由调用方处理
    }),
  
  getCurrentUser: () => 
    instance.get('/auth/me', {
      skipAuthError: true // 获取用户信息时跳过认证错误处理（登录流程中调用）
    }),
  
  // 对话
  getConversations: (page = 1, pageSize = 20) => 
    instance.get('/conversations', { params: { page, page_size: pageSize } }),
  
  getMessages: (conversationId) => 
    instance.get(`/conversations/${conversationId}/messages`),
  
  deleteConversation: (conversationId) => 
    instance.delete(`/conversations/${conversationId}`),
  
  renameConversation: (conversationId, title) =>
    instance.put(`/conversations/${conversationId}`, { title }),
  
  // 聊天
  chat: (question, conversationId = null, documentId = null) => 
    instance.post('/chat', { 
      message: question,
      conversation_id: conversationId,
      use_document: documentId
    }),
  
  // 流式聊天
  chatStream: async function* (question, conversationId = null, documentId = null) {
    const token = localStorage.getItem('admin_token') || localStorage.getItem('token')
    
    const requestBody = {
      message: question,
      conversation_id: conversationId,
      use_document: documentId
    }
    
    console.log('[API] chatStream request:', requestBody)
    
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(requestBody)
    })
    
    console.log('[API] chatStream response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('[API] chatStream error:', errorText)
      throw new Error('Stream request failed: ' + errorText)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          try {
            const parsed = JSON.parse(data)
            console.log('[API] chatStream chunk:', parsed)
            yield parsed
          } catch (e) {
            console.error('解析SSE数据失败:', e, 'data:', data)
          }
        }
      }
    }
  },
  
  // 文档
  uploadDocument: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return instance.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 收藏
  getFavorites: (page = 1, pageSize = 20) => 
    instance.get('/favorites', { params: { page, page_size: pageSize } }),
  
  addFavorite: (question, answer, lawContext = '', webResults = '') => 
    instance.post('/favorites', { question, answer, law_context: lawContext, web_results: webResults }),
  
  deleteFavorite: (favoriteId) => 
    instance.delete(`/favorites/${favoriteId}`),
  
  // 反馈
  submitFeedback: (messageId, rating, comment = '') =>
    instance.post('/feedback', { message_id: messageId, rating, comment }),
  
  getMessageFeedback: (messageId) =>
    instance.get(`/feedback/message/${messageId}`),
  
  deleteFeedback: (messageId) =>
    instance.delete(`/feedback/${messageId}`),
  
  // 管理员
  getAdminStats: () => 
    instance.get('/admin/stats')
}
