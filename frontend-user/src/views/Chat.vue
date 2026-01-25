<template>
  <div class="chat-page">
    <!-- 消息列表 -->
    <div class="messages-container" ref="messagesContainer">
      <!-- 欢迎界面 -->
      <div v-if="chatStore.messages.length === 0" class="welcome-section fade-in">
        <img src="/image/logo/logo.png" class="welcome-icon" alt="法律AI助手" />
        <h1 class="welcome-title">法律AI助手</h1>
        <p class="welcome-desc">您好！我是您的智能法律顾问，可以为您解答法律相关问题</p>
        
        <div class="example-questions">
          <div 
            v-for="(item, index) in exampleQuestions" 
            :key="index"
            class="example-item"
            @click="sendExample(item.question)"
          >
            <span class="example-icon">{{ item.icon }}</span>
            <span class="example-text">{{ item.question }}</span>
          </div>
        </div>
      </div>
      
      <!-- 消息列表 -->
      <div v-else class="messages-list">
        <div 
          v-for="(msg, index) in chatStore.messages" 
          :key="index" 
          class="message-wrapper fade-in"
          :class="msg.role"
        >
          <div class="message">
            <div class="message-avatar">
              <span v-if="msg.role === 'user'">👤</span>
              <img v-else src="/image/logo/logo.png" class="avatar-icon" alt="AI" />
            </div>
            <div class="message-content">
              <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
              
              <!-- 流式输出时显示光标 -->
              <span v-if="msg.isStreaming" class="typing-cursor">|</span>
              
              <!-- 法律依据 -->
              <el-collapse v-if="msg.law_context" class="source-collapse">
                <el-collapse-item title="📚 法律依据">
                  <div class="source-content" v-html="renderMarkdown(msg.law_context)"></div>
                </el-collapse-item>
              </el-collapse>
              
              <!-- 网络来源 -->
              <el-collapse v-if="msg.web_results" class="source-collapse">
                <el-collapse-item title="🌐 网络来源">
                  <div class="source-content" v-html="renderMarkdown(msg.web_results)"></div>
                </el-collapse-item>
              </el-collapse>
              
              <!-- 操作按钮 -->
              <div v-if="msg.role === 'assistant' && !msg.isStreaming" class="message-actions">
                <el-button link size="small" @click="handleCopy(msg.content)">
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
                <el-button link size="small" @click="handleFavorite(msg, index)">
                  <el-icon><Star /></el-icon>
                  收藏
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-container">
        <!-- 上传文件显示 -->
        <div v-if="uploadedFile" class="uploaded-file">
          <el-icon><Document /></el-icon>
          <span>{{ uploadedFile.name }}</span>
          <el-button link @click="removeFile">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        
        <div class="input-wrapper">
          <el-button class="upload-btn" link @click="triggerUpload">
            <el-icon size="20"><Plus /></el-icon>
          </el-button>
          <input 
            ref="fileInput" 
            type="file" 
            accept=".txt,.md,.pdf" 
            hidden 
            @change="handleFileUpload"
          />
          
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 5 }"
            placeholder="输入您的法律问题..."
            resize="none"
            @keydown.enter.exact.prevent="sendMessage"
          />
          
          <el-button 
            class="send-btn" 
            type="primary" 
            circle
            :disabled="!inputMessage.trim() || chatStore.isLoading"
            @click="sendMessage"
          >
            <el-icon v-if="!chatStore.isLoading"><Promotion /></el-icon>
            <el-icon v-else class="is-loading"><Loading /></el-icon>
          </el-button>
        </div>
      </div>
      <p class="disclaimer">AI回答仅供参考，具体法律问题请咨询专业律师</p>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import api from '@/api'

const route = useRoute()
const chatStore = useChatStore()
const md = new MarkdownIt()

const inputMessage = ref('')
const messagesContainer = ref(null)
const fileInput = ref(null)
const uploadedFile = ref(null)
const uploadedDocumentId = ref(null)

const exampleQuestions = [
  { icon: '🏠', question: '租房合同应该注意什么？' },
  { icon: '💼', question: '劳动合同解除有哪些情形？' },
  { icon: '🚗', question: '交通事故责任如何认定？' },
  { icon: '📝', question: '民间借贷的诉讼时效是多久？' }
]

const renderMarkdown = (text) => {
  if (!text) return ''
  return md.render(text)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(() => chatStore.messages.length, scrollToBottom)
watch(() => chatStore.messages[chatStore.messages.length - 1]?.content, scrollToBottom)

// 监听对话 ID 变化，加载历史消息
watch(() => chatStore.currentConversationId, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    console.log('对话 ID 变化，加载消息:', newId)
    await chatStore.loadConversationMessages(newId)
  }
}, { immediate: true })

onMounted(async () => {
  // 如果 URL 中有对话 ID，加载该对话
  const conversationId = route.params.id
  if (conversationId && conversationId !== chatStore.currentConversationId) {
    chatStore.currentConversationId = parseInt(conversationId)
  }
})

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || chatStore.isLoading) return
  
  console.log('Sending message:', message)
  console.log('With document ID:', uploadedDocumentId.value)
  
  inputMessage.value = ''
  await chatStore.sendMessage(message, uploadedDocumentId.value)
  
  // 清除上传的文件
  uploadedFile.value = null
  uploadedDocumentId.value = null
}

const sendExample = (question) => {
  inputMessage.value = question
  sendMessage()
}

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileUpload = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  
  console.log('Uploading file:', file.name)
  
  try {
    const result = await api.uploadDocument(file)
    console.log('Upload result:', result)
    
    uploadedFile.value = file
    // 后端返回的是 DocumentResponse，字段是 id 不是 document_id
    uploadedDocumentId.value = result.id
    console.log('Document ID set to:', uploadedDocumentId.value)
    
    ElMessage.success('文件上传成功')
  } catch (error) {
    console.error('Upload error:', error)
    ElMessage.error('文件上传失败: ' + (error.message || '未知错误'))
  }
  
  // 重置 input
  e.target.value = ''
}

const removeFile = () => {
  uploadedFile.value = null
  uploadedDocumentId.value = null
}

const handleCopy = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

const handleFavorite = async (msg, index) => {
  const userMsg = chatStore.messages[index - 1]
  if (!userMsg || userMsg.role !== 'user') return
  
  try {
    await api.addFavorite(
      userMsg.content,
      msg.content,
      msg.law_context || '',
      msg.web_results || ''
    )
    ElMessage.success('已添加到收藏夹')
  } catch {
    ElMessage.error('收藏失败')
  }
}
</script>

<style lang="scss" scoped>
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome-section {
  max-width: 600px;
  margin: 100px auto;
  text-align: center;
  
  .welcome-icon {
    width: 120px;
    height: 120px;
    margin: 0 auto 20px;
    display: block;
    object-fit: contain;
    border-radius: 20px;
  }
  
  .welcome-title {
    font-size: 2rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 12px;
  }
  
  .welcome-desc {
    font-size: 1rem;
    color: var(--text-secondary);
    margin-bottom: 40px;
  }
}

.example-questions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.example-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: var(--transition);
  
  &:hover {
    background: var(--bg-hover);
    border-color: var(--accent-color);
    transform: translateY(-2px);
  }
  
  .example-icon {
    font-size: 1.5rem;
  }
  
  .example-text {
    font-size: 0.95rem;
    color: var(--text-primary);
    text-align: left;
  }
}

.messages-list {
  max-width: 800px;
  margin: 0 auto;
}

.message-wrapper {
  margin-bottom: 24px;
  
  &.user .message {
    flex-direction: row-reverse;
    
    .message-content {
      background: var(--accent-color);
      color: white;
      border-radius: 20px 20px 4px 20px;
    }
  }
  
  &.assistant .message-content {
    background: var(--bg-tertiary);
    border-radius: 20px 20px 20px 4px;
  }
}

.message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
  
  .avatar-icon {
    width: 28px;
    height: 28px;
    object-fit: contain;
    border-radius: 50%;
  }
}

.message-content {
  max-width: 70%;
  padding: 14px 18px;
  
  .message-text {
    line-height: 1.7;
    
    :deep(p) {
      margin-bottom: 0.8em;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
    
    :deep(ul), :deep(ol) {
      padding-left: 1.5em;
      margin: 0.5em 0;
    }
    
    :deep(code) {
      background: rgba(0, 0, 0, 0.2);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.9em;
    }
    
    :deep(pre) {
      background: rgba(0, 0, 0, 0.3);
      padding: 12px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 0.5em 0;
      
      code {
        background: none;
        padding: 0;
      }
    }
  }
}

.typing-cursor {
  animation: blink 1s infinite;
  color: var(--accent-color);
  font-weight: bold;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.source-collapse {
  margin-top: 12px;
  
  :deep(.el-collapse-item__header) {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-size: 0.85rem;
    height: 32px;
    line-height: 32px;
  }
  
  :deep(.el-collapse-item__wrap) {
    background: transparent;
    border: none;
  }
  
  :deep(.el-collapse-item__content) {
    padding: 12px 0 0;
  }
  
  .source-content {
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 1.6;
  }
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color);
  
  .el-button {
    color: var(--text-secondary);
    
    &:hover {
      color: var(--accent-color);
    }
  }
}

.input-area {
  padding: 20px;
  background: var(--bg-primary);
  border-top: 1px solid var(--border-color);
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.uploaded-file {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: var(--text-secondary);
  
  .el-button {
    color: var(--text-muted);
    
    &:hover {
      color: var(--danger-color);
    }
  }
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 24px;
  transition: var(--transition);
  
  &:focus-within {
    border-color: var(--accent-color);
  }
  
  .upload-btn {
    color: var(--text-secondary);
    padding: 8px;
    
    &:hover {
      color: var(--accent-color);
    }
  }
  
  :deep(.el-textarea__inner) {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 8px 0;
    font-size: 1rem;
    line-height: 1.5;
    color: var(--text-primary);
    
    &::placeholder {
      color: var(--text-muted);
    }
  }
  
  .send-btn {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
  }
}

.disclaimer {
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 12px;
}
</style>
