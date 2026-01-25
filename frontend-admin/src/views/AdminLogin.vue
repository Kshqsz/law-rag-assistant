<template>
  <div class="admin-login-page">
    <div class="login-container fade-in">
      <!-- Logo -->
      <div class="logo-section">
        <img src="/image/logo/logo.png" class="logo-icon" alt="法律AI助手" />
        <h1 class="logo-title">管理员后台</h1>
        <p class="logo-subtitle">法律AI助手 - 数据统计与分析</p>
      </div>
      
      <!-- 登录表单 -->
      <el-form 
        ref="loginFormRef" 
        :model="loginForm" 
        :rules="loginRules"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="请输入管理员账号"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            :loading="loading"
            class="submit-btn"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'

const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const loginFormRef = ref()

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  const result = await adminStore.login(loginForm.username, loginForm.password)
  loading.value = false
  
  if (result.success) {
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } else {
    ElMessage.error(result.message || '登录失败')
  }
}
</script>

<style lang="scss" scoped>
.admin-login-page {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 50%, #1a1a2e 100%);
}

.login-container {
  width: 400px;
  padding: 48px 40px;
  background: var(--bg-tertiary);
  border-radius: 20px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
}

.logo-section {
  text-align: center;
  margin-bottom: 40px;
  
  .logo-icon {
    width: 100px;
    height: 100px;
    object-fit: contain;
    margin: 0 auto 16px;
    display: block;
    border-radius: 20px;
  }
  
  .logo-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }
  
  .logo-subtitle {
    font-size: 0.9rem;
    color: var(--text-secondary);
  }
}

.el-form-item {
  margin-bottom: 20px;
}

.submit-btn {
  width: 100%;
  height: 48px;
  font-size: 1rem;
  font-weight: 500;
  border-radius: 10px;
  margin-top: 8px;
}

.back-link {
  text-align: center;
  margin-top: 24px;
  
  a {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.9rem;
    transition: color 0.3s;
    
    &:hover {
      color: var(--accent-color);
    }
  }
}
</style>
