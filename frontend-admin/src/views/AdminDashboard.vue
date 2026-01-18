<template>
  <div class="admin-dashboard">
    <!-- 顶部导航 -->
    <header class="dashboard-header">
      <div class="header-left">
        <span class="logo-icon">📊</span>
        <span class="logo-text">管理后台</span>
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
        
        <!-- 统计图表 -->
        <div class="charts-row">
          <!-- 高频问题 -->
          <section class="section half">
            <h2 class="section-title">
              <el-icon><QuestionFilled /></el-icon>
              高频问题 Top 10
            </h2>
            <div class="chart-container">
              <div ref="topQuestionsChart" class="chart"></div>
            </div>
          </section>
          
          <!-- 知识库分类 -->
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

const userGrowthChart = ref(null)
const messageGrowthChart = ref(null)
const topQuestionsChart = ref(null)
const categoryChart = ref(null)

const todayGrowth = computed(() => {
  const growth = stats.value?.user_growth || []
  if (growth.length >= 2) {
    return growth[growth.length - 1]?.count - growth[growth.length - 2]?.count || 0
  }
  return 0
})

onMounted(async () => {
  console.log('AdminDashboard mounted')
  console.log('Admin store state:', adminStore.$state)
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
  initTopQuestionsChart()
  initCategoryChart()
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
        textStyle: { color: '#8e8e8e', fontSize: 14 }
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
      axisLabel: { color: '#8e8e8e', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: '#8e8e8e' },
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
      backgroundColor: '#2a2a2a',
      borderColor: '#3f3f3f',
      textStyle: { color: '#ececec' }
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
        textStyle: { color: '#8e8e8e', fontSize: 14 }
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
      axisLabel: { color: '#8e8e8e', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: '#8e8e8e' },
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
      backgroundColor: '#2a2a2a',
      borderColor: '#3f3f3f',
      textStyle: { color: '#ececec' }
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
        textStyle: { color: '#8e8e8e', fontSize: 14 }
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
      axisLabel: { color: '#8e8e8e' },
      splitLine: { lineStyle: { color: '#2f2f2f', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: questions.reverse(),
      axisLine: { lineStyle: { color: '#3f3f3f' } },
      axisLabel: { color: '#ececec', fontSize: 11 }
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
        color: '#ececec',
        fontSize: 11
      },
      barMaxWidth: 30
    }],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#2a2a2a',
      borderColor: '#3f3f3f',
      textStyle: { color: '#ececec' }
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
        textStyle: { color: '#8e8e8e', fontSize: 14 }
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
        color: '#ececec',
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
      backgroundColor: '#2a2a2a',
      borderColor: '#3f3f3f',
      textStyle: { color: '#ececec' }
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
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .logo-icon {
      font-size: 1.8rem;
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
  grid-template-columns: repeat(4, 1fr);
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
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-row {
    flex-direction: column;
    
    .section.half {
      width: 100%;
    }
  }
}
</style>
