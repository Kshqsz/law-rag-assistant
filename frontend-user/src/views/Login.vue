<template>
  <div class="login-page">
    <div class="login-container fade-in">
      <!-- Logo -->
      <div class="logo-section">
        <img src="/image/logo/logo.png" class="logo-icon" alt="法律AI助手" />
        <h1 class="logo-title">法律AI助手</h1>
        <p class="logo-subtitle">基于 RAG 技术的智能法律问答系统</p>
      </div>
      
      <!-- 登录/注册表单 -->
      <el-tabs v-model="activeTab" class="auth-tabs" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form 
            ref="loginFormRef" 
            :model="loginForm" 
            :rules="loginRules"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="username">
              <el-input 
                v-model="loginForm.username" 
                placeholder="请输入用户名"
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
        </el-tab-pane>
        
        <el-tab-pane label="注册" name="register">
          <el-form 
            ref="registerFormRef" 
            :model="registerForm" 
            :rules="registerRules"
            @submit.prevent="handleRegister"
          >
            <el-form-item prop="username">
              <el-input 
                v-model="registerForm.username" 
                placeholder="请输入用户名"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input 
                v-model="registerForm.password" 
                type="password" 
                placeholder="请输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input 
                v-model="registerForm.confirmPassword" 
                type="password" 
                placeholder="请确认密码"
                size="large"
                prefix-icon="Lock"
                show-password
                @keyup.enter="handleRegister"
              />
            </el-form-item>
            <el-form-item>
              <el-button 
                type="primary" 
                size="large" 
                :loading="loading"
                class="submit-btn"
                @click="handleRegister"
              >
                注 册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('login')
const loading = ref(false)

const loginFormRef = ref()
const registerFormRef = ref()

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3-20个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  const result = await userStore.login(loginForm.username, loginForm.password)
  loading.value = false
  
  if (result.success) {
    ElMessage.success('登录成功')
    router.push('/')
  } else {
    ElMessage.error(result.message || '登录失败')
  }
}

const handleRegister = async () => {
  const valid = await registerFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  const result = await userStore.register(registerForm.username, registerForm.password)
  loading.value = false
  
  if (result.success) {
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
    loginForm.password = ''
  } else {
    ElMessage.error(result.message || '注册失败')
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%);
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

.auth-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 24px;
  }
  
  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }
  
  :deep(.el-tabs__item) {
    font-size: 1rem;
    font-weight: 500;
    padding: 0 24px;
    height: 44px;
    line-height: 44px;
  }
  
  :deep(.el-tabs__active-bar) {
    background-color: var(--accent-color);
    height: 3px;
    border-radius: 2px;
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
</style>
