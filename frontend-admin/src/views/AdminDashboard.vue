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
        <router-link to="/users" class="nav-link">用户管理</router-link>
      </div>
      <div class="header-right">
        <el-button 
          class="theme-toggle-btn" 
          circle 
          @click="toggleTheme" 
          :title="isDark ? '切换到浅色模式' : '切换到深色模式'"
          style="margin-right: 16px;"
        >
          <el-icon :size="16">
            <Sunny v-if="isDark" />
            <Moon v-else />
          </el-icon>
        </el-button>
        <span class="admin-name">{{ adminStore.username }}</span>
        <el-button type="danger" plain size="small" @click="handleLogout">
          退出登录
        </el-button>
      </div>
    </header>
    
    <!-- 主内容区 -->
    <main class="dashboard-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>加载数据中...</p>
      </div>
      
      <!-- 统计内容 -->
      <div v-else-if="stats" class="stats-container fade-in">
        <!-- 概览卡片 -->
        <section class="section">
          <h2 class="section-title">
            <el-icon><TrendCharts /></el-icon>
            系统概览
          </h2>
          <div class="stats-cards">
            <div class="stat-card">
              <div class="stat-icon users">👥</div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.total_users }}</span>
                <span class="stat-label">用户总数</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon conversations">💬</div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.total_conversations }}</span>
                <span class="stat-label">对话总数</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon messages">📝</div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.total_messages }}</span>
                <span class="stat-label">消息总数</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon today">📈</div>
              <div class="stat-info">
                <span class="stat-value">{{ todayGrowth }}</span>
                <span class="stat-label">今日新增用户</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon feedback">👍</div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.satisfaction_rate }}%</span>
                <span class="stat-label">回答满意度</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon tokens">🔤</div>
              <div class="stat-info">
                <span class="stat-value">{{ formatTokens(stats.total_tokens) }}</span>
                <span class="stat-label">Token 总消耗</span>
              </div>
            </div>
          </div>
        </section>
        
        <!-- 用户增长趋势 -->
        <section class="section">
          <h2 class="section-title">
            <el-icon><DataLine /></el-icon>
            用户增长趋势（近30天）
          </h2>
          <div class="chart-container">
            <div ref="userGrowthChart" class="chart"></div>
          </div>
        </section>
        
        <!-- 问题增长趋势 -->
        <section class="section">
          <h2 class="section-title">
            <el-icon><ChatDotRound /></el-icon>
            问题增长趋势（近30天）
          </h2>
          <div class="chart-container">
            <div ref="messageGrowthChart" class="chart"></div>
          </div>
        </section>
        
        <!-- Token 使用趋势 -->
        <section class="section">
          <h2 class="section-title">
            <el-icon><Coin /></el-icon>
            Token 使用趋势（近30天）
          </h2>
          <div class="token-summary">
            <div class="token-item">
              <span class="token-count">{{ formatTokens(stats.total_tokens) }}</span>
              <span class="token-label">累计消耗</span>
            </div>
            <div class="token-item today">
              <span class="token-count">{{ formatTokens(stats.today_tokens) }}</span>
              <span class="token-label">今日消耗</span>
            </div>
          </div>
          <div class="chart-container">
            <div ref="tokenUsageChart" class="chart"></div>
          </div>
        </section>
        
        <!-- 满意度统计（整行） -->
        <section class="section">
          <h2 class="section-title">
            <el-icon><Star /></el-icon>
            用户满意度统计
          </h2>
          <div class="satisfaction-summary">
            <div class="satisfaction-item positive">
              <span class="satisfaction-count">{{ stats.positive_feedbacks }}</span>
              <span class="satisfaction-label">👍 好评</span>
            </div>
            <div class="satisfaction-item negative">
              <span class="satisfaction-count">{{ stats.negative_feedbacks }}</span>
              <span class="satisfaction-label">👎 差评</span>
            </div>
            <div class="satisfaction-item total">
              <span class="satisfaction-count">{{ stats.total_feedbacks }}</span>
              <span class="satisfaction-label">总反馈</span>
            </div>
          </div>
          <div class="chart-container">
            <div ref="feedbackChart" class="chart"></div>
          </div>
        </section>
        
        <!-- 高频问题 + 知识库分类（共一行） -->
        <div class="charts-row">
          <section class="section half">
            <h2 class="section-title">
              <el-icon><QuestionFilled /></el-icon>
              高频问题 Top 10
            </h2>
            <div class="chart-container">
              <div ref="topQuestionsChart" class="chart"></div>
            </div>
          </section>
          
          <section class="section half">
            <h2 class="section-title">
              <el-icon><PieChart /></el-icon>
              知识库分类统计
            </h2>
            <div class="chart-container">
              <div ref="categoryChart" class="chart"></div>
            </div>
          </section>
        </div>
      </div>
      
      <!-- 错误状态 -->
      <div v-else class="error-state">
        <el-icon :size="48"><WarningFilled /></el-icon>
        <p>获取数据失败</p>
        <el-button type="primary" @click="fetchData">重新加载</el-button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'

const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(true)
const stats = ref(null)
const isDark = ref(false)

// 切换主题
const toggleTheme = () => {
  isDark.value = !isDark.value
  
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

const userGrowthChart = ref(null)
const messageGrowthChart = ref(null)
const feedbackChart = ref(null)
const topQuestionsChart = ref(null)
const categoryChart = ref(null)
const tokenUsageChart = ref(null)

const todayGrowth = computed(() => {
  const growth = stats.value?.user_growth || []
  if (growth.length >= 2) {
    return growth[growth.length - 1]?.count - growth[growth.length - 2]?.count || 0
  }
  return 0
})

const formatTokens = (num) => {
  if (!num) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

onMounted(async () => {
  console.log('AdminDashboard mounted')
  console.log('Admin store state:', adminStore.$state)
  
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'light') {
    isDark.value = false
    document.documentElement.classList.remove('dark')
  } else {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }

  await fetchData()
})

const fetchData = async () => {
  loading.value = true
  console.log('Fetching stats...')
  console.log('Token:', adminStore.token)
  
  const result = await adminStore.fetchStats()
  console.log('Fetch result:', result)
  
  loading.value = false
  
  if (result.success) {
    stats.value = result.data
    console.log('Stats loaded:', result.data)
    console.log('Stats ref:', stats)
    // 等待 DOM 完全渲染
    await nextTick()
    // 再等待一帧确保 DOM 已挂载
    setTimeout(() => {
      console.log('Stats after timeout:', stats.value)
      if (stats.value) {
        initCharts()
      }
    }, 100)
  } else {
    console.error('Failed to fetch stats:', result.error)
    ElMessage.error(result.error || '获取统计数据失败')
  }
}

const initCharts = () => {
  console.log('Initializing charts...')
  console.log('userGrowthChart ref:', userGrowthChart.value)
  console.log('messageGrowthChart ref:', messageGrowthChart.value)
  console.log('topQuestionsChart ref:', topQuestionsChart.value)
  console.log('categoryChart ref:', categoryChart.value)
  
  initUserGrowthChart()
  initMessageGrowthChart()
  initFeedbackChart()
  initTopQuestionsChart()
  initCategoryChart()
  initTokenUsageChart()
}

const initUserGrowthChart = () => {
  if (!userGrowthChart.value) return
  
  const chart = echarts.init(userGrowthChart.value)
  const data = stats.value?.user_growth || []
  
  // 如果没有数据，显示空状态
  if (data.length === 0) {
    chart.setOption({
      backgroundColor: 'transparent',
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: { color: 'var(--text-secondary)', fontSize: 14 }
      }
    })
    return
  }
  
  chart.setOption({
    backgroundColor: 'transparent',
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: 'var(--text-secondary)', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: 'var(--text-secondary)' },
      splitLine: { lineStyle: { color: '#2f2f2f', type: 'dashed' } }
    },
    series: [{
      type: 'line',
      smooth: true,
      data: data.map(d => d.count),
      lineStyle: { color: '#10a37f', width: 3 },
      itemStyle: { color: '#10a37f' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(16,163,127,0.3)' },
          { offset: 1, color: 'rgba(16,163,127,0.05)' }
        ])
      }
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'var(--bg-tertiary)',
      borderColor: 'var(--border-color)',
      textStyle: { color: 'var(--text-primary)' }
    }
  })
  
  window.addEventListener('resize', () => chart.resize())
}

const initMessageGrowthChart = () => {
  if (!messageGrowthChart.value) return
  
  const chart = echarts.init(messageGrowthChart.value)
  const data = stats.value?.message_growth || []
  
  // 如果没有数据，显示空状态
  if (data.length === 0) {
    chart.setOption({
      backgroundColor: 'transparent',
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: { color: 'var(--text-secondary)', fontSize: 14 }
      }
    })
    return
  }
  
  chart.setOption({
    backgroundColor: 'transparent',
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: 'var(--text-secondary)', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: 'var(--text-secondary)' },
      splitLine: { lineStyle: { color: '#2f2f2f', type: 'dashed' } }
    },
    series: [{
      type: 'line',
      smooth: true,
      data: data.map(d => d.count),
      lineStyle: { color: '#3b82f6', width: 3 },
      itemStyle: { color: '#3b82f6' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59,130,246,0.3)' },
          { offset: 1, color: 'rgba(59,130,246,0.05)' }
        ])
      }
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'var(--bg-tertiary)',
      borderColor: 'var(--border-color)',
      textStyle: { color: 'var(--text-primary)' }
    }
  })
  
  window.addEventListener('resize', () => chart.resize())
}

const initFeedbackChart = () => {
  if (!feedbackChart.value) return
  
  const chart = echarts.init(feedbackChart.value)
  const data = stats.value?.feedback_trend || []
  
  if (data.length === 0) {
    chart.setOption({
      backgroundColor: 'transparent',
      title: {
        text: '暂无反馈数据',
        left: 'center',
        top: 'center',
        textStyle: { color: 'var(--text-secondary)', fontSize: 14 }
      }
    })
    return
  }
  
  chart.setOption({
    backgroundColor: 'transparent',
    grid: {
      left: '3%', right: '4%', bottom: '3%', top: '10%',
      containLabel: true
    },
    legend: {
      data: ['好评', '差评'],
      textStyle: { color: 'var(--text-secondary)' },
      top: 0
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: 'var(--text-secondary)', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: 'var(--text-secondary)' },
      splitLine: { lineStyle: { color: '#2f2f2f', type: 'dashed' } }
    },
    series: [
      {
        name: '好评',
        type: 'bar',
        stack: 'total',
        data: data.map(d => d.positive),
        itemStyle: { color: '#10a37f', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 20
      },
      {
        name: '差评',
        type: 'bar',
        stack: 'total',
        data: data.map(d => d.negative),
        itemStyle: { color: '#ff6b6b', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 20
      }
    ],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'var(--bg-tertiary)',
      borderColor: 'var(--border-color)',
      textStyle: { color: 'var(--text-primary)' }
    }
  })
  
  window.addEventListener('resize', () => chart.resize())
}

const initTopQuestionsChart = () => {
  if (!topQuestionsChart.value) return
  
  const chart = echarts.init(topQuestionsChart.value)
  const data = stats.value?.top_questions || []
  
  // 如果没有数据，显示空状态
  if (data.length === 0) {
    chart.setOption({
      backgroundColor: 'transparent',
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: { color: 'var(--text-secondary)', fontSize: 14 }
      }
    })
    return
  }
  
  const questions = data.map(d => {
    const q = d.question || ''
    return q.length > 15 ? q.slice(0, 15) + '...' : q
  })
  const counts = data.map(d => d.count)
  
  chart.setOption({
    backgroundColor: 'transparent',
    grid: {
      left: '3%',
      right: '15%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: 'var(--text-secondary)' },
      splitLine: { lineStyle: { color: '#2f2f2f', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: questions.reverse(),
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: 'var(--text-primary)', fontSize: 11 }
    },
    series: [{
      type: 'bar',
      data: counts.reverse(),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#10a37f' },
          { offset: 1, color: '#0e8c6d' }
        ]),
        borderRadius: [0, 4, 4, 0]
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{c} 次',
        color: 'var(--text-primary)',
        fontSize: 11
      },
      barMaxWidth: 30
    }],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'var(--bg-tertiary)',
      borderColor: 'var(--border-color)',
      textStyle: { color: 'var(--text-primary)' }
    }
  })
  
  window.addEventListener('resize', () => chart.resize())
}

const initCategoryChart = () => {
  if (!categoryChart.value) return
  
  const chart = echarts.init(categoryChart.value)
  const data = stats.value?.category_stats || []
  
  // 如果没有数据，显示空状态
  if (data.length === 0) {
    chart.setOption({
      backgroundColor: 'transparent',
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: { color: 'var(--text-secondary)', fontSize: 14 }
      }
    })
    return
  }
  
  const colors = ['#10a37f', '#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#e91e63', '#00bcd4']
  
  chart.setOption({
    backgroundColor: 'transparent',
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      data: data.map((d, i) => ({
        name: d.category,
        value: d.count,
        itemStyle: { color: colors[i % colors.length] }
      })),
      label: {
        color: 'var(--text-primary)',
        fontSize: 12,
        formatter: '{b}: {c}'
      },
      labelLine: {
        lineStyle: { color: '#6e6e6e' }
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }],
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'var(--bg-tertiary)',
      borderColor: 'var(--border-color)',
      textStyle: { color: 'var(--text-primary)' }
    }
  })
  
  window.addEventListener('resize', () => chart.resize())
}

const initTokenUsageChart = () => {
  if (!tokenUsageChart.value) return
  
  const chart = echarts.init(tokenUsageChart.value)
  const data = stats.value?.token_trend || []
  
  if (data.length === 0) {
    chart.setOption({
      backgroundColor: 'transparent',
      title: {
        text: '暂无 Token 使用数据',
        left: 'center',
        top: 'center',
        textStyle: { color: 'var(--text-secondary)', fontSize: 14 }
      }
    })
    return
  }
  
  chart.setOption({
    backgroundColor: 'transparent',
    grid: {
      left: '3%', right: '4%', bottom: '3%', top: '15%',
      containLabel: true
    },
    legend: {
      data: ['Prompt Tokens', 'Completion Tokens'],
      textStyle: { color: 'var(--text-secondary)' },
      top: 0
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: 'var(--text-secondary)', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: 'var(--text-secondary)' },
      splitLine: { lineStyle: { color: '#2f2f2f', type: 'dashed' } }
    },
    series: [
      {
        name: 'Prompt Tokens',
        type: 'bar',
        stack: 'tokens',
        data: data.map(d => d.prompt_tokens),
        itemStyle: { color: '#3b82f6', borderRadius: [0, 0, 0, 0] },
        barMaxWidth: 24
      },
      {
        name: 'Completion Tokens',
        type: 'bar',
        stack: 'tokens',
        data: data.map(d => d.completion_tokens),
        itemStyle: { color: '#10a37f', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 24
      }
    ],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'var(--bg-tertiary)',
      borderColor: 'var(--border-color)',
      textStyle: { color: 'var(--text-primary)' },
      formatter: function(params) {
        let total = 0
        let html = params[0].axisValue + '<br/>'
        params.forEach(p => {
          total += p.value
          html += p.marker + ' ' + p.seriesName + ': ' + p.value.toLocaleString() + '<br/>'
        })
        html += '<b>合计: ' + total.toLocaleString() + '</b>'
        return html
      }
    }
  })
  
  window.addEventListener('resize', () => chart.resize())
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '确认退出', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'info'
    })
    
    adminStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style lang="scss" scoped>
.admin-dashboard {
  min-height: 100vh;
  height: 100vh;
  overflow-y: auto;
  background: var(--bg-primary);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;

  .header-right {
    display: flex;
    align-items: center;

    .theme-toggle-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-primary);
      transition: var(--transition);
      
      &:hover {
        background: var(--bg-hover);
        color: var(--accent-color);
        border-color: var(--accent-color);
      }
    }
  }
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .logo-icon {
      width: 32px;
      height: 32px;
      object-fit: contain;
      border-radius: 6px;
    }
    
    .logo-text {
      font-size: 1.3rem;
      font-weight: 600;
      color: var(--text-primary);
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .admin-name {
      color: var(--text-secondary);
      font-size: 0.95rem;
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
      
      &.router-link-active {
        background: rgba(16, 163, 127, 0.15);
        color: #10a37f;
        font-weight: 600;
      }
    }
  }
}

.dashboard-content {
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  color: var(--text-secondary);
  
  p {
    margin: 16px 0;
    font-size: 1rem;
  }
}

.section {
  margin-bottom: 32px;
  
  &.half {
    width: calc(50% - 16px);
  }
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
  
  .el-icon {
    color: var(--accent-color);
  }
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  transition: var(--transition);
  
  &:hover {
    border-color: var(--accent-color);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }
  
  .stat-icon {
    font-size: 2.5rem;
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    
    &.users { background: rgba(16, 163, 127, 0.15); }
    &.conversations { background: rgba(52, 152, 219, 0.15); }
    &.messages { background: rgba(155, 89, 182, 0.15); }
    &.today { background: rgba(243, 156, 18, 0.15); }
    &.feedback { background: rgba(16, 163, 127, 0.15); }
    &.tokens { background: rgba(59, 130, 246, 0.15); }
  }
  
  .stat-info {
    display: flex;
    flex-direction: column;
    
    .stat-value {
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--text-primary);
    }
    
    .stat-label {
      font-size: 0.9rem;
      color: var(--text-secondary);
      margin-top: 4px;
    }
  }
}

.satisfaction-summary {
  display: flex;
  gap: 20px;
  margin-top: 12px;
  
  .satisfaction-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 16px;
    border-radius: 10px;
    background: var(--bg-primary);
    flex: 1;
    
    .satisfaction-count {
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--text-primary);
    }
    
    .satisfaction-label {
      font-size: 0.8rem;
      color: var(--text-secondary);
      margin-top: 4px;
    }
    
    &.positive .satisfaction-count { color: #10a37f; }
    &.negative .satisfaction-count { color: #ff6b6b; }
  }
}

.token-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  
  .token-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px 24px;
    border-radius: 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    flex: 1;
    max-width: 200px;
    
    .token-count {
      font-size: 1.6rem;
      font-weight: 700;
      color: #3b82f6;
    }
    
    .token-label {
      font-size: 0.8rem;
      color: var(--text-secondary);
      margin-top: 4px;
    }
    
    &.today .token-count { color: #f59e0b; }
  }
}

.chart-container {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
  
  .chart {
    width: 100%;
    height: 350px;
  }
}

.charts-row {
  display: flex;
  gap: 32px;
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr) !important;
  }
  
  .charts-row {
    flex-direction: column;
    
    .section.half {
      width: 100%;
    }
  }
}
</style>
