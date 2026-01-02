<template>
  <div class="home-container" :style="{ background: themeColors.background }">
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="gradient-orb orb-1" :style="{ background: themeColors.orb1 }"></div>
      <div class="gradient-orb orb-2" :style="{ background: themeColors.orb2 }"></div>
      <div class="gradient-orb orb-3" :style="{ background: themeColors.orb3 }"></div>
    </div>

    <!-- 主题切换按钮 -->
    <div class="theme-toggle" @click="toggleTheme" :style="{ color: themeColors.title }">
      <svg v-if="appStore.isDark" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"/>
        <line x1="12" y1="1" x2="12" y2="3"/>
        <line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1" y1="12" x2="3" y2="12"/>
        <line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
      </svg>
    </div>

    <!-- 主内容区 -->
    <div class="content-wrapper">
      <!-- 标题区域 -->
      <div class="title-section">
        <h1 class="main-title" :style="{ color: themeColors.title }">欢迎使用翱翔军事大模型</h1>
        <h2 class="sub-title" :style="{ color: themeColors.subtitle }">军文智写助手</h2>
        <p class="description" :style="{ color: themeColors.description }">智能化军事文档生成与知识管理平台</p>
      </div>

      <!-- 功能卡片区域 -->
      <div class="cards-container">
        <div
          class="feature-card"
          :style="{
            background: themeColors.cardBackground,
            borderColor: themeColors.cardBorder
          }"
          @click="navigateTo('/knowledge')"
        >
          <div class="card-icon" :style="{ background: themeColors.cardIcon }">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <h3 class="card-title" :style="{ color: themeColors.cardTitle }">知识库管理</h3>
          <p class="card-description" :style="{ color: themeColors.cardDescription }">上传、管理和检索军事文档资料</p>
          <div class="card-arrow" :style="{ color: themeColors.cardIcon }">→</div>
        </div>

        <div
          class="feature-card"
          :style="{
            background: themeColors.cardBackground,
            borderColor: themeColors.cardBorder
          }"
          @click="navigateTo('/chat')"
        >
          <div class="card-icon" :style="{ background: themeColors.cardIcon }">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <h3 class="card-title" :style="{ color: themeColors.cardTitle }">知识问答</h3>
          <p class="card-description" :style="{ color: themeColors.cardDescription }">智能问答系统，快速获取军事知识</p>
          <div class="card-arrow" :style="{ color: themeColors.cardIcon }">→</div>
        </div>

        <div
          class="feature-card"
          :style="{
            background: themeColors.cardBackground,
            borderColor: themeColors.cardBorder
          }"
          @click="navigateTo('/document')"
        >
          <div class="card-icon" :style="{ background: themeColors.cardIcon }">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <h3 class="card-title" :style="{ color: themeColors.cardTitle }">文档生成</h3>
          <p class="card-description" :style="{ color: themeColors.cardDescription }">AI 辅助生成高质量军事文档</p>
          <div class="card-arrow" :style="{ color: themeColors.cardIcon }">→</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()

const navigateTo = (path: string) => {
  router.push(path)
}

const toggleTheme = () => {
  appStore.toggleTheme()
}

// 根据主题返回不同的配色方案
const themeColors = computed(() => {
  if (appStore.isDark) {
    // 深色主题配色
    return {
      background: '#000000',
      title: '#ffffff',
      subtitle: '#e0e0e0',
      description: 'rgba(255, 255, 255, 0.8)',
      orb1: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      orb2: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      orb3: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      cardBackground: 'rgba(45, 45, 45, 0.8)',
      cardBorder: 'rgba(255, 255, 255, 0.1)',
      cardTitle: '#e2e8f0',
      cardDescription: '#a0aec0',
      cardIcon: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }
  } else {
    // 浅色主题配色
    return {
      background: '#ffffff',
      title: '#1a1a1a',
      subtitle: '#333333',
      description: 'rgba(0, 0, 0, 0.7)',
      orb1: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      orb2: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      orb3: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      cardBackground: 'rgba(245, 245, 245, 0.8)',
      cardBorder: 'rgba(0, 0, 0, 0.1)',
      cardTitle: '#1a202c',
      cardDescription: '#718096',
      cardIcon: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }
  }
})
</script>

<style scoped>
.home-container {
  position: relative;
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: background 0.3s ease;
}

/* 主题切换按钮 */
.theme-toggle {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 100;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

/* 背景装饰球 */
.background-decoration {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.6;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 400px;
  height: 400px;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 350px;
  height: 350px;
  bottom: -100px;
  right: -50px;
  animation-delay: -5s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  top: 50%;
  left: 50%;
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}

/* 内容区域 */
.content-wrapper {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 40px 20px;
  max-width: 1200px;
}

/* 标题区域 */
.title-section {
  margin-bottom: 80px;
}

.main-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 16px;
  letter-spacing: 2px;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  animation: fadeInUp 0.8s ease-out;
}

.sub-title {
  font-size: 2.5rem;
  font-weight: 600;
  margin-bottom: 24px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  animation: fadeInUp 0.8s ease-out 0.2s backwards;
}

.description {
  font-size: 1.1rem;
  margin-top: 16px;
  animation: fadeInUp 0.8s ease-out 0.4s backwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 卡片容器 */
.cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 32px;
  max-width: 1000px;
  margin: 0 auto;
}

/* 功能卡片 */
.feature-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 48px 32px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  animation: fadeInUp 0.8s ease-out 0.6s backwards;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s ease;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}

.feature-card:hover::before {
  transform: scaleX(1);
}

.card-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: transform 0.3s ease;
}

.feature-card:hover .card-icon {
  transform: scale(1.1) rotate(5deg);
}

.card-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 12px;
}

.card-description {
  font-size: 0.95rem;
  color: #718096;
  line-height: 1.6;
}

.card-arrow {
  position: absolute;
  top: 24px;
  right: 24px;
  font-size: 1.5rem;
  color: #667eea;
  font-weight: bold;
  opacity: 0;
  transform: translateX(-10px);
  transition: all 0.3s ease;
}

.feature-card:hover .card-arrow {
  opacity: 1;
  transform: translateX(0);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-title {
    font-size: 2rem;
  }

  .sub-title {
    font-size: 1.5rem;
  }

  .cards-container {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .feature-card {
    padding: 32px 24px;
  }
}
</style>
