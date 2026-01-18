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
import jsPDF from 'jspdf'
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
    
    // 创建 PDF
    const doc = new jsPDF()
    
    // 设置字体 (jsPDF 默认不支持中文，需要使用特殊处理)
    let yPos = 20
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 20
    const maxWidth = pageWidth - 2 * margin
    
    // 标题
    doc.setFontSize(16)
    doc.text(title, margin, yPos)
    yPos += 15
    
    // 添加时间
    doc.setFontSize(10)
    doc.text(`导出时间: ${new Date().toLocaleString('zh-CN')}`, margin, yPos)
    yPos += 15
    
    // 遍历消息
    for (const msg of messages) {
      // 检查是否需要新页面
      if (yPos > pageHeight - 40) {
        doc.addPage()
        yPos = 20
      }
      
      // 角色标识
      doc.setFontSize(12)
      const role = msg.role === 'user' ? '用户' : 'AI助手'
      doc.text(`${role}:`, margin, yPos)
      yPos += 8
      
      // 消息内容
      doc.setFontSize(10)
      const lines = doc.splitTextToSize(msg.content, maxWidth)
      
      for (const line of lines) {
        if (yPos > pageHeight - 30) {
          doc.addPage()
          yPos = 20
        }
        doc.text(line, margin, yPos)
        yPos += 6
      }
      
      yPos += 10
    }
    
    // 保存 PDF
    doc.save(`${title}.pdf`)
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
