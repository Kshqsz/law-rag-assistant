<template>
  <div class="app-container" :class="{ 'dark': isDark }">
    <router-view />
  </div>
</template>

<script setup>
import { ref } from 'vue'

// 默认使用暗色主题
const isDark = ref(true)
document.documentElement.classList.add('dark')
</script>

<style lang="scss">
.app-container {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>
