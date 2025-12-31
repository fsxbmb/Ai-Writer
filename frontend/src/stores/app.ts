import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const loading = ref(false)

  // 主题管理
  const theme = ref<'light' | 'dark' | null>(null)
  const isDark = ref(false)

  // 从 localStorage 读取主题设置
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark' || savedTheme === 'light') {
    theme.value = savedTheme
    isDark.value = savedTheme === 'dark'
  } else {
    // 检测系统主题
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    theme.value = prefersDark ? 'dark' : 'light'
    isDark.value = prefersDark
  }

  // 监听主题变化并同步到 DOM 和 localStorage
  watch(theme, (newTheme) => {
    if (newTheme) {
      isDark.value = newTheme === 'dark'
      localStorage.setItem('theme', newTheme)
      // 更新 HTML class
      if (newTheme === 'dark') {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    }
  })

  function toggleTheme() {
    theme.value = isDark.value ? 'light' : 'dark'
  }

  function setTheme(newTheme: 'light' | 'dark') {
    theme.value = newTheme
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setSidebarCollapsed(collapsed: boolean) {
    sidebarCollapsed.value = collapsed
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  return {
    sidebarCollapsed,
    loading,
    theme,
    isDark,
    toggleTheme,
    setTheme,
    toggleSidebar,
    setSidebarCollapsed,
    setLoading,
  }
})
