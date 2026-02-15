<template>
  <div class="admin-dashboard">
    <!-- 顶部导航 -->
    <header class="dashboard-header">
      <div class="header-left">
        <img src="/image/logo/logo.png" class="logo-icon" alt="法律AI助手" />
        <span class="logo-text">管理后台</span>
      </div>
      <div class="header-center">
        <router-link to="/dashboard" class="nav-link">数据统计</router-link>
        <router-link to="/users" class="nav-link active">用户管理</router-link>
      </div>
      <div class="header-right">
        <span class="admin-name">{{ adminStore.username }}</span>
        <el-button type="danger" plain size="small" @click="handleLogout">
          退出登录
        </el-button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="dashboard-content">
      <!-- 搜索栏 -->
      <section class="section">
        <div class="search-bar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用户名..."
            clearable
            @clear="fetchUsers"
            @keyup.enter="fetchUsers"
            style="width: 300px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="fetchUsers">搜索</el-button>
          <span class="total-info">共 {{ total }} 个用户</span>
        </div>
      </section>

      <!-- 用户表格 -->
      <section class="section">
        <el-table
          :data="users"
          v-loading="loading"
          stripe
          style="width: 100%"
          :header-cell-style="{ background: 'var(--bg-secondary)', color: 'var(--text-primary)' }"
          :cell-style="{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }"
        >
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '正常' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="角色" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_admin ? 'warning' : 'info'" size="small">
                {{ row.is_admin ? '管理员' : '用户' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="conversation_count" label="对话数" width="90" />
          <el-table-column prop="message_count" label="提问数" width="90" />
          <el-table-column label="注册时间" width="170">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button
                :type="row.is_active ? 'warning' : 'success'"
                size="small"
                plain
                @click="toggleActive(row)"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button
                type="info"
                size="small"
                plain
                @click="resetPassword(row)"
              >
                重置密码
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-wrapper" v-if="total > pageSize">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next, total"
            @current-change="fetchUsers"
          />
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const users = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')

onMounted(() => {
  fetchUsers()
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await api.getUsers(currentPage.value, pageSize.value, searchKeyword.value)
    users.value = res.users || []
    total.value = res.total || 0
  } catch (e) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const d = new Date(timeStr)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const toggleActive = async (user) => {
  const action = user.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户「${user.username}」吗？`, '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.updateUser(user.id, { is_active: !user.is_active })
    ElMessage.success(`已${action}用户「${user.username}」`)
    await fetchUsers()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`操作失败: ${e.message || e}`)
  }
}

const resetPassword = async (user) => {
  try {
    const { value: newPassword } = await ElMessageBox.prompt(
      `请输入用户「${user.username}」的新密码`,
      '重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^.{6,}$/,
        inputErrorMessage: '密码至少6个字符'
      }
    )
    await api.updateUser(user.id, { new_password: newPassword })
    ElMessage.success(`用户「${user.username}」密码已重置`)
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`操作失败: ${e.message || e}`)
  }
}

const handleLogout = () => {
  adminStore.logout()
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.admin-dashboard {
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .logo-icon {
      width: 36px;
      height: 36px;
      border-radius: 8px;
    }
    
    .logo-text {
      font-size: 1.3rem;
      font-weight: 700;
      background: linear-gradient(135deg, #10a37f 0%, #1a7f5a 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }
  
  .header-center {
    display: flex;
    gap: 8px;
    
    .nav-link {
      padding: 8px 20px;
      border-radius: 8px;
      color: var(--text-secondary);
      text-decoration: none;
      font-size: 0.95rem;
      transition: all 0.2s;
      
      &:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
      }
      
      &.router-link-active, &.active {
        background: rgba(16, 163, 127, 0.15);
        color: #10a37f;
        font-weight: 600;
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .admin-name {
      color: var(--text-secondary);
    }
  }
}

.dashboard-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px;
}

.section {
  margin-bottom: 24px;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .total-info {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-left: 16px;
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

:deep(.el-table) {
  --el-table-bg-color: var(--bg-tertiary);
  --el-table-tr-bg-color: var(--bg-tertiary);
  --el-table-header-bg-color: var(--bg-secondary);
  --el-table-border-color: var(--border-color);
  --el-table-text-color: var(--text-primary);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

:deep(.el-table .el-table__row:hover > td) {
  background-color: var(--bg-secondary) !important;
}

:deep(.el-pagination) {
  --el-pagination-bg-color: var(--bg-tertiary);
  --el-pagination-text-color: var(--text-primary);
  --el-pagination-button-bg-color: var(--bg-secondary);
}
</style>
