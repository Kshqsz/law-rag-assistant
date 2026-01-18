<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ 'collapsed': sidebarCollapsed }">
      <div class="sidebar-content">
        <!-- Logo -->
        <div class="sidebar-header">
          <div class="logo">
            <span class="logo-icon">⚖️</span>
            <span v-show="!sidebarCollapsed" class="logo-text">法律AI助手</span>
          </div>
          <el-button 
            v-show="!sidebarCollapsed"
            type="primary" 
            class="new-chat-btn"
            @click="handleNewChat"
          >
            <el-icon><Plus /></el-icon>
            新建对话
          </el-button>
        </div>
        
        <!-- 导航菜单 -->
        <nav class="nav-menu" v-show="!sidebarCollapsed">
          <div class="nav-section">
            <span class="nav-label">功能</span>
            <router-link to="/chat" class="nav-item" :class="{ active: $route.path === '/chat' }">
              <el-icon><ChatDotRound /></el-icon>
              <span>对话</span>
            </router-link>
            <router-link to="/favorites" class="nav-item" :class="{ active: $route.path === '/favorites' }">
              <el-icon><Star /></el-icon>
              <span>收藏夹</span>
            </router-link>
          </div>
          
          <!-- 历史对话 -->
          <div class="nav-section">
            <span class="nav-label">历史对话</span>
            <div class="conversation-list">
              <div 
                v-for="conv in chatStore.conversations.slice(0, 10)" 
                :key="conv.id"
                class="conversation-item"
                :class="{ active: chatStore.currentConversationId === conv.id }"
                @click="selectConversation(conv.id)"
              >
                <el-icon><Document /></el-icon>
                <span class="conv-title">{{ conv.title }}</span>
                <el-dropdown trigger="click" @command="handleConvCommand($event, conv.id)">
                  <el-button class="more-btn" link>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="export">
                        <el-icon><Download /></el-icon>
                        导出PDF
                      </el-dropdown-item>
                      <el-dropdown-item command="delete">
                        <el-icon><Delete /></el-icon>
                        删除对话
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
              <div v-if="chatStore.conversations.length === 0" class="no-conversations">
                暂无对话
              </div>
            </div>
          </div>
        </nav>
        
        <!-- 用户区域 -->
        <div class="user-area" v-show="!sidebarCollapsed">
          <div class="user-info">
            <el-avatar :size="36" class="user-avatar">
              {{ userStore.username.charAt(0).toUpperCase() }}
            </el-avatar>
            <span class="username">{{ userStore.username }}</span>
          </div>
          <el-button class="logout-btn" link @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
          </el-button>
        </div>
      </div>
      
      <!-- 折叠按钮 -->
      <div class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
        <el-icon>
          <ArrowLeft v-if="!sidebarCollapsed" />
          <ArrowRight v-else />
        </el-icon>
      </div>
    </aside>
    
    <!-- 主内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import { ElMessageBox, ElMessage } from 'element-plus'
import html2pdf from 'html2pdf.js'
import { marked } from 'marked'
import api from '@/api'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()

const sidebarCollapsed = ref(false)

onMounted(() => {
  chatStore.fetchConversations()
})

const handleNewChat = () => {
  chatStore.newConversation()
  router.push('/chat')
}

const selectConversation = async (conversationId) => {
  await chatStore.loadMessages(conversationId)
  router.push('/chat')
}

const handleConvCommand = async (command, conversationId) => {
  if (command === 'delete') {
    try {
      await ElMessageBox.confirm('确定要删除这个对话吗？', '确认删除', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      })
      
      const result = await chatStore.deleteConversation(conversationId)
      if (result.success) {
        ElMessage.success('对话已删除')
      }
    } catch {
      // 用户取消
    }
  } else if (command === 'export') {
    await exportConversationToPDF(conversationId)
  }
}

const exportConversationToPDF = async (conversationId) => {
  try {
    ElMessage.info('正在生成PDF...')
    
    // 获取对话消息
    const res = await api.getMessages(conversationId)
    const messages = res.messages || []
    
    if (messages.length === 0) {
      ElMessage.warning('对话为空，无法导出')
      return
    }
    
    // 获取对话标题
    const conversation = chatStore.conversations.find(c => c.id === conversationId)
    const title = conversation?.title || '法律咨询对话'
    
    // 创建临时 HTML 内容
    const content = document.createElement('div')
    content.style.padding = '20px'
    content.style.fontFamily = 'Arial, "Microsoft YaHei", sans-serif'
    content.style.fontSize = '14px'
    content.style.lineHeight = '1.6'
    content.style.color = '#333'
    
    // 添加标题
    const titleEl = document.createElement('h1')
    titleEl.textContent = title
    titleEl.style.fontSize = '24px'
    titleEl.style.marginBottom = '10px'
    titleEl.style.color = '#1a1a1a'
    content.appendChild(titleEl)
    
    // 添加时间
    const timeEl = document.createElement('p')
    timeEl.textContent = `导出时间: ${new Date().toLocaleString('zh-CN')}`
    timeEl.style.color = '#666'
    timeEl.style.fontSize = '12px'
    timeEl.style.marginBottom = '30px'
    content.appendChild(timeEl)
    
    // 添加消息
    messages.forEach(msg => {
      const msgBox = document.createElement('div')
      msgBox.style.marginBottom = '20px'
      msgBox.style.padding = '15px'
      msgBox.style.backgroundColor = msg.role === 'user' ? '#f0f9ff' : '#f9fafb'
      msgBox.style.borderRadius = '8px'
      msgBox.style.border = '1px solid ' + (msg.role === 'user' ? '#bfdbfe' : '#e5e7eb')
      
      const roleEl = document.createElement('div')
      roleEl.textContent = msg.role === 'user' ? '👤 用户' : '⚖️ AI助手'
      roleEl.style.fontWeight = 'bold'
      roleEl.style.marginBottom = '8px'
      roleEl.style.fontSize = '14px'
      roleEl.style.color = msg.role === 'user' ? '#2563eb' : '#059669'
      msgBox.appendChild(roleEl)
      
      const contentEl = document.createElement('div')
      // 使用 marked 渲染 Markdown 格式
      contentEl.innerHTML = marked.parse(msg.content)
      contentEl.style.wordBreak = 'break-word'
      contentEl.style.fontSize = '13px'
      contentEl.style.lineHeight = '1.8'
      // 为渲染后的元素添加样式
      const style = document.createElement('style')
      style.textContent = `
        h1, h2, h3 { margin-top: 16px; margin-bottom: 8px; }
        p { margin: 8px 0; }
        ul, ol { margin: 8px 0; padding-left: 24px; }
        code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
        pre { background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; }
        blockquote { border-left: 4px solid #ddd; margin: 8px 0; padding-left: 12px; color: #666; }
      `
      contentEl.appendChild(style)
      msgBox.appendChild(contentEl)
      
      content.appendChild(msgBox)
    })
    
    // 使用 html2pdf 生成 PDF
    const opt = {
      margin: 10,
      filename: `${title}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    }
    
    await html2pdf().set(opt).from(content).save()
    ElMessage.success('PDF导出成功')
  } catch (error) {
    console.error('导出PDF失败:', error)
    ElMessage.error('PDF导出失败')
  }
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '确认退出', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'info'
    })
    
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style lang="scss" scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  position: relative;
  width: 280px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  
  &.collapsed {
    width: 0;
    border-right: none;
    
    .sidebar-content {
      opacity: 0;
      pointer-events: none;
    }
  }
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  transition: opacity 0.2s ease;
}

.sidebar-header {
  margin-bottom: 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  
  .logo-icon {
    font-size: 1.8rem;
  }
  
  .logo-text {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
  }
}

.new-chat-btn {
  width: 100%;
  height: 44px;
  font-size: 0.95rem;
  border-radius: 10px;
}

.nav-menu {
  flex: 1;
  overflow-y: auto;
}

.nav-section {
  margin-bottom: 20px;
}

.nav-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 8px;
  padding-left: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: var(--transition);
  margin-bottom: 4px;
  
  &:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
  
  &.active {
    background: var(--accent-color);
    color: white;
  }
}

.conversation-list {
  max-height: 300px;
  overflow-y: auto;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition);
  margin-bottom: 2px;
  
  &:hover {
    background: var(--bg-hover);
    
    .more-btn {
      opacity: 1;
    }
  }
  
  &.active {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  .conv-title {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.9rem;
  }
  
  .more-btn {
    opacity: 0;
    transition: opacity 0.2s;
    color: var(--text-secondary);
  }
}

.no-conversations {
  padding: 12px;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.user-area {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 12px;
  border-top: 1px solid var(--border-color);
  margin-top: auto;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .user-avatar {
    background: var(--accent-color);
    color: white;
  }
  
  .username {
    font-size: 0.95rem;
    color: var(--text-primary);
    font-weight: 500;
  }
}

.logout-btn {
  color: var(--text-secondary);
  font-size: 1.2rem;
  
  &:hover {
    color: var(--danger-color);
  }
}

.collapse-btn {
  position: absolute;
  right: -14px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: var(--transition);
  z-index: 10;
  
  &:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
}

.main-content {
  flex: 1;
  overflow: hidden;
  background: var(--bg-primary);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
