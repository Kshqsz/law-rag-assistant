import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import api from '@/api'

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversations: [],
    currentConversationId: null,
    messages: [],
    isLoading: false,
    isStreaming: false,
    conversationPage: 1,
    conversationTotal: 0,
    conversationPageSize: 20,
    hasMoreConversations: true
  }),
  
  getters: {
    currentConversation: (state) => {
      return state.conversations.find(c => c.id === state.currentConversationId)
    }
  },
  
  actions: {
    async fetchConversations() {
      try {
        this.conversationPage = 1
        const res = await api.getConversations(1, this.conversationPageSize)
        this.conversations = res.conversations || []
        this.conversationTotal = res.total || 0
        this.hasMoreConversations = this.conversations.length < this.conversationTotal
      } catch (error) {
        console.error('获取对话列表失败:', error)
      }
    },
    
    async loadMoreConversations() {
      if (!this.hasMoreConversations) return
      try {
        this.conversationPage++
        const res = await api.getConversations(this.conversationPage, this.conversationPageSize)
        const moreConvs = res.conversations || []
        this.conversations.push(...moreConvs)
        this.hasMoreConversations = this.conversations.length < (res.total || 0)
      } catch (error) {
        console.error('加载更多对话失败:', error)
        this.conversationPage--
      }
    },
    
    async loadMessages(conversationId) {
      try {
        const res = await api.getMessages(conversationId)
        this.messages = res.messages || []
        this.currentConversationId = conversationId
      } catch (error) {
        console.error('加载消息失败:', error)
      }
    },
    
    async sendMessage(question, documentId = null) {
      this.isLoading = true
      this.isStreaming = true
      
      console.log('[ChatStore] sendMessage called with:', { question, documentId })
      
      // 添加用户消息
      this.messages.push({
        role: 'user',
        content: question,
        timestamp: new Date().toISOString()
      })
      
      // 添加 AI 占位消息
      const aiMessageIndex = this.messages.length
      this.messages.push({
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: true
      })
      
      try {
        let fullContent = ''
        let lawContext = ''
        let webContext = ''
        let messageId = null
        
        // 如果上传了文档但问题太宽泛，增强问题描述
        let enhancedQuestion = question
        if (documentId) {
          console.log('[ChatStore] Document ID provided, checking if question needs enhancement')
          // 检查问题是否太宽泛（没有明确的法律关键词）
          const lawKeywords = ['法律', '法规', '条例', '规定', '合同', '诉讼', '责任', '权利', '义务', '违法', '犯罪', '刑事', '民事', '行政']
          const hasLawKeyword = lawKeywords.some(keyword => question.includes(keyword))
          
          if (!hasLawKeyword) {
            // 增强问题描述，让它更明确与法律相关
            enhancedQuestion = `根据上传的法律文件内容，${question}`
            console.log('[ChatStore] Question enhanced to:', enhancedQuestion)
          } else {
            console.log('[ChatStore] Question already has law keywords')
          }
        }
        
        console.log('[ChatStore] Calling chatStream with:', { 
          enhancedQuestion, 
          conversationId: this.currentConversationId, 
          documentId 
        })
        
        // 使用流式接口（发送增强后的问题给后端，但显示原问题给用户）
        for await (const chunk of api.chatStream(enhancedQuestion, this.currentConversationId, documentId)) {
          if (chunk.token) {
            // 流式输出 token
            fullContent += chunk.token
            this.messages[aiMessageIndex].content = fullContent
          } else if (chunk.done) {
            // 流式完成
            if (chunk.conversation_id && !this.currentConversationId) {
              this.currentConversationId = chunk.conversation_id
              await this.fetchConversations()
            }
            // 如果返回了新标题，更新对话列表中的标题
            if (chunk.new_title && this.currentConversationId) {
              const conv = this.conversations.find(c => c.id === this.currentConversationId)
              if (conv) {
                conv.title = chunk.new_title
              }
            }
            lawContext = chunk.law_context || ''
            webContext = chunk.web_context || ''
            messageId = chunk.message_id || null
          } else if (chunk.error) {
            throw new Error(chunk.error)
          }
        }
        
        // 更新最终消息
        this.messages[aiMessageIndex] = {
          role: 'assistant',
          content: fullContent,
          law_context: lawContext,
          web_results: webContext,
          message_id: messageId,
          feedback: 0,
          timestamp: new Date().toISOString(),
          isStreaming: false
        }
      } catch (error) {
        this.messages[aiMessageIndex] = {
          role: 'assistant',
          content: '抱歉，回答时出现错误，请稍后重试。',
          timestamp: new Date().toISOString(),
          isStreaming: false,
          isError: true
        }
        console.error('发送消息失败:', error)
      } finally {
        this.isLoading = false
        this.isStreaming = false
      }
    },
    
    async renameConversation(conversationId, newTitle) {
      try {
        await api.renameConversation(conversationId, newTitle)
        const conv = this.conversations.find(c => c.id === conversationId)
        if (conv) conv.title = newTitle
        return { success: true }
      } catch (error) {
        return { success: false, error: error.message }
      }
    },
    
    async deleteConversation(conversationId) {
      try {
        await api.deleteConversation(conversationId)
        this.conversations = this.conversations.filter(c => c.id !== conversationId)
        
        if (this.currentConversationId === conversationId) {
          this.currentConversationId = null
          this.messages = []
        }
        
        return { success: true }
      } catch (error) {
        return { success: false, error: error.message }
      }
    },
    
    newConversation() {
      this.currentConversationId = null
      this.messages = []
    },
    
    async loadConversationMessages(conversationId) {
      try {
        console.log('[ChatStore] Loading messages for conversation:', conversationId)
        const res = await api.getMessages(conversationId)
        
        if (res.messages && Array.isArray(res.messages)) {
          // 将数据库中的消息转换为前端格式
          this.messages = res.messages.map(msg => ({
            role: msg.role,
            content: msg.content,
            law_context: msg.law_context || '',
            web_results: msg.web_context || '', // 注意：后端返回 web_context，前端使用 web_results
            message_id: msg.id || null,
            feedback: msg.feedback || 0,
            timestamp: msg.created_at,
            isStreaming: false
          }))
          console.log('[ChatStore] Loaded', this.messages.length, 'messages')
          // 输出有 web_results 的消息数量
          const withWebResults = this.messages.filter(m => m.web_results)
          console.log('[ChatStore] Messages with web_results:', withWebResults.length)
        }
      } catch (error) {
        console.error('[ChatStore] Failed to load messages:', error)
        ElMessage.error('加载消息失败')
      }
    }
  }
})
