<template>
  <div class="favorites-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Star /></el-icon>
        收藏夹
      </h1>
      <p class="page-desc">您收藏的法律问答</p>
    </div>
    
    <div class="favorites-container">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        加载中...
      </div>
      
      <div v-else-if="favorites.length === 0" class="empty-state">
        <el-icon size="48"><Star /></el-icon>
        <p>暂无收藏</p>
        <span>收藏重要的法律问答，方便随时查阅</span>
      </div>
      
      <div v-else class="favorites-list">
        <div 
          v-for="item in favorites" 
          :key="item.id" 
          class="favorite-card fade-in"
        >
          <div class="card-header">
            <div class="question">
              <el-icon><QuestionFilled /></el-icon>
              <span>{{ item.question }}</span>
            </div>
            <div class="card-actions">
              <el-button link @click="viewDetail(item)">
                <el-icon><View /></el-icon>
              </el-button>
              <el-button link @click="deleteFavorite(item.id)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          
          <div class="answer-preview">
            {{ truncateText(item.answer, 200) }}
          </div>
          
          <div class="card-meta">
            <span class="time">
              <el-icon><Clock /></el-icon>
              {{ formatDate(item.created_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 详情弹窗 -->
    <el-dialog 
      v-model="detailVisible" 
      title="收藏详情" 
      width="700px"
      class="detail-dialog"
    >
      <div v-if="currentItem" class="detail-content">
        <div class="detail-section">
          <h3>
            <el-icon><QuestionFilled /></el-icon>
            问题
          </h3>
          <p>{{ currentItem.question }}</p>
        </div>
        
        <div class="detail-section">
          <h3>
            <el-icon><ChatDotRound /></el-icon>
            回答
          </h3>
          <div class="answer-text" v-html="renderMarkdown(currentItem.answer)"></div>
        </div>
        
        <el-collapse v-if="currentItem.law_context">
          <el-collapse-item title="📚 法律依据">
            <div v-html="renderMarkdown(currentItem.law_context)"></div>
          </el-collapse-item>
        </el-collapse>
        
        <el-collapse v-if="currentItem.web_results">
          <el-collapse-item title="🌐 网络来源">
            <div v-html="renderMarkdown(currentItem.web_results)"></div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()

const favorites = ref([])
const loading = ref(true)
const detailVisible = ref(false)
const currentItem = ref(null)

onMounted(async () => {
  await fetchFavorites()
})

const fetchFavorites = async () => {
  loading.value = true
  try {
    const res = await api.getFavorites()
    favorites.value = res.favorites || []
  } catch (error) {
    console.error('获取收藏失败:', error)
  } finally {
    loading.value = false
  }
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.slice(0, maxLength) + '...' : text
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const renderMarkdown = (text) => {
  if (!text) return ''
  return md.render(text)
}

const viewDetail = (item) => {
  currentItem.value = item
  detailVisible.value = true
}

const deleteFavorite = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条收藏吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.deleteFavorite(id)
    favorites.value = favorites.value.filter(f => f.id !== id)
    ElMessage.success('已删除')
  } catch {
    // 用户取消
  }
}
</script>

<style lang="scss" scoped>
.favorites-page {
  height: 100%;
  overflow-y: auto;
  padding: 40px;
}

.page-header {
  max-width: 900px;
  margin: 0 auto 40px;
  
  .page-title {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
    
    .el-icon {
      color: var(--warning-color);
    }
  }
  
  .page-desc {
    color: var(--text-secondary);
    font-size: 1rem;
  }
}

.favorites-container {
  max-width: 900px;
  margin: 0 auto;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--text-secondary);
  
  .el-icon {
    font-size: 48px;
    margin-bottom: 16px;
    color: var(--text-muted);
  }
  
  p {
    font-size: 1.1rem;
    margin-bottom: 8px;
  }
  
  span {
    font-size: 0.9rem;
    color: var(--text-muted);
  }
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.favorite-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px 24px;
  transition: var(--transition);
  
  &:hover {
    border-color: var(--accent-color);
    box-shadow: 0 4px 20px rgba(16, 163, 127, 0.1);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  
  .question {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 1.05rem;
    font-weight: 500;
    color: var(--text-primary);
    
    .el-icon {
      color: var(--accent-color);
      margin-top: 3px;
      flex-shrink: 0;
    }
  }
  
  .card-actions {
    display: flex;
    gap: 4px;
    
    .el-button {
      color: var(--text-muted);
      
      &:hover {
        color: var(--accent-color);
      }
      
      &:last-child:hover {
        color: var(--danger-color);
      }
    }
  }
}

.answer-preview {
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1.7;
  margin-bottom: 12px;
}

.card-meta {
  .time {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    color: var(--text-muted);
  }
}

.detail-dialog {
  :deep(.el-dialog__header) {
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-color);
  }
  
  :deep(.el-dialog__body) {
    padding: 24px;
    max-height: 60vh;
    overflow-y: auto;
  }
}

.detail-content {
  .detail-section {
    margin-bottom: 24px;
    
    h3 {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 12px;
      
      .el-icon {
        color: var(--accent-color);
      }
    }
    
    p {
      color: var(--text-secondary);
      line-height: 1.7;
    }
    
    .answer-text {
      color: var(--text-secondary);
      line-height: 1.7;
      
      :deep(p) {
        margin-bottom: 0.8em;
      }
    }
  }
  
  .el-collapse {
    border: none;
    margin-top: 16px;
    
    :deep(.el-collapse-item__header) {
      background: transparent;
      border: none;
      color: var(--text-secondary);
    }
    
    :deep(.el-collapse-item__wrap) {
      background: transparent;
      border: none;
    }
    
    :deep(.el-collapse-item__content) {
      color: var(--text-secondary);
      line-height: 1.6;
    }
  }
}
</style>
